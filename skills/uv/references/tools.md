# uv Tools Reference

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Tool Execution (uvx)](#tool-execution-uvx)
3. [Tool Installation](#tool-installation)
4. [Tool Environments](#tool-environments)
5. [Version Management](#version-management)
6. [Plugins and Extra Dependencies](#plugins-and-extra-dependencies)
7. [Python Version Selection](#python-version-selection)
8. [Tool Executables and PATH](#tool-executables-and-path)
9. [System Tool Configuration](#system-tool-configuration)
10. [Tools vs. Project Dependencies Decision Guide](#tools-vs-project-dependencies-decision-guide)

## Core Concepts

Tools are Python packages that provide command-line interfaces. uv manages tools in **isolated
virtual environments** completely separate from any project environment.

**Critical principle:** A tool installed via `uv tool install` or run via `uvx` does NOT belong
in a project's `pyproject.toml` unless explicitly requested. The tool's dependencies exist only
in its own isolated environment.

Two modes of operation:
- **Execution** (`uvx` / `uv tool run`): Run in a temporary cached environment
- **Installation** (`uv tool install`): Persistent environment with PATH-accessible executables

## Tool Execution (uvx)

`uvx` is an alias for `uv tool run`. It runs a tool without permanent installation.

```bash
# Basic execution
uvx ruff check .
uvx black --diff src/

# When package name differs from command name
uvx --from httpie http GET https://example.com
uvx --from 'mypy[faster-cache,reports]' mypy --xml-report report/

# Specific version
uvx ruff@0.5.0 check .
uvx ruff@latest check .
uvx --from 'ruff==0.5.0' ruff check .
uvx --from 'ruff>0.2.0,<0.3.0' ruff check .

# From alternative sources
uvx --from git+https://github.com/httpie/cli httpie
uvx --from git+https://github.com/httpie/cli@main httpie
uvx --from git+https://github.com/httpie/cli@v3.2.1 httpie

# With additional dependencies (plugins)
uvx --with mkdocs-material mkdocs serve
uvx --with 'click>=8' mycli run
```

**Caching behavior:**
- First invocation downloads and caches the tool
- Subsequent invocations use the cached version
- Use `@latest` suffix to force cache refresh: `uvx ruff@latest`
- Cache is in the uv cache directory; `uv cache clean` removes it
- If tool is installed via `uv tool install`, `uvx` uses the installed version

**Relationship to `uv run`:**
`uvx <name>` is nearly equivalent to `uv run --no-project --with <name> -- <name>`, except:
- `--with` is not needed (package inferred from command)
- Environment is cached in a dedicated location
- `--no-project` is implicit (tools always isolated)
- If tool is installed, `uvx` uses installed version; `uv run` does not

**When to use `uv run` instead:** If the tool needs access to project code (e.g., `pytest`,
`mypy` checking your source), use `uv run` not `uvx`.

## Tool Installation

`uv tool install` creates a persistent isolated environment and symlinks executables to PATH.

```bash
# Basic installation
uv tool install ruff
uv tool install 'black>=24,<25'
uv tool install httpie

# From alternative sources
uv tool install git+https://github.com/httpie/cli
uv tool install git+https://github.com/astral-sh/ruff@v0.5.0

# With plugins/extras
uv tool install mkdocs --with mkdocs-material --with mkdocs-awesome-pages-plugin
uv tool install ansible --with-executables-from ansible-core,ansible-lint

# List installed tools
uv tool list

# Uninstall
uv tool uninstall ruff

# Update PATH configuration
uv tool update-shell
```

**Key behaviors:**
- Installs ALL executables provided by the package
- Executables symlinked (Unix) or copied (Windows) to the tool bin directory
- Will NOT overwrite executables from other installers (pipx, etc.) unless `--force`
- Dependencies of tool packages do NOT have their executables installed
- Module imports from tool packages are NOT available: `python -c "import ruff"` fails

## Tool Environments

Each installed tool gets its own isolated virtual environment:

- **Location**: uv tools directory (platform-specific)
  - Linux/macOS: `~/.local/share/uv/tools/`
  - Windows: `%APPDATA%\uv\data\tools\`
- **Isolation**: Complete — no sharing between tools or with projects
- **Mutability**: Never modify manually (no `pip install` into tool envs)
- **Lifecycle**: Persists until `uv tool uninstall`; deleting manually breaks the tool

For `uvx` (ephemeral execution):
- Environment stored in uv cache directory
- Treated as disposable; `uv cache clean` removes it
- Automatically recreated on next invocation if missing

## Version Management

### Upgrading

```bash
# Upgrade single tool (respects original version constraints)
uv tool upgrade ruff

# Upgrade all tools
uv tool upgrade --all

# Upgrade specific dependency within tool environment
uv tool upgrade black --upgrade-package click

# Reinstall packages during upgrade
uv tool upgrade black --reinstall
uv tool upgrade black --reinstall-package click
```

Upgrades respect constraints from installation. `uv tool install 'ruff>=0.3,<0.4'` followed
by `uv tool upgrade ruff` stays within `>=0.3,<0.4`.

To change constraints, reinstall:
```bash
uv tool install 'ruff>=0.5'
```

### Version pinning patterns

```bash
# Exact version
uv tool install 'ruff==0.5.4'

# Range
uv tool install 'black>=24,<25'

# Minimum
uv tool install 'mypy>=1.10'
```

## Plugins and Extra Dependencies

### With `uvx` (ephemeral)

```bash
uvx --with mkdocs-material mkdocs serve
uvx --with 'pygments>=2.16' --with rich mycli
```

### With `uv tool install` (persistent)

```bash
# --with: include as dependency but don't install its executables
uv tool install mkdocs --with mkdocs-material --with mkdocs-awesome-pages-plugin

# --with-executables-from: include AND install executables from additional packages
uv tool install ansible --with-executables-from ansible-core,ansible-lint
```

**Difference:**
- `--with`: Adds packages as dependencies only
- `--with-executables-from`: Adds packages AND installs their executables

## Python Version Selection

Each tool environment links to a specific Python version.

```bash
# Run with specific Python
uvx --python 3.10 ruff check .

# Install with specific Python
uv tool install --python 3.12 mypy

# Upgrade with specific Python
uv tool upgrade --python 3.12 ruff
```

Tool environments ignore `.python-version` files and `requires-python` from `pyproject.toml`.
Only global Python discovery is used.

**Warning:** If the Python version used by a tool is uninstalled, the tool environment breaks.

## Tool Executables and PATH

Executables include all console entry points, script entry points, and binary scripts from the
tool package.

**Executable directory:**
- Linux/macOS: `~/.local/bin/`
- Windows: `%APPDATA%\uv\data\bin\` or `%USERPROFILE%\.local\bin\`

This directory must be in PATH. If not, uv warns on install. Fix with:
```bash
uv tool update-shell
```

**Overwrite behavior:**
- Will NOT overwrite executables not previously installed by uv
- Use `--force` to override: `uv tool install --force ruff`

## System Tool Configuration

Recommended system tools to install globally (not as project dependencies):

```bash
# Linting and formatting
uv tool install ruff
uv tool install black

# Type checking
uv tool install mypy
uv tool install pyright

# Code quality
uv tool install bandit
uv tool install vulture

# Documentation
uv tool install mkdocs --with mkdocs-material
uv tool install sphinx

# Build and publish
uv tool install build
uv tool install twine

# Utilities
uv tool install httpie
uv tool install pipx
uv tool install cookiecutter
uv tool install pre-commit
```

**After installing system tools:**
- They are available directly in any terminal: `ruff check .`, `black .`, `mypy src/`
- They do NOT need `uvx` prefix (though `uvx` still works)
- They do NOT appear in any project's `pyproject.toml`
- Per-project pinning (if needed) uses dependency groups, not `project.dependencies`

## Tools vs. Project Dependencies Decision Guide

| Scenario | Approach |
|----------|----------|
| Linter/formatter used across all projects | `uv tool install ruff` |
| Linter pinned to specific version for CI | `uv add --group lint 'ruff==0.5.4'` |
| Test framework for this project | `uv add --dev pytest` |
| CLI utility for personal use | `uv tool install httpie` |
| Library your code imports | `uv add httpx` |
| Build tool for documentation | `uv tool install mkdocs --with mkdocs-material` |
| Project-specific docs build | `uv add --group docs mkdocs mkdocs-material` |

**Decision rule:**
1. Does your Python code `import` this package? → Project dependency (`uv add`)
2. Is it a CLI tool used for development? → System tool (`uv tool install`)
3. Must it be version-pinned per-project for CI? → Dev group (`uv add --group <name>`)
4. Never add a tool to `project.dependencies` unless your runtime code imports it
