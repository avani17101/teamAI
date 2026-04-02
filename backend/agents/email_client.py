"""
Email Client — sends personalized task assignment emails via SMTP.

Setup (works with Gmail, Outlook, or any SMTP provider):
  Gmail:
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=you@gmail.com
    SMTP_PASS=<app-password>   # https://myaccount.google.com/apppasswords

  Add to .env, then restart the server.
"""
from __future__ import annotations
import asyncio
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ..config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, DEBUG_MODE


def _is_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def _send_smtp(to_email: str, subject: str, html: str, text: str) -> bool:
    """Synchronous SMTP send (run in executor for async compatibility)."""
    # Debug mode: log but don't actually send
    if DEBUG_MODE:
        print(f"[Email] DEBUG_MODE: Would send to {to_email} | Subject: {subject[:50]}...")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"TeamAI <{SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[Email] SMTP send failed to {to_email}: {e}")
        return False


async def send_task_email(member: dict, task: dict, meeting_title: str) -> bool:
    """
    Send a task assignment email to a team member.
    Falls back gracefully if SMTP is not configured.
    """
    if not _is_configured():
        print("[Email] SMTP not configured — set SMTP_HOST/SMTP_USER/SMTP_PASS in .env")
        return False

    to_email = member.get("email", "")
    if not to_email:
        return False

    name = member.get("name", "Team member")
    desc = task.get("description", "")
    deadline = task.get("deadline", "Not specified")
    dept = task.get("department", "")
    notion_url = task.get("notion_url", "")

    subject = f"[TeamAI] New task assigned: {desc[:60]}"

    notion_link = (
        f'<a href="{notion_url}" style="color:#6c63ff">View in Notion →</a>'
        if notion_url else ""
    )

    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:-apple-system,sans-serif;background:#f5f5f5;padding:20px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;padding:28px;border:1px solid #e5e7eb">
    <div style="font-size:22px;font-weight:700;margin-bottom:4px">👋 Hi {name},</div>
    <div style="color:#6b7280;margin-bottom:20px">You have a new task assigned from <strong>{meeting_title}</strong>.</div>
    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:20px">
      <div style="font-size:15px;font-weight:600;margin-bottom:10px">📌 {desc}</div>
      <div style="display:flex;gap:16px;font-size:13px;color:#6b7280">
        <span>📅 Due: <strong style="color:#111">{deadline}</strong></span>
        {"<span>🏷 " + dept + "</span>" if dept else ""}
      </div>
    </div>
    {"<div style='margin-bottom:16px'>" + notion_link + "</div>" if notion_link else ""}
    <div style="font-size:12px;color:#9ca3af;border-top:1px solid #f3f4f6;padding-top:12px">
      Sent by TeamAI · Department Intelligence System
    </div>
  </div>
