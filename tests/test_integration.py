"""Integration tests - validate the scripts work end-to-end as CLI tools."""

import subprocess
from pathlib import Path

import pytest

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


class TestQuickValidateCLI:
    """Test quick_validate.py as a CLI tool."""

    def test_valid_skill_exits_zero(self):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-creator/scripts/quick_validate.py",
             "skills/skill-sync"])
        assert result.returncode == 0
        assert "valid" in result.stdout.lower()

    def test_nonexistent_skill_exits_nonzero(self, tmp_path):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-creator/scripts/quick_validate.py",
             str(tmp_path / "nonexistent")])
        assert result.returncode == 1
        assert "not found" in result.stdout.lower()

    def test_no_args_exits_nonzero(self):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-creator/scripts/quick_validate.py"])
        assert result.returncode == 1


class TestPackageSkillCLI:
    """Test package_skill.py as a CLI tool."""

    def test_packages_real_skill(self, tmp_path):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-creator/scripts/package_skill.py",
             "skills/skill-sync", str(tmp_path)])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (tmp_path / "skill-sync.skill").exists()

    def test_no_args_shows_usage(self):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-creator/scripts/package_skill.py"])
        assert result.returncode == 1
        assert "Usage" in result.stdout


class TestInitSkillCLI:
    """Test init_skill.py as a CLI tool."""

    def test_creates_new_skill(self, tmp_path):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-creator/scripts/init_skill.py",
             "test-cli-skill", "--path", str(tmp_path)])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (tmp_path / "test-cli-skill" / "SKILL.md").exists()

    def test_no_args_shows_usage(self):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-creator/scripts/init_skill.py"])
        assert result.returncode == 1
        assert "Usage" in result.stdout


class TestDeployDryRun:
    """Test deploy.py in dry-run mode (safe for CI)."""

    def test_deploy_dry_run_all(self):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-sync/scripts/deploy.py",
             "--all", "--dry-run"])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "dry-run" in result.stdout.lower()

    def test_deploy_no_target_fails(self):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-sync/scripts/deploy.py"])
        assert result.returncode != 0


class TestPullDryRun:
    """Test pull.py in dry-run mode (safe for CI)."""

    def test_pull_dry_run_all(self):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-sync/scripts/pull.py",
             "--all", "--dry-run"])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "dry-run" in result.stdout.lower()

    def test_pull_no_target_fails(self):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-sync/scripts/pull.py"])
        assert result.returncode != 0


class TestAllSkillsValidate:
    """Validate all skills in the repo pass validation."""

    @pytest.mark.parametrize("skill_name", ["skill-sync", "nushell", "skill-creator", "unit-testing"])
    def test_skill_validates(self, skill_name):
        result = _run([UV, "run", "--project", ".devtools",
             "skills/skill-creator/scripts/quick_validate.py",
             f"skills/{skill_name}"])
        assert result.returncode == 0, f"{skill_name} failed validation: {result.stdout}"

