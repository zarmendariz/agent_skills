#!/usr/bin/env python3
"""
pull.py - Pull skills and configuration from global CLI installations back into the repo.

Supports KiloCode CLI and GitHub Copilot CLI on Linux, macOS, and Windows.
Auth tokens, secrets, and runtime state are never pulled.

Usage:
    uv run --project .devtools .kilocode/skills/skill-sync/scripts/pull.py --all
    uv run --project .devtools .kilocode/skills/skill-sync/scripts/pull.py --kilocode
    uv run --project .devtools .kilocode/skills/skill-sync/scripts/pull.py --copilot
    uv run --project .devtools .kilocode/skills/skill-sync/scripts/pull.py --all --dry-run
    uv run --project .devtools .kilocode/skills/skill-sync/scripts/pull.py --all --force

Environment variable overrides (same as deploy.py):
    KILOCODE_SKILLS_DIR        Override KiloCode global skills directory
    COPILOT_SKILLS_DIR         Override GitHub Copilot global skills directory
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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / ".devtools"))
from agent_skills_lib import paths as _paths  # noqa: E402


# ── Path resolution (delegating to shared module) ─────────────────────────────

def repo_root() -> Path:
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

NEVER_PULL = {
    "config.json",
    "global-state.json",
    "secrets.json",
}

NEVER_PULL_DIRS = {
    "cache",
    "tasks",
    "workspaces",
    "logs",
}


def pull_file(src: Path, dst: Path, dry_run: bool, force: bool, label: str) -> bool:
    if not src.exists():
        print(f"  {label} — not found at {src}, skipping")
        return True

    if dst.exists() and not force:
        print(f"  {label} — already exists at {dst}, skipping (use --force to overwrite)")
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


def pull_skills(src_dir: Path, dst_dir: Path, dry_run: bool, force: bool) -> bool:
    if not src_dir.exists():
        print(f"  Skills source not found: {src_dir}, skipping")
        return True

    skills = [p for p in src_dir.iterdir() if p.is_dir()]
    if not skills:
        print("  No skills found in global installation.")
        return True

    print(f"  Skills found: {', '.join(s.name for s in skills)}")

    all_ok = True
    for skill in skills:
        dst = dst_dir / skill.name
        if dst.exists() and not force:
            print(f"  skill: {skill.name} — already exists, skipping (use --force to overwrite)")
            continue
        print(f"  skill: {skill.name}")
        print(f"    {skill}")
        print(f"    → {dst}")
        if dry_run:
            print("    [dry-run] skipped")
            continue
        try:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(skill, dst)
            print("    OK")
        except Exception as e:
            print(f"    FAILED: {e}")
            all_ok = False

    return all_ok


# ── Pull targets ───────────────────────────────────────────────────────────────

def pull_kilocode(root: Path, dry_run: bool, force: bool) -> bool:
    print("\n── KiloCode CLI ──────────────────────────────────────────────")
    all_ok = True

    # Skills
    all_ok &= pull_skills(
        kilocode_skills_dir(),
        root / ".kilocode" / "skills",
        dry_run, force,
    )

    # mcp_settings.json
    all_ok &= pull_file(
        kilocode_settings_dir() / "mcp_settings.json",
        root / ".kilocode" / "cli" / "global" / "settings" / "mcp_settings.json",
        dry_run, force, "mcp_settings.json",
    )

    # custom_modes.yaml
    all_ok &= pull_file(
        kilocode_settings_dir() / "custom_modes.yaml",
        root / ".kilocode" / "cli" / "global" / "settings" / "custom_modes.yaml",
        dry_run, force, "custom_modes.yaml",
    )

    # opencode.json
    all_ok &= pull_file(
        kilocode_opencode_path(),
        root / "opencode.json",
        dry_run, force, "opencode.json",
    )

    return all_ok


def pull_copilot(root: Path, dry_run: bool, force: bool) -> bool:
    print("\n── GitHub Copilot CLI ────────────────────────────────────────")
    all_ok = True

    # Skills from Copilot global dir (if present)
    all_ok &= pull_skills(
        copilot_skills_dir(),
        root / ".kilocode" / "skills",
        dry_run, force,
    )

    # copilot-instructions.md
    all_ok &= pull_file(
        copilot_instructions_path(),
        root / ".github" / "copilot-instructions.md",
        dry_run, force, "copilot-instructions.md",
    )

    return all_ok


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pull skills and config from global CLI installations into the repo."
    )
    parser.add_argument("--kilocode", action="store_true", help="Pull from KiloCode CLI")
    parser.add_argument("--copilot", action="store_true", help="Pull from GitHub Copilot CLI")
    parser.add_argument("--all", dest="all_targets", action="store_true", help="Pull from all CLI tools")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be pulled, make no changes")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing files in repo")
    args = parser.parse_args()

    if not (args.kilocode or args.copilot or args.all_targets):
        parser.error("Specify at least one target: --kilocode, --copilot, or --all")

    root = repo_root()
    print(f"Repository root: {root}")
    if args.dry_run:
        print("[dry-run mode — no changes will be made]")

    results = []

    if args.all_targets or args.kilocode:
        ok = pull_kilocode(root, args.dry_run, args.force)
        results.append(("KiloCode CLI", ok))

    if args.all_targets or args.copilot:
        ok = pull_copilot(root, args.dry_run, args.force)
        results.append(("GitHub Copilot CLI", ok))

    print("\n── Summary ───────────────────────────────────────────────────")
    all_ok = True
    for name, ok in results:
        status = "OK" if ok else "FAILED"
        print(f"  {name}: {status}")
        all_ok = all_ok and ok

    if args.dry_run:
        print("\n[dry-run] No changes were made.")
    else:
        print("\nTip: Review changes with: git diff")
        print("Note: Secrets and runtime state were never pulled.")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
