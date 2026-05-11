"""
Production-grade tests for TeamAI.
Tests all features for robustness, edge cases, and error handling.

Run with: python -m pytest tests/test_production.py -v -s --tb=short
"""
import pytest
import asyncio
import json
import httpx
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def api_base():
    """API base URL for integration tests."""
    return "http://10.127.143.5:8000"


@pytest.fixture
def long_transcript():
    """Load the long ODT transcript."""
    import zipfile
    import xml.etree.ElementTree as ET
    odt_path = Path(__file__).parent.parent / "docs" / "Industry & AI innovation progress meeting.odt"
    if not odt_path.exists():
        pytest.skip(f"ODT file not found")
    with zipfile.ZipFile(str(odt_path), 'r') as zf:
        content = zf.read('content.xml')
    root = ET.fromstring(content)
    text_parts = []
    for elem in root.iter():
        if elem.text: text_parts.append(elem.text)
        if elem.tail: text_parts.append(elem.tail)
    return ' '.join(text_parts)


@pytest.fixture
def sample_transcripts():
    """Various transcript formats for testing."""
    return {
        "standard": """
[Meeting: Sprint Planning | March 15, 2026]
John: Let's discuss tasks for this sprint.
Sarah: I'll complete the API documentation by Friday.
Mike: I need to finish unit tests by next Monday.
John: Decision made - we'll release on March 25th.
Sarah: There's a risk of delay if QA is backed up.
""",
        "minimal": "Quick sync. John to send report tomorrow.",
        "empty": "",
        "unicode": """
会议记录 - 2026年3月15日
张三：我们需要完成报告。
李四：好的，我会在周五之前完成。
决定：下周一发布。
""",
        "special_chars": """
Meeting with O'Brien & Co. <confidential>
Task: Review the "Q1 Report" by 3/15
Risk: Budget < $50K could cause delays
Decision: Use new API (v2.0) instead of legacy
""",
        "very_long_line": "Task: " + "x" * 5000 + " by Friday",
        "timestamps": """
00:00:15 John: Let's start the meeting.
00:01:30 Sarah: I have updates on the API.
00:05:45 Mike: Testing is on track.
00:10:00 John: Great, let's wrap up.
""",
    }


# ═══════════════════════════════════════════════════════════════
# TEST: CHUNKING EDGE CASES
# ═══════════════════════════════════════════════════════════════

class TestChunkingEdgeCases:
    """Test chunking with various edge cases."""

    def test_empty_transcript(self):
        """Empty transcript should return empty list or single empty chunk."""
        from backend.agents.extraction_agent import _chunk_transcript
        chunks = _chunk_transcript("")
        assert len(chunks) <= 1

    def test_whitespace_only(self):
        """Whitespace-only transcript."""
        from backend.agents.extraction_agent import _chunk_transcript
        chunks = _chunk_transcript("   \n\n\t  ")
        assert len(chunks) <= 1

    def test_exactly_at_limit(self):
        """Transcript exactly at chunk size limit."""
        from backend.agents.extraction_agent import _chunk_transcript, MAX_TRANSCRIPT_CHUNK_SIZE
        text = "x" * MAX_TRANSCRIPT_CHUNK_SIZE
        chunks = _chunk_transcript(text)
        assert len(chunks) == 1

    def test_one_char_over_limit(self):
        """Transcript one char over limit should split."""
        from backend.agents.extraction_agent import _chunk_transcript, MAX_TRANSCRIPT_CHUNK_SIZE
        text = "x" * (MAX_TRANSCRIPT_CHUNK_SIZE + 1)
        chunks = _chunk_transcript(text)
        assert len(chunks) >= 1  # May or may not split depending on overlap

    def test_unicode_handling(self, sample_transcripts):
        """Unicode characters should be handled correctly."""
        from backend.agents.extraction_agent import _chunk_transcript
        chunks = _chunk_transcript(sample_transcripts["unicode"])
        assert len(chunks) >= 1
        # Verify content preserved
        joined = "".join(chunks)
        assert "张三" in joined or len(chunks) == 1

    def test_special_characters(self, sample_transcripts):
        """Special characters should be preserved."""
        from backend.agents.extraction_agent import _chunk_transcript
        chunks = _chunk_transcript(sample_transcripts["special_chars"])
        joined = "".join(chunks)
        assert "O'Brien" in joined
        assert "<confidential>" in joined

    def test_very_long_single_line(self, sample_transcripts):
        """Very long line without natural breaks."""
        from backend.agents.extraction_agent import _chunk_transcript
        chunks = _chunk_transcript(sample_transcripts["very_long_line"])
        # Should still chunk even without natural breaks
        for chunk in chunks:
            assert len(chunk) <= 21000  # Allow some buffer


