#!/usr/bin/env python3
"""Test K2-V2-Instruct extraction directly"""
import requests
import json

# Use the Innovation sample transcript
TRANSCRIPT = """[Innovation Lab Weekly Sync | Feb 16, 10:00 AM]

[Prof. Ibrahim Al-Mansour, Lab Director]
Good morning everyone. Let's jump right in. Aisha, give us an update on the ACL submission.

[Dr. Aisha Rahman, Research Lead]
So... the deadline is March 15th, which gives us about 4 weeks. The paper itself is solid, but we still haven't finished the benchmark experiments. And here's the problem - I need GPU access on the cluster, but it's totally maxed out right now. Like 95% utilization. Another team is running their models 24/7.

[Ibrahim]
That's a blocker. I'll talk to IT today about expanding capacity or getting you priority access. Mohammed, what's happening with the TechCorp MoU?

[Mohammed Al-Hashimi, Partnerships]
Yeah, it's in final legal review. I'm following up with legal tomorrow to nail down the signing date. We're targeting end of month, so that's, like, two weeks from now.

[Ibrahim]
Good. Keep on them. Nadia, Sara - grant application?

[Dr. Nadia Khan, Research Scientist]
ADEK grant is due March 20th. I'm writing the technical proposal, Sara's doing the financials. We're asking for 2 million dirhams. Both parts should be done by next week, then we need to merge and review everything by March 17th.

[Sara Ahmed, Program Manager]
Yep, on track for that.

[Meeting ends 10:38 AM]"""

SYSTEM_PROMPT = """You are a meeting intelligence agent for a department AI system.
Your job is to analyze meeting transcripts and extract structured information.
Always respond with valid JSON only - no markdown, no explanation outside the JSON.

Department: Industry Innovation
Focus on:
- Research milestones: paper submissions, dataset releases, model evaluations
- Industry partnerships: MoUs, pilots, joint projects
- Grant applications and funding deadlines
- Innovation lab experiments and prototypes
- IP and patent filing tasks
- Conference submissions and presentations"""

USER_PROMPT = """Extract tasks, decisions, and risks from this meeting transcript.

Output ONLY this JSON (no thinking, no explanation):
{
  "tasks": [{ "description": "...", "owner": "...", "deadline": "...", "status": "pending" }],
  "decisions": [{ "description": "..." }],
  "risks": [{ "description": "...", "severity": "high|medium|low" }],
  "summary": "..."
}

Transcript:
""" + TRANSCRIPT

print("=" * 80)
print("TESTING K2-V2-Instruct DIRECT CALL")
print("=" * 80)
print(f"\nCalling: http://instruct-api-3.ifmapp.net:8000/v1/chat/completions")
print(f"Model: LLM360/K2-V2-Instruct")
print(f"Temperature: 0.0")
print(f"Max tokens: 8000")
print()

response = requests.post(
    "http://instruct-api-3.ifmapp.net:8000/v1/chat/completions",
    headers={
        "Authorization": "Bearer sk-XRQV0fFqJ7VfUIcfswIpZTckzFfL8LTqC1M2R1O30z7d2KQA2S",
        "Content-Type": "application/json",
    },
    json={
        "model": "LLM360/K2-V2-Instruct",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        "max_tokens": 8000,
        "temperature": 0.0,
    },
    timeout=120.0,
)

print(f"Response status: {response.status_code}")
print()

if response.status_code == 200:
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    print(f"Response length: {len(content)} characters")
    print()
    print("=" * 80)
    print("RAW RESPONSE:")
    print("=" * 80)
    print(content)
    print()
    print("=" * 80)

    # Try to parse as JSON
    try:
        # Look for JSON object
        import re
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            print("✅ SUCCESSFULLY PARSED JSON")
            print()
            print(json.dumps(parsed, indent=2))
        else:
            print("❌ NO JSON OBJECT FOUND IN RESPONSE")
    except json.JSONDecodeError as e:
        print(f"❌ JSON PARSE ERROR: {e}")
else:
    print(f"❌ API ERROR: {response.text}")
