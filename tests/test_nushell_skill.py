"""Tests for nushell skill content and invocation patterns.

Validates that the nushell skill correctly instructs agents to invoke nu
through the PowerShell tool layer on Windows (copilot-cli hardcodes PowerShell).
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "nushell"
SKILL_MD = SKILL_DIR / "SKILL.md"
LANG_GUIDE = SKILL_DIR / "references" / "language-guide.md"
PATTERNS_MD = SKILL_DIR / "references" / "patterns.md"


class TestSkillMdInvocationPatterns:
    """Verify SKILL.md teaches PowerShell-compatible nu invocation."""

    @pytest.fixture(autouse=True)
    def load_skill(self):
        self.content = SKILL_MD.read_text(encoding="utf-8")

    def test_mentions_powershell_tool_context(self):
        """SKILL.md must acknowledge it operates via the PowerShell tool."""
        assert "powershell" in self.content.lower(), (
            "SKILL.md must mention PowerShell since copilot-cli uses it on Windows"
        )

    def test_has_nu_c_invocation_pattern(self):
        """SKILL.md must show `nu -c` as the primary invocation pattern."""
        assert "nu -c" in self.content, (
            "SKILL.md must show `nu -c` as the invocation pattern"
        )

    def test_has_multiline_invocation_pattern(self):
        """SKILL.md must show a multi-line nu script invocation pattern."""
        # Should show either nu <scriptfile> or a multi-line approach
        has_script_file = "nu_run" in self.content or ".nu" in self.content
        has_multiline = '"""' in self.content or "here-string" in self.content.lower() or "@'" in self.content or '@"' in self.content
        assert has_script_file or has_multiline, (
            "SKILL.md must show a multi-line nu invocation pattern (script file or here-string)"
        )

    def test_no_bash_heredoc_as_primary_pattern(self):
        """SKILL.md must NOT use bash heredoc as the primary invocation.

        Since copilot-cli uses PowerShell on Windows, bash heredocs are invalid.
        """
        # The skill should not present `nu << 'EOF'` as a primary/core pattern
        lines = self.content.split("\n")
        core_section_lines = []
        in_core = False
        for line in lines:
            if "## Core Invocation" in line or "## Invocation" in line:
                in_core = True
            elif line.startswith("## ") and in_core:
                break
            if in_core:
                core_section_lines.append(line)

        core_section = "\n".join(core_section_lines)
        assert "<<" not in core_section, (
            "Core invocation section must not use bash heredoc syntax (invalid on Windows/PowerShell)"
        )

    def test_mentions_windows_platform(self):
        """SKILL.md should mention Windows context since that's the target."""
        # At minimum, must reference that the tool is PowerShell on Windows
        lower = self.content.lower()
        assert "windows" in lower or "powershell" in lower, (
            "SKILL.md must acknowledge the Windows/PowerShell execution context"
        )

    def test_has_escaping_guidance(self):
        """SKILL.md must provide guidance on escaping for PowerShell->nu."""
        lower = self.content.lower()
        assert "escap" in lower or "quote" in lower or "backtick" in lower, (
            "SKILL.md must provide escaping/quoting guidance for PowerShell->nu"
        )


class TestLanguageGuideInvocation:
    """Verify language-guide.md has correct invocation patterns."""

    @pytest.fixture(autouse=True)
    def load_guide(self):
        self.content = LANG_GUIDE.read_text(encoding="utf-8")

    def test_has_invocation_section(self):
        """Language guide must have an invocation patterns section."""
        assert "invocation" in self.content.lower()

    def test_shows_powershell_invocation(self):
        """Language guide must show how to invoke nu from PowerShell."""
        assert "nu -c" in self.content

    def test_shows_script_file_invocation(self):
        """Language guide must show nu <script.nu> invocation."""
        assert re.search(r"nu\s+\S+\.nu", self.content), (
            "Language guide must show `nu script.nu` invocation pattern"
        )

    def test_has_env_var_passing_pattern(self):
        """Language guide must show how to pass env vars to nu from PowerShell."""
        lower = self.content.lower()
        has_env = "$env:" in self.content or "env" in lower
        assert has_env, "Language guide must show env var passing to nu"


class TestPatternsReference:
    """Verify patterns.md has practical patterns for common tasks."""

    @pytest.fixture(autouse=True)
    def load_patterns(self):
        self.content = PATTERNS_MD.read_text(encoding="utf-8")

    def test_has_error_handling(self):
        """Must have error handling patterns."""
        assert "error" in self.content.lower()
        assert "try" in self.content

    def test_has_external_command_patterns(self):
        """Must show how to call external commands."""
        assert "^" in self.content or "complete" in self.content

    def test_has_data_transformation(self):
        """Must show structured data operations."""
        lower = self.content.lower()
        assert "json" in lower or "table" in lower or "record" in lower


class TestSkillFrontmatter:
    """Verify SKILL.md frontmatter is correct and comprehensive."""

    @pytest.fixture(autouse=True)
    def load_skill(self):
        self.content = SKILL_MD.read_text(encoding="utf-8")

    def test_frontmatter_mentions_powershell(self):
        """Frontmatter description should mention PowerShell context."""
        # Extract frontmatter (between --- markers)
        parts = self.content.split("---")
        assert len(parts) >= 3, "SKILL.md must have YAML frontmatter"
        frontmatter = parts[1]
        lower = frontmatter.lower()
        assert "powershell" in lower or "shell tool" in lower, (
            "Frontmatter must mention PowerShell/shell tool context for triggering"
        )

    def test_frontmatter_has_trigger_keywords(self):
        """Frontmatter should have keywords that trigger on nu-related requests."""
        parts = self.content.split("---")
        frontmatter = parts[1].lower()
        # Should trigger on common nu-related keywords
        triggers = ["nu", "nushell", "structured data", "shell"]
        found = sum(1 for t in triggers if t in frontmatter)
        assert found >= 3, f"Frontmatter should contain at least 3 trigger keywords, found {found}"
