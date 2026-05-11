"""
Test chunking and extraction for long transcripts.
"""
import pytest
import asyncio
from pathlib import Path

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


def extract_odt_text(file_path: str) -> str:
    """Extract text from ODT file."""
    import zipfile
    import xml.etree.ElementTree as ET

    with zipfile.ZipFile(file_path, 'r') as zf:
        content = zf.read('content.xml')

    root = ET.fromstring(content)
    # Extract all text nodes
    text_parts = []
    for elem in root.iter():
        if elem.text:
            text_parts.append(elem.text)
        if elem.tail:
            text_parts.append(elem.tail)

    return ' '.join(text_parts)


class TestChunking:
    """Test the chunking functionality."""

    @pytest.fixture
    def long_transcript(self):
        """Load the long ODT transcript."""
        odt_path = Path(__file__).parent.parent / "docs" / "Industry & AI innovation progress meeting.odt"
        if not odt_path.exists():
            pytest.skip(f"ODT file not found: {odt_path}")
        return extract_odt_text(str(odt_path))

    def test_transcript_length(self, long_transcript):
        """Verify the transcript is actually long."""
        print(f"\n[TEST] Transcript length: {len(long_transcript)} characters")
        assert len(long_transcript) > 20000, "Transcript should be > 20K chars for chunking test"

    def test_langchain_chunking(self, long_transcript):
        """Test LangChain text splitter directly."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        max_chunk_size = 20000
        separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=500,
            separators=separators,
            length_function=len,
            is_separator_regex=False,
        )

        chunks = splitter.split_text(long_transcript)

        print(f"\n[TEST] LangChain split into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {len(chunk)} chars")

        assert len(chunks) >= 1, "Should produce at least 1 chunk"
        for chunk in chunks:
            assert len(chunk) <= max_chunk_size + 100, f"Chunk too large: {len(chunk)}"

    def test_chunk_transcript_function(self, long_transcript):
        """Test our _chunk_transcript function."""
        from backend.agents.extraction_agent import _chunk_transcript

        chunks = _chunk_transcript(long_transcript)

        print(f"\n[TEST] _chunk_transcript produced {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {len(chunk)} chars")

        assert len(chunks) >= 1, "Should produce at least 1 chunk"
        # Verify total content is preserved (approximately, due to overlap)
        total_chars = sum(len(c) for c in chunks)
        print(f"  Total chars in chunks: {total_chars} (original: {len(long_transcript)})")


class TestExtraction:
    """Test the full extraction pipeline."""

    @pytest.fixture
    def long_transcript(self):
        """Load the long ODT transcript."""
        odt_path = Path(__file__).parent.parent / "docs" / "Industry & AI innovation progress meeting.odt"
        if not odt_path.exists():
            pytest.skip(f"ODT file not found: {odt_path}")
        return extract_odt_text(str(odt_path))

    @pytest.mark.asyncio
    async def test_extract_single_chunk(self, long_transcript):
        """Test extracting from a single chunk."""
        from backend.agents.extraction_agent import _extract_single_chunk, EXTRACTION_SYSTEM_PROMPT

        # Take first 15K chars as a test chunk
        test_chunk = long_transcript[:15000]

        print(f"\n[TEST] Testing single chunk extraction ({len(test_chunk)} chars)")

        try:
            result = await _extract_single_chunk(
                test_chunk,
                EXTRACTION_SYSTEM_PROMPT,
                chunk_num=1,
                total_chunks=1
            )

            print(f"[TEST] Extracted: {len(result.get('tasks', []))} tasks")
            print(f"[TEST] Extracted: {len(result.get('decisions', []))} decisions")
            print(f"[TEST] Extracted: {len(result.get('risks', []))} risks")

            assert isinstance(result, dict), "Should return a dict"
            assert "tasks" in result or "summary" in result, "Should have tasks or summary"

        except Exception as e:
            print(f"[TEST] Extraction failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_full_extraction(self, long_transcript):
        """Test full extraction pipeline with chunking."""
        from backend.agents.extraction_agent import extract_meeting

        print(f"\n[TEST] Testing full extraction ({len(long_transcript)} chars)")

        try:
            result, summary, updates = await extract_meeting(
                transcript=long_transcript,
                title="Test Meeting",
                department="innovation"
            )

            print(f"[TEST] Full extraction result:")
            print(f"  Tasks: {len(result.tasks)}")
            print(f"  Decisions: {len(result.decisions)}")
            print(f"  Risks: {len(result.risks)}")
            print(f"  Summary length: {len(summary)} chars")

            # Print first few tasks
            for i, task in enumerate(result.tasks[:5]):
                print(f"  Task {i+1}: {task.description[:80]}...")

            assert len(result.tasks) > 0, "Should extract at least some tasks"

        except Exception as e:
            print(f"[TEST] Full extraction failed: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    # Run just the chunking tests first
    pytest.main([__file__, "-v", "-s", "-k", "chunk"])
