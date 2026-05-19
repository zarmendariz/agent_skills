# ast-grep CLI Reference

## Table of Contents

1. [Commands Overview](#commands-overview)
2. [run — Search and Rewrite](#run)
3. [scan — Rule-based Analysis](#scan)
4. [test — Rule Testing](#test)
5. [new — Project Scaffolding](#new)
6. [lsp — Language Server](#lsp)
7. [Output Formats](#output-formats)
8. [Common Options](#common-options)

---

## Commands Overview

```
ast-grep <COMMAND> [OPTIONS]

Commands:
  run          Search/rewrite with inline pattern (default command)
  scan         Scan with YAML rules
  test         Test ast-grep rules
  new          Create new project/rule/test/util
  lsp          Start language server
  completions  Generate shell completion script
```

Global option: `-c, --config <CONFIG_FILE>` — path to sgconfig.yml (default: auto-detect)

---

## run

One-time structural search or rewrite from command line.

```
ast-grep run [OPTIONS] --pattern <PATTERN> [PATHS]...
```

### Required

| Flag | Description |
|------|-------------|
| `-p, --pattern <PATTERN>` | AST pattern to match |

### Key Options

| Flag | Description |
|------|-------------|
| `-r, --rewrite <FIX>` | Replacement template for matched nodes |
| `-l, --lang <LANG>` | Language of the pattern |
| `--selector <KIND>` | Sub-node kind to actually match within pattern |
| `--strictness <LEVEL>` | Match strictness: cst, smart, ast, relaxed, signature |
| `-i, --interactive` | Interactive accept/reject each match |
| `-U, --update-all` | Apply all rewrites without confirmation |
| `--json[=STYLE]` | JSON output: pretty (default), stream, compact |
| `--debug-query[=FORMAT]` | Show pattern AST: pattern, ast, cst, sexp |

### Display Options

| Flag | Description |
|------|-------------|
| `-A, --after <NUM>` | Lines of context after match |
| `-B, --before <NUM>` | Lines of context before match |
| `-C, --context <NUM>` | Lines before and after match |
| `--color <WHEN>` | Color output: auto, always, ansi, never |
| `--heading <WHEN>` | File name heading: auto, always, never |
| `--files-with-matches` | Print only file paths (no match content) |

### File Selection

| Flag | Description |
|------|-------------|
| `--globs <GLOBS>` | Include/exclude paths (gitignore-style) |
| `--no-ignore <TYPE>` | Skip ignore files: hidden, dot, vcs, parent, global, exclude |
| `--follow` | Follow symbolic links |
| `--stdin` | Read code from stdin |
| `-j, --threads <NUM>` | Thread count (0 = auto) |

### Examples

```bash
# Simple search
ast-grep run -p 'eval($X)' -l javascript

# Search with context
ast-grep run -p 'TODO' -l javascript -C 3

# Rewrite with auto-apply
ast-grep run -p 'var $X = $Y' --rewrite 'const $X = $Y' -l javascript -U

# JSON output for scripting
ast-grep run -p 'fetch($URL)' -l typescript --json=stream

# Debug pattern parsing
ast-grep run -p 'async function $F() {}' -l javascript --debug-query=cst

# Search in specific paths
ast-grep run -p 'import $$$' -l python src/ lib/

# Only show file paths
ast-grep run -p 'console.log($$$)' -l javascript --files-with-matches
```

---

## scan

Scan codebase using YAML rule files. Supports single rule or project-wide scanning.

```
ast-grep scan [OPTIONS] [PATHS]...
```

### Key Options

| Flag | Description |
|------|-------------|
| `-r, --rule <RULE_FILE>` | Single rule file to scan with |
| `--inline-rules <RULE_TEXT>` | Rule defined as inline YAML text |
| `--filter <REGEX>` | Filter rules by ID regex (project scan) |
| `--format <FORMAT>` | Output: github, sarif |
| `--report-style <STYLE>` | Diagnostic display: rich, medium, short |
| `-i, --interactive` | Interactive rewrite session |
| `-U, --update-all` | Apply all fixes without confirmation |
| `--json[=STYLE]` | JSON output: pretty, stream, compact |
| `--include-metadata` | Include rule metadata in JSON |
| `--max-results <NUM>` | Stop after N matches |

### Severity Override

| Flag | Description |
|------|-------------|
| `--error[=RULE_ID...]` | Set rule(s) to error severity |
| `--warning[=RULE_ID...]` | Set rule(s) to warning severity |
| `--info[=RULE_ID...]` | Set rule(s) to info severity |
| `--hint[=RULE_ID...]` | Set rule(s) to hint severity |
| `--off[=RULE_ID...]` | Disable rule(s) |

### Examples

```bash
# Scan with single rule
ast-grep scan --rule rules/no-eval.yml

# Scan entire project (uses sgconfig.yml)
ast-grep scan

# Only run security rules
ast-grep scan --filter "security-.*"

# GitHub Actions format
ast-grep scan --format github

# SARIF for security tools
ast-grep scan --format sarif > results.sarif

# Override severity
ast-grep scan --error=no-eval --warning=no-console

# Interactive fix
ast-grep scan --rule migration.yml -i

# Limit results for large codebases
ast-grep scan --max-results 100
```

---

## test

Test ast-grep rules against expected valid/invalid cases.

```
ast-grep test [OPTIONS]
```

### Options

| Flag | Description |
|------|-------------|
| `-c, --config <CONFIG>` | Path to sgconfig.yml |
| `-t, --test-dir <DIR>` | Test directory override |
| `-u, --update-snapshots` | Update snapshot files |
| `--snapshot-dir <DIR>` | Snapshot directory override |
| `--filter <REGEX>` | Run only tests matching regex |

### Test File Format

```yaml
id: rule-id-matching-the-rule
valid:
  - "code that should NOT trigger the rule"
  - |
    multi_line_code()
    that_is_valid()
invalid:
  - "code that SHOULD trigger the rule"
  - pattern: "code triggering rule"
    fixed: "expected output after fix"
```

### Examples

```bash
# Run all tests
ast-grep test

# Update snapshots
ast-grep test -u

# Test specific rules
ast-grep test --filter "no-eval"
```

---

## new

Scaffold new ast-grep projects, rules, tests, and utilities.

```
ast-grep new <ITEM>
```

### Items

| Command | Creates |
|---------|---------|
| `ast-grep new project` | Full project structure (sgconfig.yml, dirs) |
| `ast-grep new rule` | New rule YAML file |
| `ast-grep new test` | New test YAML file |
| `ast-grep new util` | New utility rule file |

All commands are interactive — they prompt for required information.

---

## lsp

Start the ast-grep language server for editor integration.

```
ast-grep lsp
```

Editors connect via stdio. Configure in VS Code settings or editor LSP config.

---

## Output Formats

### JSON (`--json`)

```json
[
  {
    "text": "eval(input)",
    "range": {"byteOffset": {"start": 42, "end": 53}, ...},
    "file": "src/main.js",
    "lines": "  return eval(input);",
    "replacement": "safeEval(input)",
    "language": "JavaScript",
    "metaVariables": {"single": {"EXPR": {"text": "input", ...}}}
  }
]
```

### SARIF (`--format sarif`)

Standard Static Analysis Results Interchange Format. Compatible with GitHub Code
Scanning, SonarQube, and other security platforms.

### GitHub (`--format github`)

GitHub Actions annotation format:
```
::warning file=src/main.js,line=5,col=3::eval() usage detected
```

---

## Common Options

These options are shared across `run` and `scan`:

| Flag | Description | Default |
|------|-------------|---------|
| `--globs <PATTERN>` | File filter (gitignore syntax) | — |
| `--no-ignore <TYPE>` | Skip ignore files | — |
| `--follow` | Follow symlinks | false |
| `--stdin` | Read from stdin | false |
| `-j, --threads <N>` | Thread count | 0 (auto) |
| `--color <WHEN>` | Color control | auto |
| `--inspect <LEVEL>` | Debug: nothing, summary, entity | nothing |

### Language identifiers

Use with `-l` flag or `language` field in rules:

```
c, cpp, csharp, css, dart, elixir, go, haskell, html, java,
javascript, json, kotlin, lua, nix, python, ruby, rust, scala,
swift, tsx, typescript, yaml
```
