---
name: ast-grep
description: >
  Structural code search, linting, and transformation using ast-grep (AST pattern matching).
  Invoke when the user needs to: search code by structure (not text), write lint rules,
  refactor code at scale, migrate APIs, detect security patterns, enforce coding standards,
  or perform any AST-based code analysis. Triggers on: "ast-grep", "structural search",
  "code pattern", "refactor", "lint rule", "find usage", "code transformation",
  "migrate API", "detect pattern", or requests involving tree-sitter-based code matching.
  Supports C, C++, Rust, Go, Java, Python, JavaScript, TypeScript, and 10+ other languages.
---

# ast-grep: Structural Code Search & Transformation

Search, lint, and rewrite code using AST pattern matching powered by tree-sitter.

## Prerequisites

ast-grep must be installed:

```bash
# Via cargo (recommended)
cargo install ast-grep --locked

# Via npm
npm install -g @ast-grep/cli

# Via homebrew
brew install ast-grep
```

Verify: `ast-grep --version`

## Core Concepts

ast-grep matches **code structure** (AST nodes), not text. Patterns are written in the
target language's own syntax with metavariables as wildcards.

**Metavariables:**
- `$VAR` — matches one named AST node (captures it)
- `$$$ARGS` — matches zero or more consecutive nodes
- `$$VAR` — matches including unnamed (punctuation) nodes
- `$_` — non-capturing wildcard

**Strictness levels** (how patterns match):
- `smart` (default) — unnamed tokens in pattern required; unnamed in code skipped
- `cst` — exact match including all tokens
- `ast` — match only named nodes, ignore all unnamed
- `relaxed` — like ast but also ignores comments
- `signature` — match node kinds only, ignore text

## Quick Reference

### Search (one-off)

```bash
ast-grep run -p 'console.log($$$ARGS)' -l javascript
ast-grep run -p 'eval($EXPR)' -l javascript --json
ast-grep run -p 'subprocess.call($CMD, shell=True)' -l python src/
```

### Rewrite

```bash
ast-grep run -p 'var $X = $Y' --rewrite 'const $X = $Y' -l javascript -U
ast-grep run -p 'require($MOD)' --rewrite 'import $MOD from $MOD' -l javascript -i
```

### Scan with rules

```bash
ast-grep scan --rule rules/no-eval.yml
ast-grep scan                              # uses sgconfig.yml
ast-grep scan --format sarif               # CI integration
```

### Test rules

```bash
ast-grep test                              # uses sgconfig.yml testConfigs
ast-grep test --config sgconfig.yml
```

## YAML Rule Structure

```yaml
id: rule-id
language: JavaScript
rule:
  pattern: dangerous_function($$$ARGS)
message: "Explain what was found"
severity: error          # error | warning | info | hint
note: "Remediation guidance"
fix: safe_function($$$ARGS)
```

### Atomic Rules (match node properties)

| Rule | Matches on | Example |
|------|-----------|---------|
| `pattern` | AST structure | `pattern: fetch($URL)` |
| `kind` | tree-sitter node type | `kind: function_declaration` |
| `regex` | node text content | `regex: "^test"` |

### Relational Rules (match context)

| Rule | Relationship | Example |
|------|-------------|---------|
| `has` | has descendant matching | `has: {pattern: return, stopBy: end}` |
| `inside` | is inside ancestor matching | `inside: {kind: class_declaration}` |
| `follows` | preceded by sibling matching | `follows: {pattern: import $$$}` |
| `precedes` | followed by sibling matching | `precedes: {kind: export_statement}` |

### Composite Rules (logic)

```yaml
rule:
  all:                    # AND — all must match
    - pattern: $OBJ.query($SQL)
    - has:
        kind: template_string
        stopBy: end
  any:                    # OR — at least one matches
    - pattern: eval($X)
    - pattern: Function($X)
  not:                    # negation
    pattern: safe_eval($X)
```

### Relational Rule Options

- `stopBy: end` — search all descendants (not just immediate children)
- `stopBy: {kind: function_declaration}` — stop at boundary
- `field: name` — match only the named field of parent node

### Metavariable Constraints

```yaml
constraints:
  VAR:
    regex: "^unsafe_"
    kind: identifier
```

### Metavariable Transforms

```yaml
transform:
  NEW_NAME:
    replace:
      source: $OLD_NAME
      replace: "^get"
      by: "fetch"
fix: $NEW_NAME($$$ARGS)
```

## Project Configuration (sgconfig.yml)

