#!/usr/bin/env python3
"""
End-to-end validation for TeamAI demo.
Tests all critical functionality without external dependencies.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

async def validate_k2_api():
    """Test K2 API connectivity."""
    print("\n🔍 Testing K2 API...")
    try:
        import httpx
        from backend.config import K2_THINK_BASE_URL, K2_INSTRUCT_BASE_URL, K2_API_KEY

        # Test K2-Think-V2
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{K2_THINK_BASE_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {K2_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "LLM360/K2-Think-V2",
                    "messages": [{"role": "user", "content": "Say 'OK'"}],
                    "max_tokens": 5
                }
            )
            assert response.status_code == 200, f"K2-Think API failed: {response.status_code}"
            print("   ✅ K2-Think-V2 API working")

        # Test K2-V2-Instruct
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{K2_INSTRUCT_BASE_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {K2_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "LLM360/K2-V2-Instruct",
                    "messages": [{"role": "user", "content": "Say 'OK'"}],
                    "max_tokens": 5
                }
            )
            assert response.status_code == 200, f"K2-Instruct API failed: {response.status_code}"
            print("   ✅ K2-V2-Instruct API working")

        return True
    except Exception as e:
        print(f"   ❌ K2 API failed: {e}")
        return False


async def validate_notion():
    """Test Notion API connectivity."""
    print("\n🔍 Testing Notion API...")
    try:
        import httpx
        from backend.config import NOTION_API_KEY, NOTION_DATABASE_ID

        if not NOTION_API_KEY:
            print("   ⚠️  Notion API key not configured (optional)")
            return True

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}",
                headers={
                    "Authorization": f"Bearer {NOTION_API_KEY}",
                    "Notion-Version": "2022-06-28"
                }
            )
            if response.status_code == 200:
                data = response.json()
                db_name = data.get("title", [{}])[0].get("plain_text", "Unknown")
                print(f"   ✅ Connected to Notion database: {db_name}")
                return True
            else:
                print(f"   ❌ Notion API failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Notion test failed: {e}")
        return False


def validate_email():
    """Test email configuration."""
    print("\n🔍 Testing Email Configuration...")
    try:
        from backend.config import SMTP_HOST, SMTP_USER, SMTP_PASS, TEAMAI_EMAIL, TEAMAI_EMAIL_PASSWORD

        if not SMTP_USER or not SMTP_PASS:
            print("   ⚠️  SMTP not configured (optional)")
        else:
            print(f"   ✅ SMTP configured: {SMTP_USER}@{SMTP_HOST}")

        if not TEAMAI_EMAIL or not TEAMAI_EMAIL_PASSWORD:
            print("   ⚠️  IMAP not configured (optional)")
        else:
            print(f"   ✅ IMAP configured: {TEAMAI_EMAIL}")

        return True
    except Exception as e:
        print(f"   ❌ Email config failed: {e}")
        return False


def validate_database():
    """Test database connectivity."""
    print("\n🔍 Testing Database...")
    try:
        import sqlite3
        from backend.config import DB_PATH

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check tables exist
        tables = ["meetings", "tasks", "decisions", "risks", "team_members", "org_context"]
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        missing = set(tables) - existing_tables
        if missing:
            print(f"   ⚠️  Missing tables: {missing}")
        else:
            print(f"   ✅ All database tables present")

        # Count records
        cursor.execute("SELECT COUNT(*) FROM meetings")
        meeting_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tasks")
        task_count = cursor.fetchone()[0]

        print(f"   📊 {meeting_count} meetings, {task_count} tasks")

        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False


async def validate_extraction():
    """Test meeting extraction."""
    print("\n🔍 Testing Meeting Extraction...")
    try:
        from backend.agents.extraction_agent import extract_meeting

        test_transcript = """
        Team meeting notes:
        - Alice will finish the report by Friday
        - Decision: Use React for the frontend
        - Risk: Timeline is tight, high severity
        """

        result, summary = await extract_meeting(
            transcript=test_transcript,
            title="Test Meeting",
            department="engineering"
        )

        print(f"   ✅ Extraction working: {len(result.tasks)} tasks, {len(result.decisions)} decisions, {len(result.risks)} risks")
        if summary:
            print(f"   📝 Summary: {summary[:80]}...")

        return True
    except Exception as e:
        print(f"   ❌ Extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 70)
    print("  TeamAI - End-to-End Validation")
    print("=" * 70)

    results = []

    # Run all validations
    results.append(await validate_k2_api())
    results.append(await validate_notion())
    results.append(validate_email())
    results.append(validate_database())
    results.append(await validate_extraction())

    # Summary
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("=" * 70)
        print("\n🚀 TeamAI is ready for demo!")
        print("\nStart the backend:")
        print("  uvicorn backend.main:app --reload --port 8001")
        print("\nThen open: http://localhost:8001")
        return 0
    else:
        print(f"⚠️  SOME CHECKS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
