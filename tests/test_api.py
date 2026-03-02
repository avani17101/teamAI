"""Quick API test script to verify backend works correctly"""
import requests
import json

API = "http://localhost:8000"

def test_departments():
    """Test GET /api/departments"""
    print("\n🧪 Testing /api/departments...")
    r = requests.get(f"{API}/api/departments")
    print(f"Status: {r.status_code}")
    if r.ok:
        print(f"✅ Got {len(r.json())} departments")
    else:
        print(f"❌ Error: {r.text}")
    return r.ok

def test_save_org_context():
    """Test PUT /api/org/context"""
    print("\n🧪 Testing /api/org/context...")
    payload = {
        "department": "test-dept",
        "mission": "Test mission",
        "notion_database_id": "",
        "notion_page_id": ""
    }
    r = requests.put(f"{API}/api/org/context", json=payload)
    print(f"Status: {r.status_code}")
    if r.ok:
        print(f"✅ Org context saved")
    else:
        print(f"❌ Error: {r.text}")
    return r.ok

def test_add_team_member():
    """Test POST /api/team"""
    print("\n🧪 Testing /api/team...")
    payload = {
        "name": "Test User",
        "role": "Tester",
        "role_details": "",
        "responsibilities": "Testing things",
        "department": "test-dept",
        "email": "test@example.com",
        "telegram_handle": ""
    }
    r = requests.post(f"{API}/api/team", json=payload)
    print(f"Status: {r.status_code}")
    if r.ok:
        print(f"✅ Team member added: {r.json()}")
    else:
        print(f"❌ Error: {r.text}")
    return r.ok

def test_upload_meeting():
    """Test POST /api/meetings/upload"""
    print("\n🧪 Testing /api/meetings/upload...")
    payload = {
        "title": "Test Meeting",
        "transcript": "This is a test meeting transcript. John will complete the project report by Friday. Sarah needs to review the code by tomorrow. We decided to use Python for the backend.",
        "department": "test-dept",
        "auto_sync_notion": False  # Skip Notion for test
    }
    r = requests.post(f"{API}/api/meetings/upload", json=payload)
    print(f"Status: {r.status_code}")
    if r.ok:
        result = r.json()
        print(f"✅ Meeting uploaded")
        print(f"  Tasks: {len(result.get('tasks', []))}")
        print(f"  Decisions: {len(result.get('decisions', []))}")
        print(f"  Risks: {len(result.get('risks', []))}")
    else:
        print(f"❌ Error: {r.text}")
    return r.ok

def main():
    print("=" * 60)
    print("TeamAI API Test Suite")
    print("=" * 60)

    try:
        # Test basic endpoints
        results = []
        results.append(("Departments", test_departments()))
        results.append(("Org Context", test_save_org_context()))
        results.append(("Team Member", test_add_team_member()))
        results.append(("Upload Meeting", test_upload_meeting()))

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {name}")

        all_passed = all(r[1] for r in results)
        if all_passed:
            print("\n🎉 All tests passed! Backend is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check errors above.")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend at http://localhost:8000")
        print("Make sure the backend is running:")
        print("  source venv/bin/activate")
        print("  python -m backend.main")

if __name__ == "__main__":
    main()
