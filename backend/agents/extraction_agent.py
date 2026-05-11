from __future__ import annotations
"""
Extraction Agent - uses K2-Think-V2 to extract structured data from meeting transcripts.
K2-Think-V2 is the reasoning model: it thinks through the transcript and outputs clean JSON.
Falls back to OpenAI if K2 is unavailable.

Production features:
- Retry logic with exponential backoff
- Comprehensive error handling
- Input validation and sanitization
- Graceful degradation
- Automatic deadline conversion (relative -> absolute dates)
"""
import json
import re
import httpx
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 30.0  # seconds


async def retry_with_backoff(func, *args, max_retries=MAX_RETRIES, **kwargs):
    """
    Retry an async function with exponential backoff.
    Handles transient failures gracefully.
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except httpx.TimeoutException as e:
            last_exception = e
            delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
            logger.warning(f"[Retry] Timeout on attempt {attempt + 1}/{max_retries}, retrying in {delay}s...")
            await asyncio.sleep(delay)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 500, 502, 503, 504):
                last_exception = e
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                logger.warning(f"[Retry] HTTP {e.response.status_code} on attempt {attempt + 1}/{max_retries}, retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                raise  # Don't retry client errors (4xx except 429)
        except Exception as e:
            logger.error(f"[Retry] Unexpected error: {type(e).__name__}: {e}")
            raise

    logger.error(f"[Retry] All {max_retries} attempts failed")
    raise last_exception or Exception("All retry attempts failed")


def detect_meeting_date(transcript: str) -> datetime:
    """
    Detect meeting date from transcript. If not found, default to today.
    Looks for patterns like:
    - "March 30, 2026"
    - "20260330" (in filename/header)
    - "Meeting Recording March 30"
    """
    # Pattern 1: Full date like "March 30, 2026" or "30 March 2026"
    patterns = [
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
        r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(\d{4})',
        r'(\d{4})(\d{2})(\d{2}).*(?:Meeting|Recording)',  # 20260330 format
    ]

    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }

    # Check first 500 chars (usually header/title area)
    header = transcript[:500]

    for pattern in patterns:
        match = re.search(pattern, header, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                if pattern == patterns[2]:  # YYYYMMDD format
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                elif groups[0].isdigit():  # Day first format
                    day, month_name, year = int(groups[0]), groups[1].lower(), int(groups[2])
                    month = months.get(month_name, 1)
                else:  # Month first format
                    month_name, day, year = groups[0].lower(), int(groups[1]), int(groups[2])
                    month = months.get(month_name, 1)

                meeting_date = datetime(year, month, day)
                logger.info(f"[Extraction] Detected meeting date: {meeting_date.strftime('%Y-%m-%d')}")
                return meeting_date
            except (ValueError, KeyError):
                continue

    # Default to today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    logger.info(f"[Extraction] No meeting date found, using today: {today.strftime('%Y-%m-%d')}")
    return today


def convert_relative_deadline(deadline: str, meeting_date: datetime) -> str:
    """
    Convert relative deadline to actual date.
    Examples:
    - "tomorrow" -> "March 31, 2026"
    - "Wednesday" -> "April 1, 2026" (next Wednesday from meeting date)
    - "this week" -> "April 4, 2026" (Friday of meeting week)
    - "next week" -> "April 7, 2026" (Monday of next week)
    - "end of month" -> "March 31, 2026"
    """
    if not deadline:
        return deadline

    dl = deadline.lower().strip()

    # Already an actual date? Return as-is
    if re.search(r'\d{4}|\d{1,2}/\d{1,2}|january|february|march|april|may|june|july|august|september|october|november|december', dl, re.IGNORECASE):
        if not re.match(r'^(tomorrow|today|this|next|end)', dl, re.IGNORECASE):
            return deadline

    # Skip non-date values
    skip_values = ['tbd', 'not specified', 'ongoing', 'asap', 'as needed', 'n/a', '']
    if dl in skip_values:
        return deadline

    result_date = None

    # Today
    if 'today' in dl:
        result_date = meeting_date

    # Tomorrow
    elif 'tomorrow' in dl:
        result_date = meeting_date + timedelta(days=1)

    # Day of week (Monday, Tuesday, etc.)
    elif any(day in dl for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(days):
            if day in dl:
                current_weekday = meeting_date.weekday()
                target_weekday = i
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:  # Target day is today or already passed this week
                    days_ahead += 7
                result_date = meeting_date + timedelta(days=days_ahead)
                break

    # This week (assume Friday)
    elif 'this week' in dl:
        days_until_friday = (4 - meeting_date.weekday()) % 7
        if days_until_friday == 0 and meeting_date.weekday() > 4:
            days_until_friday = 7
        result_date = meeting_date + timedelta(days=days_until_friday if days_until_friday > 0 else 4)

    # Next week (assume Monday)
    elif 'next week' in dl:
        days_until_monday = (7 - meeting_date.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        result_date = meeting_date + timedelta(days=days_until_monday)

    # End of month
    elif 'end of' in dl and 'month' in dl:
        next_month = meeting_date.replace(day=28) + timedelta(days=4)
        result_date = next_month - timedelta(days=next_month.day)

    # In X days
    elif match := re.search(r'in\s+(\d+)\s+days?', dl):
        days = int(match.group(1))
        result_date = meeting_date + timedelta(days=days)

    if result_date:
        formatted = result_date.strftime('%B %d, %Y')
        # Preserve any time info from original (e.g., "tomorrow morning")
        time_info = ''
        if 'morning' in dl:
            time_info = ' (morning)'
        elif 'afternoon' in dl:
            time_info = ' (afternoon)'
        elif 'evening' in dl:
            time_info = ' (evening)'
        return formatted + time_info

    return deadline


def convert_all_deadlines(parsed: dict, meeting_date: datetime) -> dict:
    """Convert all relative deadlines in parsed extraction to actual dates."""
    if 'tasks' in parsed:
        for task in parsed['tasks']:
            if 'deadline' in task and task['deadline']:
                original = task['deadline']
                converted = convert_relative_deadline(original, meeting_date)
                if converted != original:
                    logger.info(f"[Extraction] Deadline converted: '{original}' -> '{converted}'")
                task['deadline'] = converted
    return parsed


from ..config import (
    K2_THINK_BASE_URL, K2_INSTRUCT_BASE_URL, K2_API_KEY, K2_THINK_MODEL, K2_INSTRUCT_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL
)
from ..models.schemas import ExtractionResult, Task, Decision, Risk
from .departments import get_department

EXTRACTION_SYSTEM_PROMPT = """You are a meeting intelligence agent for a department AI system.
Your job is to analyze meeting transcripts and extract ALL action items, decisions, and risks.

