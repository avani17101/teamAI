#!/usr/bin/env python3
"""
Direct K2-Think-V2 API test on real transcript
"""
import asyncio
import httpx
import json
import re

K2_THINK_BASE_URL = "http://build-api-2.ifmapp.net:8000"
K2_API_KEY = "sk-XRQV0fFqJ7VfUIcfswIpZTckzFfL8LTqC1M2R1O30z7d2KQA2S"

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

async def test_extraction():
    # Read the real transcript
    with open('/Users/avanigupta/teamAI/transcript_sample.txt', 'r') as f:
        transcript = f.read()

    print("Testing K2-Think-V2 extraction on real transcript...")
    print("=" * 70)
    print(f"Transcript length: {len(transcript)} characters")
    print("=" * 70)

    prompt = EXTRACTION_USER_PROMPT.format(transcript=transcript)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{K2_THINK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {K2_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "LLM360/K2-Think-V2",
                "messages": [
                    {"role": "system", "content": "You are a meeting intelligence agent for a department AI system. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 8000,
                "temperature": 0.0,
            },
        )

        data = response.json()
        message = data["choices"][0]["message"]
        raw_content = message.get("content") or message.get("reasoning_content") or message.get("reasoning")

        print(f"\n📊 Response length: {len(raw_content)} characters")
        print(f"\n📄 First 500 chars:\n{raw_content[:500]}")

        # Parse JSON
        if "</think_fast>" in raw_content:
            raw_content = raw_content.split("</think_fast>")[-1].strip()
        if "</think>" in raw_content:
            raw_content = raw_content.split("</think>")[-1].strip()

        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if match:
            parsed = json.loads(match.group())

            print("\n" + "=" * 70)
            print("✅ EXTRACTION SUCCESSFUL")
            print("=" * 70)

            print(f"\n📋 TASKS ({len(parsed.get('tasks', []))}):")
            for i, task in enumerate(parsed.get('tasks', []), 1):
                desc = task.get('description', '') if isinstance(task, dict) else task
                owner = task.get('owner', 'Unassigned') if isinstance(task, dict) else 'Unassigned'
                deadline = task.get('deadline', 'Not specified') if isinstance(task, dict) else 'Not specified'
                print(f"\n  {i}. {desc}")
                print(f"     Owner: {owner}")
                print(f"     Deadline: {deadline}")

            print(f"\n✅ DECISIONS ({len(parsed.get('decisions', []))}):")
            for i, decision in enumerate(parsed.get('decisions', []), 1):
                desc = decision.get('description', '') if isinstance(decision, dict) else decision
                print(f"  {i}. {desc}")

            print(f"\n⚠️  RISKS ({len(parsed.get('risks', []))}):")
            for i, risk in enumerate(parsed.get('risks', []), 1):
                desc = risk.get('description', '') if isinstance(risk, dict) else risk
                severity = risk.get('severity', 'medium') if isinstance(risk, dict) else 'medium'
                print(f"  {i}. [{severity.upper()}] {desc}")

            summary = parsed.get('summary', '')
            print(f"\n📝 SUMMARY:")
            print(f"  {summary[:300]}..." if len(summary) > 300 else f"  {summary}")

            print("\n" + "=" * 70)
            print("✅ Test PASSED! Real transcript extraction working.")
            print("=" * 70)

        else:
            print("\n❌ No JSON found in response")
            print(f"Full response:\n{raw_content}")

asyncio.run(test_extraction())
