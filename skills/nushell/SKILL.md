---
name: nushell
description: >
  Nushell (nu) shell language skill for executing commands, scripts, and automation using
  nushell instead of bash/PowerShell. Use this skill whenever the user prefers nushell, asks
  to run nu commands, wants to write .nu scripts, needs to work with structured data in the
  shell, or when the environment is configured to use nushell as the primary shell. On
  Windows, copilot-cli hardcodes PowerShell as the shell tool — invoke nu via the PowerShell
  tool using `nu -c '...'`. Covers: Nu language syntax, pipelines, structured data, error
  handling, file I/O, process execution, and translating PowerShell/bash idioms to nu.
---

# Nushell Skill

Nushell (nu) is the user's preferred shell. **Always use nu for command invocations** unless
a task explicitly requires native PowerShell or bash behavior.

Nu treats all data as structured (tables, records, lists) rather than raw text.

## Core Invocation Rule

On Windows, the copilot-cli **PowerShell tool** is the execution layer. Invoke nu through it:

### One-liners (preferred for simple commands)
```powershell
nu -c 'ls | where type == file | first 5'
```

### With string interpolation (use single quotes to prevent PS expansion)
```powershell
nu -c 'let x = 42; print $"Value: ($x)"'
```

### Multi-line scripts (use temp file)
```powershell
@'
let files = ls | where type == file
let count = $files | length
print $"Found ($count) files"
'@ | Set-Content -Path $env:TEMP\__nu_script.nu -Encoding UTF8
nu $env:TEMP\__nu_script.nu
Remove-Item $env:TEMP\__nu_script.nu -ErrorAction SilentlyContinue
```

## Linux/macOS (bash tool context)

When running on Linux/macOS, the bash tool is the execution layer:

```bash
nu -c 'ls | where type == file | first 5'
# Or for multi-line with heredoc:
nu << 'EOF'
let files = ls | where type == file
print $"Found ($files | length) files"
EOF
```

## Quoting and Escaping
**Rules:**
- **Always use single quotes** around nu code in PowerShell to prevent `$` interpolation
- If the nu code itself contains single quotes, double them: `nu -c 'print ''hello'''`
- For complex scripts with mixed quoting, use the temp file pattern above
- Backtick (`` ` ``) is PowerShell's escape character — avoid it inside nu code

### The `nu_run.py` Helper

For scripts that need timeout control, env injection, or structured error reporting:

```powershell
uv run skills/nushell/scripts/nu_run.py 'ls | get name | first 5'
uv run skills/nushell/scripts/nu_run.py $env:TEMP\task.nu --file
uv run skills/nushell/scripts/nu_run.py 'print $env.X' --env X=hello --timeout 30
```

Returns exit code 0 on success, non-zero on failure. Prints `--- nu_run: SUCCESS/FAILED ---` to stderr.

### The `nu_invoke.py` Module

Python helper for generating PowerShell-safe nu invocations programmatically:

```python
from nu_invoke import execute, format_for_powershell

# Execute directly
result = execute("ls | where type == file")
print(result.stdout)

# Generate PowerShell command string
ps_cmd = format_for_powershell('let x = 42; print $"Value: ($x)"')
# Returns: nu -c 'let x = 42; print $"Value: ($x)"'
```

## Quick Reference

### Variables and types
```nu
let x = 42           # immutable int
mut count = 0        # mutable
let name = "alice"   # string
let data = {key: "value", num: 42}  # record
let list = [1 2 3]   # list
```

### String interpolation
```nu
print $"Hello, ($name)! Count is ($count)"
```

### Pipelines and structured data
```nu
ls | where type == file | sort-by size -r | first 5
open data.json | get users | where active | select name email
```

### Error handling
```nu
try {
    open config.json
} catch {|e|
    print $"Failed: ($e.msg)"
}

# External command with exit code
let r = do { ^git pull } | complete
if $r.exit_code != 0 { error make {msg: $r.stderr} }
```

### External commands
```nu
^git status           # ^ prefix = always external command
^npm install
let out = ^git log --oneline | lines
```

## Reference Files

Load these when you need deeper guidance:

- **[`references/language-guide.md`](references/language-guide.md)** — Full language reference:
  types, variables, operators, control flow, custom commands, pipelines, file I/O, env vars,
  external commands. Load when writing non-trivial scripts or translating from bash.

- **[`references/patterns.md`](references/patterns.md)** — Practical patterns: error handling
  recipes, bash-to-Nu translation table, data transformation, JSON/TOML/YAML, parallel
  execution, retry logic, debugging techniques. Load when handling errors or complex workflows.

## Common Pitfalls

| Problem | Solution |
|---------|----------|
| PowerShell expands `$` in double-quoted strings | Use single quotes: `nu -c '...$var...'` |
| Command not found in nu | Use `^cmd` to call external commands explicitly |
| `$x` inside closure mutability error | Use `mut` and `loop`/`for` instead of `each` |
| Exit code of external cmd | Use `\| complete` to capture `.exit_code`, `.stdout`, `.stderr` |
| Passing env vars from PS to nu | Set `$env:VAR = "val"` then in nu use `$env.VAR` |
| Nu script has no output | Last expression is auto-returned; use `print` to explicitly output |
| Single quote inside nu code | Double it: `nu -c 'print ''hello'''` |
| Long/complex script | Use temp file pattern (see Core Invocation Rule above) |

- **[`references/api_reference.md`](references/api_reference.md)** — Deep reference from The
  Nushell Book: all 16 data types with annotations and examples, every special variable (`$nu`,
  `$env`, `$in`), custom command signatures (params, flags, rest, `--wrapped`, `--env`,
  attributes), `error make` / `try` / `complete`, stdout/stderr/exit-code redirections, and
  the full module system (`export`, `export-env`, submodules, `main`). Load when authoring
  complex commands, modules, or when precise type/API details are needed.
