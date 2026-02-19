"""
Telegram Bot — sends task due reminders to a configured chat.

Setup (one-time, takes 2 minutes):
  1. Open Telegram → search @BotFather → /newbot → copy the token
  2. Start a chat with your new bot, then open:
     https://api.telegram.org/bot<TOKEN>/getUpdates
     Copy the chat.id from the response
  3. Add to .env:
     TELEGRAM_BOT_TOKEN=<token>
     TELEGRAM_CHAT_ID=<chat_id>
"""
from __future__ import annotations
import httpx
from datetime import datetime, timedelta
from ..config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


TELEGRAM_BASE = "https://api.telegram.org"


def _is_configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


async def send_message(text: str) -> bool:
    """Send a plain text message to the configured Telegram chat."""
    if not _is_configured():
        print("[Telegram] Not configured — set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env")
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{TELEGRAM_BASE}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": text,
                    "parse_mode": "Markdown",
                },
            )
            ok = r.status_code == 200
            if not ok:
                print(f"[Telegram] Failed: {r.status_code} {r.text[:200]}")
            return ok
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return False


async def send_due_reminders(tasks: list[dict], days_ahead: int = 2) -> dict:
    """
    Send a Telegram digest for tasks due within the next `days_ahead` days.
    tasks: list of task dicts from get_all_tasks() — must have 'deadline' field.
    Returns {sent: bool, tasks_mentioned: int}.
    """
    if not _is_configured():
        return {"sent": False, "reason": "Telegram not configured"}

    now = datetime.utcnow().date()
    cutoff = now + timedelta(days=days_ahead)

    due_soon = []
    for t in tasks:
        deadline = t.get("deadline", "")
        if not deadline or deadline in ("Not specified", "not specified"):
            continue
        # Try to parse ISO date
        try:
            d = datetime.strptime(deadline[:10], "%Y-%m-%d").date()
            if now <= d <= cutoff:
                due_soon.append((d, t))
        except ValueError:
            continue

    if not due_soon:
        return {"sent": False, "reason": "No tasks due soon", "tasks_mentioned": 0}

    due_soon.sort(key=lambda x: x[0])

    lines = [f"🔔 *TeamAI — Tasks Due Soon* (next {days_ahead} days)\n"]
    for d, t in due_soon:
        dept = t.get("department", "")
        owner = t.get("owner", "Unassigned")
        desc = t.get("description", "")[:80]
        notion_url = t.get("notion_url", "")
        date_str = d.strftime("%b %d")
        link = f" [→ Notion]({notion_url})" if notion_url else ""
        lines.append(f"📌 *{date_str}* — {desc}\n   👤 {owner}  |  🏷 {dept}{link}")

    message = "\n\n".join(lines)
    sent = await send_message(message)
    return {"sent": sent, "tasks_mentioned": len(due_soon)}


async def send_task_assigned(member: dict, task: dict, meeting_title: str) -> bool:
    """
    Send a personalized task assignment notification to a team member.
    Uses the shared group chat (TELEGRAM_CHAT_ID) and mentions them by name.
    For per-person DMs, each member would need their own chat_id stored.
    """
    name = member.get("name", "Team member")
    handle = member.get("telegram_handle", "")
    mention = f"@{handle}" if handle else f"*{name}*"

    desc = task.get("description", "")
    deadline = task.get("deadline", "Not specified")
    dept = task.get("department", "")

    text = (
        f"👋 Hi {mention}, you have a new task!\n\n"
        f"📌 *{desc}*\n"
        f"📅 Due: {deadline}\n"
        f"📂 From: {meeting_title}"
        + (f"\n🏷 Department: {dept}" if dept else "")
        + "\n\n_Log in to TeamAI to update your progress._"
    )
    return await send_message(text)


async def check_bot_status() -> dict:
    """Verify bot token is valid and return bot info."""
    if not _is_configured():
        return {"ok": False, "reason": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"{TELEGRAM_BASE}/bot{TELEGRAM_BOT_TOKEN}/getMe")
            if r.status_code == 200:
                data = r.json()
                return {
                    "ok": True,
                    "bot_name": data["result"].get("first_name", ""),
                    "username": data["result"].get("username", ""),
                    "chat_id": TELEGRAM_CHAT_ID,
                }
            return {"ok": False, "reason": f"API error {r.status_code}"}
    except Exception as e:
        return {"ok": False, "reason": str(e)}
