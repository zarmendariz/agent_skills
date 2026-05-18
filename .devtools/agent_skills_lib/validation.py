"""Skill validation logic — single source of truth.

Used by both package_skill.py and quick_validate.py.
"""

import re
from pathlib import Path

import yaml

ALLOWED_PROPERTIES = frozenset({"name", "description", "license", "allowed-tools", "metadata"})
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024


def validate_skill(skill_path) -> tuple[bool, str]:
    """Validate a skill directory.

    Checks:
      - SKILL.md exists
      - YAML frontmatter present and well-formed
      - Required fields: name, description
      - No unexpected top-level keys
      - Name is hyphen-case, max 64 chars
      - Description has no angle brackets, max 1024 chars

    Returns:
        (is_valid, message) tuple.
    """
    skill_path = Path(skill_path)

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    if "name" not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if "description" not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Validate name
    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        if not re.match(r"^[a-z0-9-]+$", name):
            return False, f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)"
        if name.startswith("-") or name.endswith("-") or "--" in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        if len(name) > MAX_NAME_LENGTH:
            return False, f"Name is too long ({len(name)} characters). Maximum is {MAX_NAME_LENGTH} characters."

    # Validate description
    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        if "<" in description or ">" in description:
            return False, "Description cannot contain angle brackets (< or >)"
        if len(description) > MAX_DESCRIPTION_LENGTH:
            return False, (
                f"Description is too long ({len(description)} characters). "
                f"Maximum is {MAX_DESCRIPTION_LENGTH} characters."
            )

    return True, "Skill is valid!"
