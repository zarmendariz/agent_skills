"""Path resolution for deploy and pull operations — single source of truth.

Provides platform-aware path resolution for KiloCode CLI and GitHub Copilot CLI
global installations, with environment variable overrides.
"""

import os
import platform
from pathlib import Path


def repo_root_from_script(script_path: str) -> Path:
    """Resolve repo root from a script located at .kilocode/skills/<skill>/scripts/<script>.py."""
    return Path(script_path).resolve().parent.parent.parent.parent.parent


def kilocode_skills_dir() -> Path:
    """Global KiloCode skills directory. Override: KILOCODE_SKILLS_DIR."""
    override = os.environ.get("KILOCODE_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".kilocode" / "skills"


def kilocode_settings_dir() -> Path:
    """Global KiloCode CLI settings directory."""
    return Path.home() / ".kilocode" / "cli" / "global" / "settings"


def kilocode_opencode_path() -> Path:
    """Destination for opencode.json (KiloCode reads from ~/.config/kilo/)."""
    if platform.system() == "Windows":
        config = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return config / "kilo" / "opencode.json"
    return Path.home() / ".config" / "kilo" / "opencode.json"


def copilot_skills_dir() -> Path:
    """Global GitHub Copilot skills directory. Override: COPILOT_SKILLS_DIR."""
    override = os.environ.get("COPILOT_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    if platform.system() == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return local / "github-copilot" / "skills"
    return Path.home() / ".config" / "github-copilot" / "skills"


def copilot_instructions_path() -> Path:
    """Global copilot-instructions.md path. Override: COPILOT_INSTRUCTIONS_PATH."""
    override = os.environ.get("COPILOT_INSTRUCTIONS_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".github" / "copilot-instructions.md"
