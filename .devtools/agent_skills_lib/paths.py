"""Path resolution for deploy and pull operations — single source of truth.

Provides platform-aware path resolution for KiloCode CLI and GitHub Copilot CLI
global installations, with environment variable overrides.

Copilot CLI configuration directory (per official docs):
  Default: ~/.copilot/  (overridable via COPILOT_HOME env var)
  Skills:  ~/.copilot/skills/
  Instructions: ~/.copilot/copilot-instructions.md

KiloCode / Kilo CLI configuration directory:
  Skills (current):  ~/.kilo/skills/
  Skills (legacy):   ~/.kilocode/skills/  (still scanned for backward compat)
  Settings: ~/.kilo/cli/global/settings/

Cross-client interoperability (agentskills.io standard):
  Skills:  ~/.agents/skills/
"""

import os
import platform
from pathlib import Path


def repo_root_from_script(script_path: str) -> Path:
    """Resolve repo root from a script located at skills/<skill>/scripts/<script>.py."""
    return Path(script_path).resolve().parent.parent.parent.parent


def kilocode_skills_dir() -> Path:
    """Global KiloCode/Kilo CLI skills directory. Override: KILOCODE_SKILLS_DIR.

    Kilo CLI 1.0 uses ~/.kilo/skills/ as primary path.
    Legacy path ~/.kilocode/skills/ is still scanned for backward compatibility.
    """
    override = os.environ.get("KILOCODE_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".kilo" / "skills"


def kilocode_legacy_skills_dir() -> Path:
    """Legacy KiloCode skills directory (~/.kilocode/skills/). Still scanned by Kilo CLI."""
    return Path.home() / ".kilocode" / "skills"


def kilocode_devtools_dir() -> Path:
    """Global KiloCode/Kilo CLI .devtools directory. Override: KILOCODE_DEVTOOLS_DIR."""
    override = os.environ.get("KILOCODE_DEVTOOLS_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".kilo" / ".devtools"


def kilocode_settings_dir() -> Path:
    """Global KiloCode/Kilo CLI settings directory."""
    return Path.home() / ".kilo" / "cli" / "global" / "settings"


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


def copilot_devtools_dir() -> Path:
    """Global GitHub Copilot CLI .devtools directory. Override: COPILOT_DEVTOOLS_DIR."""
    override = os.environ.get("COPILOT_DEVTOOLS_DIR")
    if override:
        return Path(override).expanduser()
    return copilot_home() / ".devtools"


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


def agents_skills_dir() -> Path:
    """Cross-client ~/.agents/skills/ directory (agentskills.io standard). Override: AGENTS_SKILLS_DIR."""
    override = os.environ.get("AGENTS_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".agents" / "skills"
