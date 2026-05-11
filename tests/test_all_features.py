"""
Comprehensive tests for TeamAI features.
Run with: python -m pytest tests/test_all_features.py -v -s
"""
import pytest
import asyncio
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def extract_odt_text(file_path: str) -> str:
    """Extract text from ODT file."""
    import zipfile
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(file_path, 'r') as zf:
        content = zf.read('content.xml')
    root = ET.fromstring(content)
    text_parts = []
    for elem in root.iter():
        if elem.text: text_parts.append(elem.text)
        if elem.tail: text_parts.append(elem.tail)
    return ' '.join(text_parts)


@pytest.fixture
def long_transcript():
    """Load the long ODT transcript."""
    odt_path = Path(__file__).parent.parent / "docs" / "Industry & AI innovation progress meeting.odt"
    if not odt_path.exists():
        pytest.skip(f"ODT file not found: {odt_path}")
    return extract_odt_text(str(odt_path))


@pytest.fixture
def short_transcript():
    """A short test transcript."""
    return """
    [Meeting: Weekly Sync | March 15, 2026]

    John: Let's discuss the project status.
    Sarah: I'll finish the API documentation by Friday.
    John: Great. Mike, what about the testing?
    Mike: I need to complete unit tests by next week. There's a risk we might miss the deadline if QA is delayed.
    John: Okay, let's prioritize that. Decision made: we'll move the release to March 25th.
    Sarah: I'll update the roadmap.
    """


# ═══════════════════════════════════════════════════════════════
# TEST: CHUNKING
# ═══════════════════════════════════════════════════════════════

class TestChunking:
    """Test text chunking functionality."""

    def test_short_transcript_no_chunking(self, short_transcript):
        """Short transcripts should not be chunked."""
        from backend.agents.extraction_agent import _chunk_transcript
        chunks = _chunk_transcript(short_transcript)
        assert len(chunks) == 1, "Short transcript should be single chunk"

    def test_long_transcript_chunking(self, long_transcript):
        """Long transcripts should be split into multiple chunks."""
        from backend.agents.extraction_agent import _chunk_transcript
        chunks = _chunk_transcript(long_transcript)

        print(f"\n[TEST] Transcript: {len(long_transcript)} chars")
        print(f"[TEST] Chunks: {len(chunks)}")
        for i, c in enumerate(chunks):
            print(f"  Chunk {i+1}: {len(c)} chars")

        assert len(chunks) > 1, "Long transcript should be split"
        for chunk in chunks:
            assert len(chunk) <= 20500, f"Chunk too large: {len(chunk)}"

    def test_chunk_overlap(self, long_transcript):
        """Chunks should have overlap for context preservation."""
        from backend.agents.extraction_agent import _chunk_transcript
        chunks = _chunk_transcript(long_transcript)

        if len(chunks) > 1:
            # Check that end of chunk 1 appears near start of chunk 2
            end_of_first = chunks[0][-200:]
            start_of_second = chunks[1][:700]
            # There should be some overlap
            overlap_found = any(
                end_of_first[i:i+50] in start_of_second
                for i in range(0, len(end_of_first)-50, 10)
            )
            print(f"\n[TEST] Overlap found: {overlap_found}")


# ═══════════════════════════════════════════════════════════════
# TEST: EXTRACTION
# ═══════════════════════════════════════════════════════════════

class TestExtraction:
    """Test LLM extraction functionality."""

    @pytest.mark.asyncio
    async def test_short_extraction(self, short_transcript):
        """Test extraction from short transcript."""
        from backend.agents.extraction_agent import extract_meeting

        result, summary, updates = await extract_meeting(
            transcript=short_transcript,
            title="Test Meeting",
            department="engineering"
        )

        print(f"\n[TEST] Tasks: {len(result.tasks)}")
        print(f"[TEST] Decisions: {len(result.decisions)}")
        print(f"[TEST] Risks: {len(result.risks)}")

        assert len(result.tasks) >= 1, "Should extract at least one task"

    @pytest.mark.asyncio
    async def test_long_extraction_with_chunking(self, long_transcript):
        """Test full extraction pipeline with chunking."""
        from backend.agents.extraction_agent import extract_meeting

        print(f"\n[TEST] Starting long extraction ({len(long_transcript)} chars)...")

        result, summary, updates = await extract_meeting(
            transcript=long_transcript,
            title="Industry & AI Innovation Meeting",
            department="innovation"
        )

        print(f"[TEST] Extraction complete:")
        print(f"  Tasks: {len(result.tasks)}")
        print(f"  Decisions: {len(result.decisions)}")
        print(f"  Risks: {len(result.risks)}")
        print(f"  Summary: {len(summary)} chars")

        # Print some tasks
        for i, task in enumerate(result.tasks[:5]):
            print(f"  Task {i+1}: {task.description[:60]}...")

        assert len(result.tasks) >= 3, "Should extract multiple tasks from long meeting"


# ═══════════════════════════════════════════════════════════════
# TEST: MERGE & CONSOLIDATE
# ═══════════════════════════════════════════════════════════════

