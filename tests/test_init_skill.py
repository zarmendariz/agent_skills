"""Tests for skill initialization logic (init_skill.py)."""

from pathlib import Path

import pytest

from init_skill import init_skill, title_case_skill_name


class TestTitleCaseSkillName:
    """Test the title_case_skill_name helper."""

    def test_single_word(self):
        assert title_case_skill_name("nushell") == "Nushell"

    def test_two_words(self):
        assert title_case_skill_name("my-skill") == "My Skill"

    def test_multiple_words(self):
        assert title_case_skill_name("a-very-long-skill-name") == "A Very Long Skill Name"

    def test_with_numbers(self):
        assert title_case_skill_name("skill-2-go") == "Skill 2 Go"


class TestInitSkill:
    """Test init_skill function."""

    def test_creates_skill_directory(self, tmp_path):
        result = init_skill("test-skill", str(tmp_path))
        assert result is not None
        assert (tmp_path / "test-skill").is_dir()

    def test_creates_skill_md(self, tmp_path):
        init_skill("test-skill", str(tmp_path))
        skill_md = tmp_path / "test-skill" / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text(encoding="utf-8")
        assert content.startswith("---")
        assert "name: test-skill" in content
        assert "Test Skill" in content

    def test_creates_scripts_directory(self, tmp_path):
        init_skill("test-skill", str(tmp_path))
        scripts_dir = tmp_path / "test-skill" / "scripts"
        assert scripts_dir.is_dir()
        assert (scripts_dir / "example.py").exists()

    def test_creates_references_directory(self, tmp_path):
        init_skill("test-skill", str(tmp_path))
        refs_dir = tmp_path / "test-skill" / "references"
        assert refs_dir.is_dir()
        assert (refs_dir / "api_reference.md").exists()

    def test_creates_assets_directory(self, tmp_path):
        init_skill("test-skill", str(tmp_path))
        assets_dir = tmp_path / "test-skill" / "assets"
        assert assets_dir.is_dir()
        assert (assets_dir / "example_asset.txt").exists()

    def test_skill_name_in_template(self, tmp_path):
        init_skill("data-analyzer", str(tmp_path))
        script_content = (tmp_path / "data-analyzer" / "scripts" / "example.py").read_text(encoding="utf-8")
        assert "data-analyzer" in script_content

    def test_returns_none_if_directory_exists(self, tmp_path):
        (tmp_path / "existing-skill").mkdir()
        result = init_skill("existing-skill", str(tmp_path))
        assert result is None

    def test_returns_path_on_success(self, tmp_path):
        result = init_skill("new-skill", str(tmp_path))
        assert result == (tmp_path / "new-skill").resolve()

    def test_creates_nested_parent_directories(self, tmp_path):
        nested_path = tmp_path / "deep" / "nested" / "path"
        result = init_skill("test-skill", str(nested_path))
        assert result is not None
        assert (nested_path / "test-skill").is_dir()

    def test_skill_md_frontmatter_format(self, tmp_path):
        init_skill("my-skill", str(tmp_path))
        content = (tmp_path / "my-skill" / "SKILL.md").read_text(encoding="utf-8")
        assert content.startswith("---\n")
        assert "\n---\n" in content[4:]
        assert "name: my-skill" in content