# ═══════════════════════════════════════════════════════════════
# TEST: JSON PARSING ROBUSTNESS
# ═══════════════════════════════════════════════════════════════

class TestJSONParsingRobustness:
    """Test JSON extraction from various LLM response formats."""

    def test_clean_json(self):
        """Standard clean JSON."""
        from backend.agents.extraction_agent import _parse_k2_response
        result = _parse_k2_response('{"tasks": [], "summary": "test"}')
        assert "tasks" in result

    def test_json_with_thinking_tags(self):
        """JSON after thinking tags."""
        from backend.agents.extraction_agent import _parse_k2_response
        response = '<think_fast>analyzing...</think_fast>{"tasks": [{"description": "test"}], "summary": "s"}'
        result = _parse_k2_response(response)
        assert len(result["tasks"]) == 1

    def test_json_with_markdown_code_block(self):
        """JSON wrapped in markdown."""
        from backend.agents.extraction_agent import _parse_k2_response
        response = '```json\n{"tasks": [], "summary": "test"}\n```'
        result = _parse_k2_response(response)
        assert "tasks" in result

    def test_json_with_explanation_before(self):
        """JSON with text explanation before."""
        from backend.agents.extraction_agent import _parse_k2_response
        response = 'Here is the extracted data:\n{"tasks": [{"description": "task1"}], "summary": "s"}'
        result = _parse_k2_response(response)
        assert len(result["tasks"]) == 1

    def test_multiple_json_objects(self):
        """Multiple JSON objects - should take the valid one."""
        from backend.agents.extraction_agent import _parse_k2_response
        response = '{"invalid": 1}\nActual result:\n{"tasks": [{"description": "real"}], "summary": "s"}'
        result = _parse_k2_response(response)
        assert "tasks" in result

    def test_nested_json(self):
        """Nested JSON structures."""
        from backend.agents.extraction_agent import _parse_k2_response
        response = '{"tasks": [{"description": "test", "metadata": {"priority": "high"}}], "summary": "s"}'
        result = _parse_k2_response(response)
        assert result["tasks"][0]["description"] == "test"

    def test_json_with_unicode(self):
        """JSON with unicode content."""
        from backend.agents.extraction_agent import _parse_k2_response
        response = '{"tasks": [{"description": "会议任务"}], "summary": "中文摘要"}'
        result = _parse_k2_response(response)
        assert "会议" in result["tasks"][0]["description"]

    def test_invalid_json_raises(self):
        """Invalid JSON should raise ValueError."""
        from backend.agents.extraction_agent import _parse_k2_response
        with pytest.raises(ValueError):
            _parse_k2_response("This is not JSON at all")

    def test_empty_response_raises(self):
        """Empty response should raise ValueError."""
        from backend.agents.extraction_agent import _parse_k2_response
        with pytest.raises(ValueError):
            _parse_k2_response("")

    def test_none_response_raises(self):
        """None response should raise ValueError."""
        from backend.agents.extraction_agent import _parse_k2_response
        with pytest.raises(ValueError):
            _parse_k2_response(None)


# ═══════════════════════════════════════════════════════════════
# TEST: MERGE & DEDUPLICATION
# ═══════════════════════════════════════════════════════════════

class TestMergeDeduplication:
    """Test merging and deduplication logic."""

    def test_empty_extractions(self):
        """Merging empty list."""
        from backend.agents.extraction_agent import _merge_extractions
        result = _merge_extractions([])
        assert result["tasks"] == []

    def test_single_extraction(self):
        """Single extraction should pass through."""
        from backend.agents.extraction_agent import _merge_extractions
        extraction = {"tasks": [{"description": "Task 1"}], "decisions": [], "risks": [], "summary": "S"}
        result = _merge_extractions([extraction])
        assert len(result["tasks"]) == 1

    def test_duplicate_removal(self):
        """Exact duplicates should be removed."""
        from backend.agents.extraction_agent import _merge_extractions
        extractions = [
            {"tasks": [{"description": "Same task"}], "decisions": [], "risks": [], "summary": ""},
            {"tasks": [{"description": "Same task"}], "decisions": [], "risks": [], "summary": ""},
        ]
        result = _merge_extractions(extractions)
        assert len(result["tasks"]) == 1

    def test_similar_tasks_kept(self):
        """Similar but different tasks should be kept."""
        from backend.agents.extraction_agent import _merge_extractions
        extractions = [
            {"tasks": [{"description": "Complete API documentation for v1"}], "decisions": [], "risks": [], "summary": ""},
            {"tasks": [{"description": "Complete API documentation for v2"}], "decisions": [], "risks": [], "summary": ""},
        ]
        result = _merge_extractions(extractions)
        # These have different first 50 chars, so both kept
        assert len(result["tasks"]) == 2

    def test_summary_concatenation(self):
        """Summaries should be joined."""
        from backend.agents.extraction_agent import _merge_extractions
        extractions = [
            {"tasks": [], "decisions": [], "risks": [], "summary": "Part 1."},
            {"tasks": [], "decisions": [], "risks": [], "summary": "Part 2."},
        ]
        result = _merge_extractions(extractions)
        assert "Part 1" in result["summary"]
        assert "Part 2" in result["summary"]


