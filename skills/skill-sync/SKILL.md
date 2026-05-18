---
name: skill-sync
description: >
  Synchronization skill for pushing and pulling agent skills and configuration between this
  repository and the global installations of KiloCode CLI and GitHub Copilot CLI.
  Use when the user wants to: deploy or install skills globally so they are available
  in any project, push local config changes to one or both CLI tools, pull global
  configuration back into the repo, sync skills between machines, or set up the tools
  on a new machine (Linux or Windows). Covers deploy.py and pull.py scripts, path
  resolution for both platforms, and handling both KiloCode CLI (~/.kilocode/) and
  GitHub Copilot CLI (~/.copilot/) environments.
---

# Skill Sync

Synchronizes skills and configuration between this repo and the global installations
of **KiloCode CLI** and **GitHub Copilot CLI** on Linux and Windows.

## Workflow

```
Deploy:  repo (skills/)  →  global CLI install
Pull:    global CLI install  →  repo (skills/)
```

Use `scripts/deploy.py` to push and `scripts/pull.py` to pull. Both scripts are
cross-platform and target one or both CLI tools.

## Deploy (repo → global)

```bash
# Deploy to both tools (recommended)
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all

# Deploy to KiloCode CLI only
uv run --project .devtools skills/skill-sync/scripts/deploy.py --kilocode

# Deploy to GitHub Copilot CLI only
uv run --project .devtools skills/skill-sync/scripts/deploy.py --copilot

# Preview without making changes
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --dry-run

# Skip confirmation prompts
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --force
```

## Pull (global → repo)

```bash
# Pull config from both tools back to repo
uv run --project .devtools skills/skill-sync/scripts/pull.py --all

# Pull from KiloCode CLI only
uv run --project .devtools skills/skill-sync/scripts/pull.py --kilocode

# Pull from GitHub Copilot CLI only
uv run --project .devtools skills/skill-sync/scripts/pull.py --copilot

# Preview without making changes
uv run --project .devtools skills/skill-sync/scripts/pull.py --all --dry-run
```

## What Gets Deployed

### KiloCode CLI

| Source (repo)                              | Destination (global)                   |
|--------------------------------------------|----------------------------------------|
| `skills/`                                  | `~/.kilocode/skills/`                  |
| `.kilocode/cli/global/settings/mcp_settings.json` | `~/.kilocode/cli/global/settings/mcp_settings.json` |
| `.kilocode/cli/global/settings/custom_modes.yaml` | `~/.kilocode/cli/global/settings/custom_modes.yaml` |
| `opencode.json`                            | `~/.config/kilo/opencode.json`         |

### GitHub Copilot CLI

| Source (repo)                              | Destination (global)                   |
|--------------------------------------------|----------------------------------------|
| `skills/`                                  | `~/.copilot/skills/`                   |
| `.github/copilot-instructions.md`          | `~/.copilot/copilot-instructions.md`   |

## Global Config Paths

The scripts resolve paths automatically based on OS:

### KiloCode CLI
| Platform | Skills path |
|----------|-------------|
| Linux/macOS | `~/.kilocode/skills/` |
| Windows | `%USERPROFILE%\.kilocode\skills\` |

### GitHub Copilot CLI
| Platform | Skills path | Instructions path |
|----------|-------------|-------------------|
| Linux/macOS | `~/.copilot/skills/` | `~/.copilot/copilot-instructions.md` |
| Windows | `%USERPROFILE%\.copilot\skills\` | `%USERPROFILE%\.copilot\copilot-instructions.md` |

Override paths via environment variables:
- `KILOCODE_SKILLS_DIR` — KiloCode skills dir
- `COPILOT_SKILLS_DIR` — Copilot skills dir
- `COPILOT_HOME` — Copilot home dir (default: `~/.copilot`)
- `COPILOT_INSTRUCTIONS_PATH` — Copilot instructions file

## What Gets Pulled

`pull.py --kilocode` mirrors `scripts/merge-config.nu` but cross-platform:
- Skills from `~/.kilocode/skills/` → `skills/`
- `mcp_settings.json` and `custom_modes.yaml` from global settings
- `opencode.json` from `~/.config/kilo/`

`pull.py --copilot` pulls:
- `~/.copilot/copilot-instructions.md` → `.github/copilot-instructions.md`

> **Note:** Pull never overwrites — it reports conflicts and skips unless `--force` is passed.
> Auth tokens, secrets, and runtime state are never pulled (same exclusions as `merge-config.nu`).

## Setting Up a New Machine

1. Clone the repo
2. Install prerequisites: `uv` (Python tooling), `nu` (Nushell, optional), `gh` (GitHub CLI, optional)
3. Deploy everything: `uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --force`
4. Restart KiloCode CLI and/or GitHub Copilot CLI to load the new skills

