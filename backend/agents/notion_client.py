"""
Notion Integration - syncs extracted tasks to the Tasks Tracker database.
Database: https://www.notion.so/30a4529e75ee80b08e33e1d6c582a95c
Properties: Task name, Status, Priority, Due date, Description, Department, Assignee
"""
from __future__ import annotations
import httpx
from datetime import datetime
from ..config import NOTION_API_KEY, NOTION_DATABASE_ID

# Module-level cache of workspace members: [{id, name}]
_workspace_members: list = []


async def _load_workspace_members() -> list:
    """Fetch and cache Notion workspace members (persons only)."""
    global _workspace_members
    if _workspace_members:
        return _workspace_members
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{NOTION_BASE}/users",
            headers={
                "Authorization": f"Bearer {NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
            },
        )
        if r.status_code == 200:
            _workspace_members = [
                {"id": u["id"], "name": u.get("name", "").lower()}
                for u in r.json().get("results", [])
                if u.get("type") == "person"
            ]
    return _workspace_members


def _match_owner_to_user_id(owner: str, members: list) -> str | None:
    """Fuzzy-match an owner name string to a Notion user ID.
    Matches on first name, last name, or full name (case-insensitive).
    Returns user ID string or None if no match.
    """
    if not owner or not members:
        return None
    owner_lower = owner.lower().strip()
    # Exact match first
    for m in members:
        if m["name"] == owner_lower:
            return m["id"]
    # Partial: owner is substring of member name or vice versa
    for m in members:
        if owner_lower in m["name"] or m["name"].split()[0] in owner_lower:
            return m["id"]
    return None

NOTION_VERSION = "2022-06-28"
NOTION_BASE = "https://api.notion.com/v1"

STATUS_MAP = {
    "pending": "Not started",
    "in_progress": "In progress",
    "done": "Done",
}

# Emoji prefix for task name display
DEPT_TAG = {
    "engineering": "⚙️ Engineering",
    "hr": "👥 HR",
    "marcom": "📣 MarCom",
    "innovation": "🚀 Innovation",
}

# Must exactly match multi_select option names in the Notion Tasks Tracker database
DEPT_SELECT = {
    "engineering": "Engineering",
    "hr": "HR",
    "marcom": "Marketing & Comms",
    "innovation": "Industry Innovation",
}


def _headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def create_task(
    description: str,
    owner: str,
    deadline: str,
    status: str = "pending",
    meeting_title: str = "",
    priority: str = "Medium",
    task_id: str = "",
    department: str = "engineering",
    members: list = None,
    database_id: str = None,
) -> dict:
    """Create a single task in the Notion Tasks Tracker database."""
    # Use department-specific database ID or fall back to global config
    db_id = database_id or NOTION_DATABASE_ID
    if not db_id:
        raise ValueError("No Notion database ID configured for this department")

    dept_label = DEPT_TAG.get(department, department.title())
    task_name = f"[{dept_label}] {description}"

    # Build properties payload matching the existing database schema
    properties = {
        "Task name": {
            "title": [{"text": {"content": task_name}}]
        },
        "Status": {
            "status": {"name": STATUS_MAP.get(status, "Not started")}
        },
        "Priority": {
            "select": {"name": priority}
        },
        "Department": {
            "multi_select": [{"name": DEPT_SELECT.get(department, department.title())}]
        },
        "Description": {
            "rich_text": [
                {
                    "text": {
                        "content": f"Owner: {owner} | Meeting: {meeting_title} | ID: {task_id}"
                    }
                }
            ]
        },
    }

    # Assignee: fuzzy-match owner name to a Notion workspace user
    if members:
        user_id = _match_owner_to_user_id(owner, members)
        if user_id:
            properties["Assignee"] = {"people": [{"id": user_id}]}

    # Add due date only if it's a real date (not "Not specified" or "Friday")
    if deadline and deadline not in ("Not specified", "not specified", ""):
        # Try to parse natural deadlines; store as text in description if unparseable
        iso_date = _try_parse_date(deadline)
        if iso_date:
            properties["Due date"] = {"date": {"start": iso_date}}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{NOTION_BASE}/pages",
            headers=_headers(),
            json={
                "parent": {"database_id": db_id},
                "properties": properties,
            },
        )
        response.raise_for_status()
        data = response.json()
        return {
            "ok": True,
            "notion_page_id": data["id"],
            "notion_url": data.get("url", ""),
        }


