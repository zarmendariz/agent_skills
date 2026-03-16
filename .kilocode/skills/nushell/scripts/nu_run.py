#!/usr/bin/env python3
"""
nu_run.py - Execute a Nushell script safely, report structured results.

Usage:
    uv run .kilocode/skills/nushell/scripts/nu_run.py <script_content_or_file> [--file] [--env KEY=VALUE ...]

Options:
    --file          Treat first argument as a path to a .nu script file
    --env KEY=VAL   Pass environment variables to the nu process (repeatable)
    --timeout INT   Seconds before killing the process (default: 60)
    --quiet         Suppress the structured summary, only print stdout/stderr

Examples:
    uv run .kilocode/skills/nushell/scripts/nu_run.py 'ls | get name | first 5'
    uv run .kilocode/skills/nushell/scripts/nu_run.py /tmp/task.nu --file
    uv run .kilocode/skills/nushell/scripts/nu_run.py 'print $env.MY_VAR' --env MY_VAR=hello
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run a Nushell script safely.")
    parser.add_argument("script", help="Nu script content, or path if --file given")
    parser.add_argument("--file", action="store_true", help="Treat script arg as file path")
    parser.add_argument("--env", action="append", default=[], metavar="KEY=VALUE",
                        help="Extra environment variables (repeatable)")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds (default 60)")
    parser.add_argument("--quiet", action="store_true", help="Only print stdout/stderr, no summary")
    args = parser.parse_args()

    # Build environment
    env = os.environ.copy()
    for kv in args.env:
        if "=" not in kv:
            print(f"ERROR: --env value must be KEY=VALUE, got: {kv!r}", file=sys.stderr)
            sys.exit(2)
        k, v = kv.split("=", 1)
        env[k] = v

    # Determine script path
    cleanup_file = None
    if args.file:
        script_path = args.script
    else:
        # Write inline script to temp file
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".nu", delete=False)
        tmp.write(args.script)
        tmp.close()
        script_path = tmp.name
        cleanup_file = tmp.name

    try:
        result = subprocess.run(
            ["nu", script_path],
            capture_output=True,
            text=True,
            env=env,
            timeout=args.timeout,
        )
    except FileNotFoundError:
        print("ERROR: 'nu' not found in PATH. Install nushell: https://www.nushell.sh/", file=sys.stderr)
        sys.exit(127)
    except subprocess.TimeoutExpired:
        print(f"ERROR: Script timed out after {args.timeout}s", file=sys.stderr)
        sys.exit(124)
    finally:
        if cleanup_file:
            Path(cleanup_file).unlink(missing_ok=True)

    # Output
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if not args.quiet:
        status = "SUCCESS" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
        print(f"\n--- nu_run: {status} ---", file=sys.stderr)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
