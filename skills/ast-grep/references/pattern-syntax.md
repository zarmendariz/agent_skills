# ast-grep Pattern Syntax Reference

## Table of Contents

1. [Pattern Fundamentals](#pattern-fundamentals)
2. [Metavariables](#metavariables)
3. [Multi-node Matching ($$$)](#multi-node-matching)
4. [Pattern Objects](#pattern-objects)
5. [Strictness Levels](#strictness-levels)
6. [Named vs Unnamed Nodes](#named-vs-unnamed-nodes)
7. [Common Pitfalls](#common-pitfalls)

---

## Pattern Fundamentals

A pattern is a code fragment written in the target language. ast-grep parses it with
tree-sitter and matches its AST structure against source code.

**Key principle:** Patterns match structure, not text. Whitespace, formatting, and
line breaks are irrelevant — only the tree shape matters.

```bash
# All of these match the same pattern: console.log($MSG)
console.log(x)
console.log( x )
console
  .log(x)
console.log(
  x
)
```

### Pattern string (CLI)

```bash
ast-grep run -p 'pattern_here' -l language
```

Always use **single quotes** to prevent shell expansion of `$` metavariables.

### Pattern in YAML rules

```yaml
rule:
  pattern: console.log($MSG)
```

For multi-line patterns, use YAML block scalar:

```yaml
rule:
  pattern: |
    function $NAME($$$PARAMS) {
      $$$BODY
    }
```

---

## Metavariables

Metavariables are wildcards that capture AST subtrees during matching.

| Syntax | Captures | Named nodes | Unnamed nodes |
|--------|----------|-------------|---------------|
| `$VAR` | Single node | ✅ Yes | ❌ No |
| `$$$VAR` | Zero or more consecutive | ✅ Yes | ❌ No |
| `$$VAR` | Single node | ✅ Yes | ✅ Yes |
| `$_` | Single (non-capturing) | ✅ Yes | ❌ No |
| `$$$` | Zero or more (non-capturing) | ✅ Yes | ❌ No |

### Single-node metavariable: `$VAR`

Matches exactly one named AST node. The node can be any type (identifier, expression,
statement, literal, etc.).

```yaml
# $FUNC captures the function name, $ARG captures the argument
pattern: $FUNC($ARG)

# Matches:
#   foo(bar)       → $FUNC=foo, $ARG=bar
#   calculate(x+1) → $FUNC=calculate, $ARG=x+1
#   obj.method(y)  → NO MATCH (obj.method is member_expression, $FUNC expects plain call)
```

### Multi-node metavariable: `$$$VAR`

Matches zero or more consecutive named nodes. Essential for variable-length constructs.

```yaml
# Match function with any number of parameters
pattern: function $NAME($$$PARAMS) { $$$BODY }

# Match any number of arguments
pattern: console.log($$$ARGS)

# $$$ARGS matches:
#   console.log()          → $$$ARGS = (empty)
#   console.log(a)         → $$$ARGS = a
#   console.log(a, b, c)   → $$$ARGS = a, b, c
```

### Unnamed-inclusive metavariable: `$$VAR`

Matches a single node including unnamed (anonymous) tokens like operators and punctuation.

```yaml
# Match any binary operation
pattern: $A $$OP $B
# $$OP captures the operator token (+, -, *, /, ==, etc.)
```

### Non-capturing wildcards: `$_` and `$$$`

Use when you need to match but don't need to reference the capture:

```yaml
# Match any function call, don't care about name or args
pattern: $_($$$)

# Match member access on any object
pattern: $_.method()
```

### Metavariable naming rules

- Must start with `$`
- Name must be UPPERCASE letters, digits, and underscores
- Valid: `$VAR`, `$MY_VAR`, `$X1`, `$$$ARGS`
- Invalid: `$var`, `$my-var`, `$123`

### Metavariable sharing across rules

When a metavariable is captured in one part of a rule, it can be referenced in other
parts. The same name must match the same text.

```yaml
# Detect self-assignment (a = a)
rule:
  pattern: $X = $X

# Detect recursive function calls
rule:
  pattern: function $F($$$) { $$$ }
  has:
    pattern: $F($$$)
    stopBy: end
```

---

## Multi-node Matching ($$$)

The `$$$` metavariable matches sequences. Key behaviors:

1. **Greedy by default** — captures as many nodes as possible
2. **Works in argument lists** — `f($$$BEFORE, target, $$$AFTER)`
3. **Works in statement blocks** — `{ $$$BEFORE; target; $$$AFTER }`
4. **Can be empty** — matches zero nodes

```yaml
# Match object destructuring with any properties
pattern: "const { $$$PROPS } = $OBJ"

# Match array with specific element surrounded by others
pattern: "[$$$HEAD, targetElement, $$$TAIL]"

# Match function body containing a return
pattern: |
  function $F($$$) {
    $$$BEFORE
    return $RET
    $$$AFTER
  }
```

---

## Pattern Objects

When a pattern is ambiguous (multiple valid parse interpretations), use a pattern
object with explicit context:

```yaml
rule:
  pattern:
    context: "class A { $FIELD = $VALUE }"
    selector: field_definition
```

- `context` — provides surrounding code so the pattern parses unambiguously
- `selector` — specifies which node kind in the parsed context is the actual match target

**When to use:** Assignments like `x = 5` are ambiguous in JavaScript (could be
assignment expression OR class field). Pattern objects disambiguate.

---

## Strictness Levels

Control how precisely patterns match unnamed nodes:

| Level | Pattern unnamed | Code unnamed | Use case |
|-------|----------------|--------------|----------|
| `cst` | Required | Required | Exact token matching |
| `smart` (default) | Required | Skipped | Normal usage |
| `ast` | Skipped | Skipped | Loose structural match |
| `relaxed` | Skipped + no comments | Skipped + no comments | Ignore comments |
| `signature` | Kind only | Kind only | Shape matching |

### Example: `async` keyword handling

```javascript
// Pattern: function $F($$$) { $$$ }
// With smart strictness (default):

function foo() {}       // ✅ matches
async function bar() {} // ✅ matches (async is unnamed, skipped in code)

// Pattern: async function $F($$$) { $$$ }
// With smart strictness:

function foo() {}       // ❌ no match (async required in pattern)
async function bar() {} // ✅ matches
```

Set strictness in CLI:
```bash
ast-grep run -p 'pattern' --strictness relaxed -l javascript
```

---

## Named vs Unnamed Nodes

Tree-sitter grammars define two types of nodes:

- **Named nodes**: Defined by grammar rules (e.g., `identifier`, `function_declaration`,
  `binary_expression`). These are the "abstract" structural elements.
- **Unnamed (anonymous) nodes**: Defined by string literals in grammars (e.g., `+`, `{`,
  `async`, `;`). These are syntactic tokens.

**Why this matters for patterns:**
- `$VAR` only matches named nodes
- `$$VAR` matches both named and unnamed
- In `smart` mode, unnamed nodes in source code that don't appear in the pattern are ignored

### Viewing node types

```bash
# Show the AST for a pattern
ast-grep run -p 'x + 1' -l javascript --debug-query=ast
ast-grep run -p 'x + 1' -l javascript --debug-query=cst
```

---

## Common Pitfalls

### 1. Shell expansion of metavariables
```bash
# WRONG — shell expands $VAR
ast-grep run -p "console.log($MSG)" -l javascript

# CORRECT — single quotes prevent expansion
ast-grep run -p 'console.log($MSG)' -l javascript
```

### 2. Argument count mismatch
```bash
# This matches ONLY one-argument calls
ast-grep run -p 'console.log($MSG)' -l javascript

# This matches ANY number of arguments
ast-grep run -p 'console.log($$$ARGS)' -l javascript
```

### 3. Pattern must be valid syntax
```bash
# INVALID — incomplete syntax
ast-grep run -p 'for (' -l javascript    # parse error

# VALID — complete structural fragment
ast-grep run -p 'for ($INIT; $COND; $UPDATE) { $$$BODY }' -l javascript
```

### 4. Metavariable boundary in fix templates
```yaml
# WRONG — parser reads $VARNAME as one metavariable
fix: $VARname

# Correct — use transform or spacing
fix: $VAR name
```

### 5. Regex without structural constraint
```yaml
# WRONG — evaluates regex on every node (slow + rejected by ast-grep)
rule:
  regex: "^test"

# CORRECT — constrain with kind first
rule:
  kind: identifier
  regex: "^test"
```
