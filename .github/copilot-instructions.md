# Copilot Instructions

This repository manages AI agent **skills** for both [GitHub Copilot CLI](https://docs.github.com/copilot/concepts/agents/about-copilot-cli) and [KiloCode CLI](https://kilo.ai), following the Anthropic Agent Skill specification. Skills are modular packages that extend Claude's capabilities with specialized knowledge, workflows, and tools.

Requires **Python 3.13+** and [uv](https://docs.astral.sh/uv/).

## Key Commands

All Python tooling runs via `uv` with the `.devtools` project:

```bash
# Run tests
uv run --project .devtools pytest

# Run tests with coverage
uv run --project .devtools pytest --cov

# Run a single test file
uv run --project .devtools pytest tests/test_validate_skill.py

# Run a single test by name pattern
uv run --project .devtools pytest -k "test_valid_skill_passes"

# Initialize a new skill (creates directory + template files)
uv run --project .devtools skills/skill-creator/scripts/init_skill.py <skill-name>
uv run --project .devtools skills/skill-creator/scripts/init_skill.py <skill-name> --path skills

# Validate and package a skill into a distributable .skill file
uv run --project .devtools skills/skill-creator/scripts/package_skill.py skills/<skill-name>

# Validate only (without packaging)
uv run --project .devtools skills/skill-creator/scripts/quick_validate.py skills/<skill-name>
```

**Global context (outside repo):** When skills are deployed globally, `.devtools` lives at
`~/.copilot/.devtools/` (Copilot CLI) or `~/.kilocode/.devtools/` (KiloCode CLI). Use the
absolute path:

```bash
uv run --project ~/.copilot/.devtools skills/skill-creator/scripts/init_skill.py <skill-name>
```

### uv Tool Preference

Tools installed system-wide via `uv tool install` must always be invoked directly rather than
added as project dependencies. Check available tools with `uv tool list`. For example, if
`docling` is installed as a tool, invoke it as `docling <args>` — never via
`uv run --project .devtools docling`.

**Rule:** If a CLI executable is available from `uv tool list`, use it directly. Only use
`uv run --project .devtools` for scripts that depend on `agent_skills_lib` (validation,
packaging, deployment scripts).

### Deployment (Kilo CLI + GitHub Copilot CLI + Cross-Client)

Cross-platform Python scripts handle deploying to and pulling from all tool environments:

```bash
# Deploy skills + config to all tools
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all
uv run --project .devtools skills/skill-sync/scripts/deploy.py --kilocode   # Kilo CLI only
uv run --project .devtools skills/skill-sync/scripts/deploy.py --copilot    # Copilot only
uv run --project .devtools skills/skill-sync/scripts/deploy.py --agents     # ~/.agents/ only
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --dry-run
uv run --project .devtools skills/skill-sync/scripts/deploy.py --all --force

# Pull config from global installs back into repo
uv run --project .devtools skills/skill-sync/scripts/pull.py --all
uv run --project .devtools skills/skill-sync/scripts/pull.py --all --dry-run
```

**Global install paths (auto-detected by scripts):**

| Tool | Skills path | .devtools path | Instructions |
|------|-------------|----------------|--------------|
| Kilo CLI | `~/.kilo/skills/` | `~/.kilo/.devtools/` | N/A |
| Kilo CLI (legacy) | `~/.kilocode/skills/` | — | N/A |
| GitHub Copilot CLI | `~/.copilot/skills/` | `~/.copilot/.devtools/` | `~/.copilot/copilot-instructions.md` |
| Cross-Client | `~/.agents/skills/` | — | — |

Override via env vars: `KILOCODE_SKILLS_DIR`, `KILOCODE_DEVTOOLS_DIR`, `COPILOT_SKILLS_DIR`, `COPILOT_DEVTOOLS_DIR`, `COPILOT_HOME`, `COPILOT_INSTRUCTIONS_PATH`, `AGENTS_SKILLS_DIR`.

### Legacy Nushell scripts (KiloCode CLI only)

```bash
# Push skills to ~/.kilocode/skills/ (Nushell required)
nu scripts/push-skills.nu
nu scripts/push-skills.nu --dry-run
nu scripts/push-skills.nu --force

# Pull global KiloCode/OpenCode config into the repo (Nushell required)
nu scripts/merge-config.nu
```

Prefer the Python deploy scripts above for cross-platform and cross-tool support.

## Architecture

```
skills/                    # All skills live here (source of truth for all CLI tools)
  ast-grep/                # Structural code search/transform via AST pattern matching
  docling/                 # Document parsing (uses docling uv tool)
  nushell/                 # Nushell language skill
  skill-creator/           # Skill authoring workflow
  skill-sync/              # Deploy/pull skill — manages global installs
  tools/                   # System tool registry
  unit-testing/            # Embedded C unit testing skill
  uv/                      # Python project management with uv
.kilocode/
  cli/global/settings/     # KiloCode CLI settings (mcp_settings.json, custom_modes.yaml)
.devtools/                 # Python tooling (pyproject.toml, uv.lock) — Python 3.13+
  agent_skills_lib/        # Shared library (validation, path resolution)
.github/
  copilot-instructions.md  # Project-level Copilot instructions (also deployed globally)
  workflows/ci.yml         # GitHub Actions CI pipeline
tests/                     # pytest test suite
scripts/                   # Nushell repo-management utilities (KiloCode only)
opencode.json              # KiloCode/OpenCode config (synced from ~/.config/kilo/)
```

**Skills are the primary artifact.** The same skills are deployed to Kilo CLI (`~/.kilo/skills/`), GitHub Copilot CLI (`~/.copilot/skills/`), and the cross-client path (`~/.agents/skills/`) via `deploy.py`. The `skills/` directory is the canonical source. The `.devtools/` project is deployed alongside to provide the shared `agent_skills_lib` used by skill scripts.

## Testing Notes

- CI runs on **Ubuntu**, **Windows**, and **macOS** with Python 3.13
- CI validates all skills via `quick_validate.py` after tests pass — new skills must be explicitly added to `.github/workflows/ci.yml`
- `pytest.ini` adds skill script directories to `pythonpath`, so tests can directly import skill scripts (e.g., `from deploy import ...`)
- Test fixtures use `tmp_path` and `conftest.py` provides `valid_skill_dir` and `mock_repo_root` helpers

## Skill Conventions

### SKILL.md structure

Every `SKILL.md` requires YAML frontmatter. Required fields: `name` and `description`. Optional: `license`, `allowed-tools`, `compatibility`, `metadata`. No other keys are allowed.

```yaml
---
name: my-skill
description: >
  What this skill does and when to use it. Include specific triggers and scenarios.
  All "when to use" context belongs here — not in the body — because the body
  only loads after the skill triggers.
---
```

The body is loaded only after triggering; keep it **under 500 lines**. Write in imperative/infinitive form.

### Progressive disclosure (three levels)

1. **Frontmatter** (~100 words) — always in context; determines if skill triggers
2. **SKILL.md body** (<5k words) — loaded when skill triggers
3. **Bundled resources** — loaded by Claude only when needed

Keep `SKILL.md` lean. Move detailed reference material and schemas to `references/` files, and explicitly reference them from `SKILL.md` so Claude knows they exist and when to load them.

### Skill naming

Skill directories use **hyphen-case**, lowercase, max 64 characters (e.g., `skill-creator`, `unit-testing`). Name cannot start/end with a hyphen or contain consecutive hyphens. Description cannot contain angle brackets and is limited to 1024 characters.

### Bundled resources

- **`scripts/`** — Deterministic code. Scripts that need `agent_skills_lib` use `uv run --project <devtools-path>`. Self-contained scripts use PEP 723 inline metadata and run with `uv run <script>`. Always test scripts before packaging.
- **`references/`** — Lazy-loaded docs. For files >100 lines, include a table of contents so Claude can assess scope before reading.
- **`assets/`** — Files used in output (templates, images, boilerplate), never loaded into context.

Do **not** add auxiliary docs (README, CHANGELOG, INSTALLATION_GUIDE, etc.) inside a skill directory.

### Packaging output

`package_skill.py` runs validation first, then creates `<skill-name>.skill` (a zip with `.skill` extension) in `skill-files/` by default. Fix all validation errors before packaging.

## Nushell Scripts

The `scripts/` utilities are written in Nushell (`.nu`). Run them with `nu scripts/<script>.nu`. The `push-skills.nu` script copies from `skills/` to `~/.kilocode/skills/`; `merge-config.nu` pulls the reverse direction (global config → repo).

### Nushell as Preferred Shell

Nushell (`nu`) is the preferred command execution environment. On Windows, copilot-cli
hardcodes PowerShell as the shell tool — there is no configuration to change this. To use
nushell, invoke it through the PowerShell tool:

```powershell
# One-liner (single quotes prevent PowerShell $-interpolation)
nu -c 'ls | where type == file | sort-by size -r | first 10'

# Multi-line via temp file
@'
let files = ls | where type == file
print $"Found ($files | length) files"
'@ | Set-Content $env:TEMP\__nu.nu -Encoding UTF8; nu $env:TEMP\__nu.nu
```

The `nushell` skill provides comprehensive language reference and invocation patterns.
Always prefer `nu -c '...'` over raw PowerShell for data processing and querying tasks.

## opencode.json

Tracks KiloCode/OpenCode configuration. Sensitive files (`config.json`, `secrets.json`, `global-state.json`, cache directories) are intentionally excluded from the repo.
