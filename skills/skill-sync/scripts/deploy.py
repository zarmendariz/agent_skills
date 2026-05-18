#!/usr/bin/env python3
"""
deploy.py - Push skills and configuration from repo to global CLI installations.

Supports KiloCode CLI and GitHub Copilot CLI on Linux, macOS, and Windows.

Usage:
    uv run --project .devtools skills/skill-sync/scripts/deploy.py --all
    uv run --project .devtools skills/skill-sync/scripts/deploy.py --kilocode
    uv run --project .devtools skills/skill-sync/scripts/deploy.py --copilot
    uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --dry-run
    uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --force

Environment variable overrides:
    KILOCODE_SKILLS_DIR        Override KiloCode global skills directory
    COPILOT_SKILLS_DIR         Override GitHub Copilot global skills directory
    COPILOT_HOME               Override Copilot CLI home directory (default: ~/.copilot)
    COPILOT_INSTRUCTIONS_PATH  Override global copilot-instructions.md path
"""

import argparse
import os
import platform
import shutil
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows (scripts use Unicode box-drawing chars)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add shared library to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / ".devtools"))
from agent_skills_lib import paths as _paths  # noqa: E402


# ── Path resolution (delegating to shared module) ─────────────────────────────

def repo_root() -> Path:
    """Return repo root (two levels up from this script: skills/deploy/scripts/)."""
    return _paths.repo_root_from_script(__file__)


def kilocode_skills_dir() -> Path:
    return _paths.kilocode_skills_dir()


def kilocode_settings_dir() -> Path:
    return _paths.kilocode_settings_dir()


def kilocode_opencode_path() -> Path:
    return _paths.kilocode_opencode_path()


def copilot_skills_dir() -> Path:
    return _paths.copilot_skills_dir()


def copilot_instructions_path() -> Path:
    return _paths.copilot_instructions_path()


# ── File operations ────────────────────────────────────────────────────────────

def copy_dir(src: Path, dst: Path, dry_run: bool, label: str) -> bool:
    """Copy src directory to dst, removing dst first if it exists. Returns success."""
    print(f"  {label}")
    print(f"    {src}")
    print(f"    → {dst}")
    if dry_run:
        print("    [dry-run] skipped")
        return True
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print("    OK")
        return True
    except Exception as e:
        print(f"    FAILED: {e}")
        return False


def copy_file(src: Path, dst: Path, dry_run: bool, label: str) -> bool:
    """Copy a single file. Returns success."""
    if not src.exists():
        print(f"  {label} — source not found, skipping: {src}")
        return True
    print(f"  {label}")
    print(f"    {src}")
    print(f"    → {dst}")
    if dry_run:
        print("    [dry-run] skipped")
        return True
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print("    OK")
        return True
    except Exception as e:
        print(f"    FAILED: {e}")
        return False


def copy_skills(src_skills_dir: Path, dst_skills_dir: Path, dry_run: bool, force: bool) -> bool:
    """Copy all skill subdirectories. Returns True if all succeeded."""
    if not src_skills_dir.exists():
        print(f"  Source skills directory not found: {src_skills_dir}")
        return False

    skills = [p for p in src_skills_dir.iterdir() if p.is_dir()]
    if not skills:
        print("  No skills found.")
        return True

    print(f"  Skills: {', '.join(s.name for s in skills)}")

    # Check for conflicts
    existing = [s for s in skills if (dst_skills_dir / s.name).exists()]
    if existing and not force:
        print(f"  Will overwrite: {', '.join(s.name for s in existing)}")
        if not dry_run:
            answer = input("  Overwrite existing skills? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("  Aborted.")
                return False

    all_ok = True
    for skill in skills:
        dst = dst_skills_dir / skill.name
        ok = copy_dir(skill, dst, dry_run, f"skill: {skill.name}")
        all_ok = all_ok and ok
    return all_ok


# ── Deploy targets ─────────────────────────────────────────────────────────────

def deploy_kilocode(root: Path, dry_run: bool, force: bool) -> bool:
    print("\n── KiloCode CLI ──────────────────────────────────────────────")
    all_ok = True

    # Skills
    src_skills = root / "skills"
    all_ok &= copy_skills(src_skills, kilocode_skills_dir(), dry_run, force)

    # MCP settings
    all_ok &= copy_file(
        root / ".kilocode" / "cli" / "global" / "settings" / "mcp_settings.json",
        kilocode_settings_dir() / "mcp_settings.json",
        dry_run, "mcp_settings.json",
    )

    # Custom modes
    all_ok &= copy_file(
        root / ".kilocode" / "cli" / "global" / "settings" / "custom_modes.yaml",
        kilocode_settings_dir() / "custom_modes.yaml",
        dry_run, "custom_modes.yaml",
    )

    # opencode.json
    all_ok &= copy_file(
        root / "opencode.json",
        kilocode_opencode_path(),
        dry_run, "opencode.json",
    )

    return all_ok


def deploy_copilot(root: Path, dry_run: bool, force: bool) -> bool:
    print("\n── GitHub Copilot CLI ────────────────────────────────────────")
    all_ok = True

    # Skills (same source, different destination)
    src_skills = root / "skills"
    all_ok &= copy_skills(src_skills, copilot_skills_dir(), dry_run, force)

    # copilot-instructions.md
    all_ok &= copy_file(
        root / ".github" / "copilot-instructions.md",
        copilot_instructions_path(),
        dry_run, "copilot-instructions.md",
    )

    return all_ok


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deploy skills and config from repo to global CLI installations."
    )
    parser.add_argument("--kilocode", action="store_true", help="Deploy to KiloCode CLI")
    parser.add_argument("--copilot", action="store_true", help="Deploy to GitHub Copilot CLI")
    parser.add_argument("--all", dest="all_targets", action="store_true", help="Deploy to all CLI tools")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be copied, make no changes")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()

    if not (args.kilocode or args.copilot or args.all_targets):
        parser.error("Specify at least one target: --kilocode, --copilot, or --all")

    root = repo_root()
    print(f"Repository root: {root}")
    if args.dry_run:
        print("[dry-run mode — no changes will be made]")

    results = []

    if args.all_targets or args.kilocode:
        ok = deploy_kilocode(root, args.dry_run, args.force)
        results.append(("KiloCode CLI", ok))

    if args.all_targets or args.copilot:
        ok = deploy_copilot(root, args.dry_run, args.force)
        results.append(("GitHub Copilot CLI", ok))

    print("\n── Summary ───────────────────────────────────────────────────")
    all_ok = True
    for name, ok in results:
        status = "OK" if ok else "FAILED"
        print(f"  {name}: {status}")
        all_ok = all_ok and ok

    if args.dry_run:
        print("\n[dry-run] No changes were made.")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
