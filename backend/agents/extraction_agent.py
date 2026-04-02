from __future__ import annotations
"""
Extraction Agent - uses K2-Think-V2 to extract structured data from meeting transcripts.
K2-Think-V2 is the reasoning model: it thinks through the transcript and outputs clean JSON.
Falls back to OpenAI if K2 is unavailable.
"""
import json
import re
import httpx
from typing import Optional
from ..config import (
    K2_THINK_BASE_URL, K2_INSTRUCT_BASE_URL, K2_API_KEY, K2_THINK_MODEL, K2_INSTRUCT_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL
)
from ..models.schemas import ExtractionResult, Task, Decision, Risk
from .departments import get_department

EXTRACTION_SYSTEM_PROMPT = """You are a meeting intelligence agent for a department AI system.
Your job is to analyze meeting transcripts and extract structured information.

CRITICAL: Output ONLY valid JSON. No explanations, no reasoning, no thinking - just the JSON object.
Do NOT explain what you are doing. Do NOT write "We need to..." or "Let me...".
Start your response with { and end with }.
"""

EXTRACTION_USER_PROMPT = """Extract tasks, decisions, and risks from this meeting transcript.

Output ONLY this JSON (no thinking, no explanation):
{{
  "tasks": [{{ "description": "...", "owner": "...", "deadline": "...", "status": "pending", "is_update": false }}],
  "decisions": [{{ "description": "..." }}],
  "risks": [{{ "description": "...", "severity": "high|medium|low" }}],
  "summary": "..."
}}

For tasks:
- Set "is_update": true if the transcript mentions updating, completing, or changing status of an existing task
- Set "is_update": false for new tasks being assigned
- If a task status is mentioned (e.g., "completed", "done", "in progress"), set the appropriate status

Transcript:
{transcript}"""


EXTRACTION_WITH_EXISTING_TASKS_PROMPT = """Extract tasks, decisions, and risks from this meeting transcript.

EXISTING TASKS (check if any are mentioned/updated in this meeting):
{existing_tasks}

Output ONLY this JSON (no thinking, no explanation):
{{
  "tasks": [{{ "description": "...", "owner": "...", "deadline": "...", "status": "pending", "is_update": false, "updates_task_id": null }}],
  "decisions": [{{ "description": "..." }}],
  "risks": [{{ "description": "...", "severity": "high|medium|low" }}],
  "summary": "..."
}}

For tasks:
- If the transcript mentions updating, completing, or referencing an existing task from the list above:
  - Set "is_update": true
  - Set "updates_task_id" to the ID of the existing task being updated
  - Include any new status, deadline, or owner changes
- For completely new tasks, set "is_update": false and "updates_task_id": null
- If a task status is mentioned (e.g., "completed", "done", "in progress"), set the appropriate status

Transcript:
{transcript}"""


# Maximum characters per chunk for K2 (leaves room for system prompt + output)
MAX_TRANSCRIPT_CHUNK_SIZE = 20000


def _chunk_transcript(transcript: str, max_chunk_size: int = MAX_TRANSCRIPT_CHUNK_SIZE) -> list[str]:
    """
    Split a long transcript into overlapping chunks for processing.
    Tries to split at natural boundaries (speaker turns, paragraphs).
    """
    if len(transcript) <= max_chunk_size:
        return [transcript]

    chunks = []
    # Overlap to avoid losing context at chunk boundaries
    overlap = 500

    # Find good split points (double newlines, speaker turns indicated by timestamps)
    import re
    # Common patterns: "Name 0:04", "Speaker 1:30", double newlines
    split_pattern = re.compile(r'\n\s*\n|\n[A-Z][a-zA-Z\s]+\d+:\d+')

    current_pos = 0
    while current_pos < len(transcript):
        end_pos = min(current_pos + max_chunk_size, len(transcript))

        if end_pos >= len(transcript):
            # Last chunk
            chunks.append(transcript[current_pos:])
            break

        # Look for a good split point within the last 20% of the chunk
        search_start = current_pos + int(max_chunk_size * 0.8)
        search_region = transcript[search_start:end_pos]
        matches = list(split_pattern.finditer(search_region))

        if matches:
            # Use the last good split point found
            split_at = search_start + matches[-1].start()
        else:
            # No good split point, just split at max size
            split_at = end_pos

        chunks.append(transcript[current_pos:split_at])
        # Move forward with overlap
        current_pos = max(current_pos + 1, split_at - overlap)

    print(f"[Extraction] Split transcript into {len(chunks)} chunks: {[len(c) for c in chunks]} chars each")
    return chunks


