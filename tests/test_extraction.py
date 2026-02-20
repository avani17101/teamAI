"""
Unit tests for extraction agent
Tests K2-Instruct extraction functionality
"""
import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.extraction_agent import extract_meeting, _parse_k2_response


class TestExtractionAgent:
    """Test extraction agent functionality"""

    @pytest.mark.asyncio
    async def test_simple_extraction(self):
        """Test extraction from simple transcript"""
        transcript = "Alice will finish the report by Friday. Bob is working on the database."
        result, summary = await extract_meeting(transcript, "Test Meeting", "engineering")

        assert len(result.tasks) >= 1, "Should extract at least 1 task"
        assert summary != "", "Should generate a summary"

    @pytest.mark.asyncio
    async def test_complex_extraction(self):
        """Test extraction from complex transcript with decisions and risks"""
        transcript = """
        [Sprint Planning]

        Manager: Sarah, what are you working on?
        Sarah: I'll finish the authentication by Wednesday.

        Manager: We decided to use JWT tokens for authentication.

        Tom: There's a risk - the staging environment is down.
        """

        result, summary = await extract_meeting(transcript, "Sprint Planning", "engineering")

        assert len(result.tasks) >= 1, "Should extract tasks"
        assert len(result.decisions) >= 1, "Should extract decisions"
        assert len(result.risks) >= 1, "Should extract risks"

    @pytest.mark.asyncio
    async def test_empty_transcript(self):
        """Test handling of empty transcript"""
        transcript = ""
        result, summary = await extract_meeting(transcript, "Empty", "engineering")

        # Should not crash, may return empty results
        assert result is not None

    def test_parse_k2_response_with_reasoning(self):
        """Test parsing K2 response with reasoning tags"""
        content = """
        </think_fast>
        {
            "tasks": [{"description": "Test task", "owner": "Alice", "deadline": "Friday", "status": "pending"}],
            "decisions": [],
            "risks": [],
            "summary": "Test summary"
        }
        """

        parsed = _parse_k2_response(content)
        assert "tasks" in parsed
        assert len(parsed["tasks"]) == 1

    def test_parse_k2_response_with_markdown(self):
        """Test parsing K2 response with markdown code blocks"""
        content = """
        ```json
        {
            "tasks": [],
            "decisions": [{"description": "Use PostgreSQL"}],
            "risks": [],
            "summary": "Test"
        }
        ```
        """

        parsed = _parse_k2_response(content)
        assert "decisions" in parsed
        assert len(parsed["decisions"]) == 1

    @pytest.mark.asyncio
    async def test_department_specific_extraction(self):
        """Test extraction with department-specific context"""
        transcript = "We need to post about the new product launch on social media by Monday."

        result, summary = await extract_meeting(transcript, "MarCom Meeting", "marcom")

        assert len(result.tasks) >= 1
        # MarCom department should understand social media context


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
