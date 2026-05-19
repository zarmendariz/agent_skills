# C/C++ Patterns for ast-grep

## Table of Contents

1. [Memory Safety](#memory-safety)
2. [Buffer Overflow Prevention](#buffer-overflow-prevention)
3. [Null Pointer Safety](#null-pointer-safety)
4. [Resource Management](#resource-management)
5. [Security Vulnerabilities](#security-vulnerabilities)
6. [Code Quality](#code-quality)
7. [MISRA-Style Rules](#misra-style-rules)
8. [C++ Specific](#c-specific)
9. [Grammar Configuration](#grammar-configuration)

---

## Memory Safety

### Detect malloc without NULL check

```yaml
id: malloc-no-null-check
language: c
rule:
  pattern: "$PTR = malloc($SIZE)"
  not:
    precedes:
      pattern: "if ($PTR == NULL)"
      stopBy: end
message: "malloc() result not checked for NULL"
severity: warning
note: "Always check malloc return value before use"
```

### Detect unsafe realloc pattern

```yaml
id: unsafe-realloc
language: c
rule:
  pattern: "$PTR = realloc($PTR, $SIZE)"
message: "Assigning realloc() to same pointer — loses original on failure"
severity: error
note: "Use a temporary: tmp = realloc(ptr, size); if (tmp) ptr = tmp;"
fix: |
  void *tmp = realloc($PTR, $SIZE);
  if (tmp != NULL) { $PTR = tmp; }
```

### Detect double-free potential

```yaml
id: double-free-risk
language: c
rule:
  pattern: "free($PTR)"
  follows:
    pattern: "free($PTR)"
    stopBy: end
message: "Potential double-free: $PTR freed multiple times"
severity: error
```

### Detect use-after-free pattern

```yaml
id: use-after-free
language: c
rule:
  pattern: "$PTR->$MEMBER"
  follows:
    pattern: "free($PTR)"
    stopBy: end
message: "Potential use-after-free: accessing $PTR after free()"
severity: error
```

---

## Buffer Overflow Prevention

### Unsafe string functions

```yaml
id: no-strcpy
language: c
rule:
  pattern: strcpy($DST, $SRC)
message: "strcpy() has no bounds checking — use strncpy() or strlcpy()"
severity: error
fix: strncpy($DST, $SRC, sizeof($DST) - 1)
---
id: no-strcat
language: c
rule:
  pattern: strcat($DST, $SRC)
message: "strcat() has no bounds checking — use strncat()"
severity: error
---
id: no-sprintf
language: c
rule:
  pattern: sprintf($BUF, $$$ARGS)
message: "sprintf() has no bounds checking — use snprintf()"
severity: error
fix: snprintf($BUF, sizeof($BUF), $$$ARGS)
---
id: no-gets
language: c
rule:
  pattern: gets($BUF)
message: "gets() is unsafe and removed in C11 — use fgets()"
severity: error
fix: fgets($BUF, sizeof($BUF), stdin)
```

### Unsafe memory functions

```yaml
id: memcpy-sizeof-check
language: c
rule:
  all:
    - pattern: memcpy($DST, $SRC, $SIZE)
    - not:
        has:
          pattern: sizeof($DST)
          stopBy: end
message: "memcpy without sizeof(destination) — verify size manually"
severity: info
```

---

## Null Pointer Safety

### Pointer dereference without check

```yaml
id: null-deref-after-function
language: c
rule:
  pattern: "$PTR = $FUNC($$$)"
  precedes:
    pattern: "$PTR->$MEMBER"
    stopBy:
      kind: if_statement
message: "Pointer dereference without NULL check after function call"
severity: warning
```

### Detect NULL passed to non-nullable parameter

```yaml
id: null-to-nonnull
language: c
rule:
  pattern: $FUNC(NULL)
message: "NULL passed as argument — verify function accepts NULL"
severity: info
```

---

## Resource Management

### File handle leak

```yaml
id: file-handle-leak
language: c
rule:
  pattern: "$FILE = fopen($PATH, $MODE)"
  not:
    inside:
      has:
        pattern: fclose($FILE)
        stopBy: end
      stopBy: end
message: "fopen() without corresponding fclose() in scope"
severity: warning
```

### Socket not closed

```yaml
id: socket-leak
language: c
rule:
  pattern: "$SOCK = socket($$$ARGS)"
  not:
    inside:
      has:
        pattern: close($SOCK)
        stopBy: end
      stopBy: end
message: "Socket opened without close() in scope"
severity: warning
```

---

## Security Vulnerabilities

### Format string vulnerability

```yaml
id: format-string-vuln
language: c
rule:
  any:
    - pattern: printf($VAR)
    - pattern: fprintf($FILE, $VAR)
    - pattern: sprintf($BUF, $VAR)
  not:
    has:
      kind: string_literal
      stopBy: end
message: "Format string from variable — potential format string attack"
severity: error
note: "Use printf(\"%s\", var) instead of printf(var)"
```

### Detect system() calls

```yaml
id: no-system-call
language: c
rule:
  pattern: system($CMD)
message: "system() executes via shell — potential command injection"
severity: error
note: "Use exec family (execvp, etc.) for safer process execution"
```

### Detect rand() for security purposes

```yaml
id: insecure-random
language: c
rule:
  any:
    - pattern: rand()
    - pattern: srand($SEED)
message: "rand()/srand() are not cryptographically secure"
severity: warning
note: "Use /dev/urandom, arc4random(), or a CSPRNG for security-sensitive randomness"
```

---

## Code Quality

### Detect magic numbers

```yaml
id: magic-numbers
language: c
rule:
  kind: number_literal
  not:
    any:
      - regex: "^[01]$"
      - inside:
          kind: preproc_def
          stopBy: end
      - inside:
          kind: enum_specifier
          stopBy: end
  inside:
    any:
      - kind: binary_expression
      - kind: call_expression
    stopBy: end
message: "Magic number — consider defining as named constant"
severity: hint
```

### Detect goto usage

```yaml
id: no-goto
language: c
rule:
  kind: goto_statement
message: "goto statement — consider structured control flow"
severity: info
note: "goto is acceptable for error cleanup in C; review context"
```

### Detect deeply nested blocks

```yaml
id: deep-nesting
language: c
rule:
  kind: compound_statement
  has:
    kind: compound_statement
    has:
      kind: compound_statement
      has:
        kind: compound_statement
        stopBy: end
      stopBy: end
    stopBy: end
message: "Deeply nested block (4+ levels) — consider refactoring"
severity: info
```

---

## MISRA-Style Rules

### No implicit int conversion

```yaml
id: implicit-conversion-in-condition
language: c
rule:
  kind: if_statement
  has:
    kind: identifier
    field: condition
message: "Implicit boolean conversion — use explicit comparison"
severity: warning
note: "MISRA C Rule 14.4: Use explicit comparison (x != 0)"
```

### No assignment in condition

```yaml
id: no-assign-in-condition
language: c
rule:
  any:
    - kind: if_statement
    - kind: while_statement
  has:
    kind: assignment_expression
    field: condition
message: "Assignment in condition — use explicit comparison"
severity: warning
note: "MISRA C Rule 13.4: No assignment operators in boolean expressions"
```

### Single return point

```yaml
id: single-return
language: c
rule:
  kind: function_definition
  has:
    pattern: "return $$$"
    follows:
      pattern: "return $$$"
      stopBy: end
    stopBy: end
message: "Multiple return statements — MISRA prefers single exit point"
severity: hint
note: "MISRA C Rule 15.5: A function should have a single point of exit"
```

---

## C++ Specific

### Prefer smart pointers

```yaml
id: raw-new-without-smart-ptr
language: cpp
rule:
  pattern: "new $TYPE($$$ARGS)"
  not:
    inside:
      any:
        - pattern: "std::unique_ptr<$$$>($$$)"
        - pattern: "std::shared_ptr<$$$>($$$)"
        - pattern: "std::make_unique<$$$>($$$)"
        - pattern: "std::make_shared<$$$>($$$)"
      stopBy: end
message: "Raw new without smart pointer — prefer make_unique/make_shared"
severity: warning
fix: null
```

### Detect manual delete

```yaml
id: no-manual-delete
language: cpp
rule:
  any:
    - pattern: "delete $PTR"
    - pattern: "delete[] $PTR"
message: "Manual delete — use RAII/smart pointers"
severity: warning
```

### Use override keyword

```yaml
id: missing-override
language: cpp
rule:
  kind: function_definition
  inside:
    kind: class_specifier
    stopBy: end
  has:
    kind: virtual_function_specifier
  not:
    regex: "override"
message: "Virtual function override without 'override' keyword"
severity: warning
```

### Detect exception in destructor

```yaml
id: throw-in-destructor
language: cpp
rule:
  pattern: "throw $EXCEPTION"
  inside:
    kind: destructor_name
    stopBy:
      kind: function_definition
message: "throw in destructor — can cause std::terminate()"
severity: error
note: "Destructors should be noexcept; use error handling without exceptions"
```

---

## Grammar Configuration

### Setting up C/C++ with ast-grep

C and C++ are supported out-of-the-box. Use language identifiers:
- `c` for C files (.c, .h)
- `cpp` for C++ files (.cpp, .cc, .cxx, .hpp, .hxx)

### Custom extensions mapping

```yaml
# sgconfig.yml
languageGlobs:
  c: ['*.c', '*.h']
  cpp: ['*.cpp', '*.cc', '*.cxx', '*.hpp', '*.hxx', '*.ipp']
```

### Key C/C++ node kinds

| Construct | C node kind | C++ node kind |
|-----------|-------------|---------------|
| Function definition | function_definition | function_definition |
| Function call | call_expression | call_expression |
| Variable declaration | declaration | declaration |
| If statement | if_statement | if_statement |
| For loop | for_statement | for_statement |
| Struct/class | struct_specifier | class_specifier |
| Pointer dereference | pointer_expression | pointer_expression |
| Include | preproc_include | preproc_include |
| Macro definition | preproc_def | preproc_def |
| Type cast | cast_expression | cast_expression |
| Template | — | template_declaration |
| Namespace | — | namespace_definition |

### Inspecting node types

```bash
# View the AST for C code
ast-grep run -p 'int *ptr = malloc(sizeof(int))' -l c --debug-query=ast

# View full CST including all tokens
ast-grep run -p 'if (ptr == NULL)' -l c --debug-query=cst
```