def _merge_extractions(extractions: list[dict]) -> dict:
    """
    Merge multiple chunk extractions into a single result.
    Deduplicates tasks, decisions, and risks.
    """
    merged = {
        "tasks": [],
        "decisions": [],
        "risks": [],
        "summary": ""
    }

    seen_tasks = set()
    seen_decisions = set()
    seen_risks = set()
    summaries = []

    for extraction in extractions:
        # Merge tasks (dedupe by description similarity)
        for task in extraction.get("tasks", []):
            desc = task.get("description", "") if isinstance(task, dict) else str(task)
            # Simple dedupe: lowercase, strip, take first 50 chars
            key = desc.lower().strip()[:50]
            if key and key not in seen_tasks:
                seen_tasks.add(key)
                merged["tasks"].append(task)

        # Merge decisions
        for decision in extraction.get("decisions", []):
            desc = decision.get("description", "") if isinstance(decision, dict) else str(decision)
            key = desc.lower().strip()[:50]
            if key and key not in seen_decisions:
                seen_decisions.add(key)
                merged["decisions"].append(decision)

        # Merge risks
        for risk in extraction.get("risks", []):
            desc = risk.get("description", "") if isinstance(risk, dict) else str(risk)
            key = desc.lower().strip()[:50]
            if key and key not in seen_risks:
                seen_risks.add(key)
                merged["risks"].append(risk)

        # Collect summaries
        if extraction.get("summary"):
            summaries.append(extraction["summary"])

    # Combine summaries
    if summaries:
        merged["summary"] = " ".join(summaries)

    print(f"[Extraction] Merged: {len(merged['tasks'])} tasks, {len(merged['decisions'])} decisions, {len(merged['risks'])} risks")
    return merged


def _parse_k2_response(content: str) -> dict:
    """Extract JSON from K2-Think-V2 response (strips reasoning/thinking)."""
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

    # Find ALL JSON objects and try to parse them (prefer the last complete one)
    # This handles cases where the model outputs reasoning with JSON examples before the actual answer
    json_candidates = []
    brace_count = 0
    start_idx = None

    for i, char in enumerate(content):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx is not None:
                json_candidates.append(content[start_idx:i+1])
                start_idx = None

    # Try candidates from last to first (actual answer is usually last)
    for candidate in reversed(json_candidates):
        try:
            parsed = json.loads(candidate)
            # Verify it has expected structure
            if isinstance(parsed, dict) and ("tasks" in parsed or "summary" in parsed):
                print(f"[Parse] Found valid JSON with keys: {list(parsed.keys())}")
                return parsed
        except json.JSONDecodeError:
            continue

    # Fallback: try the first match with greedy regex
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            print(f"[Parse] JSON decode failed on matched content")
            print(f"[Parse] Matched JSON (first 500 chars): {match.group()[:500]}")
            print(f"[Parse] Parse error: {e}")

    # Try parsing the stripped content directly
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError as e:
        print(f"[Parse] No valid JSON object found in K2 response")
        print(f"[Parse] Content after stripping (first 500 chars): {content.strip()[:500]}")
        raise ValueError(f"Could not extract valid JSON from K2 response: {e}")


def _is_looping_text(text: str, threshold: int = 3) -> bool:
    """Detect if text contains repetitive patterns (looping)."""
    if len(text) < 500:
        return False
    # Check for repeated phrases (100+ chars appearing 3+ times)
    for phrase_len in [100, 200, 300]:
        chunks = [text[i:i+phrase_len] for i in range(0, len(text)-phrase_len, phrase_len)]
        from collections import Counter
        counts = Counter(chunks)
        if counts.most_common(1)[0][1] >= threshold:
            print(f"[Extraction] Detected looping text (phrase repeated {counts.most_common(1)[0][1]} times)")
            return True
    return False