async def sync_tasks(tasks: list[dict], meeting_title: str = "", department: str = "engineering", database_id: str = None) -> dict:
    """
    Sync a list of extracted tasks to Notion.
    Returns summary including per-task notion_url keyed by task_id.
    """
    if not NOTION_API_KEY:
        return {"ok": False, "error": "Notion API key not configured"}

    # Get department-specific database ID from org_context if not provided
    db_id = database_id
    if not db_id:
        from .memory_store import get_org_context
        org_context = get_org_context(department)
        db_id = org_context.get("notion_database_id") or NOTION_DATABASE_ID

    if not db_id:
        return {"ok": False, "error": f"No Notion database configured for {department} department"}

    created = []
    failed = []
    # task_id → notion_url mapping for storing back in SQLite
    url_map = {}

    # Load workspace members once for Assignee matching
    members = []
    try:
        members = await _load_workspace_members()
        print(f"[Notion] Loaded {len(members)} workspace members for Assignee matching")
    except Exception as e:
        print(f"[Notion] Could not load workspace members: {e}")

    for task in tasks:
        try:
            result = await create_task(
                description=task.get("description", ""),
                owner=task.get("owner", "Unassigned"),
                deadline=task.get("deadline", ""),
                status=task.get("status", "pending"),
                meeting_title=meeting_title,
                priority="Medium",
                task_id=task.get("id", ""),
                department=department,
                members=members,
                database_id=db_id,
            )
            tid = task.get("id", "")
            created.append({
                "task_id": tid,
                "description": task["description"],
                "notion_url": result["notion_url"],
                "notion_page_id": result["notion_page_id"],
            })
            if tid:
                url_map[tid] = result["notion_url"]
        except Exception as e:
            err = str(e)
            print(f"[Notion] FAILED to create task '{task.get('description','')}': {err}")
            failed.append({"description": task.get("description", ""), "error": err})

    print(f"[Notion] Sync complete: {len(created)} created, {len(failed)} failed (dept={department})")
    return {
        "ok": True,
        "created": len(created),
        "failed": len(failed),
        "pages": created,
        "url_map": url_map,
        "database_url": f"https://www.notion.so/{db_id.replace('-', '')}",
    }


async def update_task_status(notion_page_id: str, status: str) -> dict:
    """Update the status of an existing Notion task page."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(
            f"{NOTION_BASE}/pages/{notion_page_id}",
            headers=_headers(),
            json={
                "properties": {
                    "Status": {
                        "status": {"name": STATUS_MAP.get(status, "Not started")}
                    }
                }
            },
        )
        response.raise_for_status()
        return {"ok": True}


def _try_parse_date(deadline: str):
    """Try to convert a deadline string to ISO date format (YYYY-MM-DD)."""
    deadline = deadline.strip()

    # Already ISO format
    if len(deadline) == 10 and deadline[4] == "-":
        return deadline

    # Month Day format: "March 12th", "March 12"
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }
    lower = deadline.lower()
    for month_name, month_num in months.items():
        if month_name in lower:
            # Extract day number
            import re
            day_match = re.search(r"\d+", lower)
            if day_match:
                day = int(day_match.group())
                year = datetime.utcnow().year
                try:
                    return f"{year}-{month_num:02d}-{day:02d}"
                except Exception:
                    return None

    # Relative: "Friday", "next Monday" → not parseable to exact date, skip
    return None
