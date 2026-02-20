"""
Unit tests for department management
Tests static and dynamic department loading
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.departments import get_department, list_departments, DEPARTMENTS


class TestDepartments:
    """Test department functionality"""

    def test_list_departments(self):
        """Test listing all departments"""
        depts = list_departments()

        assert len(depts) > 0, "Should have at least one department"
        assert all("id" in d for d in depts), "All departments should have id"
        assert all("name" in d for d in depts), "All departments should have name"
        assert all("icon" in d for d in depts), "All departments should have icon"

    def test_get_hardcoded_department(self):
        """Test retrieving hardcoded department"""
        eng = get_department("engineering")

        assert eng["id"] == "engineering"
        assert eng["name"] == "Engineering"
        assert "extraction_context" in eng
        assert "sample_transcript" in eng

    def test_get_nonexistent_department(self):
        """Test fallback for nonexistent department"""
        result = get_department("nonexistent_dept")

        # Should fallback to engineering
        assert result["id"] == "engineering"

    def test_all_hardcoded_departments(self):
        """Test all hardcoded departments are valid"""
        for dept_id in ["engineering", "hr", "marcom", "innovation", "sales", "product"]:
            dept = get_department(dept_id)

            assert dept["id"] == dept_id
            assert dept["name"] != ""
            assert dept["icon"] != ""
            assert dept["extraction_context"] != ""
            assert dept["query_context"] != ""

    def test_department_icons(self):
        """Test all departments have emoji icons"""
        depts = list_departments()
        icons = {d["icon"] for d in depts}

        # Should have unique icons
        assert len(icons) >= len(DEPARTMENTS), "Each department should have a unique icon"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
