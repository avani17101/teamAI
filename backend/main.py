"""
TeamAI - Department Intelligence System
FastAPI backend: handles meeting ingestion, chat Q&A, task management.
K2-Think-V2 = reasoning brain | K2-V2-Instruct = Q&A | OpenClaw = execution
"""
from __future__ import annotations
import uuid
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agents.extraction_agent import extract_meeting, detect_cross_meeting_insights
from .agents.departments import list_departments, get_department
from .agents.memory_store import (
    init_db, save_meeting, get_all_tasks, get_all_meetings,
    get_meeting_by_id, update_task_status, update_task_notion_urls,
    get_department_state, search_memory,
    save_team_member, get_team_members, delete_team_member,
    get_org_context, save_org_context,
    get_task_by_id, update_task as db_update_task,
)
from .agents.query_agent import answer_question
from .agents.openclaw_client import openclaw
from .agents.notion_client import (
    sync_tasks as notion_sync_tasks,
    update_task_status as notion_update_status,
    update_task as notion_update_task,
)
from .agents.telegram_client import send_due_reminders as telegram_send_reminders, check_bot_status, send_task_assigned
from .agents.email_client import send_task_email, send_due_reminders as email_send_reminders
from .agents.opportunity_extractor import (
    is_opportunity_email, process_opportunity_email,
    get_all_opportunities, update_opportunity_status, export_to_excel as export_opportunities_excel
)
from .models.schemas import (
    MeetingUploadRequest, ChatRequest, ChatResponse,
    TaskUpdateRequest, FullTaskUpdateRequest, NotionSyncRequest,
    TeamMemberRequest, OrgContextRequest, NotificationRequest
)

app = FastAPI(
    title="TeamAI - Department Intelligence System",
    description="AI that attends meetings, understands decisions, and becomes the interface to team knowledge.",
    version="1.0.0",
)

from .config import CORS_ORIGINS, ENV

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


def _find_member(owner: str, team: list[dict]) -> Optional[dict]:
    """Fuzzy-match a task owner name to a team member record."""
    if not owner or not team:
        return None
    owner_lower = owner.lower().strip()
    # Exact match
    for m in team:
        if m["name"].lower() == owner_lower:
            return m
    # Partial: owner is substring of name or vice versa (handles first-name-only)
    for m in team:
        name_lower = m["name"].lower()
        if owner_lower in name_lower or name_lower.split()[0] in owner_lower:
            return m
    return None


