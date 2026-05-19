---
name: uv
description: >
  Python project management with uv — the fast Rust-based package manager that replaces pip,
  pip-tools, pipx, poetry, pyenv, and virtualenv. Use this skill when creating Python projects,
  managing dependencies via pyproject.toml, running scripts with inline metadata (PEP 723),
  installing system tools with `uv tool`, managing Python versions, working with virtual
  environments, building/publishing packages, or any task involving uv commands. Triggers on:
  "uv", "pyproject.toml", "python project", "add dependency", "virtual environment",
  "uv tool", "uvx", "inline script", "dependency group", or Python packaging workflows.
---

# uv — Python Project & Package Manager

uv is an extremely fast Python package and project manager written in Rust by Astral. It
provides a single tool replacing `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `twine`, and
`virtualenv`.

## Critical Distinction: Tools vs. Project Dependencies

**Tools** (`uv tool install`, `uvx`) run in isolated environments completely separate from any
project. They provide system-wide CLI commands (like `ruff`, `black`, `mypy`) without polluting
project dependencies.

**Project dependencies** (`uv add`) are declared in `pyproject.toml` and installed into the
project's `.venv`.

**Rule: If a tool is installed on the system via `uv tool install`, do NOT add it as a project
dependency unless the user explicitly requests it.** For example, `ruff` installed via
`uv tool install ruff` is available system-wide — adding it to `project.dependencies` is
incorrect. If it must be pinned per-project, use a development dependency group instead:

```bash
uv add --group lint ruff
```

## Tools — System-Wide CLI Applications

Tools are Python packages providing CLI commands, installed in isolated environments.
See [`references/tools.md`](references/tools.md) for the complete tools reference including
environment management, version pinning, plugins, and upgrade workflows.

### Quick Reference

```bash
# Run a tool without installing (ephemeral environment)
uvx ruff check .
uvx black --check .
uvx --from httpie http GET example.com

# Install persistently (adds to PATH)
uv tool install ruff
uv tool install 'black>=24'
uv tool install mkdocs --with mkdocs-material

# Manage installed tools
uv tool list
uv tool upgrade ruff
uv tool upgrade --all
uv tool uninstall ruff

# Update shell PATH
uv tool update-shell
```

### Key Behaviors

- `uvx <tool>` = `uv tool run <tool>` — runs in a temporary cached environment
- `uv tool install <tool>` — creates a persistent isolated environment, symlinks executables
- Tool environments are **never** the project `.venv` — complete isolation
- `uvx` uses cached version after first invocation; use `@latest` to force refresh
- Once installed, `uvx ruff` uses the installed version (not ephemeral)

## Projects — Creating and Managing

See [`references/projects.md`](references/projects.md) for the complete project and dependency
management reference including pyproject.toml structure, dependency groups, sources, workspaces,
lock/sync workflows, PEP standards, and best practices.

### Quick Reference

```bash
# Create projects
uv init my-app                    # Application (no build system)
uv init --lib my-lib              # Library (src layout, build system)
uv init --package my-cli          # Packaged app (entry points)
uv init --bare my-project         # Minimal pyproject.toml only

# Dependency management
uv add httpx                      # Add to project.dependencies
uv add --dev pytest               # Add to [dependency-groups] dev
uv add --group lint ruff          # Add to [dependency-groups] lint
uv add --optional viz matplotlib  # Add to [project.optional-dependencies]
uv add 'numpy>=1.26,<2'          # With version constraints
uv remove httpx                   # Remove dependency

# Environment operations
uv sync                           # Install all deps from lockfile
uv sync --frozen                  # Without checking lockfile freshness
uv lock                           # Resolve and write uv.lock
uv lock --upgrade                 # Upgrade all packages
uv lock --upgrade-package httpx   # Upgrade single package
uv run python main.py             # Run in project environment
uv run pytest                     # Run project command

# Python version management
uv python install 3.12            # Install Python version
uv python pin 3.12                # Pin for this directory
uv python list                    # List available versions
```

## Scripts — Inline Dependencies (PEP 723)

Python scripts can declare their own dependencies via inline metadata, running in isolated
environments independent of any project. See [`references/scripts.md`](references/scripts.md)
for the complete scripts reference.

### Quick Reference

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.27",
#   "rich",
# ]
# ///

import httpx
from rich import print
print(httpx.get("https://example.com").status_code)
```

```bash
# Run script (auto-installs deps in isolated env)
uv run script.py

# Add dependencies to script metadata
uv add --script script.py 'requests<3' 'rich'

# Initialize a script with metadata
uv init --script example.py --python 3.12

# Run with ad-hoc dependencies (no metadata needed)
uv run --with rich --with httpx script.py

# Lock script dependencies for reproducibility
uv lock --script example.py
```

### Key Behaviors

- Scripts with inline metadata run **isolated from the project** — even inside a project dir
- The `dependencies` field is required (use `[]` if empty)
- `uv run --with` for ad-hoc deps; inline metadata for permanent declaration
- `--no-project` flag is NOT needed when script has inline metadata
- Supports `[tool.uv]` section for `exclude-newer`, indexes, etc.

## Python Version Management

```bash
uv python install 3.10 3.11 3.12    # Install multiple versions
uv python list                       # Show installed/available
uv python pin 3.12                   # Create .python-version
uv python find 3.11                  # Locate interpreter
uv run --python 3.11 script.py       # Run with specific version
```

## Common Workflows

| Task | Command |
|------|---------|
| Start new project | `uv init my-project && cd my-project` |
| Add runtime dep | `uv add httpx` |
| Add dev-only dep | `uv add --dev pytest` |
| Add linter (per-project) | `uv add --group lint ruff` |
| Run tests | `uv run pytest` |
| Run linter (system tool) | `uvx ruff check .` or just `ruff check .` |
| Update lockfile | `uv lock --upgrade` |
| Export requirements.txt | `uv export --format requirements.txt` |
| Build package | `uv build` |
| Publish to PyPI | `uv publish` |

## Reference Files

Load these when deeper guidance is needed:

- **[`references/tools.md`](references/tools.md)** — Complete `uv tool` reference: installation,
  environments, version management, plugins, upgrade patterns, Python version selection,
  executables, and the critical distinction from project dependencies.

- **[`references/projects.md`](references/projects.md)** — Full project & dependency management:
  pyproject.toml anatomy, PEP 621/631/508/517/518/735/751/723 compliance, dependency groups,
  sources, optional deps, workspaces, lock/sync/export, build systems, entry points, and
  Python best practices.

- **[`references/scripts.md`](references/scripts.md)** — Inline script metadata (PEP 723),
  shebang patterns, locking scripts, reproducibility, alternative indexes, and GUI scripts.
