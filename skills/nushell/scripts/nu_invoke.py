#!/usr/bin/env python3
"""
nu_invoke.py - PowerShell-compatible nushell invocation helper.

Generates correct nu command invocations that work when executed through
the copilot-cli PowerShell tool layer. Handles escaping, multi-line scripts,
environment variable passing, and timeout management.

Usage from agent context (via PowerShell tool):
    nu -c "ls | where type == file"
    nu script.nu

Usage as Python module:
    from nu_invoke import execute, build_command, format_for_powershell

    result = execute("ls | where type == file")
    print(result.stdout)
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class NuResult:
    """Result of a nu command execution."""
    exit_code: int
    stdout: str
    stderr: str


def build_command(
    script: str,
    env: Optional[dict[str, str]] = None,
    timeout: Optional[int] = None,
) -> list[str]:
    """Build a nu command invocation as a list of arguments.

    For single-line scripts: returns ['nu', '-c', '<script>']
    For multi-line scripts: returns ['nu', '<temp-file-path>']

    Args:
        script: Nu script content (single or multi-line).
        env: Optional environment variables (handled at execution time).
        timeout: Optional timeout in seconds (handled at execution time).

    Returns:
        List of command arguments suitable for subprocess.run().
    """
    if '\n' in script:
        # Multi-line: write to temp file
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".nu", delete=False, encoding="utf-8"
        )
        tmp.write(script)
        tmp.close()
        return ['nu', tmp.name]
    else:
        return ['nu', '-c', script]


def format_for_powershell(script: str) -> str:
    """Format a nu invocation as a PowerShell command string.

    Generates a string that can be pasted into a PowerShell prompt or
    passed to the copilot-cli powershell tool.

    For single-line: nu -c 'script'  (using single quotes to prevent PS interpolation)
    For multi-line: Uses a temp file approach with Set-Content + nu

    Args:
        script: Nu script content.

    Returns:
        PowerShell command string.
    """
    if '\n' in script:
        # Multi-line: use PowerShell here-string to write temp file, then invoke
        # Escape single quotes in the script for the here-string
        escaped = script.replace("'", "''")
        return (
            f"$__nu_script = @'\n{script}\n'@\n"
            f"$__nu_tmp = [System.IO.Path]::GetTempFileName() + '.nu'\n"
            f"Set-Content -Path $__nu_tmp -Value $__nu_script -Encoding UTF8\n"
            f"nu $__nu_tmp\n"
            f"Remove-Item $__nu_tmp -ErrorAction SilentlyContinue"
        )
    else:
        # Single-line: use single quotes to prevent PowerShell interpolation
        # Escape any single quotes in the nu script
        escaped = script.replace("'", "''")
        return f"nu -c '{escaped}'"


def execute(
    script: str,
    env: Optional[dict[str, str]] = None,
    cwd: Optional[str] = None,
    timeout: int = 60,
) -> NuResult:
    """Execute a nu script and return the result.

    Args:
        script: Nu script content (single or multi-line).
        env: Optional extra environment variables to pass.
        cwd: Optional working directory.
        timeout: Timeout in seconds (default 60).

    Returns:
        NuResult with exit_code, stdout, stderr.
    """
    # Build environment
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    # Build command
    cmd = build_command(script)
    cleanup_file = None
    if len(cmd) == 2 and cmd[1].endswith('.nu'):
        cleanup_file = cmd[1]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=run_env,
            cwd=cwd,
            timeout=timeout,
        )
        return NuResult(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except FileNotFoundError:
        return NuResult(
            exit_code=127,
            stdout="",
            stderr="ERROR: 'nu' not found in PATH.",
        )
    except subprocess.TimeoutExpired:
        return NuResult(
            exit_code=124,
            stdout="",
            stderr=f"ERROR: Script timed out after {timeout}s",
        )
    finally:
        if cleanup_file:
            Path(cleanup_file).unlink(missing_ok=True)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: nu_invoke.py <script> [--env KEY=VAL ...] [--timeout N]")
        sys.exit(1)

    # Simple CLI interface
    script_arg = sys.argv[1]
    extra_env = {}
    timeout_val = 60

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--env" and i + 1 < len(sys.argv):
            k, v = sys.argv[i + 1].split("=", 1)
            extra_env[k] = v
            i += 2
        elif sys.argv[i] == "--timeout" and i + 1 < len(sys.argv):
            timeout_val = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    result = execute(script_arg, env=extra_env, timeout=timeout_val)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    sys.exit(result.exit_code)
