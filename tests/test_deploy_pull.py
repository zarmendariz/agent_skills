"""Tests for deploy.py and pull.py path resolution and file operations."""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

import deploy
import pull


REPO_ROOT = Path(__file__).resolve().parent.parent
UV = "uv"


def _run(*args, **kwargs):
    """Run a subprocess with UTF-8 encoding and standard defaults."""
    kwargs.setdefault("cwd", str(REPO_ROOT))
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("errors", "replace")
    kwargs.setdefault("timeout", 30)
    return subprocess.run(*args, **kwargs)


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
            os.environ.pop("COPILOT_HOME", None)
            with patch("agent_skills_lib.paths.platform.system", return_value="Linux"):
                assert deploy.copilot_skills_dir() == Path.home() / ".copilot" / "skills"

    def test_copilot_skills_dir_default_windows(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("COPILOT_SKILLS_DIR", None)
            os.environ.pop("COPILOT_HOME", None)
            with patch("agent_skills_lib.paths.platform.system", return_value="Windows"):
                result = deploy.copilot_skills_dir()
                assert str(result).endswith(".copilot\\skills") or str(result).endswith(".copilot/skills")

    def test_copilot_skills_dir_override(self):
        with patch.dict(os.environ, {"COPILOT_SKILLS_DIR": "/my/copilot/skills"}):
            assert deploy.copilot_skills_dir() == Path("/my/copilot/skills")

    def test_copilot_home_override(self):
        with patch.dict(os.environ, {"COPILOT_HOME": "/custom/copilot"}):
            os.environ.pop("COPILOT_SKILLS_DIR", None)
            os.environ.pop("COPILOT_INSTRUCTIONS_PATH", None)
            assert deploy.copilot_skills_dir() == Path("/custom/copilot/skills")
            assert deploy.copilot_instructions_path() == Path("/custom/copilot/copilot-instructions.md")

    def test_copilot_instructions_path_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("COPILOT_INSTRUCTIONS_PATH", None)
            os.environ.pop("COPILOT_HOME", None)
            assert deploy.copilot_instructions_path() == Path.home() / ".copilot" / "copilot-instructions.md"

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


class TestDeployEndToEnd:
    """End-to-end tests that deploy to temp directories and verify file structure."""

    def test_deploy_copilot_creates_skills_and_instructions(self, tmp_path, mock_repo_root):
        """Verify deploy --copilot actually writes skills and instructions to correct paths."""
        copilot_home = tmp_path / "copilot_home"
        copilot_home.mkdir()

        with patch.dict(os.environ, {
            "COPILOT_SKILLS_DIR": str(copilot_home / "skills"),
            "COPILOT_INSTRUCTIONS_PATH": str(copilot_home / "copilot-instructions.md"),
        }):
            ok = deploy.deploy_copilot(mock_repo_root, dry_run=False, force=True)

        assert ok is True
        # Skills deployed
        assert (copilot_home / "skills" / "sample-skill" / "SKILL.md").exists()
        skill_content = (copilot_home / "skills" / "sample-skill" / "SKILL.md").read_text(encoding="utf-8")
        assert "sample-skill" in skill_content
        # Instructions deployed
        assert (copilot_home / "copilot-instructions.md").exists()
        assert "# Instructions" in (copilot_home / "copilot-instructions.md").read_text(encoding="utf-8")

    def test_deploy_kilocode_creates_skills_and_config(self, tmp_path, mock_repo_root):
        """Verify deploy --kilocode actually writes skills and settings to correct paths."""
        kilo_skills = tmp_path / "kilo_skills"
        kilo_skills.mkdir()

        with patch.dict(os.environ, {"KILOCODE_SKILLS_DIR": str(kilo_skills)}):
            with patch("deploy.kilocode_settings_dir", return_value=tmp_path / "settings"):
                with patch("deploy.kilocode_opencode_path", return_value=tmp_path / "opencode.json"):
                    ok = deploy.deploy_kilocode(mock_repo_root, dry_run=False, force=True)

        assert ok is True
        assert (kilo_skills / "sample-skill" / "SKILL.md").exists()
        assert (tmp_path / "settings" / "mcp_settings.json").exists()
        assert (tmp_path / "settings" / "custom_modes.yaml").exists()
        assert (tmp_path / "opencode.json").exists()

    def test_deploy_copilot_dry_run_no_writes(self, tmp_path, mock_repo_root):
        """Verify dry-run doesn't create any files."""
        copilot_home = tmp_path / "copilot_home"

        with patch.dict(os.environ, {
            "COPILOT_SKILLS_DIR": str(copilot_home / "skills"),
            "COPILOT_INSTRUCTIONS_PATH": str(copilot_home / "copilot-instructions.md"),
        }):
            ok = deploy.deploy_copilot(mock_repo_root, dry_run=True, force=True)

        assert ok is True
        assert not copilot_home.exists()

    def test_deploy_copilot_cli_subprocess(self, tmp_path):
        """Test deploy.py via subprocess with env overrides — real end-to-end."""
        copilot_skills = tmp_path / "copilot_skills"

        env = os.environ.copy()
        env["COPILOT_SKILLS_DIR"] = str(copilot_skills)
        env["COPILOT_INSTRUCTIONS_PATH"] = str(tmp_path / "instructions.md")

        result = _run(
            [UV, "run", "--project", ".devtools",
             "skills/skill-sync/scripts/deploy.py",
             "--copilot", "--force"],
            env=env,
        )
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
        # Verify actual skills were deployed
        assert (copilot_skills / "skill-sync" / "SKILL.md").exists()
        assert (copilot_skills / "nushell" / "SKILL.md").exists()
        assert (copilot_skills / "skill-creator" / "SKILL.md").exists()
        assert (copilot_skills / "unit-testing" / "SKILL.md").exists()
        # Verify instructions deployed
        assert (tmp_path / "instructions.md").exists()

    def test_deploy_kilocode_cli_subprocess(self, tmp_path):
        """Test deploy.py --kilocode via subprocess with env overrides."""
        kilo_skills = tmp_path / "kilo_skills"

        env = os.environ.copy()
        env["KILOCODE_SKILLS_DIR"] = str(kilo_skills)

        result = _run(
            [UV, "run", "--project", ".devtools",
             "skills/skill-sync/scripts/deploy.py",
             "--kilocode", "--force"],
            env=env,
        )
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
        assert (kilo_skills / "skill-sync" / "SKILL.md").exists()
        assert (kilo_skills / "nushell" / "SKILL.md").exists()


class TestPullEndToEnd:
    """End-to-end tests that pull from temp directories and verify file structure."""

    def test_pull_copilot_retrieves_instructions(self, tmp_path, mock_repo_root):
        """Verify pull --copilot pulls instructions from global path to repo."""
        copilot_home = tmp_path / "copilot_home"
        copilot_home.mkdir()
        (copilot_home / "copilot-instructions.md").write_text("# Global Instructions", encoding="utf-8")

        # Remove repo instructions to test pull
        (mock_repo_root / ".github" / "copilot-instructions.md").unlink()

        with patch.dict(os.environ, {
            "COPILOT_SKILLS_DIR": str(copilot_home / "skills"),
            "COPILOT_INSTRUCTIONS_PATH": str(copilot_home / "copilot-instructions.md"),
        }):
            ok = pull.pull_copilot(mock_repo_root, dry_run=False, force=True)

        assert ok is True
        assert (mock_repo_root / ".github" / "copilot-instructions.md").exists()
        content = (mock_repo_root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        assert "# Global Instructions" in content

    def test_pull_copilot_retrieves_skills(self, tmp_path, mock_repo_root):
        """Verify pull --copilot pulls skills from global Copilot dir to repo."""
        copilot_home = tmp_path / "copilot_home"
        copilot_skills = copilot_home / "skills"
        copilot_skills.mkdir(parents=True)
        (copilot_skills / "remote-skill").mkdir()
        (copilot_skills / "remote-skill" / "SKILL.md").write_text(
            "---\nname: remote-skill\ndescription: From global.\n---\n# Remote\n",
            encoding="utf-8",
        )

        with patch.dict(os.environ, {
            "COPILOT_SKILLS_DIR": str(copilot_skills),
            "COPILOT_INSTRUCTIONS_PATH": str(copilot_home / "copilot-instructions.md"),
        }):
            ok = pull.pull_copilot(mock_repo_root, dry_run=False, force=True)

        assert ok is True
        assert (mock_repo_root / "skills" / "remote-skill" / "SKILL.md").exists()

    def test_pull_kilocode_retrieves_skills(self, tmp_path, mock_repo_root):
        """Verify pull --kilocode pulls skills from global KiloCode dir to repo."""
        kilo_skills = tmp_path / "kilo_skills"
        kilo_skills.mkdir()
        (kilo_skills / "kilo-skill").mkdir()
        (kilo_skills / "kilo-skill" / "SKILL.md").write_text(
            "---\nname: kilo-skill\ndescription: From global.\n---\n# Kilo\n",
            encoding="utf-8",
        )

        with patch.dict(os.environ, {"KILOCODE_SKILLS_DIR": str(kilo_skills)}):
            with patch("pull.kilocode_settings_dir", return_value=tmp_path / "no_settings"):
                with patch("pull.kilocode_opencode_path", return_value=tmp_path / "no_opencode.json"):
                    ok = pull.pull_kilocode(mock_repo_root, dry_run=False, force=True)

        assert ok is True
        assert (mock_repo_root / "skills" / "kilo-skill" / "SKILL.md").exists()

    def test_pull_copilot_cli_subprocess(self, tmp_path):
        """Test pull.py --copilot via subprocess with env overrides (dry-run to avoid repo mutation)."""
        copilot_home = tmp_path / "copilot_home"
        copilot_home.mkdir()
        (copilot_home / "copilot-instructions.md").write_text("# Pulled", encoding="utf-8")
        skills_dir = copilot_home / "skills"
        skills_dir.mkdir()

        env = os.environ.copy()
        env["COPILOT_SKILLS_DIR"] = str(skills_dir)
        env["COPILOT_INSTRUCTIONS_PATH"] = str(copilot_home / "copilot-instructions.md")

        result = _run(
            [UV, "run", "--project", ".devtools",
             "skills/skill-sync/scripts/pull.py",
             "--copilot", "--dry-run"],
            env=env,
        )
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
        assert "dry-run" in result.stdout.lower()


class TestDeployPullRoundTrip:
    """Tests that verify deploy → pull round-trip preserves content."""

    def test_deploy_then_pull_preserves_skills(self, tmp_path, mock_repo_root):
        """Deploy skills to a temp dir, then pull them back — content should match."""
        copilot_skills = tmp_path / "copilot_skills"
        copilot_instructions = tmp_path / "instructions.md"

        # Deploy
        with patch.dict(os.environ, {
            "COPILOT_SKILLS_DIR": str(copilot_skills),
            "COPILOT_INSTRUCTIONS_PATH": str(copilot_instructions),
        }):
            deploy.deploy_copilot(mock_repo_root, dry_run=False, force=True)

        # Create a fresh repo root to pull into
        fresh_root = tmp_path / "fresh_repo"
        fresh_root.mkdir()
        (fresh_root / "skills").mkdir()
        (fresh_root / ".github").mkdir()

        # Pull
        with patch.dict(os.environ, {
            "COPILOT_SKILLS_DIR": str(copilot_skills),
            "COPILOT_INSTRUCTIONS_PATH": str(copilot_instructions),
        }):
            pull.pull_copilot(fresh_root, dry_run=False, force=True)

        # Verify round-trip
        original = (mock_repo_root / "skills" / "sample-skill" / "SKILL.md").read_text(encoding="utf-8")
        pulled = (fresh_root / "skills" / "sample-skill" / "SKILL.md").read_text(encoding="utf-8")
        assert original == pulled

        original_instr = (mock_repo_root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        pulled_instr = (fresh_root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        assert original_instr == pulled_instr