class TestMergeConsolidate:
    """Test merging and consolidation of chunk extractions."""

    def test_merge_extractions(self):
        """Test merging multiple extractions."""
        from backend.agents.extraction_agent import _merge_extractions

        extractions = [
            {
                "tasks": [{"description": "Task A", "owner": "John", "deadline": "Friday"}],
                "decisions": [{"description": "Decision 1"}],
                "risks": [{"description": "Risk 1", "severity": "high"}],
                "summary": "Part 1 summary."
            },
            {
                "tasks": [
                    {"description": "Task B", "owner": "Sarah", "deadline": "Monday"},
                    {"description": "Task A", "owner": "John", "deadline": "Friday"}  # Duplicate
                ],
                "decisions": [{"description": "Decision 2"}],
                "risks": [{"description": "Risk 1", "severity": "high"}],  # Duplicate
                "summary": "Part 2 summary."
            }
        ]

        merged = _merge_extractions(extractions)

        print(f"\n[TEST] Merged tasks: {len(merged['tasks'])} (expected 2, not 3)")
        print(f"[TEST] Merged decisions: {len(merged['decisions'])}")
        print(f"[TEST] Merged risks: {len(merged['risks'])} (expected 1, not 2)")

        assert len(merged['tasks']) == 2, "Duplicate tasks should be removed"
        assert len(merged['risks']) == 1, "Duplicate risks should be removed"

    @pytest.mark.asyncio
    async def test_consolidation(self):
        """Test consolidation pass."""
        from backend.agents.extraction_agent import _consolidate_extractions

        merged = {
            "tasks": [
                {"description": "Finish API docs", "owner": "John", "deadline": "Friday"},
                {"description": "Complete API documentation", "owner": "John", "deadline": "End of week"},
                {"description": "Write unit tests", "owner": "Mike", "deadline": "Monday"},
            ],
            "decisions": [{"description": "Move release to March 25th"}],
            "risks": [{"description": "QA delay risk", "severity": "medium"}],
            "summary": "Meeting about project status."
        }

        consolidated = await _consolidate_extractions(merged)

        print(f"\n[TEST] Before: {len(merged['tasks'])} tasks")
        print(f"[TEST] After: {len(consolidated['tasks'])} tasks")

        # Consolidation should reduce similar tasks
        assert len(consolidated['tasks']) <= len(merged['tasks'])


# ═══════════════════════════════════════════════════════════════
# TEST: TEAM MEMBERS API
# ═══════════════════════════════════════════════════════════════

class TestTeamMembersAPI:
    """Test team member CRUD operations."""

    def test_bulk_add_schema(self):
        """Test bulk add request schema."""
        from backend.models.schemas import BulkTeamMemberRequest, TeamMemberRequest

        request = BulkTeamMemberRequest(
            members=[
                TeamMemberRequest(name="John Doe", role="Engineer", department="engineering"),
                TeamMemberRequest(name="Jane Smith", role="Designer", email="jane@example.com"),
            ]
        )

        assert len(request.members) == 2
        assert request.members[0].name == "John Doe"


# ═══════════════════════════════════════════════════════════════
# TEST: JSON PARSING
# ═══════════════════════════════════════════════════════════════

class TestJSONParsing:
    """Test JSON extraction from LLM responses."""

    def test_parse_clean_json(self):
        """Test parsing clean JSON response."""
        from backend.agents.extraction_agent import _parse_k2_response

        response = '{"tasks": [{"description": "Test task"}], "summary": "Test"}'
        parsed = _parse_k2_response(response)

        assert "tasks" in parsed
        assert len(parsed["tasks"]) == 1

    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        from backend.agents.extraction_agent import _parse_k2_response

        response = '''```json
{"tasks": [{"description": "Test task"}], "summary": "Test"}
```'''
        parsed = _parse_k2_response(response)

        assert "tasks" in parsed

    def test_parse_json_with_thinking(self):
        """Test parsing JSON after thinking tags."""
        from backend.agents.extraction_agent import _parse_k2_response

        response = '''<think_fast>Let me analyze this...</think_fast>
{"tasks": [{"description": "Task 1"}], "decisions": [], "risks": [], "summary": "Meeting summary"}'''

        parsed = _parse_k2_response(response)
        assert "tasks" in parsed
        assert len(parsed["tasks"]) == 1


# ═══════════════════════════════════════════════════════════════
# TEST: NOTION SYNC
# ═══════════════════════════════════════════════════════════════

class TestNotionSync:
    """Test Notion integration (mocked)."""

    def test_status_mapping(self):
        """Test status value mapping."""
        from backend.agents.notion_client import STATUS_MAP

        assert STATUS_MAP["pending"] == "Not started"
        assert STATUS_MAP["in_progress"] == "In progress"
        assert STATUS_MAP["done"] == "Done"

    def test_department_labels(self):
        """Test department label mapping."""
        from backend.agents.notion_client import DEPT_TAG, DEPT_SELECT

        assert "Engineering" in DEPT_TAG["engineering"]
        assert DEPT_SELECT["engineering"] == "Engineering"


# ══════════════════════════════════════════════════════════���════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
