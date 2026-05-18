# Nushell Language Guide

## Table of Contents
1. [Invocation Patterns](#invocation-patterns)
2. [Types and Values](#types-and-values)
3. [Variables](#variables)
4. [String Interpolation](#string-interpolation)
5. [Operators](#operators)
6. [Control Flow](#control-flow)
7. [Custom Commands (Functions)](#custom-commands)
8. [Pipelines](#pipelines)
9. [Structured Data](#structured-data)
10. [File and I/O Operations](#file-and-io)
11. [Environment Variables](#environment-variables)
12. [External Commands](#external-commands)
13. [Error Handling](#error-handling)

---

## Invocation Patterns

The Bash tool invokes bash. To run Nu commands, use one of these patterns:

### Inline one-liners
```bash
nu -c "ls | where type == file | get name"
```

### Here-doc script (preferred for multi-line)
```bash
nu << 'EOF'
let x = 42
print $"Value: ($x)"
EOF
```

### Script file
```bash
nu /path/to/script.nu
```

### With arguments
```bash
nu -c "def greet [name] { print $\"Hi ($name)\" }; greet 'world'"
# or via script file:
nu script.nu arg1 arg2   # accessed as $args.0, $args.1 or via parameters
```

**Critical rule**: Use `nu << 'EOF' ... EOF` (single-quoted heredoc) in bash to avoid bash interpolating `$` variables. Only use `nu -c "..."` for short one-liners with no `$` variables.

---

## Types and Values

```nu
# Primitives
42           # int
3.14         # float
"hello"      # string
true / false # bool
null         # nothing

# Collections
[1 2 3]                        # list
{name: "alice", age: 30}       # record
[[name age]; ["alice" 30]]     # table (list of records)

# Special
1..10                          # range (inclusive)
1..<10                         # range (exclusive end)
2025-03-16                     # date
1min 30sec                     # duration
1mb 500kb                      # filesize
```

---

## Variables

```nu
let x = 42           # immutable (default)
mut count = 0        # mutable
const PI = 3.14159   # parse-time constant

$count += 1          # mutate with +=, -=, *=, /=, ++=

# Shadowing (immutable vars can be re-let in same scope)
let x = $x + 1
```

---

## String Interpolation

```nu
let name = "world"
print $"Hello, ($name)!"           # $"..." with ($expr) interpolation

# Multi-line strings
let msg = $"Line 1
Line 2 ($name)"

# Raw strings (no interpolation)
let path = 'C:\Users\no\interpolation\here'
```

---

## Operators

```nu
# Arithmetic
1 + 2; 10 - 3; 4 * 5; 10 / 3; 10 // 3; 10 mod 3; 2 ** 8

# Comparison
1 == 1; 1 != 2; 1 < 2; 2 >= 2

# String / regex
"hello" =~ "hel"      # regex match → true
"hello" !~ "xyz"      # no match → true
"hello" starts-with "he"
"hello" ends-with "lo"

# Membership
2 in [1 2 3]          # true
"a" not-in ["b" "c"]  # true

# List append
[1 2] ++ [3 4]        # [1 2 3 4]

# Boolean
true and false; true or false; not true
```

---

## Control Flow

### if / else
```nu
if $x > 0 { "positive" } else if $x == 0 { "zero" } else { "negative" }
```

### match
```nu
match $status {
    "ok"    => { print "success" }
    "error" => { print "failed" }
    _       => { print "unknown" }
}
```

### Loops
```nu
# for loop
for i in 1..5 { print $i }

# while
mut i = 0
while $i < 5 { $i += 1 }

# loop with break
loop {
    if $condition { break }
}

# each (functional, preferred over for when collecting results)
[1 2 3] | each {|x| $x * 2 }   # → [2 4 6]
```

---

## Custom Commands

```nu
# Basic
def greet [name: string] {
    print $"Hello, ($name)!"
}

# With flags and defaults
def process [
    input: string,
    --count(-n): int = 1,   # named flag with shorthand and default
    --verbose(-v),           # boolean flag
] {
    if $verbose { print $"Processing ($count) times" }
    $input | str repeat $count
}

# Return value is last expression (no explicit return needed)
def double [x: int] -> int {
    $x * 2
}

# Pipeline commands (receive piped input via $in)
def add-prefix [] {
    $in | each {|line| $">> ($line)" }
}
"hello" | add-prefix   # → ">> hello"
```

---

## Pipelines

```nu
# Basic pipe
ls | where type == file | get name

# Save pipeline result to variable
let big_files = ls | where size > 1mb | sort-by size -r

# Pipe into variable (= captures last pipeline value)
let result = "hello world" | split words | length

# $in captures piped input anywhere
ls | each {|f| $f.name | str upcase }

# Tee (inspect mid-pipeline)
ls | tee { print $"Count: ($in | length)" } | get name
```

---

## Structured Data

```nu
# Record access
let person = {name: "alice", age: 30}
$person.name           # "alice"
$person | get age     # 30

# Nested access
let data = {user: {profile: {city: "NYC"}}}
$data.user.profile.city   # "NYC"

# Update record
let updated = $person | upsert age 31
let with_email = $person | insert email "alice@example.com"

# Lists
let nums = [1 2 3 4 5]
$nums | first 3       # [1 2 3]
$nums | last 2        # [4 5]
$nums | get 2         # 3 (0-indexed)
$nums | where {|n| $n > 2}    # [3 4 5]
$nums | each {|n| $n * 2}     # [2 4 6 8 10]
$nums | reduce {|it acc| $acc + $it}  # 15

# Tables (list of records)
let people = [[name age]; ["alice" 30] ["bob" 25]]
$people | where age > 27 | get name   # ["alice"]
$people | sort-by age
$people | select name                  # table with only name column
```

---

## File and I/O

```nu
# Read files
open file.txt           # string
open data.json          # parsed as record/list
open data.csv           # table

# Write files
"content" | save output.txt
{key: "value"} | to json | save data.json
$table | to csv | save report.csv

# File system
ls                      # table of files
ls **/*.nu              # glob
mkdir new-dir
cp source dest
mv old new
rm file.txt
rm -rf dir/

# Path operations
"~/docs" | path expand        # absolute path
"/a/b/c.txt" | path dirname   # "/a/b"
"/a/b/c.txt" | path basename  # "c.txt"
"/a/b/c.txt" | path extension # "txt"
["/a" "b" "c.txt"] | path join  # "/a/b/c.txt"
```

---

## Environment Variables

```nu
# Read
$env.HOME
$env.PATH             # list on Nu (split from : string)
$env | get PATH

# Set (current scope only)
$env.MY_VAR = "value"

# Temporary env for a command
with-env {MY_VAR: "value"} { ^some-command }

# Check existence
if "MY_VAR" in $env { ... }
```

---

## External Commands

Prefix with `^` to explicitly call external (non-Nu) commands:

```nu
^git status
^npm install
^python3 script.py

# Capture output as string
let output = ^git log --oneline -5
let lines = ^git log --oneline | lines

# Capture exit code
let result = do { ^false } | complete
print $result.exit_code    # 1
print $result.stdout       # ""
print $result.stderr       # ""

# Check success
let r = do { ^git pull } | complete
if $r.exit_code != 0 {
    error make {msg: $"git pull failed: ($r.stderr)"}
}
```

Without `^`, Nu looks for a built-in command first. Always use `^` when calling system commands to avoid ambiguity.
