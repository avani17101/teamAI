from __future__ import annotations
"""
Extraction Agent - uses K2-Think-V2 to extract structured data from meeting transcripts.
K2-Think-V2 is the reasoning model: it thinks through the transcript and outputs clean JSON.
"""
import json
import re
import httpx
from typing import Optional
from ..config import K2_THINK_BASE_URL, K2_INSTRUCT_BASE_URL, K2_API_KEY, K2_THINK_MODEL, K2_INSTRUCT_MODEL
from ..models.schemas import ExtractionResult, Task, Decision, Risk
from .departments import get_department

EXTRACTION_SYSTEM_PROMPT = """You are a meeting intelligence agent for a department AI system.
Your job is to analyze meeting transcripts and extract structured information.
Always respond with valid JSON only - no markdown, no explanation outside the JSON.
"""

EXTRACTION_USER_PROMPT = """Extract tasks, decisions, and risks from this meeting transcript.

Output ONLY this JSON (no thinking, no explanation):
{{
  "tasks": [{{ "description": "...", "owner": "...", "deadline": "...", "status": "pending" }}],
  "decisions": [{{ "description": "..." }}],
  "risks": [{{ "description": "...", "severity": "high|medium|low" }}],
  "summary": "..."
}}

Transcript:
{transcript}"""


def _parse_k2_response(content: str) -> dict:
    """Extract JSON from K2-Think-V2 response (strips <think_fast> reasoning tags)."""
    # Handle None or empty content
    if not content:
        raise ValueError("K2 API returned empty response")

    # K2-Think-V2 outputs reasoning then </think_fast> then the answer
    if "</think_fast>" in content:
        content = content.split("</think_fast>")[-1].strip()
    if "</think>" in content:
        content = content.split("</think>")[-1].strip()

    # Strip any markdown code blocks
    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"```\s*", "", content)

    # Find JSON object
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        return json.loads(match.group())

    return json.loads(content.strip())


async def extract_meeting(transcript: str, title: str = "", department: str = "engineering") -> tuple[ExtractionResult, str]:
    """
    Call K2-Think-V2 to extract structured data from a meeting transcript.
    Returns (ExtractionResult, summary_string).
    """
    dept = get_department(department)
    dept_context = dept.get("extraction_context", "")

    # Inject department mission/priorities and team members
    from .memory_store import get_org_context, get_team_members
    org_ctx = get_org_context(department)
    mission = org_ctx.get("mission", "").strip()
    if mission:
        dept_context += f"\n\nDepartment Mission & Priorities:\n{mission}"

    # Add team member context for better task assignment
    team_members = get_team_members(department=department)
    if team_members:
        dept_context += "\n\nTeam Members:"
        for member in team_members:
            member_info = f"\n- {member['name']}"
            if member.get('role'):
                member_info += f" ({member['role']})"
            if member.get('responsibilities'):
                member_info += f": {member['responsibilities']}"
            dept_context += member_info
        dept_context += "\n\nWhen extracting tasks, assign to the most appropriate team member based on their responsibilities."

    system_prompt = EXTRACTION_SYSTEM_PROMPT + f"\n\nDepartment: {dept['name']}\n{dept_context}"
    prompt = EXTRACTION_USER_PROMPT.format(transcript=transcript)

    # Use K2-V2-Instruct for extraction (direct output, no reasoning loops)
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{K2_INSTRUCT_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {K2_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": K2_INSTRUCT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 4000,
                "temperature": 0.1,
            },
        )
        response.raise_for_status()

    data = response.json()

    # Better error handling for API response
    if "choices" not in data or not data["choices"]:
        raise ValueError(f"K2 API returned invalid response: {data}")

    if "message" not in data["choices"][0]:
        raise ValueError(f"K2 API response missing message: {data['choices'][0]}")

    message = data["choices"][0]["message"]

    # K2-V2-Instruct returns content in 'content' field
    # K2-Think-V2 may return in 'reasoning_content' or 'reasoning' fields
    raw_content = message.get("content") or message.get("reasoning_content") or message.get("reasoning")

    if not raw_content:
        raise ValueError(f"K2 API returned empty content. Message: {message}")

    try:
        parsed = _parse_k2_response(raw_content)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse K2-Think-V2 response: {e}\nRaw: {raw_content[:500] if raw_content else 'None'}")

    # Parse tasks, handling both object and string formats
    tasks = []
    for t in parsed.get("tasks", []):
        if isinstance(t, str):
            tasks.append(Task(description=t, owner="Unassigned", deadline="Not specified", status="pending"))
        else:
            # Ensure required fields have default values
            task_data = {
                "description": t.get("description", ""),
                "owner": t.get("owner") or "Unassigned",
                "deadline": t.get("deadline") or "Not specified",
                "status": t.get("status", "pending")
            }
            tasks.append(Task(**task_data))

    # Parse decisions, handling both object and string formats
    decisions = []
    for d in parsed.get("decisions", []):
        if isinstance(d, str):
            decisions.append(Decision(description=d))
        else:
            decisions.append(Decision(**d))

    # Parse risks, handling both object and string formats
    risks = []
    for r in parsed.get("risks", []):
        if isinstance(r, str):
            risks.append(Risk(description=r, severity="medium"))
        else:
            # Ensure required fields have default values
            risk_data = {
                "description": r.get("description", ""),
                "severity": r.get("severity") or "medium"
            }
            risks.append(Risk(**risk_data))

    summary = parsed.get("summary", "")

    return ExtractionResult(tasks=tasks, decisions=decisions, risks=risks), summary


async def detect_cross_meeting_insights(
    new_extraction: ExtractionResult,
    previous_extractions: list[dict],
) -> list[str]:
    """
    Use K2-Think-V2 to find conflicts, ownership gaps, and patterns across meetings.
    This is the differentiator feature - cross-meeting reasoning.
    """
    if not previous_extractions:
        return []

    context = json.dumps(
        {
            "new_meeting": {
                "tasks": [t.dict() for t in new_extraction.tasks],
                "decisions": [d.dict() for d in new_extraction.decisions],
                "risks": [r.dict() for r in new_extraction.risks],
            },
            "previous_meetings": previous_extractions[-5:],  # last 5 meetings
        },
        indent=2,
    )

    prompt = f"""Analyze these meeting records and identify:
1. Tasks with no owner assigned
2. Contradictions between new and previous decisions
3. Recurring risks that haven't been resolved
4. People who are overloaded with tasks
5. Missing follow-ups from previous meetings

Return ONLY a JSON array of insight strings:
["insight 1", "insight 2", ...]

Meeting data:
{context}"""

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{K2_THINK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {K2_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": K2_THINK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.1,
            },
        )
        response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"]

    try:
        parsed = _parse_k2_response(raw)
        if isinstance(parsed, list):
            return parsed
        # Sometimes model wraps in object
        return parsed.get("insights", parsed.get("items", []))
    except Exception:
        # Extract array from text as fallback
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
