---
name: skill-sync
description: >
  Synchronization skill for pushing and pulling agent skills and configuration between this
  repository and the global installations of Kilo CLI, GitHub Copilot CLI, and the cross-client
  ~/.agents/skills/ directory. Use when the user wants to: deploy or install skills globally so
  they are available in any project, push local config changes to one or both CLI tools, pull
  global configuration back into the repo, sync skills between machines, or set up the tools
  on a new machine (Linux, macOS, or Windows). Covers deploy.py and pull.py scripts, path
  resolution for all platforms, and handling Kilo CLI (~/.kilo/), GitHub Copilot CLI
  (~/.copilot/), and cross-client (~/.agents/) environments.
---

# Skill Sync

Synchronizes skills and configuration between this repo and the global installations
of **Kilo CLI**, **GitHub Copilot CLI**, and the **cross-client `~/.agents/skills/`** directory
on Linux, macOS, and Windows.

## Workflow

```
Deploy:  repo (skills/)  →  global CLI install
Pull:    global CLI install  →  repo (skills/)
```

Use `scripts/deploy.py` to push and `scripts/pull.py` to pull. Both scripts are
cross-platform and target one or more CLI tools.

## Deploy (repo → global)

```bash
# Deploy to all tools (recommended)
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all

# Deploy to Kilo CLI only
uv run --project .devtools skills/skill-sync/scripts/deploy.py --kilocode

# Deploy to GitHub Copilot CLI only
uv run --project .devtools skills/skill-sync/scripts/deploy.py --copilot

# Deploy to cross-client ~/.agents/skills/ only
uv run --project .devtools skills/skill-sync/scripts/deploy.py --agents

# Preview without making changes
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --dry-run

# Skip confirmation prompts
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --force
```

## Pull (global → repo)

```bash
# Pull config from all tools back to repo
uv run --project .devtools skills/skill-sync/scripts/pull.py --all

# Pull from Kilo CLI only
uv run --project .devtools skills/skill-sync/scripts/pull.py --kilocode

# Pull from GitHub Copilot CLI only
uv run --project .devtools skills/skill-sync/scripts/pull.py --copilot

# Pull from cross-client ~/.agents/skills/
uv run --project .devtools skills/skill-sync/scripts/pull.py --agents

# Preview without making changes
uv run --project .devtools skills/skill-sync/scripts/pull.py --all --dry-run
```

## What Gets Deployed

### Kilo CLI

| Source (repo)                              | Destination (global)                   |
|--------------------------------------------|----------------------------------------|
| `skills/`                                  | `~/.kilo/skills/`                      |
| `skills/` (legacy)                         | `~/.kilocode/skills/` (if exists)      |
| `.devtools/`                               | `~/.kilo/.devtools/`                   |
| `.kilocode/cli/global/settings/mcp_settings.json` | `~/.kilo/cli/global/settings/mcp_settings.json` |
| `.kilocode/cli/global/settings/custom_modes.yaml` | `~/.kilo/cli/global/settings/custom_modes.yaml` |
| `opencode.json`                            | `~/.config/kilo/opencode.json`         |

### GitHub Copilot CLI

| Source (repo)                              | Destination (global)                   |
|--------------------------------------------|----------------------------------------|
| `skills/`                                  | `~/.copilot/skills/`                   |
| `.devtools/`                               | `~/.copilot/.devtools/`                |
| `.github/copilot-instructions.md`          | `~/.copilot/copilot-instructions.md`   |

### Cross-Client (agentskills.io standard)

| Source (repo)                              | Destination (global)                   |
|--------------------------------------------|----------------------------------------|
| `skills/`                                  | `~/.agents/skills/`                    |

The `~/.agents/skills/` path is the cross-client convention recognized by Cursor, Gemini CLI,
JetBrains Junie, GitHub Copilot CLI, and other Agent Skills-compatible tools.

## Global Config Paths

The scripts resolve paths automatically based on OS:

### Kilo CLI
| Platform | Skills path |
|----------|-------------|
| Linux/macOS | `~/.kilo/skills/` |
| Windows | `%USERPROFILE%\.kilo\skills\` |

Legacy path `~/.kilocode/skills/` is still scanned by Kilo CLI for backward compatibility.

### GitHub Copilot CLI
| Platform | Skills path | Instructions path |
|----------|-------------|-------------------|
| Linux/macOS | `~/.copilot/skills/` | `~/.copilot/copilot-instructions.md` |
| Windows | `%USERPROFILE%\.copilot\skills\` | `%USERPROFILE%\.copilot\copilot-instructions.md` |

### Cross-Client
| Platform | Skills path |
|----------|-------------|
| All | `~/.agents/skills/` |

Override paths via environment variables:
- `KILOCODE_SKILLS_DIR` — Kilo CLI skills dir
- `KILOCODE_DEVTOOLS_DIR` — Kilo CLI .devtools dir
- `COPILOT_SKILLS_DIR` — Copilot skills dir
- `COPILOT_DEVTOOLS_DIR` — Copilot .devtools dir
- `COPILOT_HOME` — Copilot home dir (default: `~/.copilot`)
- `COPILOT_INSTRUCTIONS_PATH` — Copilot instructions file
- `AGENTS_SKILLS_DIR` — Cross-client skills dir

## What Gets Pulled

`pull.py --kilocode` mirrors `scripts/merge-config.nu` but cross-platform:
- Skills from `~/.kilo/skills/` → `skills/`
- `mcp_settings.json` and `custom_modes.yaml` from global settings
- `opencode.json` from `~/.config/kilo/`

`pull.py --copilot` pulls:
- Skills from `~/.copilot/skills/` → `skills/`
- `~/.copilot/copilot-instructions.md` → `.github/copilot-instructions.md`

`pull.py --agents` pulls:
- Skills from `~/.agents/skills/` → `skills/`

> **Note:** Pull never overwrites — it reports conflicts and skips unless `--force` is passed.
> Auth tokens, secrets, and runtime state are never pulled (same exclusions as `merge-config.nu`).

## Setting Up a New Machine

1. Clone the repo
2. Install prerequisites: `uv` (Python tooling), `nu` (Nushell, optional), `gh` (GitHub CLI, optional)
3. Deploy everything: `uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --force`
4. Restart Kilo CLI and/or GitHub Copilot CLI to load the new skills

