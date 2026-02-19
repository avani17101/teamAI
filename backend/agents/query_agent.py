from __future__ import annotations
"""
Query Agent - uses K2-V2-Instruct + department memory to answer questions.
Falls back to OpenClaw agent chat if available (for more autonomous responses).
"""
import json
import httpx
from ..config import K2_INSTRUCT_BASE_URL, K2_API_KEY, K2_INSTRUCT_MODEL
from ..agents.memory_store import search_memory, get_department_state, get_team_members, get_org_context
from ..agents.openclaw_client import openclaw
from ..agents.departments import get_department

QUERY_SYSTEM_PROMPT = """You are the Department AI Assistant - an intelligent system that knows everything about this team's work.

You have access to:
- All meeting transcripts and summaries
- All tasks, their owners, and deadlines
- All decisions made by the team
- All identified risks and blockers

Answer questions clearly and concisely. When referencing information, say which meeting it came from.
If asked about task status, provide the current status from your knowledge.
If you detect risks or issues, proactively mention them.
Be direct and helpful - you are the team's organizational intelligence."""


def _build_context(query: str, department: str = None) -> tuple[str, list[str]]:
    """Build context from memory for the query. Returns (context_string, source_list)."""
    # 1. Semantic search for relevant content (filtered by department if given)
    search_results = search_memory(query, n_results=6, department=department)

    # 2. Always include current department state for task/risk questions
    dept_state = get_department_state(department=department)

    # 3. Get team members and org context for better responses
    team_members = get_team_members(department=department)
    org_context = get_org_context(department) if department else {"mission": ""}

    context_parts = []
    sources = []

    # Add org context first
    if org_context.get("mission"):
        context_parts.append("=== ORGANIZATION CONTEXT ===")
        context_parts.append(f"Mission: {org_context['mission']}")
        context_parts.append("")

    # Add team members with responsibilities
    if team_members:
        context_parts.append("=== TEAM MEMBERS ===")
        for member in team_members:
            member_info = f"- {member['name']}"
            if member.get('role'):
                member_info += f" ({member['role']})"
            if member.get('role_details'):
                member_info += f" - {member['role_details']}"
            if member.get('responsibilities'):
                member_info += f"\n  Responsibilities: {member['responsibilities']}"
            if member.get('email'):
                member_info += f"\n  Contact: {member['email']}"
            context_parts.append(member_info)
        context_parts.append("")

    # Add semantic search results
    if search_results:
        context_parts.append("=== RELEVANT MEETING CONTENT ===")
        for r in search_results:
            meta = r["metadata"]
            sources.append(meta.get("title", "Unknown meeting"))
            context_parts.append(f"[{meta.get('type', 'content').upper()} from '{meta.get('title', 'meeting')}']")
            context_parts.append(r["text"])
            context_parts.append("")

    # Add pending tasks
    if dept_state["pending_tasks"]:
        context_parts.append("=== CURRENT PENDING TASKS ===")
        for task in dept_state["pending_tasks"][:10]:
            context_parts.append(
                f"- {task['description']} | Owner: {task['owner']} | Deadline: {task['deadline']} | From: {task.get('meeting_title', 'unknown')}"
            )
        context_parts.append("")

    # Add recent decisions
    if dept_state["recent_decisions"]:
        context_parts.append("=== RECENT DECISIONS ===")
        for d in dept_state["recent_decisions"][:5]:
            context_parts.append(f"- {d['description']} (from: {d.get('meeting_title', 'unknown')})")
        context_parts.append("")

    # Add open risks
    if dept_state["open_risks"]:
        context_parts.append("=== OPEN RISKS & BLOCKERS ===")
        for r in dept_state["open_risks"][:5]:
            context_parts.append(f"- [{r['severity'].upper()}] {r['description']} (from: {r.get('meeting_title', 'unknown')})")
        context_parts.append("")

    context_parts.append(f"=== STATS ===")
    context_parts.append(f"Total meetings processed: {dept_state['total_meetings']}")

    return "\n".join(context_parts), list(set(sources))


async def answer_question(
    question: str,
    history: list[dict] = None,
    use_openclaw: bool = True,
    department: str = None,
) -> tuple[str, list[str], bool]:
    """
    Answer a department question using K2-V2-Instruct + memory context.
    Tries OpenClaw first (if available), falls back to direct K2 call.
    Returns (answer, sources, used_openclaw).
    """
    context, sources = _build_context(question, department=department)

    # Use department-specific system prompt if available
    dept_info = get_department(department) if department else None
    system_prompt = QUERY_SYSTEM_PROMPT
    if dept_info:
        system_prompt = f"You are the {dept_info['name']} Department AI. {dept_info['query_context']}\n\n{QUERY_SYSTEM_PROMPT}"

    # Try OpenClaw agent first - it can also execute actions while answering
    if use_openclaw and openclaw.available:
        try:
            enriched_message = f"""Department Context:
{context}

Question: {question}"""
            answer = await openclaw.chat_with_agent(
                message=enriched_message,
                history=history or [],
            )
            return answer, sources, True
        except Exception:
            pass  # Fall through to direct K2 call

    # Direct K2-V2-Instruct call
    messages = [{"role": "system", "content": system_prompt}]

    # Add history
    if history:
        messages.extend(history[-6:])  # last 3 exchanges

    # Add context + question
    messages.append({
        "role": "user",
        "content": f"""Here is the current department knowledge:

{context}

---
Question: {question}

Answer based on the above context. If the information is not available, say so clearly.""",
    })

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{K2_INSTRUCT_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {K2_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": K2_INSTRUCT_MODEL,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.3,
            },
        )
        response.raise_for_status()

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Strip any think tags from instruct model
    if "</think_fast>" in content:
        content = content.split("</think_fast>")[-1].strip()
    if "</think>" in content:
        content = content.split("</think>")[-1].strip()

    return content, sources, False
