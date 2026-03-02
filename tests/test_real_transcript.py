#!/usr/bin/env python3
"""
Test extraction on the real transcript from transcript_sample.txt
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from backend.agents.extraction_agent import extract_meeting

async def test_real_transcript():
    # Read the transcript
    with open('/Users/avanigupta/teamAI/transcript_sample.txt', 'r') as f:
        transcript = f.read()

    print("Testing extraction on real transcript...")
    print("=" * 70)
    print(f"Transcript length: {len(transcript)} characters")
    print("=" * 70)

    try:
        result, summary = await extract_meeting(
            transcript=transcript,
            title="Finance Operations Meeting",
            department="innovation"
        )

        print("\n✅ EXTRACTION SUCCESSFUL")
        print("=" * 70)

        print(f"\n📋 TASKS ({len(result.tasks)}):")
        for i, task in enumerate(result.tasks, 1):
            print(f"\n  {i}. {task.description}")
            print(f"     Owner: {task.owner}")
            print(f"     Deadline: {task.deadline}")
            print(f"     Status: {task.status}")

        print(f"\n✅ DECISIONS ({len(result.decisions)}):")
        for i, decision in enumerate(result.decisions, 1):
            print(f"  {i}. {decision.description}")

        print(f"\n⚠️  RISKS ({len(result.risks)}):")
        for i, risk in enumerate(result.risks, 1):
            print(f"  {i}. [{risk.severity.upper()}] {risk.description}")

        print(f"\n📝 SUMMARY:")
        print(f"  {summary[:300]}..." if len(summary) > 300 else f"  {summary}")

        print("\n" + "=" * 70)
        print("✅ Test passed! Extraction working correctly.")

        return True

    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_transcript())
    sys.exit(0 if success else 1)
