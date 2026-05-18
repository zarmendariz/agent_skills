"""Tests for deploy.py and pull.py path resolution and file operations."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

import deploy
import pull


class TestPathResolution:
    """Test shared path resolution (deploy.py and pull.py delegate to agent_skills_lib.paths)."""

    def test_repo_root_is_absolute(self):
        assert deploy.repo_root().is_absolute()

    def test_kilocode_skills_dir_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("KILOCODE_SKILLS_DIR", None)
            assert deploy.kilocode_skills_dir() == Path.home() / ".kilocode" / "skills"

    def test_kilocode_skills_dir_override(self):
        with patch.dict(os.environ, {"KILOCODE_SKILLS_DIR": "/custom/path"}):
            assert deploy.kilocode_skills_dir() == Path("/custom/path")

    def test_copilot_skills_dir_default_linux(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("COPILOT_SKILLS_DIR", None)
            with patch("agent_skills_lib.paths.platform.system", return_value="Linux"):
                assert deploy.copilot_skills_dir() == Path.home() / ".config" / "github-copilot" / "skills"

    def test_copilot_skills_dir_default_windows(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("COPILOT_SKILLS_DIR", None)
            with patch("agent_skills_lib.paths.platform.system", return_value="Windows"):
                result = deploy.copilot_skills_dir()
                assert "github-copilot" in str(result) and "skills" in str(result)

    def test_copilot_skills_dir_override(self):
        with patch.dict(os.environ, {"COPILOT_SKILLS_DIR": "/my/copilot/skills"}):
            assert deploy.copilot_skills_dir() == Path("/my/copilot/skills")

    def test_copilot_instructions_path_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("COPILOT_INSTRUCTIONS_PATH", None)
            assert deploy.copilot_instructions_path() == Path.home() / ".github" / "copilot-instructions.md"

    def test_copilot_instructions_path_override(self):
        with patch.dict(os.environ, {"COPILOT_INSTRUCTIONS_PATH": "/custom/instructions.md"}):
            assert deploy.copilot_instructions_path() == Path("/custom/instructions.md")

    def test_kilocode_opencode_path_linux(self):
        with patch("agent_skills_lib.paths.platform.system", return_value="Linux"):
            assert deploy.kilocode_opencode_path() == Path.home() / ".config" / "kilo" / "opencode.json"

    def test_kilocode_opencode_path_windows(self):
        with patch("agent_skills_lib.paths.platform.system", return_value="Windows"):
            result = deploy.kilocode_opencode_path()
            assert "kilo" in str(result) and "opencode.json" in str(result)

    def test_pull_uses_same_path_resolution(self):
        """Verify pull.py delegates to the same shared path module."""
        with patch.dict(os.environ, {"KILOCODE_SKILLS_DIR": "/shared"}):
            assert pull.kilocode_skills_dir() == deploy.kilocode_skills_dir()


class TestDeployFileOperations:
    """Test deploy.py file copy operations."""

    def test_copy_dir_creates_destination(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "file.txt").write_text("content", encoding="utf-8")
        dst = tmp_path / "dst" / "nested"

        assert deploy.copy_dir(src, dst, dry_run=False, label="test") is True
        assert (dst / "file.txt").read_text(encoding="utf-8") == "content"

    def test_copy_dir_dry_run_makes_no_changes(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "file.txt").write_text("content", encoding="utf-8")
        dst = tmp_path / "dst"

        assert deploy.copy_dir(src, dst, dry_run=True, label="test") is True
        assert not dst.exists()

    def test_copy_dir_overwrites_existing(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "new.txt").write_text("new", encoding="utf-8")

        dst = tmp_path / "dst"
        dst.mkdir()
        (dst / "old.txt").write_text("old", encoding="utf-8")

        deploy.copy_dir(src, dst, dry_run=False, label="test")
        assert (dst / "new.txt").exists()
        assert not (dst / "old.txt").exists()

    def test_copy_file_success(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("hello", encoding="utf-8")
        dst = tmp_path / "dest" / "dest.txt"

        assert deploy.copy_file(src, dst, dry_run=False, label="test") is True
        assert dst.read_text(encoding="utf-8") == "hello"

    def test_copy_file_skips_missing_source(self, tmp_path):
        assert deploy.copy_file(tmp_path / "nope", tmp_path / "dst", dry_run=False, label="test") is True

    def test_copy_file_dry_run_makes_no_changes(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("hello", encoding="utf-8")
        dst = tmp_path / "dest.txt"

        assert deploy.copy_file(src, dst, dry_run=True, label="test") is True
        assert not dst.exists()

    def test_copy_skills_copies_all(self, tmp_path):
        src_skills = tmp_path / "src_skills"
        src_skills.mkdir()
        for name in ("skill-a", "skill-b"):
            (src_skills / name).mkdir()
            (src_skills / name / "SKILL.md").write_text(name, encoding="utf-8")

        dst_skills = tmp_path / "dst_skills"
        dst_skills.mkdir()

        assert deploy.copy_skills(src_skills, dst_skills, dry_run=False, force=True) is True
        assert (dst_skills / "skill-a" / "SKILL.md").exists()
        assert (dst_skills / "skill-b" / "SKILL.md").exists()

    def test_copy_skills_returns_false_for_missing_source(self, tmp_path):
        assert deploy.copy_skills(tmp_path / "nope", tmp_path / "dst", dry_run=False, force=True) is False

    def test_copy_skills_handles_empty_source(self, tmp_path):
        src = tmp_path / "empty"
        src.mkdir()
        assert deploy.copy_skills(src, tmp_path / "dst", dry_run=False, force=True) is True


class TestPullFileOperations:
    """Test pull.py file operations."""

    def test_pull_file_copies_content(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("content", encoding="utf-8")
        dst = tmp_path / "dest.txt"

        assert pull.pull_file(src, dst, dry_run=False, force=True, label="test") is True
        assert dst.read_text(encoding="utf-8") == "content"

    def test_pull_file_skips_missing_source(self, tmp_path):
        assert pull.pull_file(tmp_path / "missing", tmp_path / "dst", dry_run=False, force=False, label="test") is True

    def test_pull_file_skips_existing_without_force(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("new", encoding="utf-8")
        dst = tmp_path / "dest.txt"
        dst.write_text("old", encoding="utf-8")

        pull.pull_file(src, dst, dry_run=False, force=False, label="test")
        assert dst.read_text(encoding="utf-8") == "old"

    def test_pull_file_overwrites_with_force(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("new", encoding="utf-8")
        dst = tmp_path / "dest.txt"
        dst.write_text("old", encoding="utf-8")

        pull.pull_file(src, dst, dry_run=False, force=True, label="test")
        assert dst.read_text(encoding="utf-8") == "new"

    def test_pull_file_dry_run_makes_no_changes(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("content", encoding="utf-8")
        dst = tmp_path / "dest.txt"

        assert pull.pull_file(src, dst, dry_run=True, force=True, label="test") is True
        assert not dst.exists()

    def test_pull_skills_copies_directories(self, tmp_path):
        src = tmp_path / "global_skills"
        src.mkdir()
        (src / "skill-x").mkdir()
        (src / "skill-x" / "SKILL.md").write_text("x", encoding="utf-8")

        dst = tmp_path / "repo_skills"
        dst.mkdir()

        assert pull.pull_skills(src, dst, dry_run=False, force=True) is True
        assert (dst / "skill-x" / "SKILL.md").exists()

    def test_pull_skills_skips_existing_without_force(self, tmp_path):
        src = tmp_path / "global"
        src.mkdir()
        (src / "skill-a").mkdir()
        (src / "skill-a" / "SKILL.md").write_text("new", encoding="utf-8")

        dst = tmp_path / "repo"
        dst.mkdir()
        (dst / "skill-a").mkdir()
        (dst / "skill-a" / "SKILL.md").write_text("old", encoding="utf-8")

        pull.pull_skills(src, dst, dry_run=False, force=False)
        assert (dst / "skill-a" / "SKILL.md").read_text(encoding="utf-8") == "old"

    def test_pull_skills_handles_missing_source(self, tmp_path):
        assert pull.pull_skills(tmp_path / "nope", tmp_path / "dst", dry_run=False, force=True) is True

    def test_never_pull_constants_exist(self):
        """Verify security-sensitive files and dirs are in exclusion lists."""
        assert "secrets.json" in pull.NEVER_PULL
        assert "cache" in pull.NEVER_PULL_DIRS
