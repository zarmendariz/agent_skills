"""Pytest configuration and shared fixtures for agent_skills tests."""

import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def valid_skill_md_content():
    """Return valid SKILL.md content for testing."""
    return """---
name: test-skill
description: A test skill for validating the packaging system.
---

# Test Skill

This is a test skill body.
"""


@pytest.fixture
def valid_skill_dir(tmp_path, valid_skill_md_content):
    """Create a valid skill directory structure for testing."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(valid_skill_md_content, encoding="utf-8")
    (skill_dir / "scripts").mkdir()
    (skill_dir / "references").mkdir()
    return skill_dir


@pytest.fixture
def mock_repo_root(tmp_path):
    """Create a mock repository structure for deploy/pull testing."""
    root = tmp_path / "repo"
    root.mkdir()

    # Create .kilocode/skills/ with a sample skill
    skills_dir = root / ".kilocode" / "skills" / "sample-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(
        "---\nname: sample-skill\ndescription: A sample.\n---\n# Sample\n",
        encoding="utf-8",
    )

    # Create .kilocode/cli/global/settings/
    settings_dir = root / ".kilocode" / "cli" / "global" / "settings"
    settings_dir.mkdir(parents=True)
    (settings_dir / "mcp_settings.json").write_text("{}", encoding="utf-8")
    (settings_dir / "custom_modes.yaml").write_text("modes: []", encoding="utf-8")

    # Create .github/
    github_dir = root / ".github"
    github_dir.mkdir()
    (github_dir / "copilot-instructions.md").write_text("# Instructions", encoding="utf-8")

    # Create opencode.json
    (root / "opencode.json").write_text("{}", encoding="utf-8")

    return root
