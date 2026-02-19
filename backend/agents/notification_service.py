"""
Notification Service - Send task reminders via Telegram and Email
"""
from __future__ import annotations
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict
from ..config import (
    TELEGRAM_BOT_TOKEN,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASS,
)


async def send_telegram_notification(chat_id: str, message: str) -> dict:
    """Send a notification via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN:
        return {"ok": False, "error": "Telegram bot token not configured"}

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                }
            )
            response.raise_for_status()
            return {"ok": True, "data": response.json()}
    except Exception as e:
        print(f"[Telegram] Failed to send notification: {e}")
        return {"ok": False, "error": str(e)}


def send_email_notification(to_email: str, subject: str, body: str) -> dict:
    """Send a notification via email."""
    if not SMTP_USER or not SMTP_PASS:
        return {"ok": False, "error": "Email credentials not configured"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_email

        # Create HTML version
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            {body}
        </body>
        </html>
        """

        # Attach both plain text and HTML
        text_part = MIMEText(body, "plain")
        html_part = MIMEText(html, "html")
        msg.attach(text_part)
        msg.attach(html_part)

        # Send via SMTP
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        return {"ok": True}
    except Exception as e:
        print(f"[Email] Failed to send notification: {e}")
        return {"ok": False, "error": str(e)}


def format_task_notification(task: dict, team_member: dict) -> tuple[str, str]:
    """Format a task notification message.
    Returns (subject, body) tuple.
    """
    deadline = task.get("deadline", "Not specified")
    description = task.get("description", "")
    status = task.get("status", "pending")

    subject = f"Task Reminder: {description[:50]}{'...' if len(description) > 50 else ''}"

    body = f"""
Hello {team_member.get('name', 'there')}!

You have a task that needs attention:

📋 Task: {description}
⏰ Deadline: {deadline}
📊 Status: {status.replace('_', ' ').title()}

Please make sure to complete this task before the deadline.

Best regards,
TeamAI
    """.strip()

    return subject, body


def format_telegram_task_notification(task: dict, team_member: dict) -> str:
    """Format a task notification for Telegram."""
    deadline = task.get("deadline", "Not specified")
    description = task.get("description", "")
    status = task.get("status", "pending")
    notion_url = task.get("notion_url", "")

    message = f"""
🔔 *Task Reminder*

👤 {team_member.get('name', 'there')}!

📋 *Task:* {description}
⏰ *Deadline:* {deadline}
📊 *Status:* {status.replace('_', ' ').title()}
"""

    if notion_url:
        message += f"\n🔗 [View in Notion]({notion_url})"

    return message.strip()


async def get_due_tasks(department: str = None, days_ahead: int = 3) -> List[Dict]:
    """Get tasks that are due within the specified number of days."""
    from .memory_store import _get_db

    conn = _get_db()

    # Calculate date range
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=days_ahead)

    query = """
        SELECT t.*, m.title as meeting_title
        FROM tasks t
        LEFT JOIN meetings m ON t.meeting_id = m.id
        WHERE t.status != 'done'
    """
    params = []

    if department:
        query += " AND m.department = ?"
        params.append(department)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    due_tasks = []
    for row in rows:
        task = dict(row)
        deadline_str = task.get("deadline", "")

        # Try to parse deadline
        if deadline_str and deadline_str not in ("Not specified", "not specified", ""):
            # Simple ISO date parsing
            if len(deadline_str) == 10 and deadline_str[4] == "-":
                try:
                    deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                    if today <= deadline_date <= end_date:
                        due_tasks.append(task)
                except:
                    pass

    return due_tasks


async def notify_team_member(
    team_member: dict,
    tasks: List[dict],
    via_telegram: bool = True,
    via_email: bool = True
) -> dict:
    """Send notifications to a team member about their tasks."""
    results = {"telegram": None, "email": None}

    if not tasks:
        return {"ok": True, "message": "No tasks to notify"}

    # Send via Telegram
    if via_telegram and team_member.get("telegram_handle"):
        # For now, we'll need the chat_id. In production, you'd get this from the bot's user mapping.
        # For demo purposes, we'll skip if not available
        chat_id = team_member.get("telegram_chat_id")
        if chat_id:
            for task in tasks:
                message = format_telegram_task_notification(task, team_member)
                result = await send_telegram_notification(chat_id, message)
                results["telegram"] = result
        else:
            results["telegram"] = {"ok": False, "error": "No Telegram chat ID available"}

    # Send via Email
    if via_email and team_member.get("email"):
        # Send summary email with all tasks
        if len(tasks) == 1:
            subject, body = format_task_notification(tasks[0], team_member)
        else:
            subject = f"You have {len(tasks)} tasks due soon"
            body = f"Hello {team_member.get('name', 'there')}!\n\nYou have {len(tasks)} tasks that need attention:\n\n"
            for i, task in enumerate(tasks, 1):
                body += f"{i}. {task.get('description', '')}\n"
                body += f"   Deadline: {task.get('deadline', 'Not specified')}\n\n"
            body += "Please complete these tasks before their deadlines.\n\nBest regards,\nTeamAI"

        result = send_email_notification(team_member["email"], subject, body)
        results["email"] = result

    return {"ok": True, "results": results}


async def send_department_notifications(department: str, days_ahead: int = 3) -> dict:
    """Send notifications to all team members in a department about their due tasks."""
    from .memory_store import get_team_members

    # Get all due tasks
    due_tasks = await get_due_tasks(department, days_ahead)

    if not due_tasks:
        return {"ok": True, "message": "No tasks due", "notified": 0}

    # Get team members
    team_members = get_team_members(department=department)

    notifications_sent = 0
    results = []

    for member in team_members:
        # Filter tasks for this member
        member_tasks = [
            task for task in due_tasks
            if task.get("owner", "").lower() == member.get("name", "").lower()
        ]

        if member_tasks:
            result = await notify_team_member(member, member_tasks)
            results.append({
                "member": member.get("name"),
                "tasks": len(member_tasks),
                "result": result
            })
            notifications_sent += 1

    return {
        "ok": True,
        "department": department,
        "total_tasks": len(due_tasks),
        "notified": notifications_sent,
        "details": results
    }
