---
name: nushell
description: >
  Nushell (nu) shell language skill for executing commands, scripts, and automation using
  nushell instead of bash. Use this skill whenever the user prefers nushell, asks to run nu
  commands, wants to write .nu scripts, needs to work with structured data in the shell, or
  when the environment is configured to use nushell as the primary shell. Covers: invoking nu
  through the Bash tool, Nu language syntax, pipelines, structured data, error handling,
  file I/O, process execution, and translating bash idioms to nu equivalents.
---

# Nushell Skill

Nushell (nu) is the user's preferred shell. **Always use nu for command invocations instead of
bash** unless a task explicitly requires bash-only behavior.

Nu treats all data as structured (tables, records, lists) rather than raw text. It is
installed at `/usr/bin/nu` (version 0.104.1 confirmed in this environment).

## Core Invocation Rule

The Bash tool always spawns bash — but can invoke nu. Use this pattern for all nu invocations:

```bash
nu << 'EOF'
# Nu script here — bash won't interpolate $ because of single-quoted EOF
let files = ls | where type == file
print $"Found ($files | length) files"
EOF
```

**Rules:**
- Always use `nu << 'EOF' ... EOF` (single-quoted heredoc) so bash doesn't expand `$` variables
- For one-liners with no variables: `nu -c "ls | first 5"` is acceptable
- For complex or reusable scripts: write to `/tmp/script.nu` then `nu /tmp/script.nu`
- To pass bash shell variables into nu, prefix the command: `MY_VAR="val" nu << 'EOF' ... $env.MY_VAR ... EOF`

### The `nu_run.py` Helper

For scripts that need timeout control, env injection, or structured error reporting, use:

```bash
uv run skills/nushell/scripts/nu_run.py 'ls | get name | first 5'
uv run skills/nushell/scripts/nu_run.py /tmp/task.nu --file
uv run skills/nushell/scripts/nu_run.py 'print $env.X' --env X=hello --timeout 30
```

Returns exit code 0 on success, non-zero on failure. Prints `--- nu_run: SUCCESS/FAILED ---` to stderr.

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
| Bash interpolates `$` in heredoc | Use `'EOF'` (single-quoted) not `EOF` |
| Command not found in nu | Use `^cmd` to call external commands explicitly |
| `$x` inside closure mutability error | Use `mut` and `loop`/`for` instead of `each` |
| Exit code of external cmd | Use `\| complete` to capture `.exit_code`, `.stdout`, `.stderr` |
| Passing bash var to nu | Pass via env: `VAR=val nu << 'EOF'` then `$env.VAR` |
| Nu script has no output | Last expression is auto-returned; use `print` to explicitly output |

- **[`references/api_reference.md`](references/api_reference.md)** — Deep reference from The
  Nushell Book: all 16 data types with annotations and examples, every special variable (`$nu`,
  `$env`, `$in`), custom command signatures (params, flags, rest, `--wrapped`, `--env`,
  attributes), `error make` / `try` / `complete`, stdout/stderr/exit-code redirections, and
  the full module system (`export`, `export-env`, submodules, `main`). Load when authoring
  complex commands, modules, or when precise type/API details are needed.
