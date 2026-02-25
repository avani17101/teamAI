#!/usr/bin/env python3
"""
Test K2-Think-V2 extraction with different parameters
"""
import asyncio
import httpx
import json

K2_THINK_BASE_URL = "http://build-api-2.ifmapp.net:8000"
K2_API_KEY = "sk-XRQV0fFqJ7VfUIcfswIpZTckzFfL8LTqC1M2R1O30z7d2KQA2S"

async def test_extraction():
    test_prompt = """Extract tasks, decisions, and risks from this meeting transcript.

Output ONLY this JSON (no thinking, no explanation):
{
  "tasks": [{ "description": "...", "owner": "...", "deadline": "...", "status": "pending" }],
  "decisions": [{ "description": "..." }],
  "risks": [{ "description": "...", "severity": "high|medium|low" }],
  "summary": "..."
}

Transcript:
Team standup:
- Alice will finish the dashboard redesign by Friday
- Decision: We'll use React instead of Vue
- Risk: Timeline is aggressive, high severity
- Bob will review the PR tomorrow
"""

    print("Testing K2-Think-V2 extraction...")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{K2_THINK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {K2_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "LLM360/K2-Think-V2",
                "messages": [
                    {"role": "system", "content": "You are a meeting intelligence agent. Always respond with valid JSON only."},
                    {"role": "user", "content": test_prompt},
                ],
                "max_tokens": 2000,
                "temperature": 0.0,  # Deterministic
            },
        )

        data = response.json()
        message = data["choices"][0]["message"]

        print(f"\nResponse fields: {list(message.keys())}")
        print(f"\nContent: {message.get('content', 'None')}")
        print(f"\nReasoning: {message.get('reasoning', 'None')[:500] if message.get('reasoning') else 'None'}")
        print(f"\nReasoning_content: {message.get('reasoning_content', 'None')[:500] if message.get('reasoning_content') else 'None'}")

        # Try to find JSON
        raw = message.get("content") or message.get("reasoning_content") or message.get("reasoning") or ""
        print(f"\n\nFull raw output ({len(raw)} chars):\n{raw[:1000]}")

        # Try parsing
        if "</think_fast>" in raw:
            raw = raw.split("</think_fast>")[-1].strip()
        if "</think>" in raw:
            raw = raw.split("</think>")[-1].strip()

        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                print("\n\n✅ Successfully parsed JSON:")
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError as e:
                print(f"\n\n❌ JSON parse failed: {e}")
        else:
            print("\n\n❌ No JSON object found in response")

asyncio.run(test_extraction())