@app.on_event("startup")
async def startup():
    """Initialize DB and check OpenClaw availability."""
    init_db()
    available = await openclaw.check_health()
    print(f"[TeamAI] OpenClaw gateway: {'CONNECTED' if available else 'not running (fallback mode)'}")
    print("[TeamAI] K2-Think-V2 + K2-V2-Instruct ready")

    # Start email forwarding service if configured
    from .config import TEAMAI_EMAIL, TEAMAI_EMAIL_PASSWORD
    if TEAMAI_EMAIL and TEAMAI_EMAIL_PASSWORD and TEAMAI_EMAIL_PASSWORD != "PUT_YOUR_16_CHAR_APP_PASSWORD_HERE":
        from .agents.email_forwarder import EmailForwarder, process_forwarded_email

        forwarder = EmailForwarder(
            email_address=TEAMAI_EMAIL,
            password=TEAMAI_EMAIL_PASSWORD
        )

        async def handle_email(email_data):
            """Process forwarded emails - route to department based on sender and subject"""
            sender_email = email_data['sender']['email'].lower()
            subject = email_data['subject'].lower()

            # First check if this is an opportunity email (Call for Interest, CFP, etc.)
            if is_opportunity_email(email_data['subject'], email_data.get('body', '')):
                print(f"[EmailForwarder] Detected OPPORTUNITY email: {email_data['subject']}")
                try:
                    opp_result = await process_opportunity_email(email_data, department="innovation")
                    if opp_result.get("is_opportunity"):
                        print(f"[EmailForwarder] Saved opportunity {opp_result['opportunity_id']}")
                        print(f"[EmailForwarder] Extracted: {opp_result['extraction'].get('title')}")
                        print(f"[EmailForwarder] Deadline: {opp_result['extraction'].get('deadline')}")
                        # Send confirmation email for opportunity with Excel attachment
                        from .agents.email_forwarder import send_processing_confirmation
                        try:
                            extraction_for_reply = {
                                "tasks_count": 1,
                                "decisions_count": 0,
                                "risks_count": 0,
                                "summary": f"Opportunity detected: {opp_result['extraction'].get('title')}\n\nDeadline: {opp_result['extraction'].get('deadline')}\nOrganization: {opp_result['extraction'].get('organization')}\n\nThis has been added to the opportunities tracker. See attached Excel for all opportunities.",
                                "extraction": None,
                            }
                            # Attach the opportunities Excel file
                            excel_path = Path(__file__).parent.parent / "data" / "opportunities.xlsx"
                            send_processing_confirmation(
                                to_email=email_data['sender']['email'],
                                original_subject=email_data['subject'],
                                extraction_result=extraction_for_reply,
                                attachment_path=str(excel_path) if excel_path.exists() else None,
                            )
                        except Exception as reply_err:
                            print(f"[EmailForwarder] Opportunity confirmation failed: {reply_err}")
                        return  # Don't process as regular meeting
                except Exception as opp_err:
                    print(f"[EmailForwarder] Opportunity processing failed: {opp_err}")
                    # Fall through to regular processing

            # Check subject for department tags: [Innovation], [MarCom], etc.
            dept_from_subject = None
            if '[innovation]' in subject or '[innov]' in subject:
                dept_from_subject = 'innovation'
            elif '[marcom]' in subject or '[marketing]' in subject:
                dept_from_subject = 'marcom'
            elif '[engineering]' in subject or '[eng]' in subject:
                dept_from_subject = 'engineering'
            elif '[hr]' in subject:
                dept_from_subject = 'hr'
            elif '[sales]' in subject:
                dept_from_subject = 'sales'
            elif '[product]' in subject:
                dept_from_subject = 'product'

            # Map emails to default departments
            email_to_dept = {
                "avani.gupta@mbzuai.ac.ae": "innovation",  # Avani's primary dept
                "ramzi.benouaghrem@mbzuai.ac.ae": "innovation",  # Ramzi
                # Add more team members as needed
            }

            # Priority: Subject tag > Email mapping > Default to engineering
            if dept_from_subject:
                department = dept_from_subject
                print(f"[EmailForwarder] Routing via subject tag → {department} department")
            else:
                department = email_to_dept.get(sender_email, "engineering")
                print(f"[EmailForwarder] Routing {sender_email} → {department} department")

            try:
                result = await process_forwarded_email(email_data, department=department)
                print(f"[EmailForwarder] Processed email '{email_data['subject']}' → Meeting ID: {result['meeting_id']}")

                # Send auto-reply with summary and Notion link
                from .agents.email_forwarder import send_processing_confirmation
                from .agents.memory_store import get_org_context

                # Get Notion database URL for this department
                org_context = get_org_context(department)
                notion_db_id = org_context.get("notion_database_id", "")
                notion_url = None
                if notion_db_id:
                    notion_url = f"https://www.notion.so/{notion_db_id.replace('-', '')}"

                # Send confirmation email
                try:
                    sent = send_processing_confirmation(
                        to_email=email_data['sender']['email'],
                        original_subject=email_data['subject'],
                        extraction_result=result,
                        notion_database_url=notion_url
                    )
                    if sent:
                        print(f"[EmailForwarder] Sent confirmation to {email_data['sender']['email']}")
                    else:
                        print(f"[EmailForwarder] Failed to send confirmation to {email_data['sender']['email']}")
                except Exception as reply_error:
                    print(f"[EmailForwarder] Error sending confirmation: {reply_error}")

            except Exception as e:
                print(f"[EmailForwarder] Failed to process email: {e}")

        # Start polling in background
        asyncio.create_task(forwarder.poll_inbox(interval=30, callback=handle_email))
        print(f"[EmailForwarder] Started polling {TEAMAI_EMAIL} every 30 seconds")
    else:
        print("[EmailForwarder] Skipped - email credentials not configured")

    # Start daily task reminder scheduler
    async def daily_reminder_scheduler():
        """Send task due reminders every day at 9 AM"""
        import time
        from datetime import datetime, timedelta

        while True:
            now = datetime.now()
            # Calculate next 9 AM
            next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if now.hour >= 9:
                next_run += timedelta(days=1)

            # Wait until next 9 AM
            sleep_seconds = (next_run - now).total_seconds()
            print(f"[Reminders] Next daily reminder check at {next_run.strftime('%Y-%m-%d %I:%M %p')}")
            await asyncio.sleep(sleep_seconds)

            # Send reminders for tasks due today or tomorrow (1 day ahead)
            try:
                all_tasks = get_all_tasks()
                all_members = get_team_members()

                result = await email_send_reminders(
                    tasks=all_tasks,
                    team_members=all_members,
                    days_ahead=1  # Tasks due today or tomorrow
                )

                if result.get("sent", 0) > 0:
                    print(f"[Reminders] Sent {result['sent']} reminder emails for {result['tasks_mentioned']} tasks")
                    print(f"[Reminders] Recipients: {', '.join(result.get('recipients', []))}")
                else:
                    print(f"[Reminders] No reminders sent: {result.get('reason', 'No tasks due')}")

            except Exception as e:
                print(f"[Reminders] Error sending daily reminders: {e}")

    asyncio.create_task(daily_reminder_scheduler())
    print("[Reminders] Daily reminder scheduler started (runs at 9 AM)")