</body>
</html>"""

    plain = (
        f"Hi {name},\n\n"
        f"You have a new task from {meeting_title}:\n\n"
        f"  {desc}\n"
        f"  Due: {deadline}\n"
        + (f"  Department: {dept}\n" if dept else "")
        + (f"\n  View in Notion: {notion_url}\n" if notion_url else "")
        + "\nLog in to TeamAI to update your progress.\n"
    )

    return await asyncio.get_event_loop().run_in_executor(
        None, _send_smtp, to_email, subject, html, plain
    )


def _parse_deadline(deadline_str: str) -> datetime.date | None:
    """
    Parse various deadline formats into a date object.
    Supports: ISO dates (2026-02-20), relative dates (tomorrow, friday), or None.
    """
    if not deadline_str or deadline_str.lower() in ("not specified", "unspecified", "n/a"):
        return None

    deadline_lower = deadline_str.lower().strip()
    today = datetime.now().date()

    # Relative dates
    if deadline_lower in ("today", "asap"):
        return today
    elif deadline_lower == "tomorrow":
        return today + timedelta(days=1)
    elif deadline_lower.startswith("in "):
        # "in 2 days", "in 1 week"
        parts = deadline_lower.split()
        if len(parts) >= 3:
            try:
                num = int(parts[1])
                unit = parts[2]
                if unit.startswith("day"):
                    return today + timedelta(days=num)
                elif unit.startswith("week"):
                    return today + timedelta(weeks=num)
            except ValueError:
                pass

    # Day of week (assume this week or next week)
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if deadline_lower in weekdays:
        target_weekday = weekdays.index(deadline_lower)
        current_weekday = today.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            days_ahead = 7  # Next week if same day
        return today + timedelta(days=days_ahead)

    # ISO date format (YYYY-MM-DD)
    try:
        return datetime.strptime(deadline_str[:10], "%Y-%m-%d").date()
    except ValueError:
        pass

    # Other common formats
    formats = ["%b %d", "%B %d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(deadline_str, fmt)
            # If no year specified, assume current year
            if "%Y" not in fmt:
                parsed = parsed.replace(year=today.year)
            return parsed.date()
        except ValueError:
            continue

    return None


async def send_due_reminders(tasks: list[dict], team_members: list[dict], days_ahead: int = 1) -> dict:
    """
    Send email reminders for tasks due within the next `days_ahead` days.
    Groups tasks by owner and sends one email per person.

    Args:
        tasks: List of task dicts with 'deadline', 'owner', 'description', 'department'
        team_members: List of team member dicts with 'name', 'email'
        days_ahead: Send reminder if task is due within this many days (default: 1 day)

    Returns:
        {sent: int, failed: int, tasks_mentioned: int}
    """
    if not _is_configured():
        print("[Email] SMTP not configured — cannot send due reminders")
        return {"sent": 0, "failed": 0, "reason": "SMTP not configured"}

    today = datetime.now().date()
    cutoff = today + timedelta(days=days_ahead)

    # Find tasks due soon
    due_soon = []
    for task in tasks:
        if task.get("status") == "completed":
            continue  # Skip completed tasks

        deadline = _parse_deadline(task.get("deadline", ""))
        if deadline and today <= deadline <= cutoff:
            due_soon.append((deadline, task))

    if not due_soon:
        return {"sent": 0, "failed": 0, "tasks_mentioned": 0, "reason": "No tasks due soon"}

    # Group tasks by owner
    tasks_by_owner = {}
    for deadline, task in due_soon:
        owner = task.get("owner", "Unassigned")
        if owner == "Unassigned":
            continue  # Skip unassigned tasks

        if owner not in tasks_by_owner:
            tasks_by_owner[owner] = []
        tasks_by_owner[owner].append((deadline, task))

    # Find email for each owner
    email_map = {m.get("name", ""): m.get("email", "") for m in team_members if m.get("email")}

    sent_count = 0
    failed_count = 0

    for owner, owner_tasks in tasks_by_owner.items():
        email = email_map.get(owner)
        if not email:
            print(f"[Email] No email found for {owner}, skipping reminder")
            failed_count += 1
            continue

        # Sort by deadline
        owner_tasks.sort(key=lambda x: x[0])

        # Build email
        subject = f"[TeamAI] Task Reminder: {len(owner_tasks)} task{'s' if len(owner_tasks) > 1 else ''} due soon"

        task_rows = []
        for deadline, task in owner_tasks:
            desc = task.get("description", "")
            dept = task.get("department", "")
            notion_url = task.get("notion_url", "")
            dept_icon = {
                "engineering": "⚙️",
                "hr": "👥",
                "marcom": "📣",
                "innovation": "🚀",
                "sales": "💼",
                "product": "🎨",
            }.get(dept, "🏢")

            notion_link = f'<a href="{notion_url}" style="color:#6c63ff;text-decoration:none">View in Notion →</a>' if notion_url else ""

            days_until = (deadline - today).days
            if days_until == 0:
                due_label = "⚠️ <strong style='color:#ef4444'>DUE TODAY</strong>"
            elif days_until == 1:
                due_label = "⚠️ <strong style='color:#f59e0b'>DUE TOMORROW</strong>"
            else:
                due_label = f"📅 Due {deadline.strftime('%b %d')}"

            task_rows.append(f"""
                <div style="background:#f9fafb;border-left:3px solid #6c63ff;border-radius:6px;padding:14px;margin-bottom:12px">
                    <div style="font-size:15px;font-weight:600;margin-bottom:8px">{desc}</div>
                    <div style="display:flex;gap:16px;font-size:13px;color:#6b7280;margin-bottom:8px">
                        <span>{due_label}</span>
                        <span>{dept_icon} {dept}</span>
                    </div>
                    {f"<div style='margin-top:8px'>{notion_link}</div>" if notion_link else ""}
                </div>
            """)

        html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:-apple-system,sans-serif;background:#f5f5f5;padding:20px">
    <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;padding:28px;border:1px solid #e5e7eb">
        <div style="font-size:24px;font-weight:700;margin-bottom:4px">🔔 Task Reminder</div>
        <div style="color:#6b7280;margin-bottom:24px">Hi {owner}, you have <strong>{len(owner_tasks)}</strong> task{'s' if len(owner_tasks) > 1 else ''} due soon:</div>

        {"".join(task_rows)}

        <div style="margin-top:24px;padding:16px;background:#eff6ff;border-radius:8px;border:1px solid #bfdbfe">
            <div style="font-size:13px;color:#1e40af">
                💡 <strong>Tip:</strong> Log in to TeamAI to update task status or view full details.
            </div>
        </div>

        <div style="font-size:12px;color:#9ca3af;border-top:1px solid #f3f4f6;padding-top:12px;margin-top:20px">
            Sent by TeamAI · Department Intelligence System
        </div>
    </div>
</body>
</html>"""

        plain_tasks = "\n".join([
            f"  • {task.get('description', '')}\n    Due: {deadline.strftime('%b %d, %Y')} | {task.get('department', '')}"
            for deadline, task in owner_tasks
        ])

        plain = f"""Hi {owner},

You have {len(owner_tasks)} task{'s' if len(owner_tasks) > 1 else ''} due soon:

{plain_tasks}

Log in to TeamAI to update your progress.

--
Sent by TeamAI · Department Intelligence System
"""

        success = await asyncio.get_event_loop().run_in_executor(
            None, _send_smtp, email, subject, html, plain
        )

        if success:
            sent_count += 1
            print(f"[Email] Sent reminder to {owner} ({email}) for {len(owner_tasks)} tasks")
        else:
            failed_count += 1

    return {
        "sent": sent_count,
        "failed": failed_count,
        "tasks_mentioned": len(due_soon),
        "recipients": list(tasks_by_owner.keys())
    }
