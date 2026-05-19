# ast-grep Rule Reference

## Table of Contents

1. [Rule File Schema](#rule-file-schema)
2. [Atomic Rules](#atomic-rules)
3. [Relational Rules](#relational-rules)
4. [Composite Rules](#composite-rules)
5. [Fix and Transform](#fix-and-transform)
6. [Constraints](#constraints)
7. [Utility Rules](#utility-rules)
8. [Multi-Rule Files](#multi-rule-files)
9. [Rule Evaluation Order](#rule-evaluation-order)

---

## Rule File Schema

Complete YAML rule specification:

```yaml
# Required fields
id: rule-identifier          # unique ID (kebab-case)
language: JavaScript         # tree-sitter language name
rule: {}                     # matching specification (see below)

# Diagnostic fields
message: "What was found"    # human-readable diagnostic
severity: warning            # error | warning | info | hint | off
note: "How to fix it"       # remediation guidance (supports markdown)

# Transformation
fix: "replacement($VAR)"    # auto-fix template
transform: {}               # metavariable string operations
rewriters: []               # compositional sub-transforms

# Advanced
constraints: {}             # metavariable validation
utils: {}                   # inline utility rules
labels: {}                  # custom match highlighting
metadata: {}                # arbitrary key-value data
```

---

## Atomic Rules

Atomic rules match individual nodes based on intrinsic properties.

### pattern

Match by AST structure. The core matching primitive.

```yaml
rule:
  pattern: console.log($MSG)
```

**Pattern object** (for ambiguous patterns):
```yaml
rule:
  pattern:
    context: "class A { $FIELD = $VALUE }"
    selector: field_definition
```

**Pattern with strictness:**
```yaml
rule:
  pattern:
    pattern: async function $F() {}
    strictness: cst
```

### kind

Match by tree-sitter node type name.

```yaml
rule:
  kind: function_declaration
```

Find node kind names using `--debug-query`:
```bash
ast-grep run -p 'your_code' -l lang --debug-query=ast
```

Common node kinds by language:

| Language | Functions | Variables | Calls |
|----------|-----------|-----------|-------|
| JavaScript | function_declaration, arrow_function | variable_declarator | call_expression |
| Python | function_definition | assignment | call |
| C/C++ | function_definition | declaration | call_expression |
| Rust | function_item | let_declaration | call_expression |
| Go | function_declaration | short_var_declaration | call_expression |

### regex

Match by text content of the node. **Must** be combined with structural constraints.

```yaml
rule:
  kind: identifier
  regex: "^test_"
```

Regex features (Rust regex crate, automata-based):
- Character classes: `[a-z]`, `\w`, `\d`, `\s`
- Quantifiers: `*`, `+`, `?`, `{n,m}`
- Alternation: `a|b`
- Anchors: `^`, `$`
- Non-capturing groups: `(?:...)`
- Case-insensitive: `(?i)pattern`
- Unicode support: `\p{Letter}`

**Not supported** (requires backtracking):
- Backreferences: `\1`
- Lookahead/lookbehind: `(?=...)`, `(?<=...)`

---

## Relational Rules

Match nodes based on relationships to other nodes in the AST.

### has

Node must have a descendant matching the sub-rule.

```yaml
rule:
  kind: function_declaration
  has:
    pattern: console.log($$$)
    stopBy: end
```

### inside

Node must be inside an ancestor matching the sub-rule.

```yaml
rule:
  pattern: await $PROMISE
  inside:
    kind: for_in_statement
    stopBy: end
```

### follows

Node must be preceded by a sibling matching the sub-rule.

```yaml
rule:
  pattern: return $VALUE
  follows:
    pattern: if ($COND) { return $$$; }
```

### precedes

Node must be followed by a sibling matching the sub-rule.

```yaml
rule:
  kind: import_statement
  precedes:
    kind: export_statement
```

### Relational Rule Options

All relational rules accept these additional fields:

| Field | Description | Default |
|-------|-------------|---------|
| `stopBy: end` | Search all descendants/ancestors | immediate only |
| `stopBy: {kind: X}` | Stop traversal at node kind X | — |
| `stopBy: {pattern: X}` | Stop traversal at pattern X | — |
| `field: name` | Match only the specific named field | any child |

**stopBy semantics:**
- Without `stopBy`: only checks immediate children/parent
- `stopBy: end`: traverses entire subtree/ancestor chain
- `stopBy: {kind: function_definition}`: stops at function boundaries

**field semantics:**
```yaml
# Match only the condition part of an if statement
rule:
  kind: if_statement
  has:
    pattern: $X == null
    field: condition    # only checks the condition field, not the body
```

---

## Composite Rules

Combine multiple rules with logical operators.

### all (AND)

All sub-rules must match the same node:

```yaml
rule:
  all:
    - kind: call_expression
    - has:
        kind: identifier
        regex: "^unsafe_"
    - not:
        inside:
          kind: try_statement
          stopBy: end
```

### any (OR)

At least one sub-rule must match:

```yaml
rule:
  any:
    - pattern: eval($X)
    - pattern: new Function($X)
    - pattern: setTimeout($X, $$$)
```

### not (negation)

Node must NOT match the sub-rule:

```yaml
rule:
  pattern: $OBJ.$METHOD($$$ARGS)
  not:
    pattern: logger.$METHOD($$$ARGS)
```

### matches (utility reference)

Reference a named utility rule:

```yaml
rule:
  pattern: $FUNC($$$ARGS)
  has:
    matches: is-dangerous-function
```

---

## Fix and Transform

### fix

Template string for code replacement. Metavariables are substituted with their
captured source text.

```yaml
fix: "newFunction($ARG1, $ARG2)"
```

Multi-line fix:
```yaml
fix: |
  const result = await $PROMISE;
  if (!result) {
    throw new Error("Failed");
  }
```

**Indentation is automatically adjusted** to match the matched node's context.

### transform

Apply string operations to metavariables before substitution in fix:

```yaml
transform:
  NEW_NAME:
    replace:
      source: $OLD_NAME
      replace: "^get"
      by: "fetch"
  UPPER:
    convert:
      source: $NAME
      toCase: upperCase    # upperCase, lowerCase, camelCase, snakeCase, etc.
  PARTIAL:
    substring:
      source: $FULL
      startChar: 3
      endChar: -1
fix: "$NEW_NAME($$$ARGS)"
```

Transform operations:
- `replace` — regex replace on captured text
- `convert` — case conversion (upperCase, lowerCase, camelCase, snakeCase, pascalCase, etc.)
- `substring` — extract substring by character positions

### rewriters

Compositional transforms that recursively apply Find & Patch to sub-nodes:

```yaml
rewriters:
  - id: convert-import
    rule:
      pattern: require($MOD)
    fix: import($MOD)

rule:
  pattern: "const $NAME = require($MOD)"
fix: "import $NAME from $MOD"
```

---

## Constraints

Validate metavariable captures with additional conditions:

```yaml
constraints:
  VAR:
    regex: "^unsafe_"      # text must match regex
    kind: identifier       # must be specific node kind
    not:
      regex: "^unsafe_internal_"  # must NOT match
```

Constraints narrow matches after the pattern succeeds. Use to filter false positives.

---

## Utility Rules

Reusable matching logic defined in `utils/` directory or inline:

### File-based utility (in utilDirs)

```yaml
# utils/is-dangerous.yml
id: is-dangerous-function
language: JavaScript
rule:
  any:
    - pattern: eval
    - pattern: Function
    - pattern: setTimeout
```

### Inline utility (in rule file)

```yaml
id: no-dangerous-in-handler
language: JavaScript
utils:
  is-handler:
    kind: method_definition
    has:
      kind: identifier
      regex: "^handle"
rule:
  pattern: $FUNC($$$)
  inside:
    matches: is-handler
    stopBy: end
  has:
    matches: is-dangerous-function
```

### Recursive utilities

Utilities can reference themselves for recursive matching:

```yaml
# Match deeply nested property access: a.b.c.d...
id: deep-member-access
language: JavaScript
rule:
  kind: member_expression
  has:
    any:
      - kind: member_expression
      - matches: deep-member-access
```

---

## Multi-Rule Files

Separate multiple rules in one file with YAML document separators:

```yaml
id: rename-old-api-definition
language: JavaScript
rule:
  pattern: function oldApi($$$PARAMS) { $$$BODY }
fix: function newApi($$$PARAMS) { $$$BODY }
---
id: rename-old-api-calls
language: JavaScript
rule:
  pattern: oldApi($$$ARGS)
fix: newApi($$$ARGS)
```

All rules in a multi-rule file execute atomically in a single pass.

---

## Rule Evaluation Order

1. **Structural filter**: `kind` / `pattern` narrows candidate nodes
2. **Regex filter**: `regex` tests node text
3. **Relational checks**: `has`, `inside`, `follows`, `precedes` verify context
4. **Composite logic**: `all`, `any`, `not` combine results
5. **Constraints**: validate metavariable captures
6. **Fix generation**: apply `transform` then substitute into `fix` template

**Performance tip:** Place most-selective rules first. `kind` is fastest, then
`pattern`, then `regex`. Relational rules are most expensive.