@app.get("/")
async def root():
    index = frontend_path / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "TeamAI API running. See /docs for API reference."}


# ──────────────────────────────────────────────────────
# MEETINGS
# ──────────────────────────────────────────────────────

@app.post("/api/meetings/upload")
async def upload_meeting(request: MeetingUploadRequest):
    """
    Upload a meeting transcript.
    K2-Think-V2 extracts tasks, decisions, risks.
    OpenClaw writes meeting notes to its workspace.
    Cross-meeting insights are generated automatically.
    """
    if len(request.transcript.strip()) < 50:
        raise HTTPException(400, "Transcript too short (minimum 50 characters)")

    # Extract structured data with K2-Think-V2
    try:
        extraction, summary, task_updates = await extract_meeting(
            transcript=request.transcript,
            title=request.title,
            department=request.department,
            detect_updates=True,
        )
    except Exception as e:
        raise HTTPException(500, f"Extraction failed: {str(e)}")

    # Process task updates detected from transcript
    updated_tasks = []
    for update_info in task_updates:
        task_id = update_info["task_id"]
        updates = update_info["updates"]
        try:
            # Update in local DB
            db_update_task(task_id, updates)

            # Get the task to sync to Notion
            task = get_task_by_id(task_id)
            if task and task.get("notion_page_id"):
                await notion_update_task(
                    notion_page_id=task["notion_page_id"],
                    description=updates.get("description"),
                    owner=updates.get("owner"),
                    deadline=updates.get("deadline"),
                    status=updates.get("status"),
                    department=request.department,
                )
            updated_tasks.append({
                "task_id": task_id,
                "updates": updates,
                "notion_synced": bool(task and task.get("notion_page_id"))
            })
        except Exception as e:
            print(f"[TaskUpdate] Failed to update task {task_id}: {e}")

    # Assign IDs to extracted items
    meeting_id = str(uuid.uuid4())
    for task in extraction.tasks:
        task.id = str(uuid.uuid4())
        task.meeting_id = meeting_id
        task.created_at = datetime.utcnow().isoformat()
    for decision in extraction.decisions:
        decision.id = str(uuid.uuid4())
        decision.meeting_id = meeting_id
    for risk in extraction.risks:
        risk.id = str(uuid.uuid4())
        risk.meeting_id = meeting_id

    # Save to memory (SQLite + Chroma)
    saved_id = save_meeting(
        title=request.title,
        transcript=request.transcript,
        summary=summary,
        extraction=extraction,
        department=request.department,
    )

    # OpenClaw: write meeting notes to workspace + sync task board
    board_result = await openclaw.sync_tasks_to_board([
        {
            "id": t.id,
            "description": t.description,
            "owner": t.owner,
            "deadline": t.deadline,
            "status": t.status,
            "meeting_id": saved_id,
            "meeting_title": request.title,
        }
        for t in extraction.tasks
    ])

    await openclaw.write_meeting_summary(
        meeting_id=saved_id,
        title=request.title,
        summary=summary,
        extraction={
            "tasks": [t.dict() for t in extraction.tasks],
            "decisions": [d.dict() for d in extraction.decisions],
            "risks": [r.dict() for r in extraction.risks],
        },
    )

    # Notion: sync tasks to Tasks Tracker database (unless HITL review mode)
    notion_result = {"ok": False, "created": 0, "pages": [], "url_map": {}, "skipped": False}
    if request.auto_sync_notion:
        notion_result = await notion_sync_tasks(
            tasks=[t.dict() for t in extraction.tasks],
            meeting_title=request.title,
            department=request.department,
        )
        # Persist Notion page URLs and IDs back to SQLite
        if notion_result.get("ok") and notion_result.get("url_map"):
            update_task_notion_urls(
                notion_result["url_map"],
                notion_result.get("page_id_map", {})
            )
    else:
        notion_result = {"ok": False, "skipped": True, "message": "HITL review mode — select tasks to sync"}

    # Cross-meeting insights (K2-Think-V2 reasoning across meetings)
    all_meetings = get_all_meetings()
    insights = []
    if len(all_meetings) > 1:
        previous = [
            {
                "title": m["title"],
                "summary": m.get("summary", ""),
                "tasks": [t for t in get_all_tasks() if t["meeting_id"] == m["id"]],
            }
            for m in all_meetings[1:6]  # skip current, use last 5
        ]
        try:
            insights = await detect_cross_meeting_insights(extraction, previous)
        except Exception:
            insights = []

    # Personalized task dispatch + stakeholder detection
    # In HITL mode (auto_sync_notion=false): skip emails/notifications, just track owners
    team = get_team_members(department=request.department)
    dispatch_log = []
    unknown_stakeholders = []
    team_names_lower = {m["name"].lower() for m in team}

    for task in extraction.tasks:
        owner = (task.owner or "").strip()
        if not owner or owner.lower() in ("unassigned", "team", "everyone", ""):
            continue
        member = _find_member(owner, team)
        if member:
            sent_telegram = False
            sent_email = False
            task_dict = task.dict()
            task_dict["department"] = request.department

            # Only send notifications in auto mode, skip in HITL review mode
            if request.auto_sync_notion:
                if member.get("telegram_handle"):
                    try:
                        sent_telegram = await send_task_assigned(member, task_dict, request.title)
                    except Exception:
                        sent_telegram = False
                if member.get("email"):
                    try:
                        sent_email = await send_task_email(member, task_dict, request.title)
                    except Exception:
                        sent_email = False

            dispatch_log.append({
                "task": task.description,
                "owner": owner,
                "member_found": True,
                "telegram": sent_telegram,
                "email": sent_email,
                "skipped_hitl": not request.auto_sync_notion,
            })
        else:
            dispatch_log.append({"task": task.description, "owner": owner, "member_found": False})
            # Flag if not a generic role word
            if not any(owner.lower() in tn or tn in owner.lower() for tn in team_names_lower):
                if owner not in unknown_stakeholders:
                    unknown_stakeholders.append(owner)

    dept_info = get_department(request.department)
    return {
        "meeting_id": saved_id,
        "title": request.title,
        "department": request.department,
        "department_name": dept_info["name"],
        "department_icon": dept_info["icon"],
        "summary": summary,
        "extraction": {
            "tasks": [t.dict() for t in extraction.tasks],
            "decisions": [d.dict() for d in extraction.decisions],
            "risks": [r.dict() for r in extraction.risks],
        },
        "task_updates": updated_tasks,  # Tasks updated from transcript mentions
        "cross_meeting_insights": insights,
        "task_board": board_result,
        "notion": notion_result,
        "openclaw_active": openclaw.available,
        "dispatch": dispatch_log,
        "unknown_stakeholders": unknown_stakeholders,
    }


