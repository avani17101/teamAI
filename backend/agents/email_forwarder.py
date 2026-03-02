"""
Email Forwarder - Monitor teamAI email inbox and process forwarded emails
Users can forward emails to teamai@gmail.com and they'll be processed automatically
"""
from __future__ import annotations
import imaplib
import email
from email.header import decode_header
import asyncio
from datetime import datetime
import re
from typing import List, Dict, Optional


class EmailForwarder:
    """Monitor an email inbox and process new emails as meetings."""

    def __init__(self, email_address: str, password: str, imap_server: str = "imap.gmail.com"):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.seen_uids: set = set()

    def connect(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server."""
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.email_address, self.password)
        return mail

    def decode_email_subject(self, subject: str) -> str:
        """Decode email subject line."""
        decoded_parts = decode_header(subject)
        decoded_subject = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_subject += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_subject += part
        return decoded_subject

    def extract_email_body(self, msg: email.message.Message) -> str:
        """Extract plain text body from email."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = part.get("Content-Disposition") or ""

                # Get text/plain parts
                if content_type == "text/plain" and "attachment" not in content_disposition.lower():
                    try:
                        body_part = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body += body_part.decode(charset, errors='ignore')
                    except Exception:
                        pass
        else:
            # Not multipart - get payload directly
            try:
                body_part = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                body = body_part.decode(charset, errors='ignore')
            except Exception:
                body = str(msg.get_payload())

        return body.strip()

    def clean_email_body(self, body: str) -> str:
        """Clean email body - remove signatures, forwarding headers, etc."""
        # Handle None or empty body
        if not body:
            return ""

        # Remove common email signatures
        signature_markers = [
            "-- ",
            "Sent from my iPhone",
            "Sent from my Android",
            "Get Outlook for",
            "Best regards",
            "Thanks,",
            "Cheers,",
        ]

        lines = body.split('\n')
        cleaned_lines = []

        for i, line in enumerate(lines):
            # Handle None lines (shouldn't happen, but be safe)
            if line is None:
                continue
            # Stop at signature markers
            if any(marker in line for marker in signature_markers):
                # Keep everything before this line
                break
            cleaned_lines.append(line)

        cleaned = '\n'.join(cleaned_lines).strip()

        # Remove excessive blank lines
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)

        return cleaned

    def extract_sender_info(self, msg: email.message.Message) -> dict:
        """Extract sender name and email."""
        from_header = msg.get("From", "")

        # Parse "Name <email@example.com>" format
        match = re.match(r'(.+?)\s*<(.+?)>', from_header)
        if match:
            name = match.group(1).strip().strip('"')
            email_addr = match.group(2).strip()
        else:
            name = from_header
            email_addr = from_header

        return {
            "name": name,
            "email": email_addr
        }

    def check_new_emails(self) -> List[Dict]:
        """Check for new unread emails and return them."""
        new_emails = []

        try:
            mail = self.connect()
            mail.select("inbox")

            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")

            if status != "OK":
                return new_emails

            email_ids = messages[0].split()

            for email_id in email_ids:
                # Fetch the email
                status, msg_data = mail.fetch(email_id, "(RFC822)")

                if status != "OK":
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # Extract details
                        subject = self.decode_email_subject(msg.get("Subject", "No Subject"))
                        sender = self.extract_sender_info(msg)
                        body = self.extract_email_body(msg)
                        cleaned_body = self.clean_email_body(body)
                        date = msg.get("Date", datetime.utcnow().isoformat())

                        new_emails.append({
                            "uid": email_id.decode(),
                            "subject": subject,
                            "sender": sender,
                            "body": cleaned_body,
                            "raw_body": body,
                            "date": date,
                            "to": msg.get("To", ""),
                        })

                        # Mark as read
                        mail.store(email_id, '+FLAGS', '\\Seen')

            mail.close()
            mail.logout()

        except Exception as e:
            print(f"[EmailForwarder] Error checking emails: {e}")

        return new_emails

    async def poll_inbox(self, interval: int = 30, callback=None):
        """
        Poll inbox at regular intervals and process new emails.

        Args:
            interval: Seconds between checks
            callback: Async function to call with new emails
        """
        print(f"[EmailForwarder] Starting inbox polling every {interval}s for {self.email_address}")

        while True:
            try:
                new_emails = self.check_new_emails()

                if new_emails and callback:
                    for email_data in new_emails:
                        print(f"[EmailForwarder] New email: {email_data['subject']}")
                        await callback(email_data)

            except Exception as e:
                print(f"[EmailForwarder] Polling error: {e}")

            await asyncio.sleep(interval)


