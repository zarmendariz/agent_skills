"""Path resolution for deploy and pull operations — single source of truth.

Provides platform-aware path resolution for KiloCode CLI and GitHub Copilot CLI
global installations, with environment variable overrides.

Copilot CLI configuration directory (per official docs):
  Default: ~/.copilot/  (overridable via COPILOT_HOME env var)
  Skills:  ~/.copilot/skills/
  Instructions: ~/.copilot/copilot-instructions.md

KiloCode CLI configuration directory:
  Skills:  ~/.kilocode/skills/
  Settings: ~/.kilocode/cli/global/settings/
"""

import os
import platform
from pathlib import Path


def repo_root_from_script(script_path: str) -> Path:
    """Resolve repo root from a script located at skills/<skill>/scripts/<script>.py."""
    return Path(script_path).resolve().parent.parent.parent.parent


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


def copilot_home() -> Path:
    """Copilot CLI home directory. Override: COPILOT_HOME."""
    override = os.environ.get("COPILOT_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".copilot"


def copilot_skills_dir() -> Path:
    """Global GitHub Copilot CLI skills directory. Override: COPILOT_SKILLS_DIR."""
    override = os.environ.get("COPILOT_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    return copilot_home() / "skills"


def copilot_instructions_path() -> Path:
    """Global copilot-instructions.md path. Override: COPILOT_INSTRUCTIONS_PATH."""
    override = os.environ.get("COPILOT_INSTRUCTIONS_PATH")
    if override:
        return Path(override).expanduser()
    return copilot_home() / "copilot-instructions.md"
