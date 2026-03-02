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


async def _load_workspace_members(force_refresh: bool = False) -> list:
    """Fetch and cache Notion workspace members (persons only)."""
    global _workspace_members
    if _workspace_members and not force_refresh:
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
            _workspace_members = []
            for u in r.json().get("results", []):
                if u.get("type") == "person":
                    # Get email from person object if available
                    email = u.get("person", {}).get("email", "").lower()
                    _workspace_members.append({
                        "id": u["id"],
                        "name": u.get("name", "").lower(),
                        "email": email,
                    })
            # Log workspace members for debugging
            member_info = [(m["name"], m["email"]) for m in _workspace_members]
            print(f"[Notion] Workspace members found: {member_info}")
    return _workspace_members


def _match_owner_to_user_id(owner: str, members: list) -> str | None:
    """Fuzzy-match an owner name string to a Notion user ID.
    Matches on first name, last name, full name, or email (case-insensitive).
    Returns user ID string or None if no match.
    """
    if not owner or not members:
        return None
    owner_lower = owner.lower().strip()

    # 1. Exact name match
    for m in members:
        if m["name"] == owner_lower:
            print(f"[Notion] Matched owner '{owner}' -> '{m['name']}' (exact name)")
            return m["id"]

    # 2. Email match (if owner looks like an email or contains it)
    for m in members:
        member_email = m.get("email", "")
        if member_email:
            # Match full email or email username (before @)
            email_user = member_email.split("@")[0]
            if owner_lower == member_email or owner_lower == email_user:
                print(f"[Notion] Matched owner '{owner}' -> '{m['name']}' (email)")
                return m["id"]
            # Match if owner name appears in email
            if owner_lower.replace(" ", ".") in member_email or owner_lower.replace(" ", "") in member_email:
                print(f"[Notion] Matched owner '{owner}' -> '{m['name']}' (email contains name)")
                return m["id"]

    # 3. First name match
    for m in members:
        member_first = m["name"].split()[0] if m["name"] else ""
        owner_first = owner_lower.split()[0] if owner_lower else ""
        if member_first and owner_first and (member_first == owner_first or owner_first == member_first):
            print(f"[Notion] Matched owner '{owner}' -> '{m['name']}' (first name)")
            return m["id"]

    # 4. Partial name match: owner is substring of member name or vice versa
    for m in members:
        if owner_lower in m["name"] or m["name"] in owner_lower:
            print(f"[Notion] Matched owner '{owner}' -> '{m['name']}' (partial)")
            return m["id"]

    print(f"[Notion] No match found for owner '{owner}' in {[(m['name'], m.get('email', '')) for m in members]}")
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

    # Build properties payload matching the database schema
    properties = {
        "Name": {
            "title": [{"text": {"content": task_name}}]
        },
        "Task Status": {
            "select": {"name": STATUS_MAP.get(status, "Not started")}
        },
        "Priority": {
            "select": {"name": priority}
        },
        "Department": {
            "select": {"name": DEPT_SELECT.get(department, department.title())}
        },
        "Owner": {
            "rich_text": [{"text": {"content": owner or "Unassigned"}}]
        },
        "Description": {
            "rich_text": [
                {
                    "text": {
                        "content": f"Meeting: {meeting_title} | ID: {task_id}"
                    }
                }
            ]
        },
    }

    # Assignee: fuzzy-match owner name to a Notion workspace user (if workspace has members)
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
        # Handle missing property errors gracefully
        if response.status_code == 400:
            error_detail = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = error_detail.get("message", "")

            # If Assignee property doesn't exist, retry without it
            if "Assignee is not a property" in error_msg and "Assignee" in properties:
                print(f"[Notion] Assignee property not found in database, retrying without it")
                del properties["Assignee"]
                response = await client.post(
                    f"{NOTION_BASE}/pages",
                    headers=_headers(),
                    json={
                        "parent": {"database_id": db_id},
                        "properties": properties,
                    },
                )

        if response.status_code >= 400:
            error_detail = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            print(f"[Notion] API Error {response.status_code}: {error_detail}")
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
    # task_id → notion_url and notion_page_id mappings for storing back in SQLite
    url_map = {}
    page_id_map = {}

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
                page_id_map[tid] = result["notion_page_id"]
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
        "page_id_map": page_id_map,
        "database_url": f"https://www.notion.so/{db_id.replace('-', '')}",
    }


async def update_task_status(notion_page_id: str, status: str) -> dict:
    """Update the status of an existing Notion task page."""
    if not notion_page_id:
        return {"ok": False, "error": "No Notion page ID provided"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(
            f"{NOTION_BASE}/pages/{notion_page_id}",
            headers=_headers(),
            json={
                "properties": {
                    "Task Status": {
                        "select": {"name": STATUS_MAP.get(status, "Not started")}
                    }
                }
            },
        )
        response.raise_for_status()
        return {"ok": True}


async def update_task(
    notion_page_id: str,
    description: str = None,
    owner: str = None,
    deadline: str = None,
    status: str = None,
    priority: str = None,
    department: str = None,
) -> dict:
    """Update an existing Notion task page with any changed fields."""
    if not notion_page_id:
        return {"ok": False, "error": "No Notion page ID provided"}

    properties = {}

    if description is not None:
        dept_label = DEPT_TAG.get(department, department.title() if department else "")
        task_name = f"[{dept_label}] {description}" if dept_label else description
        properties["Name"] = {"title": [{"text": {"content": task_name}}]}

    if status is not None:
        properties["Task Status"] = {"select": {"name": STATUS_MAP.get(status, "Not started")}}

    if priority is not None:
        properties["Priority"] = {"select": {"name": priority}}

    if department is not None:
        properties["Department"] = {"select": {"name": DEPT_SELECT.get(department, department.title())}}

    if deadline is not None and deadline not in ("Not specified", "not specified", ""):
        iso_date = _try_parse_date(deadline)
        if iso_date:
            properties["Due date"] = {"date": {"start": iso_date}}

    if owner is not None:
        # Update description field with new owner info
        members = await _load_workspace_members()
        user_id = _match_owner_to_user_id(owner, members)
        if user_id:
            properties["Assignee"] = {"people": [{"id": user_id}]}

    if not properties:
        return {"ok": True, "message": "No fields to update"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(
            f"{NOTION_BASE}/pages/{notion_page_id}",
            headers=_headers(),
            json={"properties": properties},
        )
        response.raise_for_status()
        return {"ok": True, "updated_properties": list(properties.keys())}


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