CRITICAL: Output ONLY valid JSON. No explanations, no reasoning, no thinking - just the JSON object.
Do NOT explain what you are doing. Do NOT write "We need to..." or "Let me...".
Start your response with { and end with }.
"""

EXTRACTION_USER_PROMPT = """Extract ALL tasks, decisions, and risks from this meeting transcript.

IMPORTANT: Be thorough! Look for EVERY action item, commitment, or follow-up mentioned.

Output ONLY this JSON (no thinking, no explanation):
{{
  "tasks": [{{ "description": "...", "owner": "...", "deadline": "...", "status": "pending", "is_update": false }}],
  "decisions": [{{ "description": "..." }}],
  "risks": [{{ "description": "...", "severity": "high|medium|low" }}],
  "summary": "..."
}}

TASK IDENTIFICATION - Look for these patterns:
1. Commitments: "I'll...", "I will...", "I'm going to...", "I need to...", "I'm gonna...", "I wanna..."
2. Requests: "Can you...", "Could you...", "Please...", "Would you...", "You need to..."
3. Assignments: "You should...", "Make sure you...", "Don't forget to...", "[Name] will..."
4. Follow-ups: "I'll follow up...", "I'll reach out...", "I'll send...", "I'll forward...", "I'll share..."
5. Action phrases: "Let me...", "I'll check with...", "I'll get back to...", "I'll update...", "I'll schedule..."
6. Team actions: "We need to...", "We should...", "Let's..." (assign to meeting organizer or "Team")

OWNER IDENTIFICATION:
- The owner is the PERSON who will DO the task (not who requests it)
- Look at speaker names (format: "Name:" or "Name  HH:MM" or "Name Surname") to identify who said "I'll..."
- If someone says "I'll send you X", the owner is the speaker
- If "[Name], can you..." then [Name] is the owner
- For "We need to..." without clear owner, use "Team" or the meeting leader
- If truly ambiguous, use "TBD" - but try to infer from context first

