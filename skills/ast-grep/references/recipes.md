# ast-grep Recipes

## Table of Contents

1. [Security Auditing](#security-auditing)
2. [Code Quality](#code-quality)
3. [Refactoring & Migration](#refactoring--migration)
4. [Dead Code Detection](#dead-code-detection)
5. [Framework Patterns](#framework-patterns)
6. [CI/CD Integration](#cicd-integration)

---

## Security Auditing

### JavaScript/TypeScript Security

```yaml
# Detect eval() usage (code injection)
id: no-eval
language: JavaScript
rule:
  any:
    - pattern: eval($CODE)
    - pattern: new Function($$$ARGS)
    - pattern: setTimeout($CODE, $$$)
    - pattern: setInterval($CODE, $$$)
  not:
    inside:
      kind: comment
      stopBy: end
message: "Dynamic code execution detected — potential code injection"
severity: error
note: "Use safer alternatives like JSON.parse() or explicit function references"
fix: null
---
# Detect innerHTML assignment (XSS)
id: no-inner-html
language: JavaScript
rule:
  pattern: $EL.innerHTML = $VALUE
message: "Direct innerHTML assignment — potential XSS vulnerability"
severity: error
note: "Use textContent for text or a sanitization library for HTML"
---
# Detect hardcoded secrets
id: no-hardcoded-secrets
language: JavaScript
rule:
  all:
    - kind: variable_declarator
    - has:
        kind: identifier
        regex: "(?i)(password|secret|api_key|token|private_key)"
    - has:
        kind: string
        stopBy: end
message: "Possible hardcoded secret in variable"
severity: error
note: "Use environment variables or a secrets manager"
```

### SQL Injection Detection

```yaml
id: sql-injection-template-literal
language: JavaScript
rule:
  all:
    - pattern: $DB.query($SQL)
    - has:
        kind: template_string
        stopBy: end
message: "SQL query with template literal — potential injection"
severity: error
note: "Use parameterized queries: db.query('SELECT...WHERE id=$1', [id])"
---
id: sql-injection-concatenation
language: JavaScript
rule:
  all:
    - pattern: $DB.query($SQL)
    - has:
        kind: binary_expression
        has:
          kind: string
          regex: "(?i)select|insert|update|delete"
        stopBy: end
message: "SQL query with string concatenation"
severity: error
```

### Python Security

```yaml
id: no-shell-injection
language: Python
rule:
  any:
    - pattern: os.system($CMD)
    - pattern: os.popen($CMD)
    - pattern: subprocess.call($CMD, shell=True)
    - pattern: subprocess.run($CMD, shell=True)
    - pattern: subprocess.Popen($CMD, shell=True)
message: "Command execution with shell=True — potential injection"
severity: error
note: "Use subprocess.run(cmd_list, shell=False) with explicit arguments"
---
id: no-pickle-untrusted
language: Python
rule:
  any:
    - pattern: pickle.loads($DATA)
    - pattern: pickle.load($FILE)
message: "Pickle deserialization of potentially untrusted data"
severity: warning
note: "Pickle can execute arbitrary code. Use JSON or MessagePack for untrusted data"
---
id: no-sql-format-string
language: Python
rule:
  all:
    - pattern: $DB.execute($QUERY)
    - has:
        kind: string
        regex: "(%s|%d|\\{)"
        stopBy: end
message: "SQL query using string formatting — potential injection"
severity: error
```

---

## Code Quality

### Remove Debug Statements

```yaml
id: no-console-log
language: JavaScript
rule:
  pattern: console.log($$$ARGS)
message: "console.log in production code"
severity: warning
fix: ""
---
id: no-print-debug
language: Python
rule:
  pattern: print($$$ARGS)
  not:
    inside:
      kind: function_definition
      has:
        kind: identifier
        regex: "^(main|cli|print_)"
      stopBy: end
message: "print() statement — use logging module"
severity: info
```

### Detect TODO/FIXME

```yaml
id: find-todos
language: JavaScript
rule:
  kind: comment
  regex: "(TODO|FIXME|HACK|XXX)"
message: "Found TODO/FIXME marker"
severity: hint
```

### Enforce Naming Conventions

```yaml
# Constants should be UPPER_SNAKE_CASE
id: const-naming
language: JavaScript
rule:
  pattern: "const $NAME = $VALUE"
  not:
    any:
      - has:
          kind: identifier
          regex: "^[A-Z_][A-Z0-9_]*$"
          field: name
      - has:
          kind: identifier
          regex: "^[a-z]"
          field: name
constraints:
  NAME:
    regex: "^[A-Z].*[a-z]"
message: "Constants with uppercase start should be UPPER_SNAKE_CASE"
severity: hint
```

### Prevent Common Mistakes

```yaml
# Self-assignment detection
id: no-self-assign
language: JavaScript
rule:
  pattern: $X = $X
message: "Variable assigned to itself"
severity: warning
---
# Identical comparison operands
id: no-self-compare
language: JavaScript
rule:
  any:
    - pattern: $X === $X
    - pattern: $X == $X
    - pattern: $X !== $X
    - pattern: $X != $X
message: "Comparing variable with itself"
severity: warning
```

---

## Refactoring & Migration

### var → const/let Migration

```yaml
id: no-var
language: JavaScript
rule:
  pattern: var $NAME = $VALUE
message: "Use const or let instead of var"
severity: warning
fix: const $NAME = $VALUE
```

### Promise.then → async/await

```yaml
id: prefer-async-await
language: JavaScript
rule:
  pattern: $PROMISE.then($CALLBACK)
message: "Consider using async/await instead of .then()"
severity: info
```

### require → import

```yaml
id: use-import
language: JavaScript
rule:
  pattern: "const $NAME = require($MOD)"
message: "Use ES module import syntax"
severity: info
fix: "import $NAME from $MOD"
```

### API Rename (coordinated)

```yaml
id: rename-api-definition
language: JavaScript
rule:
  pattern: |
    function oldApiName($$$PARAMS) {
      $$$BODY
    }
fix: |
  function newApiName($$$PARAMS) {
    $$$BODY
  }
---
id: rename-api-calls
language: JavaScript
rule:
  pattern: oldApiName($$$ARGS)
fix: newApiName($$$ARGS)
```

### Python 2 → 3 Migration

```yaml
id: print-to-function
language: Python
rule:
  kind: print_statement
message: "Python 2 print statement"
severity: error
fix: null
---
id: dict-iteritems
language: Python
rule:
  pattern: $DICT.iteritems()
fix: $DICT.items()
message: "iteritems() removed in Python 3"
severity: error
```

---

## Dead Code Detection

### Unused Variables

```yaml
id: unused-variable-hint
language: JavaScript
rule:
  pattern: "const $NAME = $VALUE"
  not:
    inside:
      has:
        pattern: $NAME
        stopBy: end
message: "Variable $NAME may be unused"
severity: hint
```

### Empty Functions

```yaml
id: empty-function
language: JavaScript
rule:
  any:
    - pattern: "function $F($$$) {}"
    - pattern: "($$$) => {}"
  not:
    has:
      kind: comment
      stopBy: end
message: "Empty function body"
severity: info
```

---

## Framework Patterns

### React: Detect Class Components

```yaml
id: prefer-functional-component
language: TypeScript
rule:
  pattern: |
    class $NAME extends React.Component {
      $$$BODY
    }
message: "Consider converting class component to functional component with hooks"
severity: info
```

### React: Missing Key in Map

```yaml
id: missing-key-prop
language: TypeScript
rule:
  pattern: $ARR.map($$$)
  has:
    any:
      - kind: jsx_element
      - kind: jsx_self_closing_element
    not:
      has:
        pattern: key={$$$}
    stopBy: end
message: "Missing key prop in mapped JSX elements"
severity: warning
```

### Express: Detect Unhandled Async Errors

```yaml
id: async-handler-no-try-catch
language: JavaScript
rule:
  all:
    - pattern: "async ($REQ, $RES, $$$) => { $$$BODY }"
    - not:
        has:
          kind: try_statement
          stopBy: end
message: "Async route handler without try-catch — unhandled rejections crash server"
severity: warning
```

### pytest: Missing Assertions

```yaml
id: test-without-assert
language: Python
rule:
  kind: function_definition
  has:
    kind: identifier
    regex: "^test_"
    field: name
  not:
    has:
      any:
        - pattern: assert $$$
        - pattern: pytest.raises($$$)
        - pattern: $$.assert_called($$$)
      stopBy: end
message: "Test function without assertions"
severity: warning
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/lint.yml
name: ast-grep lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install ast-grep
        run: cargo install ast-grep --locked
      - name: Run ast-grep scan
        run: ast-grep scan --format github
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ast-grep
        name: ast-grep scan
        entry: ast-grep scan
        language: system
        pass_filenames: false
```

### SARIF Upload (GitHub Security)

```yaml
- name: Run security scan
  run: ast-grep scan --format sarif > results.sarif
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
```
