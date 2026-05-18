"""Tests for nu_run.py script."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import nu_run


class TestNuRunMain:
    """Test nu_run.py main function behavior via argument parsing."""

    def test_inline_script_creates_temp_file(self):
        """Verify inline script gets written to a temp file then cleaned up."""
        mock_result = MagicMock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_run.subprocess.run", return_value=mock_result) as mock_run:
            with patch("sys.argv", ["nu_run.py", "print hello", "--quiet"]):
                with pytest.raises(SystemExit) as exc_info:
                    nu_run.main()
                assert exc_info.value.code == 0
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "nu"
                assert call_args[1].endswith(".nu")

    def test_file_mode_passes_path_directly(self):
        """Verify --file mode passes the script path as-is."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_run.subprocess.run", return_value=mock_result) as mock_run:
            with patch("sys.argv", ["nu_run.py", "/tmp/test.nu", "--file", "--quiet"]):
                with pytest.raises(SystemExit) as exc_info:
                    nu_run.main()
                assert exc_info.value.code == 0
                call_args = mock_run.call_args[0][0]
                assert call_args == ["nu", "/tmp/test.nu"]

    def test_env_vars_passed_to_subprocess(self):
        """Verify --env KEY=VALUE pairs are added to process environment."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_run.subprocess.run", return_value=mock_result) as mock_run:
            with patch("sys.argv", ["nu_run.py", "test", "--env", "FOO=bar", "--env", "BAZ=qux", "--quiet"]):
                with pytest.raises(SystemExit):
                    nu_run.main()
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs["env"]["FOO"] == "bar"
                assert call_kwargs["env"]["BAZ"] == "qux"

    def test_timeout_passed_to_subprocess(self):
        """Verify --timeout value is passed to subprocess.run."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_run.subprocess.run", return_value=mock_result) as mock_run:
            with patch("sys.argv", ["nu_run.py", "test", "--timeout", "30", "--quiet"]):
                with pytest.raises(SystemExit):
                    nu_run.main()
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs["timeout"] == 30

    def test_nu_not_found_exits_127(self):
        """Verify exit code 127 when nu binary is not found."""
        with patch("nu_run.subprocess.run", side_effect=FileNotFoundError()):
            with patch("sys.argv", ["nu_run.py", "test", "--quiet"]):
                with pytest.raises(SystemExit) as exc_info:
                    nu_run.main()
                assert exc_info.value.code == 127

    def test_timeout_exits_124(self):
        """Verify exit code 124 on subprocess timeout."""
        with patch("nu_run.subprocess.run", side_effect=subprocess.TimeoutExpired("nu", 60)):
            with patch("sys.argv", ["nu_run.py", "test", "--quiet"]):
                with pytest.raises(SystemExit) as exc_info:
                    nu_run.main()
                assert exc_info.value.code == 124

    def test_nonzero_exit_code_propagated(self):
        """Verify script's non-zero exit code is propagated."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "error occurred"
        mock_result.returncode = 42

        with patch("nu_run.subprocess.run", return_value=mock_result):
            with patch("sys.argv", ["nu_run.py", "test", "--quiet"]):
                with pytest.raises(SystemExit) as exc_info:
                    nu_run.main()
                assert exc_info.value.code == 42

    def test_invalid_env_format_exits_2(self):
        """Verify exit code 2 for malformed --env without =."""
        with patch("sys.argv", ["nu_run.py", "test", "--env", "NOEQUALS", "--quiet"]):
            with pytest.raises(SystemExit) as exc_info:
                nu_run.main()
            assert exc_info.value.code == 2

    def test_quiet_flag_suppresses_summary(self, capsys):
        """Verify --quiet suppresses the structured summary line."""
        mock_result = MagicMock()
        mock_result.stdout = "output\n"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_run.subprocess.run", return_value=mock_result):
            with patch("sys.argv", ["nu_run.py", "test", "--quiet"]):
                with pytest.raises(SystemExit):
                    nu_run.main()
                captured = capsys.readouterr()
                assert "nu_run:" not in captured.err

    def test_non_quiet_shows_summary(self, capsys):
        """Verify non-quiet mode shows the status summary."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("nu_run.subprocess.run", return_value=mock_result):
            with patch("sys.argv", ["nu_run.py", "test"]):
                with pytest.raises(SystemExit):
                    nu_run.main()
                captured = capsys.readouterr()
                assert "nu_run: SUCCESS" in captured.err