DEADLINE IDENTIFICATION:
- Explicit: "by Friday", "next week", "end of month", "by March 26th", "before the meeting"
- Implicit: "tomorrow", "this week", "soon", "ASAP", "today", "after this call"
- Relative: "in 2 days", "within a week", "by end of day"
- Leave empty ONLY if absolutely no time indication

EDGE CASES TO HANDLE:
- Poor transcription: Look past typos/misheard words for intent
- Multiple similar names: Use full names when available to distinguish
- Conditional tasks: "If X happens, I'll do Y" - still extract as task
- Delegated tasks: "I'll ask John to..." - owner is John, not speaker
- Updates vs new: "I finished X" is an update, "I'll finish X" is pending task

For task status:
- "pending": New task to be done
- "in_progress": Started but not complete
- "done": Explicitly completed/finished
- Set "is_update": true ONLY if updating status of previously assigned task

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
    Uses LangChain's RecursiveCharacterTextSplitter for robust splitting.
    """
    if len(transcript) <= max_chunk_size:
        return [transcript]

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        # Custom separators for meeting transcripts:
        # 1. Double newlines (paragraph breaks)
        # 2. Speaker turns (Name followed by timestamp like "John 0:04")
        # 3. Single newlines
        # 4. Sentences (period + space)
        # 5. Words (space)
        separators = [
            "\n\n",           # Paragraph breaks
            "\n",             # Line breaks
            ". ",             # Sentence boundaries
            "? ",             # Question boundaries
            "! ",             # Exclamation boundaries
            " ",              # Words
            "",               # Characters (last resort)
        ]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=500,  # Overlap to maintain context
            separators=separators,
            length_function=len,
            is_separator_regex=False,
        )

        chunks = splitter.split_text(transcript)
        print(f"[Extraction] LangChain split transcript into {len(chunks)} chunks: {[len(c) for c in chunks]} chars each")
        return chunks

    except ImportError:
        print("[Extraction] langchain-text-splitters not installed, using simple chunking")
        # Fallback: simple fixed-size chunking with overlap
        chunks = []
        overlap = 500
        pos = 0
        while pos < len(transcript):
            end = min(pos + max_chunk_size, len(transcript))
            chunks.append(transcript[pos:end])
            pos = end - overlap if end < len(transcript) else end
        print(f"[Extraction] Simple split into {len(chunks)} chunks: {[len(c) for c in chunks]} chars each")
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


CONSOLIDATION_PROMPT = """You have been given extractions from multiple parts of a long meeting transcript.
Your job is to consolidate them into a final result.

EXTRACTED DATA:
Tasks: {tasks}
Decisions: {decisions}
Risks: {risks}
Partial Summaries: {summaries}

Instructions:
1. Remove duplicate tasks (same task mentioned multiple times, possibly with slight variations)
2. Merge related tasks if they describe the same action item
3. Keep all unique decisions and risks
4. Write a coherent 2-3 sentence summary of the entire meeting

