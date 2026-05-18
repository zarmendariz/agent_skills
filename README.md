# agent_skills

A repository for creating and maintaining AI agent skills for [GitHub Copilot CLI](https://docs.github.com/copilot/concepts/agents/about-copilot-cli) and [KiloCode CLI](https://kilo.ai), following the Anthropic Agent Skill specification. Skills are modular packages that extend Claude's capabilities with specialized knowledge, workflows, and tools.

## Quick Start

```bash
# Run tests
uv run --project .devtools pytest

# Run tests with coverage
uv run --project .devtools pytest --cov

# Initialize a new skill
uv run --project .devtools skills/skill-creator/scripts/init_skill.py <skill-name>

# Validate a skill
uv run --project .devtools skills/skill-creator/scripts/quick_validate.py skills/<skill-name>

# Package a skill
uv run --project .devtools skills/skill-creator/scripts/package_skill.py skills/<skill-name>

# Deploy skills to global CLI installations
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all

# Pull global config back into repo
uv run --project .devtools skills/skill-sync/scripts/pull.py --all
```

## Architecture

```
skills/                    # All skills (source of truth for both CLI tools)
  skill-sync/              # Deploy/pull — manages global installs
  nushell/                 # Nushell language skill
  skill-creator/           # Skill authoring workflow
  unit-testing/            # Embedded C unit testing skill
.kilocode/
  cli/global/settings/     # KiloCode-specific settings
.devtools/                 # Python tooling (pyproject.toml, uv.lock)
  agent_skills_lib/        # Shared library (validation, path resolution)
.github/
  copilot-instructions.md  # Project-level Copilot instructions
  workflows/ci.yml         # GitHub Actions CI
tests/                     # pytest test suite
scripts/                   # Legacy Nushell repo utilities
```

## Skills

| Skill | Purpose |
|-------|---------|
| **skill-sync** | Deploy/pull skills and config between repo and global CLI installs |
| **skill-creator** | Guide for creating and packaging new skills |
| **nushell** | Nushell shell language support |
| **unit-testing** | Embedded C unit testing with Unity/CMock/Ceedling |

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
uv sync --project .devtools

# Run full test suite
uv run --project .devtools pytest

# Run with coverage report
uv run --project .devtools pytest --cov --cov-report=term-missing
```