async def process_forwarded_email(email_data: dict, department: str = "engineering"):
    """
    Process a forwarded email as a meeting/task source.
    Creates tasks in "pending review" state for HITL approval.

    Args:
        email_data: Dict with subject, sender, body, date
        department: Which department to process for
    """
    from .extraction_agent import extract_meeting
    from .memory_store import save_meeting

    print(f"[EmailForwarder] Processing email: {email_data['subject']}")

    # Use subject as title
    title = f"Email: {email_data['subject']}"

    # Use cleaned body as transcript
    transcript = f"""
From: {email_data['sender']['name']} <{email_data['sender']['email']}>
Date: {email_data['date']}
Subject: {email_data['subject']}

{email_data['body']}
    """.strip()

    # Extract tasks/decisions/risks
    extraction, summary, task_updates = await extract_meeting(
        transcript=transcript,
        title=title,
        department=department
    )

    # Save to database with special flag for pending review
    meeting_id = save_meeting(
        title=title,
        transcript=transcript,
        summary=summary,
        extraction=extraction,
        department=department
    )

    print(f"[EmailForwarder] Saved meeting {meeting_id} with {len(extraction.tasks)} tasks")

    # Auto-sync to Notion if configured
    notion_result = {"ok": False, "created": 0}
    try:
        from .notion_client import sync_tasks as notion_sync_tasks
        from .memory_store import update_task_notion_urls

        notion_result = await notion_sync_tasks(
            tasks=[{
                "id": t.id,
                "description": t.description,
                "owner": t.owner,
                "deadline": t.deadline,
                "status": t.status,
            } for t in extraction.tasks],
            meeting_title=title,
            department=department,
        )

        # Save Notion URLs back to database
        if notion_result.get("ok") and notion_result.get("url_map"):
            update_task_notion_urls(
                notion_result["url_map"],
                notion_result.get("page_id_map")
            )
            print(f"[EmailForwarder] Synced {notion_result['created']} tasks to Notion")

    except Exception as e:
        print(f"[EmailForwarder] Notion sync failed: {e}")

    return {
        "meeting_id": meeting_id,
        "tasks_count": len(extraction.tasks),
        "decisions_count": len(extraction.decisions),
        "risks_count": len(extraction.risks),
        "extraction": extraction,
        "summary": summary,
        "notion_synced": notion_result.get("created", 0),
    }


