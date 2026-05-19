# uv Scripts Reference

## Table of Contents

1. [Overview](#overview)
2. [Running Scripts Without Dependencies](#running-scripts-without-dependencies)
3. [Inline Script Metadata (PEP 723)](#inline-script-metadata-pep-723)
4. [Managing Script Dependencies](#managing-script-dependencies)
5. [Ad-Hoc Dependencies](#ad-hoc-dependencies)
6. [Locking Script Dependencies](#locking-script-dependencies)
7. [Reproducibility](#reproducibility)
8. [Shebang Patterns](#shebang-patterns)
9. [Alternative Indexes](#alternative-indexes)
10. [Python Version Selection](#python-version-selection)
11. [GUI Scripts (Windows)](#gui-scripts-windows)
12. [Project Interaction](#project-interaction)

## Overview

uv manages single-file Python scripts with automatic dependency resolution and isolated
environments. Scripts can declare dependencies inline (PEP 723), request specific Python
versions, and run reproducibly across environments.

## Running Scripts Without Dependencies

```bash
# Simple script
uv run script.py

# With arguments
uv run script.py --flag value arg1 arg2

# From stdin
echo 'print("hello")' | uv run -

# Here-document
uv run - <<EOF
import sys
print(sys.version)
EOF
```

## Inline Script Metadata (PEP 723)

The standard format for declaring dependencies within a script file itself. Uses a special
comment block at the top of the file.

### Full Syntax

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.27",
#   "rich>=13",
#   "pydantic>=2.0,<3",
# ]
#
# [tool.uv]
# exclude-newer = "2024-10-01T00:00:00Z"
#
# [[tool.uv.index]]
# url = "https://example.com/simple"
# ///

import httpx
from rich import print
from pydantic import BaseModel

class Response(BaseModel):
    status: int
    body: str

resp = httpx.get("https://example.com")
print(Response(status=resp.status_code, body=resp.text[:100]))
```

### Minimal Example

```python
# /// script
# dependencies = ["requests"]
# ///

import requests
print(requests.get("https://httpbin.org/ip").json())
```

### Empty Dependencies (Python version only)

```python
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# Use Python 3.12+ syntax like type aliases
type Point = tuple[float, float]
print(Point)
```

**Important:** The `dependencies` field MUST be present, even if empty.

### Metadata Fields

| Field | Required | Description |
|-------|----------|-------------|
| `dependencies` | Yes | List of PEP 508 dependency specifiers |
| `requires-python` | No | Python version constraint |
| `[tool.uv]` | No | uv-specific configuration section |
| `[tool.uv].exclude-newer` | No | RFC 3339 timestamp for reproducibility |
| `[[tool.uv.index]]` | No | Additional package indexes |

## Managing Script Dependencies

### Adding Dependencies to a Script

```bash
# Add single dependency
uv add --script script.py requests

# Add multiple with constraints
uv add --script script.py 'requests<3' 'rich>=13'

# Add from specific index
uv add --index "https://example.com/simple" --script script.py 'my-package'
```

This modifies the inline metadata block in the script file.

### Initializing a New Script

```bash
# Create script with metadata template
uv init --script example.py --python 3.12
```

Generates:
```python
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
```

### Removing Dependencies

Edit the inline metadata block directly — there is no `uv remove --script` command.

## Ad-Hoc Dependencies

Run scripts with dependencies specified on the command line (no inline metadata needed).

```bash
# Single dependency
uv run --with rich script.py

# Multiple dependencies
uv run --with rich --with httpx script.py

# Version constraints
uv run --with 'rich>=13' --with 'httpx<1' script.py

# Without project context (if inside a project directory)
uv run --no-project --with rich script.py
```

**Use cases:**
- Quick one-off scripts without permanent metadata
- Testing with different dependency versions
- Scripts that don't warrant inline metadata

## Locking Script Dependencies

Scripts can have their dependencies locked for reproducible execution.

```bash
# Create lockfile (script.py.lock)
uv lock --script script.py

# Export locked dependencies
uv export --script script.py --format requirements.txt

# View dependency tree
uv tree --script script.py
```

The lockfile is created adjacent to the script (e.g., `example.py.lock`). Once locked,
subsequent `uv run`, `uv add --script`, and `uv export --script` reuse and update the lockfile.

## Reproducibility

### exclude-newer

Limit package resolution to versions released before a specific date:

```python
# /// script
# dependencies = ["requests", "rich"]
#
# [tool.uv]
# exclude-newer = "2024-10-16T00:00:00Z"
# ///

import requests
print(requests.__version__)  # Will always resolve same versions
```

### Combining with Lockfile

For maximum reproducibility:
1. Declare `exclude-newer` in metadata
2. Lock the script: `uv lock --script script.py`
3. Commit both script and `.lock` file

## Shebang Patterns

Make scripts directly executable on Unix systems.

### Basic Shebang

```python
#!/usr/bin/env -S uv run --script

print("Hello, world!")
```

```bash
chmod +x greet
./greet
```

### With Dependencies

```python
#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///

import httpx
print(httpx.get("https://example.com").status_code)
```

### Notes

- The shebang `#!/usr/bin/env -S uv run --script` invokes uv to manage the script
- The `-S` flag enables argument splitting in `env`
- Script must have execute permission (`chmod +x`)
- Works for scripts placed in PATH directories

## Alternative Indexes

Specify custom package indexes within script metadata:

```python
# /// script
# dependencies = ["my-internal-package"]
#
# [[tool.uv.index]]
# url = "https://internal.example.com/simple"
# ///

import my_internal_package
```

Or via command line:
```bash
uv add --index "https://example.com/simple" --script script.py 'my-package'
```

## Python Version Selection

### In Metadata

```python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
```

uv automatically finds or downloads the required Python version.

### Per Invocation

```bash
uv run --python 3.10 script.py
uv run --python 3.12 script.py
```

Overrides the script's `requires-python` for that invocation.

## GUI Scripts (Windows)

Scripts with `.pyw` extension run with `pythonw` (no console window):

```python
# example.pyw
from tkinter import Tk, ttk

root = Tk()
root.title("My App")
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text="Hello World").grid(column=0, row=0)
root.mainloop()
```

```powershell
uv run example.pyw
uv run --with PyQt5 gui_app.pyw
```

## Project Interaction

### Inside a Project Directory

| Script Type | Behavior |
|-------------|----------|
| Script with inline metadata | Runs **isolated** from project (no `--no-project` needed) |
| Script without metadata | Runs **within** project environment |
| `uv run --no-project script.py` | Force isolation from project |
| `uv run --with pkg script.py` | Adds pkg to project env for this run |

### Key Rules

1. **Inline metadata = automatic isolation** — the script gets its own environment regardless
   of whether you're in a project directory
2. **No metadata + inside project** — script runs in the project's `.venv` with all project deps
3. **`--no-project` + `--with`** — explicit isolation without inline metadata
4. **`--with` inside project (no metadata)** — deps added *on top of* project deps
