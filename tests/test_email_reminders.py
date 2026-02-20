"""
Unit tests for email reminder system
Tests deadline parsing and reminder logic
"""
import pytest
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.email_client import _parse_deadline, send_due_reminders


class TestEmailReminders:
    """Test email reminder functionality"""

    def test_parse_iso_date(self):
        """Test parsing ISO format dates"""
        result = _parse_deadline("2026-02-20")
        assert result == datetime(2026, 2, 20).date()

    def test_parse_today(self):
        """Test parsing 'today' keyword"""
        result = _parse_deadline("today")
        assert result == datetime.now().date()

    def test_parse_tomorrow(self):
        """Test parsing 'tomorrow' keyword"""
        result = _parse_deadline("tomorrow")
        assert result == datetime.now().date() + timedelta(days=1)

    def test_parse_friday(self):
        """Test parsing day of week"""
        result = _parse_deadline("Friday")
        assert result is not None
        assert result >= datetime.now().date()

    def test_parse_not_specified(self):
        """Test handling 'not specified' deadline"""
        result = _parse_deadline("Not specified")
        assert result is None

    def test_parse_empty(self):
        """Test handling empty deadline"""
        result = _parse_deadline("")
        assert result is None

    def test_parse_relative_days(self):
        """Test parsing 'in X days' format"""
        result = _parse_deadline("in 3 days")
        expected = datetime.now().date() + timedelta(days=3)
        assert result == expected

    @pytest.mark.asyncio
    async def test_send_reminders_no_tasks(self):
        """Test sending reminders with no tasks"""
        result = await send_due_reminders(
            tasks=[],
            team_members=[],
            days_ahead=1
        )

        assert result["sent"] == 0
        assert result["tasks_mentioned"] == 0

    @pytest.mark.asyncio
    async def test_send_reminders_no_due_soon(self):
        """Test sending reminders when no tasks are due soon"""
        tasks = [
            {
                "id": "1",
                "description": "Future task",
                "owner": "Alice",
                "deadline": "2027-01-01",  # Far future
                "status": "pending",
                "department": "engineering"
            }
        ]
        team_members = [
            {"name": "Alice", "email": "alice@example.com"}
        ]

        result = await send_due_reminders(tasks, team_members, days_ahead=1)

        assert result["sent"] == 0
        assert "No tasks due soon" in result.get("reason", "")

    @pytest.mark.asyncio
    async def test_reminder_skips_completed(self):
        """Test that reminders skip completed tasks"""
        today = datetime.now().date()
        tasks = [
            {
                "id": "1",
                "description": "Completed task",
                "owner": "Alice",
                "deadline": today.isoformat(),
                "status": "completed",  # Should be skipped
                "department": "engineering"
            }
        ]
        team_members = [{"name": "Alice", "email": "alice@example.com"}]

        result = await send_due_reminders(tasks, team_members, days_ahead=1)

        assert result["tasks_mentioned"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
