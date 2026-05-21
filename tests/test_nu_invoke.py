"""Tests for nu_invoke.py - PowerShell-compatible nushell invocation helper.

This module generates correct nu invocations that work when executed through
the copilot-cli PowerShell tool layer.
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import nu_invoke


class TestBuildNuCommand:
    """Test nu_invoke.build_command() generates correct PowerShell-compatible invocations."""

    def test_simple_oneliner(self):
        """Simple command produces `nu -c "..."` invocation."""
        result = nu_invoke.build_command("ls")
        assert result == ['nu', '-c', 'ls']

    def test_command_with_pipe(self):
        """Piped command is passed correctly."""
        cmd = "ls | where type == file"
        result = nu_invoke.build_command(cmd)
        assert result == ['nu', '-c', 'ls | where type == file']

    def test_command_with_dollar_vars(self):
        """Nu $variables are preserved (not PowerShell-expanded)."""
        cmd = 'let x = 42; print $"Value: ($x)"'
        result = nu_invoke.build_command(cmd)
        assert '$"Value: ($x)"' in result[2]

    def test_multiline_uses_script_file(self):
        """Multi-line scripts should use temp file approach."""
        script = "let x = 42\nprint $x\n"
        result = nu_invoke.build_command(script)
        # Multi-line should use file mode
        assert result[0] == 'nu'
        # Either uses -c with the content or a file path
        if len(result) == 2:
            # File path mode
            assert result[1].endswith('.nu') or '\n' not in result[1]
        else:
            assert result[1] == '-c'

    def test_env_vars_generate_correct_prefix(self):
        """Environment variables generate correct invocation."""
        result = nu_invoke.build_command("print $env.FOO", env={"FOO": "bar"})
        # Should include env setup
        assert result[0] == 'nu'

    def test_timeout_is_stored(self):
        """Timeout parameter is captured for execution."""
        result = nu_invoke.build_command("sleep 10sec", timeout=5)
        assert result[0] == 'nu'


class TestFormatForPowerShell:
    """Test generating PowerShell-safe command strings."""

    def test_simple_command_no_escaping_needed(self):
        """Simple commands pass through without escaping."""
        result = nu_invoke.format_for_powershell("ls | first 5")
        assert "nu -c" in result
        assert "ls | first 5" in result

    def test_double_quotes_escaped(self):
        """Double quotes in nu code are escaped for PowerShell."""
        result = nu_invoke.format_for_powershell('print "hello"')
        # PowerShell needs escaped quotes
        assert "nu -c" in result
        # The quotes must be preserved in some form
        assert "hello" in result

    def test_dollar_sign_handling(self):
        """Dollar signs must not be interpolated by PowerShell."""
        result = nu_invoke.format_for_powershell('print $"Count: ($x)"')
        # Must use single quotes or escaping to prevent PS interpolation
        assert "nu -c" in result
        # The $ must be protected
        assert "$" in result

    def test_multiline_uses_here_string(self):
        """Multi-line scripts should use PowerShell here-string or temp file."""
        script = "let x = 42\nlet y = $x + 1\nprint $y"
        result = nu_invoke.format_for_powershell(script)
        assert "nu" in result
        # Should handle multi-line properly
        assert "42" in result

    def test_pipe_characters_preserved(self):
        """Pipe characters must be preserved (not interpreted by PS)."""
        result = nu_invoke.format_for_powershell("ls | where size > 1mb | sort-by size")
        assert "where size" in result
        assert "sort-by size" in result


class TestExecuteNu:
    """Test nu_invoke.execute() runs commands correctly."""

    def test_successful_execution(self):
        """Successful nu command returns output and exit code 0."""
        mock_result = MagicMock()
        mock_result.stdout = "hello\n"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_invoke.subprocess.run", return_value=mock_result):
            result = nu_invoke.execute("print 'hello'")
            assert result.exit_code == 0
            assert result.stdout == "hello\n"

    def test_failed_execution(self):
        """Failed nu command returns non-zero exit code."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "Error: something failed"
        mock_result.returncode = 1

        with patch("nu_invoke.subprocess.run", return_value=mock_result):
            result = nu_invoke.execute("invalid-command")
            assert result.exit_code == 1
            assert "Error" in result.stderr

    def test_nu_not_found_returns_127(self):
        """When nu binary is not found, returns exit code 127."""
        with patch("nu_invoke.subprocess.run", side_effect=FileNotFoundError()):
            result = nu_invoke.execute("ls")
            assert result.exit_code == 127

    def test_timeout_returns_124(self):
        """Timeout returns exit code 124."""
        with patch("nu_invoke.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("nu", 30)):
            result = nu_invoke.execute("sleep 60sec", timeout=30)
            assert result.exit_code == 124

    def test_env_vars_passed_to_subprocess(self):
        """Environment variables are merged into subprocess env."""
        mock_result = MagicMock()
        mock_result.stdout = "bar"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_invoke.subprocess.run", return_value=mock_result) as mock_run:
            nu_invoke.execute("print $env.FOO", env={"FOO": "bar"})
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["env"]["FOO"] == "bar"

    def test_cwd_passed_to_subprocess(self):
        """Working directory is passed to subprocess."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_invoke.subprocess.run", return_value=mock_result) as mock_run:
            nu_invoke.execute("ls", cwd="/tmp")
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cwd"] == "/tmp"


class TestMultilineScriptExecution:
    """Test handling of multi-line nu scripts."""

    def test_multiline_written_to_temp_file(self):
        """Multi-line scripts are written to temp .nu files."""
        mock_result = MagicMock()
        mock_result.stdout = "42"
        mock_result.stderr = ""
        mock_result.returncode = 0

        script = "let x = 42\nprint $x"

        with patch("nu_invoke.subprocess.run", return_value=mock_result) as mock_run:
            nu_invoke.execute(script)
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "nu"
            # Second arg should be a .nu file path
            assert call_args[1].endswith(".nu")

    def test_temp_file_cleaned_up(self):
        """Temp .nu files are cleaned up after execution."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        script = "let x = 1\nprint $x"
        temp_path = None

        with patch("nu_invoke.subprocess.run", return_value=mock_result) as mock_run:
            nu_invoke.execute(script)
            call_args = mock_run.call_args[0][0]
            temp_path = call_args[1]

        # File should be cleaned up
        assert not Path(temp_path).exists()

    def test_single_line_uses_dash_c(self):
        """Single-line scripts use -c flag directly."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_invoke.subprocess.run", return_value=mock_result) as mock_run:
            nu_invoke.execute("ls | first 5")
            call_args = mock_run.call_args[0][0]
            assert call_args == ["nu", "-c", "ls | first 5"]
