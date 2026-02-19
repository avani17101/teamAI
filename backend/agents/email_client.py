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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ..config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS


def _is_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def _send_smtp(to_email: str, subject: str, html: str, text: str) -> bool:
    """Synchronous SMTP send (run in executor for async compatibility)."""
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