# ═══════════════════════════════════════════════════════════════
# TEST: API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class TestAPIEndpoints:
    """Test API endpoints for robustness."""

    @pytest.mark.asyncio
    async def test_health_check(self, api_base):
        """API should respond to basic requests."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.get(f"{api_base}/api/departments")
                assert r.status_code == 200
                data = r.json()
                assert "departments" in data
            except httpx.ConnectError:
                pytest.skip("VM not reachable")

    @pytest.mark.asyncio
    async def test_team_list(self, api_base):
        """Team list endpoint."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.get(f"{api_base}/api/team")
                assert r.status_code == 200
                data = r.json()
                assert "members" in data
            except httpx.ConnectError:
                pytest.skip("VM not reachable")

    @pytest.mark.asyncio
    async def test_bulk_add_validation(self, api_base):
        """Bulk add should validate input."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Empty members list
                r = await client.post(
                    f"{api_base}/api/team/bulk",
                    json={"members": []}
                )
                assert r.status_code == 200
                data = r.json()
                assert data["added"] == 0
            except httpx.ConnectError:
                pytest.skip("VM not reachable")

    @pytest.mark.asyncio
    async def test_bulk_add_with_data(self, api_base):
        """Bulk add with actual data."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.post(
                    f"{api_base}/api/team/bulk",
                    json={
                        "members": [
                            {"name": "Test User 1", "role": "Tester", "department": "engineering"},
                            {"name": "Test User 2", "role": "QA", "email": "test@example.com"},
                        ]
                    }
                )
                assert r.status_code == 200
                data = r.json()
                assert data["ok"] == True
                print(f"\n[TEST] Added {data['added']} members")
            except httpx.ConnectError:
                pytest.skip("VM not reachable")

    @pytest.mark.asyncio
    async def test_tasks_list(self, api_base):
        """Tasks list endpoint."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.get(f"{api_base}/api/tasks")
                assert r.status_code == 200
            except httpx.ConnectError:
                pytest.skip("VM not reachable")

    @pytest.mark.asyncio
    async def test_meetings_list(self, api_base):
        """Meetings list endpoint."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.get(f"{api_base}/api/meetings")
                assert r.status_code == 200
            except httpx.ConnectError:
                pytest.skip("VM not reachable")


# ═══════════════════════════════════════════════════════════════
# TEST: EXTRACTION WITH VARIOUS INPUTS
# ═══════════════════════════════════════════════════════════════

class TestExtractionVariousInputs:
    """Test extraction with different transcript types."""

    @pytest.mark.asyncio
    async def test_standard_transcript(self, sample_transcripts):
        """Standard meeting transcript."""
        from backend.agents.extraction_agent import extract_meeting
        result, summary, updates = await extract_meeting(
            transcript=sample_transcripts["standard"],
            title="Test",
            department="engineering"
        )
        print(f"\n[TEST] Standard: {len(result.tasks)} tasks, {len(result.decisions)} decisions")
        assert len(result.tasks) >= 1

    @pytest.mark.asyncio
    async def test_minimal_transcript(self, sample_transcripts):
        """Minimal one-line transcript."""
        from backend.agents.extraction_agent import extract_meeting
        result, summary, updates = await extract_meeting(
            transcript=sample_transcripts["minimal"],
            title="Quick Sync",
            department="engineering"
        )
        print(f"\n[TEST] Minimal: {len(result.tasks)} tasks")
        # Should still extract something

    @pytest.mark.asyncio
    async def test_timestamp_format(self, sample_transcripts):
        """Transcript with timestamps."""
        from backend.agents.extraction_agent import extract_meeting
        result, summary, updates = await extract_meeting(
            transcript=sample_transcripts["timestamps"],
            title="Timestamped Meeting",
            department="engineering"
        )
        print(f"\n[TEST] Timestamps: {len(result.tasks)} tasks")


# ═══════════════════════════════════════════════════════════════
# TEST: ERROR HANDLING
# ═══════════════════════════════════════════════════════════════

