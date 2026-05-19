"""Comprehensive tests for the ast-grep skill.

Tests cover:
- Skill validation (structure, frontmatter, body length)
- Pattern matching verification (run ast-grep on sample code)
- YAML rule validation (rules parse and produce expected results)
- Script functionality (init_project.py, run_analysis.py)
- Integration tests (end-to-end workflow)

Note: Tests that require ast-grep CLI are skipped when ast-grep is not installed.
Install via: cargo install ast-grep --locked
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "ast-grep"
SCRIPTS_DIR = SKILL_DIR / "scripts"
REFERENCES_DIR = SKILL_DIR / "references"

# Add scripts directory to path for imports
sys.path.insert(0, str(SCRIPTS_DIR))

# Check if ast-grep is available
_ast_grep_available = shutil.which("ast-grep") is not None

requires_ast_grep = pytest.mark.skipif(
    not _ast_grep_available,
    reason="ast-grep not installed (install with: cargo install ast-grep --locked)",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_js(tmp_path):
    """Create a sample JavaScript file for testing."""
    code = textwrap.dedent("""\
        const express = require('express');

        function processInput(input) {
            return eval(input);
        }

        console.log("debug info");
        console.log("data:", userData);

        async function fetchData(url) {
            const res = await fetch(url);
            return res.json();
        }

        var oldVar = "should be const";
    """)
    f = tmp_path / "sample.js"
    f.write_text(code, encoding="utf-8")
    return f


@pytest.fixture
def sample_py(tmp_path):
    """Create a sample Python file for testing."""
    code = textwrap.dedent("""\
        import os
        import subprocess

        def run_command(cmd):
            result = subprocess.call(cmd, shell=True)
            return result

        def read_file(path):
            f = open(path, 'r')
            content = f.read()
            f.close()
            return content

        class UserService:
            def get_user(self, user_id):
                query = f"SELECT * FROM users WHERE id = {user_id}"
                return self.db.execute(query)

        print("Starting server...")
    """)
    f = tmp_path / "sample.py"
    f.write_text(code, encoding="utf-8")
    return f


@pytest.fixture
def sample_c(tmp_path):
    """Create a sample C file for testing."""
    code = textwrap.dedent("""\
        #include <stdio.h>
        #include <stdlib.h>
        #include <string.h>

        void unsafe_copy(char *dst, const char *src) {
            strcpy(dst, src);
        }

        char *allocate_buffer(int size) {
            char *buf = malloc(size);
            return buf;
        }

        void use_after_free(int *ptr) {
            free(ptr);
            printf("%d", *ptr);
        }

        int main() {
            char buffer[64];
            gets(buffer);
            printf(buffer);
            return 0;
        }
    """)
    f = tmp_path / "sample.c"
    f.write_text(code, encoding="utf-8")
    return f


@pytest.fixture
def sample_rule(tmp_path):
    """Create a sample YAML rule file."""
    rule = textwrap.dedent("""\
        id: no-eval
        language: JavaScript
        rule:
          pattern: eval($EXPR)
        message: "eval() usage detected — potential code injection"
        severity: error
        note: "Use safer alternatives like JSON.parse()"
    """)
    f = tmp_path / "no-eval.yml"
    f.write_text(rule, encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# Skill Validation Tests
# ---------------------------------------------------------------------------


class TestSkillStructure:
    """Test that the ast-grep skill has correct structure."""

    def test_skill_directory_exists(self):
        assert SKILL_DIR.exists(), "skills/ast-grep/ directory should exist"

    def test_skill_md_exists(self):
        assert (SKILL_DIR / "SKILL.md").exists(), "SKILL.md should exist"

    def test_references_directory_exists(self):
        assert REFERENCES_DIR.exists(), "references/ directory should exist"

    def test_scripts_directory_exists(self):
        assert SCRIPTS_DIR.exists(), "scripts/ directory should exist"

    def test_required_reference_files(self):
        expected_files = [
            "pattern-syntax.md",
            "rule-reference.md",
            "cli-reference.md",
            "recipes.md",
            "c-cpp-patterns.md",
        ]
        for filename in expected_files:
            assert (
                REFERENCES_DIR / filename
            ).exists(), f"references/{filename} should exist"

    def test_required_script_files(self):
        expected_files = ["init_project.py", "run_analysis.py"]
        for filename in expected_files:
            assert (
                SCRIPTS_DIR / filename
            ).exists(), f"scripts/{filename} should exist"

    def test_skill_validates(self):
        """Run the skill validator and ensure it passes."""
        from agent_skills_lib.validation import validate_skill

        valid, msg = validate_skill(SKILL_DIR)
        assert valid is True, f"Skill validation failed: {msg}"

    def test_skill_md_frontmatter(self):
        """Verify frontmatter has correct fields."""
        import yaml

        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        # Extract frontmatter
        assert content.startswith("---"), "SKILL.md must start with ---"
        end = content.index("---", 3)
        frontmatter = yaml.safe_load(content[3:end])

        assert frontmatter["name"] == "ast-grep"
        assert "description" in frontmatter
        assert "structural" in frontmatter["description"].lower()
        assert len(frontmatter["description"]) <= 1024

    def test_skill_md_body_length(self):
        """Body should be under 500 lines."""
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        # Skip frontmatter
        end_idx = content.index("---", 3) + 3
        body = content[end_idx:]
        line_count = len(body.strip().splitlines())
        assert line_count < 500, f"SKILL.md body is {line_count} lines (max 500)"


# ---------------------------------------------------------------------------
# Pattern Matching Tests (require ast-grep)
# ---------------------------------------------------------------------------


class TestPatternMatching:
    """Test ast-grep pattern matching on sample code."""

    @requires_ast_grep
    def test_find_eval_in_javascript(self, sample_js):
        """ast-grep should find eval() calls."""
        result = subprocess.run(
            ["ast-grep", "run", "-p", "eval($EXPR)", "-l", "javascript",
             "--json=compact", str(sample_js)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) >= 1
        assert any("eval(input)" in m.get("text", "") for m in matches)

    @requires_ast_grep
    def test_find_console_log(self, sample_js):
        """ast-grep should find console.log() calls."""
        result = subprocess.run(
            ["ast-grep", "run", "-p", "console.log($$$ARGS)", "-l", "javascript",
             "--json=compact", str(sample_js)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) == 2

    @requires_ast_grep
    def test_find_var_declarations(self, sample_js):
        """ast-grep should find var declarations."""
        result = subprocess.run(
            ["ast-grep", "run", "-p", "var $X = $Y", "-l", "javascript",
             "--json=compact", str(sample_js)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) >= 1

    @requires_ast_grep
    def test_find_subprocess_shell_true(self, sample_py):
        """ast-grep should find subprocess.call with shell=True."""
        result = subprocess.run(
            ["ast-grep", "run", "-p", "subprocess.call($CMD, shell=True)",
             "-l", "python", "--json=compact", str(sample_py)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) >= 1

    @requires_ast_grep
    def test_find_print_statements(self, sample_py):
        """ast-grep should find print() calls."""
        result = subprocess.run(
            ["ast-grep", "run", "-p", "print($$$ARGS)", "-l", "python",
             "--json=compact", str(sample_py)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) >= 1

    @requires_ast_grep
    def test_find_strcpy_in_c(self, sample_c):
        """ast-grep should find strcpy() calls in C code."""
        result = subprocess.run(
            ["ast-grep", "run", "-p", "strcpy($DST, $SRC)", "-l", "c",
             "--json=compact", str(sample_c)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) >= 1

    @requires_ast_grep
    def test_find_malloc_in_c(self, sample_c):
        """ast-grep should find malloc() calls in C code via kind-based rule.
        
        Note: In C, single-argument function calls like malloc(x) are parsed as
        macro_type_specifier by tree-sitter at pattern level. Use kind-based rules
        for reliable C function call matching.
        """
        import tempfile

        rule = (
            "id: find-malloc\n"
            "language: c\n"
            "rule:\n"
            "  kind: call_expression\n"
            "  has:\n"
            "    kind: identifier\n"
            '    regex: "^malloc$"\n'
            "    field: function\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as rf:
            rf.write(rule)
            rule_path = rf.name

        try:
            result = subprocess.run(
                ["ast-grep", "scan", "--rule", rule_path,
                 "--json=compact", str(sample_c.parent)],
                capture_output=True, text=True,
            )
            matches = json.loads(result.stdout) if result.stdout.strip() else []
            assert len(matches) >= 1
        finally:
            Path(rule_path).unlink(missing_ok=True)

    @requires_ast_grep
    def test_find_gets_in_c(self, sample_c):
        """ast-grep should find gets() calls (banned function) via kind-based rule."""
        import tempfile

        rule = (
            "id: find-gets\n"
            "language: c\n"
            "rule:\n"
            "  kind: call_expression\n"
            "  has:\n"
            "    kind: identifier\n"
            '    regex: "^gets$"\n'
            "    field: function\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as rf:
            rf.write(rule)
            rule_path = rf.name

        try:
            result = subprocess.run(
                ["ast-grep", "scan", "--rule", rule_path,
                 "--json=compact", str(sample_c.parent)],
                capture_output=True, text=True,
            )
            matches = json.loads(result.stdout) if result.stdout.strip() else []
            assert len(matches) >= 1
        finally:
            Path(rule_path).unlink(missing_ok=True)

    @requires_ast_grep
    def test_find_format_string_vuln(self, sample_c):
        """ast-grep should find printf(var) format string vulnerabilities via rule."""
        import tempfile

        rule = (
            "id: find-printf-var\n"
            "language: c\n"
            "rule:\n"
            "  kind: call_expression\n"
            "  has:\n"
            "    kind: identifier\n"
            '    regex: "^printf$"\n'
            "    field: function\n"
            "  not:\n"
            "    has:\n"
            "      kind: string_literal\n"
            "      stopBy: end\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as rf:
            rf.write(rule)
            rule_path = rf.name

        try:
            result = subprocess.run(
                ["ast-grep", "scan", "--rule", rule_path,
                 "--json=compact", str(sample_c.parent)],
                capture_output=True, text=True,
            )
            matches = json.loads(result.stdout) if result.stdout.strip() else []
            # Should find printf(buffer) — no string literal arg
            assert len(matches) >= 1
        finally:
            Path(rule_path).unlink(missing_ok=True)

    @requires_ast_grep
    def test_no_false_positives_in_comments(self, tmp_path):
        """Patterns should not match inside comments."""
        code = '// eval(x)\nconst y = 5;\n'
        f = tmp_path / "noeval.js"
        f.write_text(code, encoding="utf-8")

        result = subprocess.run(
            ["ast-grep", "run", "-p", "eval($X)", "-l", "javascript",
             "--json=compact", str(f)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) == 0, "Should not match eval() in comments"

    @requires_ast_grep
    def test_json_output_structure(self, sample_js):
        """JSON output should have expected fields."""
        result = subprocess.run(
            ["ast-grep", "run", "-p", "eval($EXPR)", "-l", "javascript",
             "--json=pretty", str(sample_js)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        if matches:
            m = matches[0]
            assert "text" in m
            assert "range" in m
            assert "file" in m


# ---------------------------------------------------------------------------
# Rewrite Tests
# ---------------------------------------------------------------------------


class TestRewrite:
    """Test ast-grep rewrite functionality."""

    @requires_ast_grep
    def test_rewrite_var_to_const(self, tmp_path):
        """Rewrite var to const."""
        code = 'var x = 5;\nvar y = "hello";\n'
        f = tmp_path / "rewrite.js"
        f.write_text(code, encoding="utf-8")

        subprocess.run(
            ["ast-grep", "run", "-p", "var $X = $Y", "--rewrite", "const $X = $Y",
             "-l", "javascript", "-U", str(f)],
            capture_output=True, text=True,
        )

        result = f.read_text(encoding="utf-8")
        assert "const x = 5" in result
        assert "const y = " in result
        assert "var " not in result

    @requires_ast_grep
    def test_rewrite_preserves_unmatched(self, tmp_path):
        """Rewrite should not modify non-matching code."""
        code = 'const a = 1;\nvar b = 2;\nlet c = 3;\n'
        f = tmp_path / "preserve.js"
        f.write_text(code, encoding="utf-8")

        subprocess.run(
            ["ast-grep", "run", "-p", "var $X = $Y", "--rewrite", "const $X = $Y",
             "-l", "javascript", "-U", str(f)],
            capture_output=True, text=True,
        )

        result = f.read_text(encoding="utf-8")
        assert "const a = 1" in result  # untouched
        assert "const b = 2" in result  # rewritten
        assert "let c = 3" in result    # untouched


# ---------------------------------------------------------------------------
# Rule Scan Tests
# ---------------------------------------------------------------------------


class TestRuleScan:
    """Test ast-grep scan with YAML rules."""

    @requires_ast_grep
    def test_scan_with_rule_file(self, sample_js, sample_rule):
        """Scan should find matches using a rule file."""
        result = subprocess.run(
            ["ast-grep", "scan", "--rule", str(sample_rule),
             "--json=compact", str(sample_js.parent)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) >= 1

    @requires_ast_grep
    def test_scan_inline_rule(self, sample_js):
        """Scan should work with inline rules."""
        inline_rule = (
            "id: test-rule\n"
            "language: JavaScript\n"
            "rule:\n"
            "  pattern: eval($X)\n"
            "message: found eval\n"
        )
        result = subprocess.run(
            ["ast-grep", "scan", "--inline-rules", inline_rule,
             "--json=compact", str(sample_js.parent)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) >= 1


# ---------------------------------------------------------------------------
# Script Tests
# ---------------------------------------------------------------------------


class TestInitProjectScript:
    """Test the init_project.py script."""

    def test_creates_project_structure(self, tmp_path):
        """Script should create sgconfig.yml and directories."""
        target = tmp_path / "my-project"
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "init_project.py"), str(target)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert (target / "sgconfig.yml").exists()
        assert (target / "rules").is_dir()
        assert (target / "rule-tests").is_dir()
        assert (target / "utils").is_dir()

    def test_creates_with_examples(self, tmp_path):
        """Script should create example files with --with-examples."""
        target = tmp_path / "example-project"
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "init_project.py"),
             str(target), "--with-examples"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert (target / "rules" / "no-console-log.yml").exists()
        assert (target / "rule-tests" / "no-console-log-test.yml").exists()
        assert (target / "utils" / "is-test-function.yml").exists()

    def test_refuses_existing_sgconfig(self, tmp_path):
        """Script should refuse to overwrite existing sgconfig.yml."""
        target = tmp_path / "existing"
        target.mkdir()
        (target / "sgconfig.yml").write_text("existing: true", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "init_project.py"), str(target)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0

    def test_sgconfig_content_valid(self, tmp_path):
        """Generated sgconfig.yml should have correct content."""
        import yaml

        target = tmp_path / "valid-config"
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "init_project.py"), str(target)],
            capture_output=True, text=True,
        )

        config = yaml.safe_load((target / "sgconfig.yml").read_text(encoding="utf-8"))
        assert "ruleDirs" in config
        assert "rules" in config["ruleDirs"]
        assert "testConfigs" in config
        assert "utilDirs" in config


class TestRunAnalysisScript:
    """Test the run_analysis.py script."""

    def test_script_help(self):
        """Script should show help without error."""
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_analysis.py"), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "ast-grep analysis" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_search_subcommand_help(self):
        """Search subcommand should show help."""
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_analysis.py"), "search", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "pattern" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """End-to-end integration tests."""

    @requires_ast_grep
    def test_full_workflow_create_scan_fix(self, tmp_path):
        """Full workflow: create project, add rule, scan, fix."""
        # 1. Create project
        project = tmp_path / "integration-project"
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "init_project.py"),
             str(project), "--with-examples"],
            capture_output=True, text=True,
        )

        # 2. Create a source file with issues
        src = project / "src"
        src.mkdir()
        (src / "app.js").write_text(
            'console.log("debug");\nconst x = 5;\n',
            encoding="utf-8",
        )

        # 3. Scan with the example rule
        result = subprocess.run(
            ["ast-grep", "scan", "--rule", str(project / "rules" / "no-console-log.yml"),
             "--json=compact", str(src)],
            capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) >= 1
        assert any("console.log" in m.get("text", "") for m in matches)

    @requires_ast_grep
    def test_multi_language_search(self, sample_js, sample_py, sample_c):
        """ast-grep should work across multiple languages in one directory."""
        import tempfile

        parent = sample_js.parent

        # Search JavaScript
        r1 = subprocess.run(
            ["ast-grep", "run", "-p", "eval($X)", "-l", "javascript",
             "--json=compact", str(parent)],
            capture_output=True, text=True,
        )
        # Search Python
        r2 = subprocess.run(
            ["ast-grep", "run", "-p", "print($$$ARGS)", "-l", "python",
             "--json=compact", str(parent)],
            capture_output=True, text=True,
        )
        # Search C — use kind-based rule for single-arg call matching
        rule = (
            "id: find-strcpy\n"
            "language: c\n"
            "rule:\n"
            "  kind: call_expression\n"
            "  has:\n"
            "    kind: identifier\n"
            '    regex: "^strcpy$"\n'
            "    field: function\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as rf:
            rf.write(rule)
            rule_path = rf.name

        try:
            r3 = subprocess.run(
                ["ast-grep", "scan", "--rule", rule_path,
                 "--json=compact", str(parent)],
                capture_output=True, text=True,
            )
        finally:
            Path(rule_path).unlink(missing_ok=True)

        js_matches = json.loads(r1.stdout) if r1.stdout.strip() else []
        py_matches = json.loads(r2.stdout) if r2.stdout.strip() else []
        c_matches = json.loads(r3.stdout) if r3.stdout.strip() else []

        assert len(js_matches) >= 1, "Should find eval in JS"
        assert len(py_matches) >= 1, "Should find print in Python"
        assert len(c_matches) >= 1, "Should find strcpy in C"

    @requires_ast_grep
    def test_stdin_mode(self):
        """ast-grep should accept code via stdin."""
        code = 'eval("dangerous")\n'
        result = subprocess.run(
            ["ast-grep", "run", "-p", "eval($X)", "-l", "javascript",
             "--stdin", "--json=compact"],
            input=code, capture_output=True, text=True,
        )
        matches = json.loads(result.stdout) if result.stdout.strip() else []
        assert len(matches) >= 1
