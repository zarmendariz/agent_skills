#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run ast-grep analysis on a project and produce a structured report.

Wraps ast-grep scan/run with additional reporting capabilities:
- JSON output parsing and summary
- Multi-rule scanning with aggregation
- Severity-based exit codes for CI/CD

Usage:
    uv run scripts/run_analysis.py scan [--rules-dir DIR] [--format FORMAT] [PATH]
    uv run scripts/run_analysis.py search --pattern PATTERN --lang LANG [PATH]
    uv run scripts/run_analysis.py report --rules-dir DIR [--output FILE] [PATH]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def find_ast_grep() -> str:
    """Find ast-grep executable."""
    import shutil

    path = shutil.which("ast-grep")
    if not path:
        print("❌ ast-grep not found. Install with: cargo install ast-grep --locked")
        sys.exit(1)
    return path


def run_scan(
    rules_dir: str | None = None,
    rule_file: str | None = None,
    target: str = ".",
    format_: str = "json",
) -> list[dict]:
    """Run ast-grep scan and return results."""
    ast_grep = find_ast_grep()
    cmd = [ast_grep, "scan", "--json=compact"]

    if rule_file:
        cmd.extend(["--rule", rule_file])
    elif rules_dir:
        # Scan needs sgconfig.yml or --rule; use inline approach
        cmd.extend(["--rule", rules_dir])

    cmd.append(target)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not result.stdout:
        print(f"⚠️  ast-grep scan failed: {result.stderr}", file=sys.stderr)
        return []

    if not result.stdout.strip():
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        # Try stream format (one JSON per line)
        results = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return results


def run_search(pattern: str, lang: str, target: str = ".") -> list[dict]:
    """Run ast-grep run (search) and return results."""
    ast_grep = find_ast_grep()
    cmd = [ast_grep, "run", "-p", pattern, "-l", lang, "--json=compact", target]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if not result.stdout.strip():
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def format_results(results: list[dict], format_: str = "summary") -> str:
    """Format results for display."""
    if not results:
        return "✅ No issues found."

    if format_ == "json":
        return json.dumps(results, indent=2)

    # Summary format
    lines = []
    by_severity: dict[str, list] = {}
    by_file: dict[str, list] = {}

    for r in results:
        severity = r.get("severity", "info")
        file_path = r.get("file", "unknown")
        by_severity.setdefault(severity, []).append(r)
        by_file.setdefault(file_path, []).append(r)

    lines.append(f"📊 Found {len(results)} issue(s) across {len(by_file)} file(s)\n")

    # Severity breakdown
    severity_order = ["error", "warning", "info", "hint"]
    for sev in severity_order:
        if sev in by_severity:
            icon = {"error": "🔴", "warning": "🟡", "info": "🔵", "hint": "⚪"}.get(
                sev, "•"
            )
            lines.append(f"  {icon} {sev}: {len(by_severity[sev])}")

    lines.append("")

    # Top files
    sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)
    lines.append("📁 Files with most issues:")
    for file_path, issues in sorted_files[:10]:
        lines.append(f"  {file_path}: {len(issues)}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ast-grep analysis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan command
    scan_p = subparsers.add_parser("scan", help="Scan with rules")
    scan_p.add_argument("--rules-dir", help="Rules directory")
    scan_p.add_argument("--rule", help="Single rule file")
    scan_p.add_argument("--format", default="summary", choices=["summary", "json"])
    scan_p.add_argument("path", nargs="?", default=".")

    # search command
    search_p = subparsers.add_parser("search", help="Search with pattern")
    search_p.add_argument("-p", "--pattern", required=True, help="AST pattern")
    search_p.add_argument("-l", "--lang", required=True, help="Language")
    search_p.add_argument("--format", default="summary", choices=["summary", "json"])
    search_p.add_argument("path", nargs="?", default=".")

    # report command
    report_p = subparsers.add_parser("report", help="Generate analysis report")
    report_p.add_argument("--rules-dir", required=True, help="Rules directory")
    report_p.add_argument("--output", "-o", help="Output file")
    report_p.add_argument("path", nargs="?", default=".")

    args = parser.parse_args()

    if args.command == "scan":
        results = run_scan(
            rules_dir=args.rules_dir, rule_file=args.rule, target=args.path
        )
        print(format_results(results, args.format))
        # Exit with error if any errors found
        if any(r.get("severity") == "error" for r in results):
            sys.exit(1)

    elif args.command == "search":
        results = run_search(args.pattern, args.lang, args.path)
        print(format_results(results, args.format))

    elif args.command == "report":
        results = run_scan(rules_dir=args.rules_dir, target=args.path)
        report = format_results(results, "summary")
        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
            print(f"📄 Report written to {args.output}")
        else:
            print(report)


if __name__ == "__main__":
    main()
