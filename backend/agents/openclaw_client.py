from __future__ import annotations
"""
OpenClaw Client - orchestration layer for executing department actions.

OpenClaw runs locally as a gateway daemon (http://localhost:18789).
It provides:
  - POST /tools/invoke  → execute tools (file system, shell, integrations)
  - POST /v1/chat/completions → chat with a configured agent

For the hackathon demo:
- OpenClaw acts as the autonomous execution layer
- K2-Think-V2 decides WHAT to do, OpenClaw EXECUTES it
- Fallback: direct execution if OpenClaw is not running
"""
import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
import httpx

from ..config import OPENCLAW_BASE_URL, OPENCLAW_TOKEN, OPENCLAW_AGENT_ID


class OpenClawClient:
    def __init__(self):
        self.base_url = OPENCLAW_BASE_URL
        self.token = OPENCLAW_TOKEN
        self.available = False

    async def check_health(self) -> bool:
        """Check if OpenClaw gateway is running."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/health")
                self.available = r.status_code == 200
        except Exception:
            self.available = False
        return self.available

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    async def invoke_tool(self, tool: str, args: dict, session_key: str = "department-ai") -> dict:
        """
        Call OpenClaw /tools/invoke to execute a tool.
        Tools available: shell, file_read, file_write, browser, + 50+ integrations.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/tools/invoke",
                headers=self._headers(),
                json={
                    "tool": tool,
                    "args": args,
                    "sessionKey": session_key,
                },
            )
            response.raise_for_status()
            return response.json()

    async def chat_with_agent(
        self,
        message: str,
        history: list[dict] = None,
        agent_id: str = None,
    ) -> str:
        """
        Send a message to the OpenClaw department-ai agent via OpenAI-compatible API.
        The agent has full tool access and department context.
        """
        agent = agent_id or OPENCLAW_AGENT_ID
        messages = history or []
        messages.append({"role": "user", "content": message})

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers(),
                json={
                    "model": f"openclaw:{agent}",
                    "messages": messages,
                    "stream": False,
                    "user": "department-ai-session",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    # ──────────────────────────────────────────────
    # High-level orchestration actions
    # ──────────────────────────────────────────────

    async def create_task_in_board(self, task: dict) -> dict:
        """
        Write a task to the department task board (JSON file + shell notification).
        Uses OpenClaw shell tool to execute the update.
        Falls back to direct file write if OpenClaw is not running.
        """
        if self.available:
            return await self._openclaw_create_task(task)
        return await self._fallback_create_task(task)

    async def _openclaw_create_task(self, task: dict) -> dict:
        """Use OpenClaw shell tool to write task to board."""
        board_path = str(Path(__file__).parent.parent.parent / "data" / "task_board.json")
        script = f"""
import json, os
path = "{board_path}"
board = json.load(open(path)) if os.path.exists(path) else {{"tasks": []}}
task = {json.dumps(task)}
board["tasks"].append(task)
json.dump(board, open(path, "w"), indent=2)
print("Task created: " + task["description"])
"""
        result = await self.invoke_tool(
            tool="shell",
            args={"command": f"python3 -c '{script}'"},
        )
        return {"ok": True, "source": "openclaw", "result": result}

    async def _fallback_create_task(self, task: dict) -> dict:
        """Direct file write fallback when OpenClaw is not running."""
        board_path = Path(__file__).parent.parent.parent / "data" / "task_board.json"
        board_path.parent.mkdir(parents=True, exist_ok=True)

        if board_path.exists():
            with open(board_path) as f:
                board = json.load(f)
        else:
            board = {"tasks": [], "last_updated": ""}

        task["created_via"] = "direct"
        task["created_at"] = datetime.utcnow().isoformat()
        board["tasks"].append(task)
        board["last_updated"] = datetime.utcnow().isoformat()

        with open(board_path, "w") as f:
            json.dump(board, f, indent=2)

        return {"ok": True, "source": "direct", "task": task}

    async def sync_tasks_to_board(self, tasks: list[dict]) -> dict:
        """Sync all pending tasks to the visual task board file."""
        board_path = Path(__file__).parent.parent.parent / "data" / "task_board.json"
        board_path.parent.mkdir(parents=True, exist_ok=True)

        if board_path.exists():
            with open(board_path) as f:
                board = json.load(f)
        else:
            board = {"tasks": []}

        # Merge: add new tasks, preserve existing ones
        existing_ids = {t.get("id") for t in board.get("tasks", [])}
        added = 0
        for task in tasks:
            if task.get("id") not in existing_ids:
                board["tasks"].append(task)
                added += 1

        board["last_updated"] = datetime.utcnow().isoformat()
        board["total"] = len(board["tasks"])

        with open(board_path, "w") as f:
            json.dump(board, f, indent=2)

        return {"ok": True, "added": added, "total": board["total"], "board_path": str(board_path)}

    async def get_task_board(self) -> dict:
        """Read the current task board state."""
        board_path = Path(__file__).parent.parent.parent / "data" / "task_board.json"
        if board_path.exists():
            with open(board_path) as f:
                return json.load(f)
        return {"tasks": [], "total": 0}

    async def update_task_status_on_board(self, task_id: str, status: str) -> dict:
        """Update a task's status on the board."""
        board_path = Path(__file__).parent.parent.parent / "data" / "task_board.json"
        if not board_path.exists():
            return {"ok": False, "error": "No task board found"}

        with open(board_path) as f:
            board = json.load(f)

        updated = False
        for task in board.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = status
                task["updated_at"] = datetime.utcnow().isoformat()
                updated = True
                break

        if updated:
            board["last_updated"] = datetime.utcnow().isoformat()
            with open(board_path, "w") as f:
                json.dump(board, f, indent=2)

        return {"ok": updated, "task_id": task_id, "status": status}

    async def write_meeting_summary(self, meeting_id: str, title: str, summary: str, extraction: dict) -> str:
        """Write meeting notes to the OpenClaw workspace so the agent can read them."""
        workspace_path = Path(__file__).parent.parent.parent / "openclaw" / "workspace" / "meetings"
        workspace_path.mkdir(parents=True, exist_ok=True)

        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{meeting_id[:8]}.md"
        filepath = workspace_path / filename

        content = f"""# Meeting: {title}
Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
ID: {meeting_id}

## Summary
{summary}

## Tasks
{chr(10).join(f"- [ ] {t['description']} (Owner: {t['owner']}, Deadline: {t['deadline']})" for t in extraction.get("tasks", []))}

## Decisions
{chr(10).join(f"- {d['description']}" for d in extraction.get("decisions", []))}

## Risks
{chr(10).join(f"- [{r['severity'].upper()}] {r['description']}" for r in extraction.get("risks", []))}
"""
        with open(filepath, "w") as f:
            f.write(content)

        return str(filepath)


# Singleton client
openclaw = OpenClawClient()
