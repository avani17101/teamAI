"""
Integration tests for API endpoints
Tests the full meeting upload and extraction flow
"""
import pytest
import requests
import time

BASE_URL = "http://localhost:8001"


class TestAPIIntegration:
    """Integration tests for API"""

    def test_health_check(self):
        """Test basic API connectivity"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200

    def test_list_departments(self):
        """Test departments endpoint"""
        response = requests.get(f"{BASE_URL}/api/departments")
        assert response.status_code == 200

        data = response.json()
        assert "departments" in data
        assert len(data["departments"]) > 0

    def test_meeting_upload_simple(self):
        """Test uploading a simple meeting"""
        payload = {
            "title": "Test Meeting - Simple",
            "transcript": "Alice will finish report by Friday. Bob is blocked on database.",
            "department": "engineering",
            "auto_sync_notion": False
        }

        response = requests.post(
            f"{BASE_URL}/api/meetings/upload",
            json=payload,
            timeout=120
        )

        assert response.status_code == 200
        data = response.json()

        assert "meeting_id" in data
        assert "extraction" in data
        assert len(data["extraction"]["tasks"]) >= 1

    def test_meeting_upload_complex(self):
        """Test uploading a complex meeting with decisions and risks"""
        payload = {
            "title": "Sprint Planning",
            "transcript": """
[Sprint Planning Meeting]

Manager: Let's discuss sprint 15. Sarah, what are you working on?
Sarah: I'll finish the authentication module by Wednesday.

Manager: Great. We decided to use JWT tokens instead of sessions.

Tom: I'm blocked on API docs. Also, staging is down - that's a blocker.
            """,
            "department": "engineering",
            "auto_sync_notion": False
        }

        response = requests.post(
            f"{BASE_URL}/api/meetings/upload",
            json=payload,
            timeout=120
        )

        assert response.status_code == 200
        data = response.json()

        extraction = data["extraction"]
        assert len(extraction["tasks"]) >= 1
        assert len(extraction["decisions"]) >= 1
        assert len(extraction["risks"]) >= 1

    def test_get_all_meetings(self):
        """Test retrieving all meetings"""
        response = requests.get(f"{BASE_URL}/api/meetings")
        assert response.status_code == 200

        data = response.json()
        assert "meetings" in data

    def test_get_meetings_by_department(self):
        """Test filtering meetings by department"""
        response = requests.get(f"{BASE_URL}/api/meetings?department=engineering")
        assert response.status_code == 200

        data = response.json()
        for meeting in data["meetings"]:
            assert meeting["department"] == "engineering"

    def test_task_reminder_preview(self):
        """Test task reminder preview endpoint"""
        response = requests.get(f"{BASE_URL}/api/reminders/preview?days_ahead=7")
        assert response.status_code == 200

        data = response.json()
        assert "tasks_due_soon" in data
        assert "by_owner" in data

    def test_team_members(self):
        """Test team members endpoint"""
        response = requests.get(f"{BASE_URL}/api/team")
        assert response.status_code == 200

        data = response.json()
        assert "members" in data

    def test_org_context(self):
        """Test org context retrieval"""
        response = requests.get(f"{BASE_URL}/api/org/context?department=engineering")
        assert response.status_code == 200

    def test_invalid_department(self):
        """Test behavior with invalid department"""
        payload = {
            "title": "Test",
            "transcript": "Test transcript",
            "department": "nonexistent_dept_12345",
            "auto_sync_notion": False
        }

        response = requests.post(
            f"{BASE_URL}/api/meetings/upload",
            json=payload,
            timeout=120
        )

        # May return 400 for invalid department or 200 with fallback
        # Both are acceptable behaviors
        assert response.status_code in [200, 400]


class TestPerformance:
    """Performance tests"""

    def test_extraction_performance(self):
        """Test extraction completes within reasonable time"""
        payload = {
            "title": "Performance Test",
            "transcript": "Quick test. Alice will do task A. Bob will do task B. We decided X. Risk Y exists.",
            "department": "engineering",
            "auto_sync_notion": False
        }

        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/meetings/upload",
            json=payload,
            timeout=120
        )
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 30, f"Extraction took {duration}s, should be < 30s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