def send_processing_confirmation(
    to_email: str,
    original_subject: str,
    extraction_result: dict,
    notion_database_url: str = None
) -> bool:
    """
    Send an auto-reply to the email sender with processing summary.

    Args:
        to_email: Sender's email address
        original_subject: Original email subject
        extraction_result: Results from process_forwarded_email
        notion_database_url: URL to Notion database (if configured)
    """
    from ..config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    if not SMTP_USER or not SMTP_PASS:
        print("[EmailForwarder] Cannot send reply - SMTP not configured")
        return False

    tasks_count = extraction_result.get("tasks_count", 0)
    decisions_count = extraction_result.get("decisions_count", 0)
    risks_count = extraction_result.get("risks_count", 0)
    extraction = extraction_result.get("extraction")
    summary = extraction_result.get("summary", "")

    # Build task list
    task_list = ""
    if extraction and hasattr(extraction, 'tasks'):
        for i, task in enumerate(extraction.tasks[:5], 1):  # Show first 5 tasks
            owner = task.owner if task.owner else "Unassigned"
            deadline = task.deadline if task.deadline else "No deadline"
            task_list += f"{i}. {task.description}\n   → Assigned to: {owner} | Due: {deadline}\n\n"

        if len(extraction.tasks) > 5:
            task_list += f"...and {len(extraction.tasks) - 5} more tasks\n\n"

    # Build email body
    subject = f"✅ TeamAI Processed: {original_subject}"

    body = f"""
Hi there!

I've processed your email and extracted the following:

📋 SUMMARY
{summary}

✅ EXTRACTED ITEMS
• {tasks_count} Task{'s' if tasks_count != 1 else ''}
• {decisions_count} Decision{'s' if decisions_count != 1 else ''}
• {risks_count} Risk{'s' if risks_count != 1 else ''}

"""

    if task_list:
        body += f"""
📝 TASKS:
{task_list}"""

    if notion_database_url:
        body += f"""
🔗 VIEW IN NOTION
{notion_database_url}
"""

    body += """
💡 TIP: Forward any email to teamaiassistant@gmail.com and I'll process it automatically!

—
TeamAI Assistant
Your AI-powered team intelligence system
"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"TeamAI <{SMTP_USER}>"
        msg["To"] = to_email
        msg["In-Reply-To"] = original_subject  # Threading

        # HTML version
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px 8px 0 0;">
        <h2 style="color: white; margin: 0;">✅ Email Processed Successfully</h2>
    </div>

    <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 14px; color: #6b7280;">RE: {original_subject}</p>

        <div style="background: white; padding: 16px; border-radius: 6px; margin: 16px 0; border-left: 4px solid #667eea;">
            <h3 style="margin-top: 0; color: #1f2937;">📋 Summary</h3>
            <p style="margin-bottom: 0;">{summary}</p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 20px 0;">
            <div style="background: white; padding: 12px; border-radius: 6px; text-align: center; border: 1px solid #e5e7eb;">
                <div style="font-size: 24px; font-weight: bold; color: #667eea;">{tasks_count}</div>
                <div style="font-size: 12px; color: #6b7280;">Task{'s' if tasks_count != 1 else ''}</div>
            </div>
            <div style="background: white; padding: 12px; border-radius: 6px; text-align: center; border: 1px solid #e5e7eb;">
                <div style="font-size: 24px; font-weight: bold; color: #10b981;">{decisions_count}</div>
                <div style="font-size: 12px; color: #6b7280;">Decision{'s' if decisions_count != 1 else ''}</div>
            </div>
            <div style="background: white; padding: 12px; border-radius: 6px; text-align: center; border: 1px solid #e5e7eb;">
                <div style="font-size: 24px; font-weight: bold; color: #f59e0b;">{risks_count}</div>
                <div style="font-size: 12px; color: #6b7280;">Risk{'s' if risks_count != 1 else ''}</div>
            </div>
        </div>
"""

        if task_list:
            html_body += f"""
        <div style="background: white; padding: 16px; border-radius: 6px; margin: 16px 0;">
            <h3 style="margin-top: 0; color: #1f2937;">📝 Tasks</h3>
            <pre style="font-family: 'Courier New', monospace; font-size: 12px; background: #f9fafb; padding: 12px; border-radius: 4px; overflow-x: auto;">{task_list}</pre>
        </div>
"""

        if notion_database_url:
            html_body += f"""
        <div style="text-align: center; margin: 24px 0;">
            <a href="{notion_database_url}" style="display: inline-block; background: #667eea; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
                🔗 View All Tasks in Notion
            </a>
        </div>
"""

        html_body += """
        <div style="background: #f0f9ff; padding: 12px; border-radius: 6px; margin-top: 20px; border-left: 4px solid #3b82f6;">
            <p style="margin: 0; font-size: 13px; color: #1e40af;">
                💡 <strong>Tip:</strong> Forward any email to <strong>teamaiassistant@gmail.com</strong> and I'll process it automatically!
            </p>
        </div>

        <div style="text-align: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
            <p style="font-size: 12px; color: #6b7280; margin: 0;">
                TeamAI Assistant<br>
                Your AI-powered team intelligence system
            </p>
        </div>
    </div>
</body>
</html>
"""

        # Attach both plain text and HTML
        text_part = MIMEText(body, "plain")
        html_part = MIMEText(html_body, "html")
        msg.attach(text_part)
        msg.attach(html_part)

        # Send via SMTP
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"[EmailForwarder] Sent confirmation to {to_email}")
        return True

    except Exception as e:
        print(f"[EmailForwarder] Failed to send confirmation: {e}")
        return False


# Example usage:
"""
from backend.agents.email_forwarder import EmailForwarder, process_forwarded_email

forwarder = EmailForwarder(
    email_address="teamai@gmail.com",
    password="your-app-password"
)

async def handle_email(email_data):
    await process_forwarded_email(email_data, department="engineering")

# Start polling
asyncio.create_task(forwarder.poll_inbox(interval=30, callback=handle_email))
"""