@app.get("/api/departments")
async def get_departments():
    """List all available departments with their metadata and sample transcripts."""
    from .agents.departments import DEPARTMENTS
    return {"departments": list_departments(), "samples": {k: v["sample_transcript"] for k, v in DEPARTMENTS.items()}}


@app.get("/api/meetings")
async def list_meetings(department: Optional[str] = None):
    """List all processed meetings, optionally filtered by department."""
    meetings = get_all_meetings(department=department)
    return {"meetings": meetings, "total": len(meetings)}


@app.get("/api/meetings/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Get full meeting details including tasks, decisions, risks."""
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting


# ──────────────────────────────────────────────────────
# TASKS
# ──────────────────────────────────────────────────────

@app.get("/api/tasks")
async def list_tasks(status: Optional[str] = None, department: Optional[str] = None):
    """List all tasks. Filter by status and/or department."""
    tasks = get_all_tasks(status=status, department=department)
    return {"tasks": tasks, "total": len(tasks)}


@app.patch("/api/tasks/{task_id}")
async def update_task_endpoint(task_id: str, request: TaskUpdateRequest):
    """Update task status and sync to OpenClaw task board and Notion."""
    # Get the task first to check if it has a Notion page
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    # Update in SQLite
    success = update_task_status(task_id, request.status)
    if not success:
        raise HTTPException(500, "Failed to update task")

    # Sync update to OpenClaw board
    await openclaw.update_task_status_on_board(task_id, request.status)

    # Sync update to Notion if task has a Notion page
    notion_result = {"synced": False}
    if task.get("notion_page_id"):
        try:
            notion_result = await notion_update_status(task["notion_page_id"], request.status)
            notion_result["synced"] = notion_result.get("ok", False)
        except Exception as e:
            notion_result = {"synced": False, "error": str(e)}

    return {
        "ok": True,
        "task_id": task_id,
        "status": request.status,
        "notion": notion_result
    }


@app.put("/api/tasks/{task_id}")
async def full_update_task(task_id: str, request: FullTaskUpdateRequest):
    """
    Full task update - update any task fields and sync changes to Notion.
    This enables updating tasks based on meeting transcript mentions.
    """
    # Get the task first
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    # Build updates dict from non-None fields
    updates = {}
    if request.description is not None:
        updates["description"] = request.description
    if request.owner is not None:
        updates["owner"] = request.owner
    if request.deadline is not None:
        updates["deadline"] = request.deadline
    if request.status is not None:
        updates["status"] = request.status

    if not updates:
        return {"ok": True, "task_id": task_id, "message": "No updates provided"}

    # Update in SQLite
    success = db_update_task(task_id, updates)
    if not success:
        raise HTTPException(500, "Failed to update task")

    # Sync update to OpenClaw board if status changed
    if request.status is not None:
        await openclaw.update_task_status_on_board(task_id, request.status)

    # Sync update to Notion if task has a Notion page
    notion_result = {"synced": False}
    if task.get("notion_page_id"):
        try:
            notion_result = await notion_update_task(
                notion_page_id=task["notion_page_id"],
                description=request.description,
                owner=request.owner,
                deadline=request.deadline,
                status=request.status,
                priority=request.priority,
                department=task.get("department"),
            )
            notion_result["synced"] = notion_result.get("ok", False)
        except Exception as e:
            notion_result = {"synced": False, "error": str(e)}

    return {
        "ok": True,
        "task_id": task_id,
        "updated_fields": list(updates.keys()),
        "notion": notion_result
    }


@app.post("/api/meetings/sync-notion")
async def sync_selected_to_notion(request: NotionSyncRequest):
    """
    HITL: Sync only the user-approved task IDs to Notion.
    Called from the frontend after the user reviews and checks tasks.
    Now also sends email notifications for approved tasks.
    """
    all_tasks = get_all_tasks()
    # Filter to only the approved task IDs
    tasks_to_sync = [t for t in all_tasks if t["id"] in request.task_ids]
    if not tasks_to_sync:
        raise HTTPException(400, "No matching tasks found for provided task_ids")

    # Sync to Notion with people tagging enabled
    notion_result = await notion_sync_tasks(
        tasks=tasks_to_sync,
        meeting_title=request.meeting_title,
        department=request.department,
        skip_tagging=False,  # Tag people when manually approved
    )
    if notion_result.get("ok") and notion_result.get("url_map"):
        update_task_notion_urls(
            notion_result["url_map"],
            notion_result.get("page_id_map", {})
        )

    # Send email notifications for approved tasks (was skipped in HITL extraction)
    team = get_team_members(department=request.department)
    dispatch_log = []
    for task in tasks_to_sync:
        owner = (task.get("owner") or "").strip()
        if not owner or owner.lower() in ("unassigned", "team", "everyone", ""):
            continue
        member = _find_member(owner, team)
        if member:
            sent_email = False
            task["department"] = request.department
            task["notion_url"] = notion_result.get("url_map", {}).get(task.get("id"), "")
            if member.get("email"):
                try:
                    sent_email = await send_task_email(member, task, request.meeting_title)
                except Exception:
                    sent_email = False
            dispatch_log.append({
                "task": task.get("description", ""),
                "owner": owner,
                "email": sent_email,
            })

    notion_result["dispatch"] = dispatch_log
    return notion_result


@app.get("/api/board")
async def get_task_board():
    """Get the live task board managed by OpenClaw."""
    board = await openclaw.get_task_board()
    return board


# ──────────────────────────────────────────────────────
# CHAT (Department Q&A)
# ──────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Ask the department AI a question.
    Uses K2-V2-Instruct + semantic memory (Chroma) + structured data (SQLite).
    Routes through OpenClaw agent if available for autonomous tool execution.
    """
    if not request.message.strip():
        raise HTTPException(400, "Message cannot be empty")

    history = [{"role": m.role, "content": m.content} for m in (request.history or [])]

    try:
        answer, sources, used_openclaw = await answer_question(
            question=request.message,
            history=history,
            use_openclaw=True,
            department=request.department,
        )
    except Exception as e:
        raise HTTPException(500, f"Query failed: {str(e)}")

    return ChatResponse(
        answer=answer,
        sources=sources,
        used_openclaw=used_openclaw,
    )


# ──────────────────────────────────────────────────────
# DEPARTMENT STATE
# ──────────────────────────────────────────────────────

@app.get("/api/state")
async def department_state(department: Optional[str] = None):
    """
    Get full department state snapshot.
    Pass ?department=engineering|hr|marcom|innovation to filter.
    """
    state = get_department_state(department=department)
    state["openclaw_active"] = openclaw.available
    return state


@app.get("/api/search")
async def search(q: str, n: int = 5, department: Optional[str] = None):
    """Semantic search over department memory, optionally filtered by department."""
    if not q.strip():
        raise HTTPException(400, "Query required")
    results = search_memory(q, n_results=n, department=department)
    return {"query": q, "results": results}


# ──────────────────────────────────────────────────────
# OPENCLAW STATUS
# ──────────────────────────────────────────────────────

@app.get("/api/openclaw/status")
async def openclaw_status():
    """Check OpenClaw gateway status."""
    available = await openclaw.check_health()
    return {
        "available": available,
        "base_url": openclaw.base_url,
        "agent_id": "department-ai",
        "message": "OpenClaw gateway connected" if available else "OpenClaw not running - using fallback mode",
    }


@app.post("/api/openclaw/execute")
async def openclaw_execute(payload: dict):
    """
    Execute an action via OpenClaw tools invoke.
    Supported: create_task, shell, file_write, notify
    """
    if not openclaw.available:
        raise HTTPException(503, "OpenClaw gateway not running. Start it with: openclaw dashboard")

    tool = payload.get("tool")
    args = payload.get("args", {})

    if not tool:
        raise HTTPException(400, "tool is required")

    try:
        result = await openclaw.invoke_tool(tool=tool, args=args)
        return {"ok": True, "result": result}
    except Exception as e:
        raise HTTPException(500, f"OpenClaw tool invocation failed: {str(e)}")


# ──────────────────────────────────────────────────────
# TELEGRAM REMINDERS
# ──────────────────────────────────────────────────────

@app.get("/api/reminders/status")
async def telegram_status():
    """Check Telegram bot configuration and connectivity."""
    return await check_bot_status()


@app.post("/api/telegram/reminders")
async def send_telegram_reminders(days: int = 2, department: Optional[str] = None):
    """
    Send a Telegram message listing tasks due within the next `days` days.
    Optionally filter by department.
    """
    tasks = get_all_tasks(department=department)
    result = await telegram_send_reminders(tasks, days_ahead=days)
    return result


# ──────────────────────────────────────────────────────
# TEAM MEMBERS
# ──────────────────────────────────────────────────────

@app.get("/api/team")
async def list_team(department: Optional[str] = None):
    """List all team members, optionally filtered by department."""
    members = get_team_members(department=department)
    return {"members": members, "total": len(members)}


@app.post("/api/team")
async def add_team_member(request: TeamMemberRequest):
    """Add a team member to the registry."""
    member_id = save_team_member(
        name=request.name,
        role=request.role,
        role_details=request.role_details,
        responsibilities=request.responsibilities,
        department=request.department,
        email=request.email,
        telegram_handle=request.telegram_handle,
    )
    return {"ok": True, "id": member_id}


@app.put("/api/team/{member_id}")
async def update_team_member(member_id: str, request: TeamMemberRequest):
    """Update an existing team member."""
    from .agents.memory_store import _get_db

    conn = _get_db()
    result = conn.execute(
        """UPDATE team_members
           SET name=?, role=?, role_details=?, responsibilities=?, department=?, email=?, telegram_handle=?
           WHERE id=?""",
        (request.name, request.role, request.role_details, request.responsibilities,
         request.department, request.email, request.telegram_handle.lstrip('@'), member_id)
    )
    conn.commit()
    conn.close()

    if result.rowcount == 0:
        raise HTTPException(404, "Team member not found")

    return {"ok": True, "id": member_id}


@app.delete("/api/team/{member_id}")
async def remove_team_member(member_id: str):
    """Remove a team member from the registry."""
    success = delete_team_member(member_id)
    if not success:
        raise HTTPException(404, "Team member not found")
    return {"ok": True}


# ──────────────────────────────────────────────────────
# ORG CONTEXT
# ──────────────────────────────────────────────────────

@app.get("/api/org/context")
async def get_context(department: str = "engineering"):
    """Get the mission/context for a department."""
    return get_org_context(department)


@app.put("/api/org/context")
async def update_context(request: OrgContextRequest):
    """Save mission/context for a department (injected into extraction prompt)."""
    save_org_context(
        request.department,
        request.mission,
        request.notion_database_id,
        request.notion_page_id
    )
    return {"ok": True, "department": request.department}


@app.post("/api/notifications/send")
async def send_notifications(request: NotificationRequest):
    """Send task notifications to team members in a department."""
    from .agents.notification_service import send_department_notifications

    result = await send_department_notifications(
        request.department,
        request.days_ahead
    )
    return result


@app.get("/api/notifications/preview")
async def preview_notifications(department: str, days_ahead: int = 3):
    """Preview which tasks would trigger notifications."""
    from .agents.notification_service import get_due_tasks

    tasks = await get_due_tasks(department, days_ahead)
    return {
        "ok": True,
        "department": department,
        "days_ahead": days_ahead,
        "tasks_count": len(tasks),
        "tasks": tasks
    }


@app.post("/api/reminders/send")
async def send_task_reminders(department: Optional[str] = None, days_ahead: int = 1):
    """
    Send email reminders for tasks due within the next N days.
    Manually trigger the reminder system (normally runs daily at 9 AM).

    Args:
        department: Optional filter by department
        days_ahead: Send reminders for tasks due within this many days (default: 1)
    """
    all_tasks = get_all_tasks(department=department) if department else get_all_tasks()
    all_members = get_team_members(department=department) if department else get_team_members()

    result = await email_send_reminders(
        tasks=all_tasks,
        team_members=all_members,
        days_ahead=days_ahead
    )

    return {
        "ok": True,
        "sent": result.get("sent", 0),
        "failed": result.get("failed", 0),
        "tasks_mentioned": result.get("tasks_mentioned", 0),
        "recipients": result.get("recipients", []),
        "reason": result.get("reason", "")
    }


@app.get("/api/reminders/preview")
async def preview_task_reminders(department: Optional[str] = None, days_ahead: int = 1):
    """
    Preview tasks that would trigger reminders without sending emails.

    Args:
        department: Optional filter by department
        days_ahead: Preview tasks due within this many days (default: 1)
    """
    from .agents.email_client import _parse_deadline
    from datetime import datetime, timedelta

    all_tasks = get_all_tasks(department=department) if department else get_all_tasks()
    today = datetime.now().date()
    cutoff = today + timedelta(days=days_ahead)

    # Find tasks due soon
    due_soon = []
    for task in all_tasks:
        if task.get("status") == "completed":
            continue

        deadline = _parse_deadline(task.get("deadline", ""))
        if deadline and today <= deadline <= cutoff:
            days_until = (deadline - today).days
            due_label = "TODAY" if days_until == 0 else ("TOMORROW" if days_until == 1 else f"in {days_until} days")

            due_soon.append({
                "task_id": task.get("id"),
                "description": task.get("description"),
                "owner": task.get("owner"),
                "deadline": task.get("deadline"),
                "department": task.get("department"),
                "days_until": days_until,
                "due_label": due_label
            })

    # Group by owner
    by_owner = {}
    for task in due_soon:
        owner = task["owner"]
        if owner == "Unassigned":
            continue
        if owner not in by_owner:
            by_owner[owner] = []
        by_owner[owner].append(task)

    return {
        "ok": True,
        "days_ahead": days_ahead,
        "tasks_due_soon": len(due_soon),
        "tasks": due_soon,
        "by_owner": by_owner,
        "recipients": list(by_owner.keys())
    }


# ──────────────────────────────────────────────────────
# OPPORTUNITIES (Call for Interest, CFP, etc.)
# ──────────────────────────────────────────────────────

@app.get("/api/opportunities")
async def list_opportunities(department: Optional[str] = None, status: Optional[str] = None):
    """
    List all extracted opportunities from emails.
    Filter by department or status (new, reviewing, applied, rejected, won).
    """
    opportunities = get_all_opportunities(department=department, status=status)
    return {
        "opportunities": opportunities,
        "total": len(opportunities)
    }


@app.patch("/api/opportunities/{opp_id}")
async def update_opportunity(opp_id: str, status: str):
    """Update opportunity status (new, reviewing, applied, rejected, won)."""
    valid_statuses = ["new", "reviewing", "applied", "rejected", "won"]
    if status not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid_statuses}")

    success = update_opportunity_status(opp_id, status)
    if not success:
        raise HTTPException(404, "Opportunity not found")

    return {"ok": True, "id": opp_id, "status": status}


@app.get("/api/opportunities/export")
async def export_opportunities_to_excel(department: Optional[str] = None):
    """
    Export all opportunities to Excel file.
    Returns the file path and download info.
    """
    from pathlib import Path

    opportunities = get_all_opportunities(department=department)
    if not opportunities:
        return {"ok": False, "message": "No opportunities to export"}

    try:
        output_path = export_opportunities_excel(opportunities)
        return {
            "ok": True,
            "file_path": output_path,
            "total_exported": len(opportunities),
            "message": f"Exported {len(opportunities)} opportunities to {output_path}"
        }
    except ImportError as e:
        raise HTTPException(500, "Excel export requires openpyxl. Install with: pip install openpyxl")
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@app.get("/api/opportunities/download")
async def download_opportunities_excel(department: Optional[str] = None):
    """Download opportunities as Excel file."""
    from pathlib import Path

    opportunities = get_all_opportunities(department=department)
    if not opportunities:
        raise HTTPException(404, "No opportunities to export")

    try:
        output_path = export_opportunities_excel(opportunities)
        return FileResponse(
            path=output_path,
            filename="opportunities.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except ImportError:
        raise HTTPException(500, "Excel export requires openpyxl")
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


class OpportunityEmailRequest(BaseModel):
    subject: str
    body: str
    sender_email: str = ""
    department: str = "innovation"


@app.post("/api/opportunities/extract")
async def extract_opportunity_from_email(request: OpportunityEmailRequest):
    """
    Manually submit an email to extract opportunity information.
    Detects patterns like 'Call for Interest', 'CFP', etc. and extracts fields.
    Returns extracted data and saves to database + Excel.
    """
    email_data = {
        "subject": request.subject,
        "body": request.body,
        "sender": {"email": request.sender_email},
    }

    # Check if it matches opportunity patterns
    if not is_opportunity_email(request.subject, request.body):
        return {
            "is_opportunity": False,
            "message": "Email does not match opportunity patterns (Call for Interest, CFP, RFP, etc.)",
            "detected_patterns": []
        }

    # Process as opportunity
    result = await process_opportunity_email(email_data, department=request.department)

    return {
        "is_opportunity": True,
        "opportunity_id": result.get("opportunity_id"),
        "extraction": result.get("extraction"),
        "excel_exported": True,
        "message": "Opportunity extracted and saved to database + Excel"
    }
