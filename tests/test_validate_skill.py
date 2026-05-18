"""Tests for skill validation logic (shared between package_skill.py and quick_validate.py)."""

from pathlib import Path

import pytest

from agent_skills_lib.validation import validate_skill


class TestValidateSkillFrontmatter:
    """Test SKILL.md frontmatter parsing and validation."""

    def test_valid_skill_passes(self, valid_skill_dir):
        valid, msg = validate_skill(valid_skill_dir)
        assert valid is True
        assert msg == "Skill is valid!"

    def test_missing_skill_md(self, tmp_path):
        skill_dir = tmp_path / "no-skill"
        skill_dir.mkdir()
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "SKILL.md not found" in msg

    def test_no_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No frontmatter here\n", encoding="utf-8")
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "No YAML frontmatter found" in msg

    def test_invalid_frontmatter_yaml(self, tmp_path):
        skill_dir = tmp_path / "bad-yaml"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n: [invalid yaml\n---\n", encoding="utf-8")
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "Invalid YAML" in msg

    def test_frontmatter_not_dict(self, tmp_path):
        skill_dir = tmp_path / "not-dict"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n- just a list\n- of items\n---\n", encoding="utf-8")
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "must be a YAML dictionary" in msg

    def test_missing_name_field(self, tmp_path):
        skill_dir = tmp_path / "no-name"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\ndescription: Has description but no name\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "Missing 'name'" in msg

    def test_missing_description_field(self, tmp_path):
        skill_dir = tmp_path / "no-desc"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test-skill\n---\n# Body\n", encoding="utf-8")
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "Missing 'description'" in msg

    def test_unexpected_frontmatter_keys(self, tmp_path):
        skill_dir = tmp_path / "extra-keys"
        skill_dir.mkdir()
        content = "---\nname: test-skill\ndescription: Test\nauthor: someone\nversion: 1.0\n---\n# Body\n"
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "Unexpected key(s)" in msg
        assert "author" in msg

    def test_allowed_optional_keys(self, tmp_path):
        skill_dir = tmp_path / "with-optional"
        skill_dir.mkdir()
        content = (
            "---\nname: test-skill\ndescription: A valid skill\n"
            "license: MIT\nallowed-tools:\n  - bash\nmetadata:\n  version: 1.0\n---\n# Body\n"
        )
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        valid, msg = validate_skill(skill_dir)
        assert valid is True


class TestValidateSkillName:
    """Test skill name validation rules."""

    def test_valid_hyphen_case_name(self, tmp_path):
        skill_dir = tmp_path / "good-name"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill-123\ndescription: Valid\n---\n# Body\n", encoding="utf-8"
        )
        valid, _ = validate_skill(skill_dir)
        assert valid is True

    def test_name_with_uppercase(self, tmp_path):
        skill_dir = tmp_path / "upper"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: My-Skill\ndescription: Valid\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "hyphen-case" in msg

    def test_name_with_underscores(self, tmp_path):
        skill_dir = tmp_path / "underscore"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my_skill\ndescription: Valid\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "hyphen-case" in msg

    def test_name_starting_with_hyphen(self, tmp_path):
        skill_dir = tmp_path / "start-hyph"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: -bad-name\ndescription: Valid\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "cannot start/end with hyphen" in msg

    def test_name_ending_with_hyphen(self, tmp_path):
        skill_dir = tmp_path / "end-hyph"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: bad-name-\ndescription: Valid\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "cannot start/end with hyphen" in msg

    def test_name_with_consecutive_hyphens(self, tmp_path):
        skill_dir = tmp_path / "consec"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: bad--name\ndescription: Valid\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "consecutive hyphens" in msg

    def test_name_too_long(self, tmp_path):
        skill_dir = tmp_path / "long-name"
        skill_dir.mkdir()
        long_name = "a" * 65
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {long_name}\ndescription: Valid\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "too long" in msg

    def test_name_at_max_length(self, tmp_path):
        skill_dir = tmp_path / "max-name"
        skill_dir.mkdir()
        name_64 = "a" * 64
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name_64}\ndescription: Valid\n---\n# Body\n", encoding="utf-8"
        )
        valid, _ = validate_skill(skill_dir)
        assert valid is True

    def test_name_not_string(self, tmp_path):
        skill_dir = tmp_path / "int-name"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: 123\ndescription: Valid\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "must be a string" in msg


class TestValidateSkillDescription:
    """Test skill description validation rules."""

    def test_description_with_angle_brackets(self, tmp_path):
        skill_dir = tmp_path / "angle"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: Contains <html> tags\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "angle brackets" in msg

    def test_description_too_long(self, tmp_path):
        skill_dir = tmp_path / "long-desc"
        skill_dir.mkdir()
        long_desc = "x" * 1025
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: test-skill\ndescription: {long_desc}\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "too long" in msg

    def test_description_at_max_length(self, tmp_path):
        skill_dir = tmp_path / "max-desc"
        skill_dir.mkdir()
        desc_1024 = "x" * 1024
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: test-skill\ndescription: {desc_1024}\n---\n# Body\n", encoding="utf-8"
        )
        valid, _ = validate_skill(skill_dir)
        assert valid is True

    def test_description_not_string(self, tmp_path):
        skill_dir = tmp_path / "int-desc"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: 42\n---\n# Body\n", encoding="utf-8"
        )
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "must be a string" in msg

    def test_multiline_description(self, tmp_path):
        skill_dir = tmp_path / "multiline"
        skill_dir.mkdir()
        content = (
            "---\nname: test-skill\ndescription: >\n"
            "  This is a long multiline description that wraps across\n"
            "  multiple lines in the YAML.\n---\n# Body\n"
        )
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        valid, _ = validate_skill(skill_dir)
        assert valid is True