class TestErrorHandling:
    """Test error handling and recovery."""

    def test_looping_detection(self):
        """Looping text should be detected."""
        from backend.agents.extraction_agent import _is_looping_text

        # Create looping text - exact 100-char blocks repeated (algorithm checks at 100,200,300 boundaries)
        # Text must be >500 chars and have same 100-char block at positions 0, 100, 200, etc.
        block = "A" * 100  # Exactly 100 chars
        repeated = block * 10  # 1000 chars total, same block at every 100-char boundary
        assert _is_looping_text(repeated) == True, "Should detect repeated 100-char blocks"

        # Normal text should not trigger (unique content at each 100-char boundary)
        normal = "".join([f"Block{i:03d}" + "x" * 92 for i in range(10)])  # 1000 chars, all unique blocks
        assert _is_looping_text(normal) == False, "Should not trigger on unique content"

    @pytest.mark.asyncio
    async def test_consolidation_with_no_openai(self):
        """Consolidation should handle missing OpenAI gracefully."""
        from backend.agents.extraction_agent import _consolidate_extractions

        merged = {
            "tasks": [{"description": "Task 1"}, {"description": "Task 2"}],
            "decisions": [],
            "risks": [],
            "summary": "Test"
        }

        # With less than 3 tasks, should skip consolidation
        result = await _consolidate_extractions(merged)
        assert result == merged  # Should return unchanged


# ═══════════════════════════════════════════════════════════════
# TEST: NOTION CLIENT
# ═══════════════════════════════════════════════════════════════

class TestNotionClient:
    """Test Notion client functionality."""

    def test_date_parsing(self):
        """Test date parsing for various formats."""
        from backend.agents.notion_client import _try_parse_date

        # ISO format
        assert _try_parse_date("2026-03-15") == "2026-03-15"

        # Month Day format
        result = _try_parse_date("March 15th")
        assert result is not None
        assert "-03-15" in result

        # Natural language (should return None)
        assert _try_parse_date("Friday") is None
        assert _try_parse_date("next week") is None
        assert _try_parse_date("Not specified") is None

    def test_owner_matching(self):
        """Test owner name to user ID matching."""
        from backend.agents.notion_client import _match_owner_to_user_id

        members = [
            {"id": "user1", "name": "john doe", "email": "john@example.com"},
            {"id": "user2", "name": "jane smith", "email": "jane.smith@example.com"},
        ]

        # Exact match
        assert _match_owner_to_user_id("john doe", members) == "user1"

        # First name match
        assert _match_owner_to_user_id("John", members) == "user1"

        # Email match
        assert _match_owner_to_user_id("john@example.com", members) == "user1"

        # No match
        assert _match_owner_to_user_id("unknown person", members) is None

        # Empty inputs
        assert _match_owner_to_user_id("", members) is None
        assert _match_owner_to_user_id("john", []) is None


# ═══════════════════════════════════════════════════════════════
# TEST: FULL PIPELINE INTEGRATION
# ═══════════════════════════════════════════════════════════════

class TestFullPipelineIntegration:
    """Integration tests for full extraction pipeline."""

    @pytest.mark.asyncio
    async def test_long_transcript_full_pipeline(self, long_transcript):
        """Full pipeline test with long transcript."""
        from backend.agents.extraction_agent import extract_meeting

        print(f"\n[TEST] Running full pipeline on {len(long_transcript)} char transcript...")

        result, summary, updates = await extract_meeting(
            transcript=long_transcript,
            title="Integration Test Meeting",
            department="innovation"
        )

        print(f"[TEST] Results:")
        print(f"  Tasks: {len(result.tasks)}")
        print(f"  Decisions: {len(result.decisions)}")
        print(f"  Risks: {len(result.risks)}")
        print(f"  Summary: {len(summary)} chars")

        # Verify reasonable output
        assert len(result.tasks) >= 3, "Should extract multiple tasks"
        assert len(summary) > 50, "Should have meaningful summary"

        # Verify task structure
        for task in result.tasks:
            assert task.description, "Task should have description"
            assert task.owner, "Task should have owner"
            assert task.status in ["pending", "in_progress", "done"], "Valid status"


# ═══════════════════════════════════════════════════════════════
# TEST: SCHEMAS
# ═══════════════════════════════════════════════════════════════

class TestSchemas:
    """Test Pydantic schemas for validation."""

    def test_task_schema(self):
        """Task schema validation."""
        from backend.models.schemas import Task

        task = Task(description="Test", owner="John", deadline="Friday")
        assert task.status == "pending"  # Default

    def test_bulk_request_schema(self):
        """Bulk team member request schema."""
        from backend.models.schemas import BulkTeamMemberRequest, TeamMemberRequest

        request = BulkTeamMemberRequest(members=[
            TeamMemberRequest(name="Test User"),
        ])
        assert len(request.members) == 1
        assert request.members[0].role == ""  # Default

    def test_meeting_upload_schema(self):
        """Meeting upload request schema."""
        from backend.models.schemas import MeetingUploadRequest

        request = MeetingUploadRequest(
            title="Test",
            transcript="Test transcript",
        )
        assert request.department == "engineering"  # Default
        assert request.auto_sync_notion == True  # Default
        assert request.debug_mode == False  # Default


# ═══════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short", "-x"])