```yaml
ruleDirs: [rules]
testConfigs:
  - testDir: rule-tests
    snapshotDir: __snapshots__
utilDirs: [utils]
languageGlobs:
  html: ['*.vue', '*.svelte']
customLanguages:
  my-lang:
    libraryPath: path/to/parser.dll
    extensions: ['.mylang']
    expandoChar: $
```

Initialize: `ast-grep new project`

## Rule Testing

Create `rule-tests/<rule-id>-test.yml`:

```yaml
id: no-eval
valid:
  - "JSON.parse(data)"
  - "safe_function(input)"
invalid:
  - "eval(userInput)"
  - "eval('code')"
```

Run: `ast-grep test`

## Workflow Patterns

### 1. Find and fix across codebase
```bash
ast-grep run -p 'old_api($$$A)' --rewrite 'new_api($$$A)' -l python -U
```

### 2. Security audit
```bash
ast-grep scan --rule security-rules/ --format sarif > report.sarif
```

### 3. CI/CD linting
```bash
ast-grep scan --error=critical-rule --format github
```

### 4. JSON output for scripting
```bash
ast-grep run -p '$FUNC($$$)' -l javascript --json=stream | jq '.file'
```

### 5. Stdin mode (pipe code in)
```bash
echo 'eval("code")' | ast-grep run -p 'eval($X)' -l javascript --stdin
```

### 6. Interactive refactoring
```bash
ast-grep run -p 'Promise.resolve($X)' --rewrite '$X' -l typescript -i
```

## Language-Specific Guidance

### C/C++ Analysis

C/C++ patterns for memory safety, security, and code quality:

```bash
# Multi-argument patterns work directly with -p:
ast-grep run -p 'strcpy($DST, $SRC)' -l c
ast-grep run -p 'memcpy($DST, $SRC, $N)' -l c
ast-grep run -p '$PTR->$MEMBER' -l c
```

**Important:** Single-argument C function calls (e.g., `malloc(x)`, `free(x)`, `gets(buf)`)
are ambiguous with C type macros in tree-sitter's grammar. Use YAML rules with `kind: call_expression`
instead of `-p` patterns for reliable matching:

```yaml
# Reliable way to match single-arg C calls
rule:
  kind: call_expression
  has:
    kind: identifier
    regex: "^(malloc|free|gets)$"
    field: function
```

See [references/c-cpp-patterns.md](references/c-cpp-patterns.md) for comprehensive rules.

### JavaScript/TypeScript

```bash
ast-grep run -p 'document.innerHTML = $X' -l javascript    # XSS
ast-grep run -p 'new Function($$$ARGS)' -l javascript      # code injection
```

### Python

```bash
ast-grep run -p 'os.system($CMD)' -l python                # command injection
ast-grep run -p 'pickle.loads($DATA)' -l python            # deserialization
```

## Detailed References

- **[references/pattern-syntax.md](references/pattern-syntax.md)** — Complete pattern syntax, metavariables, strictness
- **[references/rule-reference.md](references/rule-reference.md)** — Full YAML rule schema, all operators
- **[references/cli-reference.md](references/cli-reference.md)** — All commands, flags, output formats
- **[references/recipes.md](references/recipes.md)** — Practical recipes organized by use case
- **[references/c-cpp-patterns.md](references/c-cpp-patterns.md)** — C/C++ specific patterns and rules

## Limitations

- Cannot perform semantic analysis (type inference, data flow, taint tracking)
- Regex engine is automata-based: no backreferences or lookaround
- Pattern must be valid parseable code fragment
- Cross-file analysis not supported (each file analyzed independently)
- Custom languages require compiled tree-sitter grammar (.so/.dll)

# Ast Grep

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" → "Reading" → "Creating" → "Editing"
- Structure: ## Overview → ## Workflow Decision Tree → ## Step 1 → ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" → "Merge PDFs" → "Split PDFs" → "Extract Text"
- Structure: ## Overview → ## Quick Start → ## Task Category 1 → ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" → "Colors" → "Typography" → "Features"
- Structure: ## Overview → ## Guidelines → ## Specifications → ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" → numbered capability list
- Structure: ## Overview → ## Core Capabilities → ### 1. Feature → ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Claude for patching or environment adjustments. Python scripts should be run using `uv run` to ensure proper dependency isolation.

### references/
Documentation and reference material intended to be loaded into context to inform Claude's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Claude should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Claude produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Any unneeded directories can be deleted.** Not every skill requires all three types of resources.