Output ONLY valid JSON (no explanation):
{{
  "tasks": [{{ "description": "...", "owner": "...", "deadline": "...", "status": "pending" }}],
  "decisions": [{{ "description": "..." }}],
  "risks": [{{ "description": "...", "severity": "high|medium|low" }}],
  "summary": "A coherent summary of the meeting..."
}}"""


async def _consolidate_extractions(merged: dict) -> dict:
    """
    Final LLM pass to consolidate/deduplicate extractions and create coherent summary.
    Uses OpenAI for reliability.
    """
    if not OPENAI_API_KEY:
        print("[Extraction] No OpenAI key for consolidation, using raw merge")
        return merged

    # Only consolidate if we have significant data
    if len(merged.get("tasks", [])) < 3:
        return merged

    tasks_text = json.dumps(merged.get("tasks", []), indent=2)
    decisions_text = json.dumps(merged.get("decisions", []), indent=2)
    risks_text = json.dumps(merged.get("risks", []), indent=2)
    summaries_text = merged.get("summary", "")

    prompt = CONSOLIDATION_PROMPT.format(
        tasks=tasks_text,
        decisions=decisions_text,
        risks=risks_text,
        summaries=summaries_text
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a meeting consolidation assistant. Output only valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 8000,
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            data = response.json()

            if "choices" in data and data["choices"]:
                content = data["choices"][0]["message"].get("content", "")
                if content:
                    consolidated = _parse_k2_response(content)
                    print(f"[Extraction] Consolidated: {len(consolidated.get('tasks', []))} tasks (was {len(merged.get('tasks', []))})")
                    return consolidated
    except Exception as e:
        print(f"[Extraction] Consolidation failed: {e}, using raw merge")

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

    # Try to parse the response
    try:
        parsed = _parse_k2_response(raw_content)
        print(f"[Extraction] Chunk {chunk_num}: Parsed {len(parsed.get('tasks', []))} tasks")
        return parsed
    except Exception as e:
        print(f"[Extraction] Chunk {chunk_num}: K2 parse failed: {e}")

        # Fallback to OpenAI if K2 returned unparseable content
        if OPENAI_API_KEY:
            print(f"[Extraction] Chunk {chunk_num}: K2 output not parseable, trying OpenAI fallback")
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
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
                        openai_content = data["choices"][0]["message"].get("content")
                        if openai_content:
                            print(f"[Extraction] Chunk {chunk_num}: OpenAI returned {len(openai_content)} characters")
                            parsed = _parse_k2_response(openai_content)
                            print(f"[Extraction] Chunk {chunk_num}: OpenAI parsed {len(parsed.get('tasks', []))} tasks")
                            return parsed
            except Exception as openai_e:
                print(f"[Extraction] Chunk {chunk_num}: OpenAI fallback also failed: {openai_e}")

        raise ValueError(f"Failed to parse response for chunk {chunk_num}: {e}")


def validate_transcript(transcript: str) -> tuple[bool, str]:
    """
    Validate transcript input before processing.
    Returns (is_valid, error_message or cleaned_transcript).
    """
    if not transcript:
        return False, "Transcript is empty"

    if not isinstance(transcript, str):
        return False, "Transcript must be a string"

    # Remove excessive whitespace while preserving structure
    cleaned = re.sub(r'\n{4,}', '\n\n\n', transcript)  # Max 3 consecutive newlines
    cleaned = cleaned.strip()

    if len(cleaned) < 30:
        return False, "Transcript too short (minimum 30 characters)"

    if len(cleaned) > 500000:  # 500KB limit
        return False, "Transcript too long (maximum 500KB)"

    # Check for actual content (not just whitespace/punctuation)
    content_chars = re.sub(r'[\s\d\W]', '', cleaned)
    if len(content_chars) < 20:
        return False, "Transcript has insufficient text content"

    return True, cleaned


def sanitize_output(text: str) -> str:
    """Sanitize extracted text to prevent XSS and injection attacks."""
    if not text:
        return ""
    # Remove potential script tags and dangerous content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    return text.strip()


async def extract_meeting(transcript: str, title: str = "", department: str = "engineering", detect_updates: bool = True) -> tuple[ExtractionResult, str, list]:
    """
    Call K2-Think-V2 to extract structured data from a meeting transcript.
    For long transcripts, automatically chunks and processes in multiple passes.
    Returns (ExtractionResult, summary_string, task_updates).

    Args:
        transcript: The meeting transcript text
        title: Optional meeting title
        department: Department for context (default: engineering)
        detect_updates: Whether to detect updates to existing tasks

    Raises:
        ValueError: If transcript is invalid
    """
    # Input validation
    is_valid, result = validate_transcript(transcript)
    if not is_valid:
        logger.error(f"[Extraction] Invalid transcript: {result}")
        raise ValueError(f"Invalid transcript: {result}")

    transcript = result  # Use cleaned transcript
    logger.info(f"[Extraction] Processing transcript: {len(transcript)} chars")

    # Detect meeting date for deadline conversion (defaults to today if not found)
    meeting_date = detect_meeting_date(transcript)
    logger.info(f"[Extraction] Meeting date: {meeting_date.strftime('%B %d, %Y (%A)')}")

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
        merged = _merge_extractions(chunk_extractions)

        # Final consolidation pass to deduplicate and create coherent summary
        parsed = await _consolidate_extractions(merged)
    else:
        # Single chunk - process directly
        parsed = await _extract_single_chunk(transcript, system_prompt)

    print(f"[Extraction] Successfully parsed JSON with {len(parsed.get('tasks', []))} tasks")

    # Convert relative deadlines to actual dates based on meeting date
    parsed = convert_all_deadlines(parsed, meeting_date)

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
