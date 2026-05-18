"""Tests for skill packaging logic (package_skill.py)."""

import zipfile
from pathlib import Path

import pytest

from package_skill import package_skill
from agent_skills_lib.validation import validate_skill


class TestPackageSkill:
    """Test package_skill function."""

    def test_packages_valid_skill(self, valid_skill_dir, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = package_skill(str(valid_skill_dir), str(output_dir))
        assert result is not None
        assert result.exists()
        assert result.suffix == ".skill"

    def test_skill_file_is_valid_zip(self, valid_skill_dir, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = package_skill(str(valid_skill_dir), str(output_dir))
        assert zipfile.is_zipfile(result)

    def test_skill_file_contains_skill_md(self, valid_skill_dir, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = package_skill(str(valid_skill_dir), str(output_dir))
        with zipfile.ZipFile(result, "r") as zf:
            names = zf.namelist()
            assert any("SKILL.md" in name for name in names)

    def test_package_nonexistent_path(self, tmp_path):
        result = package_skill(str(tmp_path / "nonexistent"), str(tmp_path))
        assert result is None

    def test_package_file_not_directory(self, tmp_path):
        file_path = tmp_path / "not-a-dir.txt"
        file_path.write_text("content", encoding="utf-8")
        result = package_skill(str(file_path), str(tmp_path))
        assert result is None

    def test_package_without_skill_md(self, tmp_path):
        skill_dir = tmp_path / "no-md"
        skill_dir.mkdir()
        result = package_skill(str(skill_dir), str(tmp_path / "output"))
        assert result is None

    def test_package_with_invalid_skill(self, tmp_path):
        skill_dir = tmp_path / "invalid-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No frontmatter\n", encoding="utf-8")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = package_skill(str(skill_dir), str(output_dir))
        assert result is None

    def test_output_file_name_matches_skill_dir(self, valid_skill_dir, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = package_skill(str(valid_skill_dir), str(output_dir))
        assert result.name == "test-skill.skill"

    def test_creates_output_directory_if_missing(self, valid_skill_dir, tmp_path):
        output_dir = tmp_path / "new" / "output"
        result = package_skill(str(valid_skill_dir), str(output_dir))
        assert result is not None
        assert output_dir.exists()

    def test_packages_subdirectories(self, tmp_path):
        skill_dir = tmp_path / "full-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: full-skill\ndescription: A skill with resources.\n---\n# Body\n",
            encoding="utf-8",
        )
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "helper.py").write_text("print('hello')", encoding="utf-8")
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "guide.md").write_text("# Guide", encoding="utf-8")

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = package_skill(str(skill_dir), str(output_dir))
        assert result is not None

        with zipfile.ZipFile(result, "r") as zf:
            names = zf.namelist()
            assert any("helper.py" in n for n in names)
            assert any("guide.md" in n for n in names)
