# uv Projects & Dependency Management Reference

## Table of Contents

1. [Project Types and Initialization](#project-types-and-initialization)
2. [pyproject.toml Anatomy](#pyprojecttoml-anatomy)
3. [Dependency Management](#dependency-management)
4. [Dependency Sources](#dependency-sources)
5. [Development Dependencies and Groups (PEP 735)](#development-dependencies-and-groups-pep-735)
6. [Optional Dependencies (Extras)](#optional-dependencies-extras)
7. [Lock and Sync Workflows](#lock-and-sync-workflows)
8. [Virtual Environment Management](#virtual-environment-management)
9. [Workspaces](#workspaces)
10. [Build Systems and Packaging](#build-systems-and-packaging)
11. [Entry Points and CLI Commands](#entry-points-and-cli-commands)
12. [PEP Standards Reference](#pep-standards-reference)
13. [Python Best Practices](#python-best-practices)

## Project Types and Initialization

### Application (default)

```bash
uv init my-app
```

Creates: `pyproject.toml`, `main.py`, `README.md`, `.python-version`

No build system — not installable as a package. Suitable for web servers, scripts, CLIs.

```toml
[project]
name = "my-app"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []
```

### Packaged Application

```bash
uv init --package my-cli
```

Creates `src/` layout with `__init__.py`, adds build system and entry point. Suitable for
installable CLIs and apps published to PyPI.

```toml
[project]
name = "my-cli"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[project.scripts]
my-cli = "my_cli:main"

[build-system]
requires = ["uv_build>=0.11.15,<0.12"]
build-backend = "uv_build"
```

### Library

```bash
uv init --lib my-lib
```

Implies `--package`. Creates `src/` layout with `py.typed` marker. For reusable code
distributed to others.

```toml
[project]
name = "my-lib"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["uv_build>=0.11.15,<0.12"]
build-backend = "uv_build"
```

### Minimal (bare)

```bash
uv init --bare my-project
```

Only creates `pyproject.toml`. No README, no source files, no `.python-version`, no git init.

### With Extension Modules

```bash
uv init --build-backend maturin my-rust-ext    # Rust via PyO3
uv init --build-backend scikit-build-core my-c-ext  # C/C++/Fortran
```

## pyproject.toml Anatomy

Complete annotated example following PEP 621:

```toml
[project]
name = "my-project"                    # Required (PEP 621)
version = "0.1.0"                      # Required (PEP 621)
description = "Project description"    # Recommended
readme = "README.md"                   # Recommended
license = "MIT"                        # SPDX identifier (PEP 639)
requires-python = ">=3.11"             # Python version constraint
authors = [
    { name = "Author Name", email = "author@example.com" }
]
keywords = ["example", "project"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
]

# Runtime dependencies (PEP 508 specifiers)
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0,<3",
    "rich",
]

[project.urls]
Homepage = "https://example.com"
Repository = "https://github.com/user/project"
Documentation = "https://docs.example.com"

# CLI entry points (requires build system)
[project.scripts]
my-cli = "my_project:main"

# GUI entry points (Windows-specific behavior)
[project.gui-scripts]
my-gui = "my_project:app"

# Plugin entry points
[project.entry-points.'my_project.plugins']
plugin_a = "my_project_plugin_a"

# Optional dependency groups (extras)
[project.optional-dependencies]
dev = ["pytest>=8", "coverage"]
docs = ["mkdocs", "mkdocs-material"]
viz = ["matplotlib>=3.8"]

# Development dependency groups (PEP 735)
[dependency-groups]
dev = ["pytest>=8", "coverage[toml]"]
lint = ["ruff>=0.5"]
type = ["mypy>=1.10", "pyright"]
test = ["pytest>=8", "pytest-cov", "hypothesis"]

# Build system (PEP 517/518)
[build-system]
requires = ["uv_build>=0.11.15,<0.12"]
build-backend = "uv_build"

# uv-specific configuration
[tool.uv]
default-groups = ["dev", "lint"]       # Groups synced by default
managed = true                          # uv manages this project
package = true                          # Force packaging behavior

# Alternative dependency sources (development only)
[tool.uv.sources]
my-lib = { path = "../my-lib", editable = true }

# Custom package indexes
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

## Dependency Management

### Adding Dependencies

```bash
# Basic (adds to project.dependencies with compatible version bound)
uv add httpx
# Result: dependencies = ["httpx>=0.27.2"]

# With explicit constraint
uv add 'httpx>=0.20'
uv add 'numpy>=1.26,<2'
uv add 'torch==2.2.2'

# With extras
uv add 'transformers[torch]'
uv add 'pandas[excel,plot]'

# Platform-specific (PEP 508 environment markers)
uv add 'pywin32; sys_platform == "win32"'
uv add 'uvloop; sys_platform != "win32"'
uv add 'numpy; python_version >= "3.11"'

# From alternative sources
uv add git+https://github.com/encode/httpx
uv add git+https://github.com/encode/httpx --tag v0.27.0
uv add git+https://github.com/encode/httpx --branch main
uv add git+https://github.com/encode/httpx --rev abc123
uv add ./packages/my-lib
uv add --editable ../my-lib

# From specific index
uv add torch --index pytorch=https://download.pytorch.org/whl/cpu

# Import from requirements.txt
uv add -r requirements.txt

# Control version bound behavior
uv add httpx --bounds lower    # >=x.y.z (default)
uv add httpx --bounds exact    # ==x.y.z
```

### Removing Dependencies

```bash
uv remove httpx
uv remove --dev pytest
uv remove --group lint ruff
uv remove --optional viz matplotlib
```

### Changing/Updating Dependencies

```bash
# Change constraint (updates pyproject.toml)
uv add 'httpx>0.25'

# Upgrade to latest within constraints
uv lock --upgrade-package httpx

# Upgrade all packages
uv lock --upgrade

# Change source
uv add 'httpx @ ../httpx'
```

## Dependency Sources

The `[tool.uv.sources]` table provides alternative sources used during development.
Sources are **only respected by uv** — other tools see only standard `project.dependencies`.

### Source Types

```toml
[tool.uv.sources]
# From specific index
torch = { index = "pytorch" }

# From Git
httpx = { git = "https://github.com/encode/httpx" }
httpx = { git = "https://github.com/encode/httpx", tag = "v0.27.0" }
httpx = { git = "https://github.com/encode/httpx", branch = "main" }
httpx = { git = "https://github.com/encode/httpx", rev = "abc123" }

# From local path
my-lib = { path = "../my-lib" }
my-lib = { path = "../my-lib", editable = true }
my-pkg = { path = "./dist/my_pkg-0.1.0-py3-none-any.whl" }

# From URL
httpx = { url = "https://files.pythonhosted.org/.../httpx-0.27.0.tar.gz" }

# Workspace member
my-lib = { workspace = true }
```

### Platform-Specific Sources

```toml
[tool.uv.sources]
# Different source per platform
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.2", marker = "sys_platform == 'darwin'" }

# Multiple sources with markers
torch = [
    { index = "torch-cpu", marker = "platform_system == 'Darwin'" },
    { index = "torch-gpu", marker = "platform_system == 'Linux'" },
]
```

### Disabling Sources

```bash
# Simulate published metadata resolution (no sources)
uv lock --no-sources
```

## Development Dependencies and Groups (PEP 735)

Development dependencies use the `[dependency-groups]` table (PEP 735). They are local-only
and never published.

### Adding to Groups

```bash
uv add --dev pytest                  # → [dependency-groups] dev
uv add --group lint ruff             # → [dependency-groups] lint
uv add --group test pytest-cov       # → [dependency-groups] test
uv add --group docs mkdocs           # → [dependency-groups] docs
```

### Group Structure

```toml
[dependency-groups]
dev = [
    "pytest>=8",
    "coverage[toml]",
    { include-group = "lint" },      # Nest other groups
    { include-group = "test" },
]
lint = ["ruff>=0.5"]
test = ["pytest>=8", "pytest-cov", "hypothesis"]
docs = ["mkdocs", "mkdocs-material"]
```

### Default Groups

```toml
[tool.uv]
default-groups = ["dev", "lint"]   # Synced by default on `uv sync` / `uv run`
# Or enable all:
# default-groups = "all"
```

### Syncing Groups

```bash
uv sync                              # Syncs default groups
uv sync --group docs                 # Include additional group
uv sync --all-groups                 # Include all groups
uv sync --no-dev                     # Exclude dev group
uv sync --no-group lint              # Exclude specific group
uv sync --only-dev                   # Only dev deps (no project)
uv sync --no-default-groups          # Skip all defaults
```

### Group-Specific Python Requirements

```toml
[tool.uv.dependency-groups]
dev = { requires-python = ">=3.12" }   # Narrower than project's requires-python
```

## Optional Dependencies (Extras)

For published libraries — allow consumers to opt into additional features.

```toml
[project.optional-dependencies]
excel = ["openpyxl>=3.1", "xlrd>=2.0"]
plot = ["matplotlib>=3.8"]
all = ["openpyxl>=3.1", "xlrd>=2.0", "matplotlib>=3.8"]
```

```bash
# Add optional dependency
uv add --optional excel openpyxl

# Sync with extras
uv sync --extra excel
uv sync --all-extras

# Consumers install with:
# pip install my-lib[excel,plot]
```

## Lock and Sync Workflows

### Lockfile (`uv.lock`)

- Universal/cross-platform (resolves for all OS, arch, Python versions)
- Human-readable TOML (uv-specific format, not for other tools)
- Commit to version control for reproducibility
- **Not** the same as PEP 751 `pylock.toml` (but can export to it)

### Commands

```bash
# Create/update lockfile
uv lock

# Check if lockfile is up-to-date (CI use)
uv lock --check

# Upgrade within constraints
uv lock --upgrade
uv lock --upgrade-package httpx
uv lock --upgrade-package 'httpx==0.28.0'

# Sync environment from lockfile
uv sync                           # Exact sync (removes extraneous)
uv sync --inexact                 # Keep extraneous packages
uv sync --frozen                  # Don't check lockfile freshness
uv sync --no-install-project      # Deps only (Docker layer caching)

# Run with auto-sync
uv run pytest                     # Auto-locks and syncs first
uv run --locked pytest            # Fail if lockfile outdated
uv run --frozen pytest            # Skip lockfile check
uv run --no-sync pytest           # Skip environment sync

# Export
uv export --format requirements.txt
uv export --format requirements.txt --no-dev
uv export --format pylock.toml    # PEP 751
uv export --format cyclonedx1.5   # SBOM
```

### Automatic Lock and Sync

`uv run` and `uv sync` automatically lock and sync. Use `--locked` in CI to fail if
lockfile is outdated rather than updating it silently.

## Virtual Environment Management

### Project Environment

- Location: `.venv/` next to `pyproject.toml`
- Created automatically on first `uv sync` or `uv run`
- Not for manual modification (use `uv add`, not `uv pip install`)
- Excluded from version control (auto-`.gitignore`)

```bash
# Explicit creation
uv venv                            # Create .venv with default Python
uv venv --python 3.12              # With specific Python
uv venv .venv-test --python 3.11   # Custom path and version

# Activation (optional — uv run handles this)
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate

# Custom environment path
UV_PROJECT_ENVIRONMENT=.custom-venv uv sync
```

### Disable Auto-Management

```toml
[tool.uv]
managed = false   # uv won't auto-lock/sync
```

## Workspaces

For monorepos with multiple interconnected packages sharing a single lockfile.

```toml
# Root pyproject.toml
[project]
name = "my-app"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["my-lib"]

[tool.uv.sources]
my-lib = { workspace = true }

[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/experimental"]
```

```bash
# Run command in specific workspace member
uv run --package my-lib pytest

# Init new member inside workspace
cd packages && uv init new-package
```

**Key behaviors:**
- Single `uv.lock` for entire workspace
- Workspace members are always editable
- Root `tool.uv.sources` apply to all members (overridable per-member)
- Single `requires-python` (intersection of all members)

**When NOT to use workspaces:**
- Members have conflicting requirements
- Members need separate virtual environments
- Use path dependencies instead for these cases

## Build Systems and Packaging

### Supported Build Backends

| Backend | Use Case | Init Command |
|---------|----------|--------------|
| `uv_build` | Default, pure Python | `uv init --package` |
| `hatchling` | Feature-rich, plugins | `uv init --build-backend hatchling` |
| `flit-core` | Minimal, simple | `uv init --build-backend flit-core` |
| `pdm-backend` | PDM ecosystem | `uv init --build-backend pdm-backend` |
| `setuptools` | Legacy/complex needs | `uv init --build-backend setuptools` |
| `maturin` | Rust extensions | `uv init --build-backend maturin` |
| `scikit-build-core` | C/C++/Fortran | `uv init --build-backend scikit-build-core` |

### Building and Publishing

```bash
# Build wheel and sdist
uv build

# Build without sources (validate publishable state)
uv build --no-sources

# Publish to PyPI
uv publish

# Publish to custom index
uv publish --index https://upload.pypi.org/legacy/
```

### Packaging Decision

```toml
# Force packaging (even without build system)
[tool.uv]
package = true

# Force no packaging (even with build system)
[tool.uv]
package = false
```

## Entry Points and CLI Commands

Requires a build system to be defined.

### Command-Line Interface

```toml
[project.scripts]
my-cli = "my_project.cli:main"          # module:function
my-tool = "my_project:cli_entry"
```

```bash
uv run my-cli --help
```

### GUI Scripts (Windows)

```toml
[project.gui-scripts]
my-app = "my_project.gui:start"
```

### Plugin Entry Points

```toml
[project.entry-points.'my_framework.plugins']
my_plugin = "my_plugin_package"
```

## PEP Standards Reference

| PEP | Standard | uv Support |
|-----|----------|-----------|
| PEP 440 | Version specifiers | Full (`>=1.0`, `~=1.4`, `==1.*`) |
| PEP 508 | Dependency specifiers & markers | Full (environment markers) |
| PEP 517 | Build system interface | Full (isolated builds) |
| PEP 518 | Build system requirements (`[build-system]`) | Full |
| PEP 621 | Project metadata in `pyproject.toml` | Full |
| PEP 631 | Dependency specification format | Full |
| PEP 639 | License expression (SPDX) | Full |
| PEP 660 | Editable installs | Full |
| PEP 685 | Normalized dependency names | Full |
| PEP 723 | Inline script metadata | Full (scripts) |
| PEP 735 | Dependency groups | Full (`[dependency-groups]`) |
| PEP 751 | Lock file format (`pylock.toml`) | Export support |

### PEP 508 Environment Markers (commonly used)

```python
sys_platform == 'win32'           # Windows
sys_platform == 'linux'           # Linux
sys_platform == 'darwin'          # macOS
platform_system == 'Windows'      # Alternative
python_version >= '3.11'          # Python version
implementation_name == 'cpython'  # CPython vs PyPy
platform_machine == 'x86_64'     # Architecture
```

### PEP 440 Version Specifiers

```
>=1.0           # Minimum version
>=1.0,<2        # Range
~=1.4           # Compatible release (>=1.4, <2.0)
~=1.4.2         # Compatible release (>=1.4.2, <1.5.0)
==1.0           # Exact
==1.*           # Prefix match
!=1.5           # Exclusion
```

## Python Best Practices

### Project Layout

**Application (flat):**
```
my-app/
├── pyproject.toml
├── main.py
├── utils.py
└── .venv/
```

**Library/Package (src layout — preferred for libraries):**
```
my-lib/
├── pyproject.toml
├── src/
│   └── my_lib/
│       ├── __init__.py
│       ├── core.py
│       └── py.typed
├── tests/
│   ├── __init__.py
│   └── test_core.py
└── .venv/
```

### Dependency Specification Best Practices

1. **Use lower bounds** for libraries: `httpx>=0.27` (consumers need flexibility)
2. **Use ranges** for applications: `httpx>=0.27,<1` (pin for stability)
3. **Avoid exact pins** in libraries: `==0.27.2` prevents consumer upgrades
4. **Use compatible release** for semver: `~=1.4` means `>=1.4, <2.0`
5. **Group related deps** in optional-dependencies for consumer choice
6. **Use dependency groups** for dev tooling, not `project.dependencies`
7. **Declare `requires-python`** always — drives dependency resolution

### Recommended Dependency Group Structure

```toml
[dependency-groups]
dev = [
    { include-group = "test" },
    { include-group = "lint" },
    { include-group = "type" },
]
test = ["pytest>=8", "pytest-cov", "hypothesis"]
lint = ["ruff>=0.5"]
type = ["mypy>=1.10"]
docs = ["mkdocs", "mkdocs-material"]

[tool.uv]
default-groups = ["dev"]
```

### Version Control

**Always commit:**
- `pyproject.toml`
- `uv.lock`
- `.python-version`

**Never commit:**
- `.venv/`
- `__pycache__/`
- `*.egg-info/`
- `dist/`