async def _extract_single_chunk(transcript_chunk: str, system_prompt: str, chunk_num: int = 1, total_chunks: int = 1) -> dict:
    """
    Extract tasks/decisions/risks from a single transcript chunk.
    Returns parsed dict with tasks, decisions, risks, summary.
    """
    chunk_context = ""
    if total_chunks > 1:
        chunk_context = f"\n\n[This is part {chunk_num} of {total_chunks} of a longer transcript. Extract any tasks, decisions, and risks from this section.]"

    prompt = EXTRACTION_USER_PROMPT.format(transcript=transcript_chunk) + chunk_context

    raw_content = None
    use_instruct_fallback = False

    async with httpx.AsyncClient(timeout=120.0) as client:
        # First attempt with K2-Think
        try:
            response = await client.post(
                f"{K2_THINK_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {K2_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": K2_THINK_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 16000,
                    "temperature": 0.1,
                    "repetition_penalty": 1.15,
                },
            )
            response.raise_for_status()
            data = response.json()

            if "choices" in data and data["choices"] and "message" in data["choices"][0]:
                message = data["choices"][0]["message"]
                raw_content = message.get("content") or message.get("reasoning_content") or message.get("reasoning")

                if raw_content and _is_looping_text(raw_content):
                    print(f"[Extraction] Chunk {chunk_num}: K2-Think produced looping text, falling back")
                    use_instruct_fallback = True
                    raw_content = None

        except Exception as e:
            print(f"[Extraction] Chunk {chunk_num}: K2-Think failed: {e}, falling back")
            use_instruct_fallback = True

        # Fallback to K2-Instruct
        if use_instruct_fallback or not raw_content:
            print(f"[Extraction] Chunk {chunk_num}: Using K2-Instruct fallback")
            try:
                response = await client.post(
                    f"{K2_INSTRUCT_BASE_URL}/chat/completions",
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
                        "repetition_penalty": 1.15,
                    },
                )
                response.raise_for_status()
                data = response.json()

                if "choices" in data and data["choices"] and "message" in data["choices"][0]:
                    message = data["choices"][0]["message"]
                    raw_content = message.get("content") or message.get("reasoning_content") or message.get("reasoning")
            except Exception as e:
                print(f"[Extraction] Chunk {chunk_num}: K2-Instruct also failed: {e}")

        # Fallback to OpenAI
        if not raw_content and OPENAI_API_KEY:
            print(f"[Extraction] Chunk {chunk_num}: Using OpenAI fallback ({OPENAI_MODEL})")
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": OPENAI_MODEL,
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

                if "choices" in data and data["choices"] and "message" in data["choices"][0]:
                    raw_content = data["choices"][0]["message"].get("content")
            except Exception as e:
                print(f"[Extraction] Chunk {chunk_num}: OpenAI also failed: {e}")

    if not raw_content:
        raise ValueError(f"All LLM providers failed for chunk {chunk_num}")

    print(f"[Extraction] Chunk {chunk_num}: LLM returned {len(raw_content)} characters")

    try:
        parsed = _parse_k2_response(raw_content)
        print(f"[Extraction] Chunk {chunk_num}: Parsed {len(parsed.get('tasks', []))} tasks")
        return parsed
    except Exception as e:
        print(f"[Extraction] Chunk {chunk_num}: Parse error: {e}")
        raise


async def extract_meeting(transcript: str, title: str = "", department: str = "engineering", detect_updates: bool = True) -> tuple[ExtractionResult, str, list]:
    """
    Call K2-Think-V2 to extract structured data from a meeting transcript.
    For long transcripts, automatically chunks and processes in multiple passes.
    Returns (ExtractionResult, summary_string, task_updates).
    """
    dept = get_department(department)
    dept_context = dept.get("extraction_context", "")

    # Inject department mission/priorities and team members
    from .memory_store import get_org_context, get_team_members, get_all_tasks
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

    # Existing tasks context disabled for now
    existing_tasks = []

    # Check if transcript needs chunking
    chunks = _chunk_transcript(transcript)

    if len(chunks) > 1:
        print(f"[Extraction] Long transcript ({len(transcript)} chars) - processing {len(chunks)} chunks")
        chunk_extractions = []
        for i, chunk in enumerate(chunks, 1):
            try:
                parsed = await _extract_single_chunk(chunk, system_prompt, chunk_num=i, total_chunks=len(chunks))
                chunk_extractions.append(parsed)
            except Exception as e:
                print(f"[Extraction] Chunk {i} failed: {e}, continuing with other chunks")
                continue

        if not chunk_extractions:
            raise ValueError("All chunks failed to process")

        # Merge all chunk extractions
        parsed = _merge_extractions(chunk_extractions)
    else:
        # Single chunk - process directly
        parsed = await _extract_single_chunk(transcript, system_prompt)

    print(f"[Extraction] Successfully parsed JSON with {len(parsed.get('tasks', []))} tasks")

    # Parse tasks, handling both object and string formats
    # Also track task updates
    tasks = []
    task_updates = []

    for t in parsed.get("tasks", []):
        if isinstance(t, str):
            tasks.append(Task(description=t, owner="Unassigned", deadline="Not specified", status="pending"))
        else:
            # Check if this is an update to an existing task
            is_update = t.get("is_update", False)
            updates_task_id = t.get("updates_task_id")

            # Ensure required fields have default values
            task_data = {
                "description": t.get("description", ""),
                "owner": t.get("owner") or "Unassigned",
                "deadline": t.get("deadline") or "Not specified",
                "status": t.get("status", "pending")
            }

            if is_update and updates_task_id:
                # This is an update - find the full task ID
                full_task_id = None
                for existing in existing_tasks:
                    if existing["id"].startswith(updates_task_id):
                        full_task_id = existing["id"]
                        break

                if full_task_id:
                    task_updates.append({
                        "task_id": full_task_id,
                        "updates": task_data,
                        "detected_from": "transcript"
                    })
                    continue  # Don't add as new task

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

    return ExtractionResult(tasks=tasks, decisions=decisions, risks=risks), summary, task_updates


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
            f"{K2_THINK_BASE_URL}/chat/completions",
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
