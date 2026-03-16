# Nushell API Reference

*Sourced directly from [The Nushell Book](https://www.nushell.sh/book/).*

## Table of Contents
1. [Types of Data](#types-of-data)
2. [Special Variables](#special-variables)
3. [Custom Commands (def)](#custom-commands)
4. [Error Handling](#error-handling)
5. [Stdout, Stderr, and Exit Codes](#stdout-stderr-and-exit-codes)
6. [Modules](#modules)

---

## Types of Data

Nushell models data using a rich type system. Use `describe` to inspect any value's type:

```nu
42 | describe          # => int
"hello" | describe     # => string
[1 2 3] | describe     # => list<int>
```

### Type Reference Table

| Type | Annotation | Literal Example |
|------|-----------|-----------------|
| Integer | `int` | `-65535`, `0xff`, `0o234`, `0b10101` |
| Float | `float` | `9.9999`, `Infinity`, `2.0` |
| String | `string` | `"hello"`, `'raw'`, `` `backtick` ``, `r#'raw-hash'#` |
| Boolean | `bool` | `true`, `false` |
| Date | `datetime` | `2025-03-16`, `2025-03-16T12:00:00Z` |
| Duration | `duration` | `2min`, `30sec`, `1hr`, `3.14day` |
| Filesize | `filesize` | `64mb`, `1gib`, `500kb`, `0.5kB` |
| Range | `range` | `0..4` (inclusive), `0..<5` (excl. end), `2..4..20` (stride) |
| Binary | `binary` | `0x[FF D8]`, `0o[1234567]`, `0b[10101010]` |
| List | `list` | `[0 1 'two' 3]` |
| Record | `record` | `{name: "Nu", lang: "Rust"}` |
| Table | `table` | `[[x y]; [12 15] [8 9]]` or `[{x:12, y:15}, {x:8, y:9}]` |
| Closure | `closure` | `{|e| $e + 1}`, `{ $in.name \| path exists }` |
| Cell-path | `cell-path` | `$.name.0` (leading `$.` optional) |
| Block | N/A | `if true { print "hello" }` |
| Nothing / Null | `nothing` | `null` |
| Any | `any` | Any value; used in type annotations only |

### Primitive Types in Detail

#### Integer
```nu
10 / 2     # => 5
0xff       # => 255  (hex)
0o17       # => 15   (octal)
0b1010     # => 10   (binary)
```

#### Float
```nu
2.5 / 5.0                  # => 0.5
# Caution: floating-point precision applies
10.2 * 5.1                 # => 52.01999999999999
```

#### String — four quoting forms

```nu
"double-quoted"         # Supports string interpolation with $"..." 
'single-quoted'         # Raw — no interpolation, no escape sequences
`backtick`              # Same as double-quoted
r#'raw-hash'#           # Raw hash — no escaping; add more # for nested quotes: r##'...'##
```

String interpolation uses `$"..."` with `(expr)` placeholders:
```nu
let name = "world"
$"Hello, ($name)!"     # => Hello, world!
```

#### Boolean
```nu
let b: bool = (2 > 1)
$b                     # => true
2 > 1 and 3 > 2        # => true
not true               # => false
```

#### Date
```nu
date now                           # current datetime
date now | format date '%Y-%m-%d'  # => "2025-03-16"
date now | format date '%s'        # Unix epoch as string
2025-03-16 | date humanize         # => "now" (if recent)
```

#### Duration
```nu
2min + 30sec              # => 2min 30sec
3.14day                   # => 3day 3hr 21min
30day / 1sec              # => 2592000 (seconds in 30 days)
```

Units: `ns`, `us`, `ms`, `sec`, `min`, `hr`, `day`, `wk`

#### Filesize
```nu
1GiB / 1B                 # => 1073741824
0.5kB                     # => 500 B
ls | where size > 1mb     # filter by filesize
```

Units: `b`, `kb`, `mb`, `gb`, `tb`, `pb`, `kib`, `mib`, `gib`, `tib`, `pib`

#### Range
```nu
1..5                   # [1 2 3 4 5] inclusive
0..<5                 # [0 1 2 3 4] exclusive end
2..4..10              # [2 4 6 8 10] with stride
1.. | first 3         # [1 2 3] — infinite range, take first 3
```

#### Binary
```nu
open logo.jpg | into binary | first 2 | $in == 0x[ff d8]   # JPEG magic bytes check
0x[8a 4c] | decode shift-jis     # decode bytes with explicit encoding
```

#### Cell-path
```nu
let cp = $.2
[foo bar goo] | get $cp           # => goo

# Optional chaining with ?
let r = {a: 5}
$r.c?                             # => null (no error)
$r.c? == null                     # => true
```

### Structured Types

#### List
```nu
let nums = [10 20 30]
$nums | get 0                     # => 10
$nums | first 2                   # => [10 20]
$nums | length                    # => 3
$nums | reverse                   # => [30 20 10]
$nums | each {|n| $n * 2}         # => [20 40 60]
$nums | where {|n| $n > 15}       # => [20 30]
```

#### Record
```nu
let r = {name: "Kylian", rank: 99}
$r.name                           # => Kylian
$r | get rank                     # => 99
$r | upsert rank 100              # updates (non-mutating)
$r | insert email "k@ex.com"      # adds key (non-mutating)
$r | select name                  # record with only name
```

#### Table
A table is a **list of records**. Extracting a row returns a record.

```nu
let people = [[name age]; ["alice" 30] ["bob" 25]]
$people | where age > 27 | get name    # => ["alice"]
$people | sort-by age
$people | get 0                        # => {name: alice, age: 30}  (a record)
$people | select name                  # table with only name column
```

#### Closure
```nu
let double = {|x| $x * 2}
5 | do $double                         # => 10

let compare = {|a| $a > 5}
[1 6 3 9] | where $compare             # => [6 9]
```

#### Nothing (Null)
```nu
null                                   # literal null
$nothing | describe                    # => nothing
{a: 1}.b? == null                     # => true  (optional operator ?)
```

---

## Special Variables

### `$nu` — Runtime Constants

`$nu` is a read-only record available at all times.

| Field | Description |
|-------|-------------|
| `$nu.default-config-dir` | Directory where Nu config files live |
| `$nu.config-path` | Path to `config.nu` |
| `$nu.env-path` | Path to `env.nu` |
| `$nu.history-path` | Path to command history file |
| `$nu.home-dir` | User's home directory (same as `~`) |
| `$nu.data-dir` | Nu data directory |
| `$nu.temp-dir` | Writeable temp directory |
| `$nu.pid` | PID of the current Nu process |
| `$nu.os-info` | Record with OS details (name, family, arch, kernel_version) |
| `$nu.startup-time` | Duration Nu took to start |
| `$nu.is-interactive` | `true` if started as interactive shell |
| `$nu.is-login` | `true` if started as login shell |
| `$nu.current-exe` | Full path to current `nu` binary |

```nu
$nu.os-info.name           # => "linux" / "macos" / "windows"
$nu.config-path            # => /home/user/.config/nushell/config.nu
$nu.is-interactive         # => false (when running a script)
nu -c "$nu.is-interactive" # => false
```

### `$env` — Environment Variables

`$env` is a mutable record containing the current environment. Initial values are inherited from the parent process.

```nu
$env.HOME                  # home directory
$env.PATH                  # list of path strings (Nu converts : string to list)
$env.MY_VAR = "value"      # set for current scope
```

#### Key `$env` entries used by Nushell

| Variable | Description |
|----------|-------------|
| `$env.CMD_DURATION_MS` | Milliseconds the previous command took |
| `$env.config` | Main Nu configuration record (`$env.config.table`, etc.) |
| `$env.CURRENT_FILE` | Fully-qualified path of the currently-running script or module |
| `$env.FILE_PWD` | Directory containing the currently-running script or module |
| `$env.LAST_EXIT_CODE` | Exit code of the last external command (equivalent of `$?` in POSIX) |
| `$env.NU_LIB_DIRS` | *(deprecated 0.101+)* Use `$NU_LIB_DIRS` constant instead |
| `$env.NU_LOG_LEVEL` | Log level for `std/log` (`debug`, `info`, `warning`, `error`, `critical`) |
| `$env.NU_VERSION` | Current Nu version string; exported to child processes |
| `$env.PATH` | Executable search path as a list |
| `$env.PROCESS_PATH` | Relative path of the script being executed |
| `$env.SHLVL` | Shell nesting depth |
| `$env.XDG_CONFIG_HOME` | Override for `$nu.default-config-dir` |
| `$env.XDG_DATA_DIR` | Override for `$nu.data-dir` |

```nu
# Read last external exit code
^ls /nonexistent e> /dev/null
$env.LAST_EXIT_CODE        # => 2

# Inject env for one command only
with-env {DEBUG: "true"} { ^my-app }
```

### `$in` — Pipeline Input

`$in` captures the value flowing in from the left side of a pipeline. Available anywhere inside an expression or block:

```nu
"hello" | $in | str upcase     # => HELLO

# Capture and reuse
ls | do { let files = $in; $files | length; $files | get name }

# In a closure parameter
[1 2 3] | each { $in * 2 }     # $in = each row value
```

### `$it` — Row Condition Shorthand

`$it` is only available in a `where` row-condition shorthand (no explicit closure parameter):

```nu
ls | where size > 1mb              # $it.size is the field being tested implicitly
```

Use an explicit closure parameter everywhere else: `where {|row| $row.size > 1mb}`.

### `$NU_LIB_DIRS` and `$NU_PLUGIN_DIRS` Constants

```nu
$NU_LIB_DIRS      # list of directories searched by source, use, overlay use
$NU_PLUGIN_DIRS   # list of directories searched by plugin add
```

---

## Custom Commands

Custom commands (`def`) are first-class commands — they appear in help, type-check at parse time, and integrate with the pipeline.

### Basic Definition

```nu
def greet [name: string] {
    $"Hello, ($name)!"
}
greet "World"     # => Hello, World!
```

The **last expression** is the implicit return value. No `return` keyword needed (unless doing an early exit).

### Return Semantics

```nu
# Implicit return — last expression
def double [x: int] -> int { $x * 2 }

# Early return
def check [n: int] {
    if $n < 0 { return null }
    $n * 10
}

# Suppressing return value (command acts as a statement)
def touch-files [] {
    [a b c] | each { |f| touch $f } | ignore
}
```

> `for` statements do **not** return a value. Use `each` to collect results.

### Parameter Types

**Required positional:**
```nu
def add [a: int, b: int] { $a + $b }
add 3 5    # => 8
```

**Optional positional (suffix with `?`):**
```nu
def greet [name?: string] {
    $"Hello, ($name | default 'You')"
}
greet         # => Hello, You
greet Alice   # => Hello, Alice
```

**Default values:**
```nu
def greet [name = "Nushell"] { $"Hello, ($name)!" }
greet             # => Hello, Nushell!
greet world       # => Hello, world!
```

**Type annotations available:**
`any`, `binary`, `bool`, `cell-path`, `closure`, `datetime`, `duration`, `filesize`, `float`,
`glob`, `int`, `list`, `nothing`, `range`, `record`, `string`, `table`

Special shapes: `number` (int or float), `path` (auto-expands `~`), `directory` (path + tab-complete dirs only)

### Flags

```nu
def process [
    input: string,
    --count(-n): int = 1,    # named flag with shorthand and default
    --verbose(-v),           # boolean switch (true when present)
] {
    if $verbose { print $"count: ($count)" }
    $input
}

process "hello" --verbose -n 3
process "hello" -v --count 3    # flags can go before or after positionals
```

> Flags with dashes are accessed as underscores: `--all-caps` → `$all_caps`.  
> Annotating a flag type as `bool` is **not** allowed; use a switch instead.

### Rest Parameters

```nu
def multi-greet [...names: string] {
    for $name in $names { print $"Hello, ($name)!" }
}
multi-greet Alice Bob Carol

# Spread a list into a rest parameter
let guests = [Alice Bob]
multi-greet ...$guests
```

### Wrapped External Commands (`def --wrapped`)

Collects unknown flags and positional args into a rest parameter for forwarding to an external:

```nu
def --wrapped my-git [...rest] {
    if '--no-pager' in $rest {
        ^git ...$rest
    } else {
        ^git --no-pager ...$rest
    }
}
my-git log --oneline -20
```

### Pipeline Input/Output Signatures

```nu
def double []: int -> int { $in * 2 }
def "str stats" []: string -> record { $in | str length }

# Multiple accepted input types
def "str join" [sep?: string]: [
    list -> string
    string -> string
] { ... }

# Accepts nothing, returns nothing
def side-effect []: nothing -> nothing { print "done" }
```

### `def --env` — Mutating the Caller's Environment

By default, environment changes inside a `def` are scoped and lost on return. Use `def --env` to persist them:

```nu
def --env go-home [] {
    cd ~                       # $env.PWD change persists to caller
}

def --env activate [] {
    $env.MY_APP_ENV = "active"
}
```

### Command Documentation and Attributes (≥0.103)

```nu
# Brief description (first non-blank line)
#
# Longer description on subsequent lines.
@example "Add two numbers" { add 3 5 } --result 8
@category "math"
def add [
    a: int    # First operand
    b: int    # Second operand
]: int -> int {
    $a + $b
}

# Deprecation warning
@deprecated "Use add instead."
def old-add [a: int, b: int] { $a + $b }
```

View with `help add` or `add --help`.

### Subcommands

```nu
def "str mycommand" [] { "hello" }   # extends built-in str namespace
def "deploy to prod" [] { ... }      # spaces in name, call with quotes
```

---

## Error Handling

### `try` / `catch`

```nu
try {
    open /nonexistent.json
} catch {|e|
    print $"Error: ($e.msg)"
}

# Fallback value
let cfg = try { open config.json } catch { {} }
```

The catch block receives a record `e` with:
- `$e.msg` — error message string
- `$e.exit_code` — exit code if from an external command

### `do --ignore-errors`

Suppresses all errors; returns `null` on failure:

```nu
let val = do --ignore-errors { open might-not-exist.txt }
if $val == null { print "file missing" }
```

### `$env.LAST_EXIT_CODE`

After running an external command, the exit code is stored:

```nu
^ls /nonexistent e> /dev/null
$env.LAST_EXIT_CODE    # => 2 (on Linux)
```

Also accessible in `catch`:
```nu
try {
    ^ls /nonexistent e> /dev/null
} catch {|e|
    print $e.exit_code    # => 2
}
```

### `| complete` — Full Capture of External Output

Runs an external command to completion and returns a record with all three streams:

```nu
let r = ^cat unknown.txt | complete
# r = { stdout: "", stderr: "cat: unknown.txt: No such file or directory", exit_code: 1 }

if $r.exit_code != 0 {
    error make {msg: $"Command failed: ($r.stderr)"}
}
print $r.stdout
```

### `error make` — Custom Errors

Raise a structured error from a custom command:

```nu
def require-positive [x: int] {
    if $x <= 0 {
        let span = (metadata $x).span
        error make {
            msg: "Value must be positive",
            label: {
                text: $"got ($x)",
                span: $span
            }
        }
    }
    $x
}
```

Minimal form (no span highlight):
```nu
error make {msg: "something went wrong"}
```

---

## Stdout, Stderr, and Exit Codes

### stdout

By default, Nushell passes the stdout of external commands directly into the pipeline. Without a pipeline, it prints to the screen:

```nu
^ls -la                        # prints to screen
^ls -la | lines | length       # count lines of output
let out = ^git log --oneline   # captures stdout as string
```

### stderr

stderr is **not** redirected by default — it prints to the screen. To work with it:

```nu
^cmd e>| str upcase            # pipe stderr into next command
^cmd e> error.log              # redirect stderr to file
^cmd o+e> combined.log         # redirect both stdout+stderr to file
^cmd o+e>| str upcase          # pipe both into next command
```

Short forms: `o>` = `out>`, `e>` = `err>`, `o+e>` = `out+err>`

### Exit Codes

Three ways to get the exit code of an external command:

```nu
# 1. Environment variable (last external only)
^false; $env.LAST_EXIT_CODE    # => 1

# 2. complete — full capture
let r = ^git push | complete
$r.exit_code                   # 0 or non-zero
$r.stdout
$r.stderr

# 3. try/catch for external commands
try {
    ^git push
} catch {|e|
    print $"Failed with exit ($e.exit_code): ($e.msg)"
}
```

### `print` vs `echo` vs `log`

| Command | Behavior |
|---------|----------|
| `print "msg"` | Outputs to stdout as text; returns nothing. Use `--stderr` to write to stderr |
| `echo "msg"` | Returns its arguments as a value (for pipelines); does NOT print directly |
| `log debug/info/warning/error/critical` | Standard library logging, controlled by `$env.NU_LOG_LEVEL` |

```nu
print "Hello"                     # writes to stdout
print --stderr "Warning message"  # writes to stderr

use std/log
log debug "details"               # NU_LOG_LEVEL=debug to see
log error "something broke"

# echo is for pipelines
echo "hello" | str upcase         # => HELLO
```

### File Redirections Summary

```nu
^cmd o> out.txt              # stdout to file
^cmd e> err.txt              # stderr to file
^cmd o+e> all.log            # both to same file
^cmd o> out.txt e> err.txt   # stdout and stderr to different files

# Pipe redirections
^cmd e>| next-command        # stderr into pipeline
^cmd o+e>| next-command      # both into pipeline

# Suppress all output
use std
^cmd o+e> (std null-device)
```

---

## Modules

Modules package commands, aliases, constants, and environment setup for reuse and sharing.

### Creating a Module (File Form)

`greeting.nu`:
```nu
# A helpful greeting module
export def hello [name: string] {
    $"Hello, ($name)!"
}

export def bye [name: string] {
    $"Goodbye, ($name)!"
}

# Private — not exported, only visible inside the module
def internal-helper [] { "shh" }
```

Import and use:
```nu
use greeting.nu *           # import all exports into current scope
use greeting.nu hello       # import only hello
use greeting.nu [hello bye] # import multiple
use greeting.nu             # namespace import: greeting hello, greeting bye
```

### Module Directory Form

When a module grows large, use a directory with `mod.nu`:

```
my-module/
  mod.nu         ← module entry point
  utils.nu       ← submodule
```

```nu
use my-module *    # or: use my-module/mod.nu *
```

### `main` Export

A command named `main` takes on the module's name when imported:

```nu
# increment.nu
export def main []: int -> int { $in + 1 }

use ./increment.nu
5 | increment      # => 6
```

### All Export Types

```nu
export def my-command [] { }              # command
export alias greet = hello               # alias
export const PI = 3.14159                # constant
export extern known-cmd [...rest]        # known external (for completion)
export module ./sub.nu                   # submodule (preserves sub. prefix)
export use ./sub.nu [cmd1 cmd2]          # re-export selected defs from submodule
export-env { $env.MY_VAR = "value" }     # environment block (runs on use)
```

### `export-env`

Runs when the module is imported with `use`. Sets environment in the **caller's** scope:

```nu
# my-module/mod.nu
export-env {
    $env.MY_MODULE_DIR = ($nu.default-config-dir | path join "my-module")
}
```

```nu
use my-module
$env.MY_MODULE_DIR    # available in caller scope
```

> **Caveat**: `export-env` only runs when the `use` call is *evaluated* (not just parsed). If
> you `use` a module inside another module, the `export-env` of the inner module won't run at
> parse time. Use `export-env { use inner-module [] }` in the outer module to force it.

### Submodules

```nu
# mod.nu — two styles:

# Style 1: export module — defs live under submodule prefix
export module ./utils.nu          # utils hello, utils bye

# Style 2: export use — defs re-exported into parent namespace
export use ./utils.nu             # hello, bye directly

# Style 3: selective re-export
export use ./utils.nu [hello]     # only hello, under parent namespace
```

### `def --env` in Modules

Available as `export def --env` to expose environment-mutating commands:

```nu
# go.nu
export def --env home [] { cd ~ }
export def --env projects [] { cd ~/projects }
```

```nu
use go.nu *
home          # changes directory in caller's scope
```

### Documenting Modules

Comments at the top of the module file appear in `help <module>`:

```nu
# String utilities
#
# Provides extra string manipulation commands
# not found in the standard library.

export def "str kebab" []: string -> string {
    str replace -ar '([A-Z])' '-${1}' | str downcase | str trim -c '-'
}
```

```nu
use my-utils.nu *
help my-utils    # shows the module description
```
