# Nushell Patterns and Best Practices

## Table of Contents
1. [Error Handling](#error-handling)
2. [Running Scripts Robustly](#running-scripts-robustly)
3. [Common Data Transformations](#common-data-transformations)
4. [Working with JSON/TOML/YAML](#working-with-structured-formats)
5. [Process Execution Patterns](#process-execution-patterns)
6. [Bash-to-Nu Translation](#bash-to-nu-translation)
7. [Debugging](#debugging)

---

## Error Handling

### try / catch
```nu
try {
    open /nonexistent.json
} catch {|e|
    print $"Error: ($e.msg)"
}
```

### try with fallback value
```nu
let result = try { open config.json } catch { {} }  # default to empty record
```

### do --ignore-errors
```nu
let val = do --ignore-errors { open might-not-exist.txt }
# val is null if command errored, otherwise the result
if $val == null { print "file missing" }
```

### Complete (capture exit code of external commands)
```nu
let r = do { ^some-command arg1 arg2 } | complete
if $r.exit_code != 0 {
    print $"FAILED (exit ($r.exit_code)): ($r.stderr)"
} else {
    print $r.stdout
}
```

### error make (throw custom errors)
```nu
def require-file [path: string] {
    if not ($path | path exists) {
        error make {
            msg: $"Required file not found: ($path)"
            label: {
                text: "this file must exist"
                span: (metadata $path).span
            }
        }
    }
}
```

### Propagate or swallow
```nu
# Swallow and continue
try { rm old-file.txt } catch { null }

# Propagate with context
try {
    ^git push
} catch {|e|
    error make {msg: $"git push failed: ($e.msg)"}
}
```

---

## Running Scripts Robustly

### Preferred: heredoc via bash tool
Use this pattern for multi-step Nu workflows called through the Bash tool:

```bash
nu << 'EOF'
# Full script here - bash won't interpolate $ variables
let files = ls | where type == file
$files | length | print
EOF
```

### Passing values from bash into nu
```bash
MY_VAR="hello"
nu << EOF
# WARNING: single-quote EOF prevents bash interpolation
# Use env vars to pass values in:
print \$env.MY_VAR
EOF
# OR: use double-quoted heredoc and escape $ for nu vars:
nu << EOF
let x = "$MY_VAR"
print \$x
EOF
```

Better approach - pass via environment:
```bash
MY_VAR="hello" nu << 'EOF'
print $env.MY_VAR
EOF
```

### Script file approach (most reliable for complex scripts)
Write the script to a file, then run it:
```bash
cat > /tmp/task.nu << 'EOF'
def main [input: string] {
    $input | str upcase
}
main "hello world"
EOF
nu /tmp/task.nu
```

---

## Common Data Transformations

### Filter and transform lists
```nu
let scores = [85 92 78 95 88]
let passing = $scores | where {|s| $s >= 80}
let avg = $scores | math avg
let max = $scores | math max
```

### Work with tables
```nu
let data = open report.csv   # parsed as table
$data
    | where status == "active"
    | sort-by name
    | select name email
    | to md                   # output as markdown table
```

### Group and aggregate
```nu
let orders = open orders.json
$orders
    | group-by category
    | items {|key vals| {category: $key, count: ($vals | length), total: ($vals | get amount | math sum)}}
```

### Flatten nested structures
```nu
let nested = [[1 2] [3 4] [5 6]]
$nested | flatten   # [1 2 3 4 5 6]

# Flatten records
let users = [{name: "alice", tags: ["admin" "user"]} {name: "bob", tags: ["user"]}]
$users | flatten tags
```

### String operations
```nu
"hello world" | split words        # ["hello" "world"]
"a,b,c" | split row ","           # ["a" "b" "c"]
["a" "b" "c"] | str join ", "     # "a, b, c"
"  trimme  " | str trim            # "trimme"
"hello" | str contains "ell"       # true
"snake_case" | str replace "_" "-" # "snake-case"
"hello" | str repeat 3             # "hellohellohello"
```

---

## Working with Structured Formats

### JSON
```nu
# Read
let config = open config.json
let value = $config | get database.host

# Write
{host: "localhost" port: 5432} | to json | save db.json
{host: "localhost" port: 5432} | to json --indent 2 | save pretty.json

# Parse from string
'{"key": "value"}' | from json
```

### TOML
```nu
let config = open Cargo.toml
$config.package.name

{version: "1.0"} | to toml | save VERSION.toml
```

### YAML
```nu
let manifest = open k8s-deploy.yaml
"key: value" | from yaml
$manifest | to yaml | save output.yaml
```

### CSV
```nu
let table = open data.csv
$table | where amount > 100 | to csv | save filtered.csv
```

### NUON (Nu's native format)
```nu
{key: [1 2 3]} | to nuon       # native Nu serialization
"[1 2 3]" | from nuon          # parse back
```

---

## Process Execution Patterns

### Run and check
```nu
def run-checked [command: string, ...args: string] {
    let r = do { run-external $command ...$args } | complete
    if $r.exit_code != 0 {
        error make {msg: $"Command '($command)' failed (exit ($r.exit_code)): ($r.stderr)"}
    }
    $r.stdout
}
```

### Run with retries
```nu
def with-retries [max: int, command: closure] {
    mut attempts = 0
    mut success = false
    mut result = null
    while not $success and $attempts < $max {
        $attempts += 1
        try {
            $result = do $command
            $success = true
        } catch {|e|
            if $attempts >= $max {
                error make {msg: $"Failed after ($max) attempts: ($e.msg)"}
            }
            print $"Attempt ($attempts) failed, retrying..."
        }
    }
    $result
}
```

### Parallel execution
```nu
let results = [file1.json file2.json file3.json]
    | par-each {|f|
        try { open $f } catch { null }
    }
```

### Timeout pattern
```nu
# Nu doesn't have native timeout, use bash's timeout:
let r = do { ^timeout 30 ^long-running-cmd } | complete
if $r.exit_code == 124 { print "Timed out!" }
```

---

## Bash-to-Nu Translation

| Bash | Nu equivalent |
|------|---------------|
| `echo "hello"` | `print "hello"` or `"hello"` |
| `VAR=value` | `let var = "value"` / `mut var = "value"` |
| `export VAR=val` | `$env.VAR = "val"` |
| `if [ -f file ]` | `if ($"file" \| path exists)` |
| `for i in 1 2 3` | `for i in [1 2 3]` |
| `$(command)` | `(^command)` or `let x = ^command` |
| `command1 \| command2` | Same `\|` syntax |
| `grep pattern file` | `open file \| lines \| where {it =~ "pattern"}` |
| `sed 's/a/b/g'` | `str replace -a "a" "b"` |
| `awk '{print $1}'` | `split row " " \| get 0` or table column access |
| `jq .key` | `get key` or `\| get nested.key` |
| `wc -l` | `lines \| length` |
| `sort` | `sort` or `sort-by column` |
| `uniq` | `uniq` |
| `head -n 5` | `first 5` |
| `tail -n 5` | `last 5` |
| `cat file` | `open file` |
| `mkdir -p dir` | `mkdir dir` (creates parents by default) |
| `rm -rf dir` | `rm -rf dir` |
| `$?` | Use `\| complete` and get `.exit_code` |
| `set -e` (fail on error) | Default behavior in scripts |
| `2>/dev/null` | `do --ignore-errors { ... }` |
| `test -d path` | `($path \| path type) == "dir"` |

---

## Debugging

### Print intermediate values
```nu
[1 2 3]
| each {|x| $x * 2}
| tee { print $"After double: ($in)" }
| math sum
```

### Inspect types
```nu
42 | describe          # "int"
"hello" | describe     # "string"
[1 2] | describe       # "list<int>"
{a: 1} | describe      # "record<a: int>"
```

### Print record/structured data
```nu
$some_record | to nuon    # compact
$some_record | to json    # pretty
$some_table | table       # formatted table
```

### Debug command (print and pass through)
```nu
[1 2 3] | each {|x| $x * 2} | tee { table | print } | math sum
```

### Verbose external command
```nu
let r = do { ^git clone https://... } | complete
print $"stdout: ($r.stdout)"
print $"stderr: ($r.stderr)"
print $"exit: ($r.exit_code)"
```
