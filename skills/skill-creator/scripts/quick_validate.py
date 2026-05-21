#!/usr/bin/env python3
"""
Quick validation script for skills - delegates to shared validation module.

Usage:
    uv run --project .devtools skills/skill-creator/scripts/quick_validate.py <skill_directory>
"""

import sys
from pathlib import Path

# Import shared library (available via uv run --project .devtools; fallback for direct execution)
try:
    from agent_skills_lib.validation import validate_skill
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / ".devtools"))
    from agent_skills_lib.validation import validate_skill  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run --project .devtools skills/skill-creator/scripts/quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)