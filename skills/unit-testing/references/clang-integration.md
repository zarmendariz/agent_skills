# Clang Integration Guide

Using LLVM/Clang as an alternative to GCC for C unit testing with Ceedling.

## Table of Contents

1. [Overview](#overview)
2. [GCC vs Clang Comparison](#gcc-vs-clang-comparison)
3. [Ceedling Configuration for Clang](#ceedling-configuration-for-clang)
4. [Sanitizers](#sanitizers)
5. [Static Analysis](#static-analysis)
6. [Clang-Tidy](#clang-tidy)
7. [Platform-Specific Setup](#platform-specific-setup)
8. [Clang Compiler Flags Reference](#clang-compiler-flags-reference)
9. [Linker Configuration](#linker-configuration)
10. [Troubleshooting](#troubleshooting)

## Overview

Clang is the LLVM-based C/C++/Objective-C compiler. Key advantages for unit testing:

- **Superior diagnostics** — clearer error messages with source annotations
- **Sanitizers** — AddressSanitizer, UBSan, MSan, TSan catch runtime bugs
- **Static analysis** — built-in `--analyze` and clang-tidy integration
- **Fast compilation** — competitive with GCC, often faster for incremental builds
- **Cross-platform** — native on macOS, excellent Linux/Windows support
- **`compile_commands.json`** — first-class support for IDE tooling

### When to Use Clang Over GCC

| Use Case | Recommendation |
|----------|---------------|
| Catching undefined behavior | Clang + UBSan |
| Memory error detection | Clang + ASan |
| Better error messages during development | Clang |
| Code coverage (gcov-compatible) | GCC or Clang (both work) |
| Cross-compilation for ARM/embedded targets | GCC (arm-none-eabi-gcc) |
| Maximum warning coverage | Clang (`-Weverything`) |
| Production firmware builds | GCC (vendor toolchains) |

## GCC vs Clang Comparison

### Flag Compatibility

Most GCC flags work identically in Clang. Key differences:

| Category | GCC | Clang | Notes |
|----------|-----|-------|-------|
| All warnings | `-Wall -Wextra` | Same | Clang may be stricter |
| Maximum warnings | — | `-Weverything` | Clang-only; very noisy |
| Suppress warning | `-Wno-<name>` | Same | |
| GNU extensions | Allowed by default | `-Wno-gnu-*` to suppress | Clang warns by default |
| Zero variadic args | — | `-Wno-gnu-zero-variadic-macro-arguments` | Common with macros |
| Color diagnostics | `-fdiagnostics-color=auto` | `-fcolor-diagnostics` | |
| Dependency gen | `-MMD -MF file.d` | Same | |
| Standards | `-std=c99/c11/c17/c2x` | Same | |
| Optimization | `-O0/-O1/-O2/-O3/-Os` | Same + `-Oz` (minimize size) | |
| Debug info | `-g` | Same + `-glldb` | |
| Link-time opt | `-flto` | Same | |
| Static analysis | — | `--analyze` | Clang-only |

### Diagnostic Quality

Clang provides:
- Fix-it hints with suggested code changes
- Column-level error positions
- Template backtrace elision
- Colored output with source annotations by default

### ABI Compatibility

On Linux, Clang and GCC produce ABI-compatible object files by default. You can:
- Compile with Clang, link with GCC (or vice versa)
- Mix Clang-compiled and GCC-compiled objects in the same binary
- Use GCC's libgcc/libstdc++ with Clang-compiled code

## Ceedling Configuration for Clang

### Method 1: Full Tool Override

```yaml
:tools:
  :test_compiler:
    :executable: clang
    :arguments:
      - -I"${5}"
      - -D"${6}"
      - -DGNU_COMPILER
      - -g
      - -std=c11
      - -Wall
      - -Wextra
      - -Wpedantic
      - -Wno-unused-function
      - -Wno-gnu-zero-variadic-macro-arguments
      - -c "${1}"
      - -o "${2}"
      - -MMD
      - -MF "${4}"

  :test_linker:
    :executable: clang
    :arguments:
      - "${1}"
      - "${5}"
      - -o "${2}"
      - "${4}"
```

### Method 2: Minimal Shortcut Override

```yaml
:tools_test_compiler:
  :executable: clang

:tools_test_linker:
  :executable: clang
```

### Method 3: Mixin File (Recommended)

Create `mixins/clang.yml`:

```yaml
:tools:
  :test_compiler:
    :executable: clang
    :arguments:
      - -I"${5}"
      - -D"${6}"
      - -DGNU_COMPILER
      - -g
      - -c "${1}"
      - -o "${2}"
      - -MMD
      - -MF "${4}"

  :test_linker:
    :executable: clang
    :arguments:
      - "${1}"
      - "${5}"
      - -o "${2}"
      - "${4}"

  :release_compiler:
    :executable: clang
    :arguments:
      - -I"${5}"
      - -D"${6}"
      - -std=c11
      - -O2
      - -c "${1}"
      - -o "${2}"
      - -MMD
      - -MF "${4}"

  :release_linker:
    :executable: clang
    :arguments:
      - "${1}"
      - "${5}"
      - -o "${2}"
      - "${4}"
```

Usage: `ceedling --mixin=mixins/clang.yml test:all`

### Important: Keep -DGNU_COMPILER

Ceedling's Unity/CMock source includes compatibility code gated behind `GNU_COMPILER`. Always include `-DGNU_COMPILER` in the defines even when using Clang to ensure proper behavior.

### Preprocessing Caveat

Ceedling's preprocessing (for mock generation from macros) is tightly coupled to GCC's preprocessor output format. Even when compiling with Clang, the preprocessor tool should remain GCC:

```yaml
:project:
  :use_test_preprocessor: :mocks    # Limit scope; uses GCC internally
```

## Sanitizers

Sanitizers are runtime instrumentation tools that detect bugs at execution time. They must be applied to both compilation AND linking.

### AddressSanitizer (ASan)

Detects: buffer overflows, use-after-free, use-after-return, double-free, memory leaks.

```yaml
# mixins/asan.yml
:flags:
  :test:
    :compile:
      :*:
        - -fsanitize=address
        - -fno-omit-frame-pointer
        - -O1
        - -g
    :link:
      :*:
        - -fsanitize=address
```

Runtime options via environment variable:
```bash
ASAN_OPTIONS="detect_leaks=1:halt_on_error=0:print_stats=1" ceedling test:all
```

### UndefinedBehaviorSanitizer (UBSan)

Detects: signed overflow, null dereference, misaligned access, shift errors, type confusion.

```yaml
# mixins/ubsan.yml
:flags:
  :test:
    :compile:
      :*:
        - -fsanitize=undefined
        - -fno-sanitize-recover=all    # Abort on first UB
        - -g
    :link:
      :*:
        - -fsanitize=undefined
```

Specific UBSan checks:
```
-fsanitize=null              # Null pointer dereference
-fsanitize=alignment         # Misaligned pointer access
-fsanitize=bounds            # Array bounds
-fsanitize=signed-integer-overflow
-fsanitize=unsigned-integer-overflow
-fsanitize=shift             # Invalid shift amounts
-fsanitize=float-divide-by-zero
-fsanitize=unreachable       # Reaching __builtin_unreachable
-fsanitize=return            # Reaching end of non-void function
-fsanitize=vla-bound         # Negative VLA size
```

### Combined ASan + UBSan (Recommended for Testing)

```yaml
# mixins/sanitizers.yml
:flags:
  :test:
    :compile:
      :*:
        - -fsanitize=address,undefined
        - -fno-omit-frame-pointer
        - -fno-sanitize-recover=all
        - -O1
        - -g
    :link:
      :*:
        - -fsanitize=address,undefined
```

### MemorySanitizer (MSan) — Linux Only

Detects: reads of uninitialized memory.

```yaml
:flags:
  :test:
    :compile:
      :*:
        - -fsanitize=memory
        - -fno-omit-frame-pointer
        - -fsanitize-memory-track-origins=2
        - -O1
        - -g
    :link:
      :*:
        - -fsanitize=memory
```

**Note**: MSan requires ALL code (including libraries) to be instrumented. Not compatible with ASan.

### ThreadSanitizer (TSan) — For Threaded Code

Detects: data races between threads.

```yaml
:flags:
  :test:
    :compile:
      :*:
        - -fsanitize=thread
        - -O1
        - -g
    :link:
      :*:
        - -fsanitize=thread
```

**Note**: Not compatible with ASan or MSan. Use separately.

### Sanitizer Compatibility Matrix

| Sanitizer | ASan | UBSan | MSan | TSan |
|-----------|------|-------|------|------|
| ASan | — | ✓ | ✗ | ✗ |
| UBSan | ✓ | — | ✓ | ✓ |
| MSan | ✗ | ✓ | — | ✗ |
| TSan | ✗ | ✓ | ✗ | — |

## Static Analysis

### Clang Static Analyzer (scan-build)

Run the analyzer over the entire build:

```bash
scan-build --status-bugs ceedling release
scan-build -o reports/ ceedling release
```

### Inline Analysis (--analyze flag)

Analyze individual files during compilation:

```yaml
:tools:
  :release_compiler:
    :executable: clang
    :arguments:
      - --analyze
      - -Xanalyzer -analyzer-output=html
      - -Xanalyzer -analyzer-checker=core,deadcode,security,alpha
      - -I"${5}"
      - -D"${6}"
      - -c "${1}"
      - -o "${2}"
```

### Available Analyzer Checkers

```
core.*          — Core checks (null deref, divide by zero, uninitialized)
deadcode.*      — Dead code detection
security.*      — Security vulnerabilities (buffer overflow, format string)
alpha.*         — Experimental checks
unix.*          — Unix API misuse
cplusplus.*     — C++ specific
```

List all available checkers:
```bash
clang --analyze -Xanalyzer -analyzer-checker-help
```

## Clang-Tidy

### Integration with Ceedling

First, enable the `compile_commands_json_db` plugin to generate the compilation database:

```yaml
:plugins:
  :enabled:
    - compile_commands_json_db
```

Then run clang-tidy against the generated database:

```bash
# After building
ceedling release

# Run clang-tidy
clang-tidy -p build/ src/*.c
clang-tidy -p build/ --checks='bugprone-*,performance-*,readability-*' src/*.c
```

### .clang-tidy Configuration File

Place in project root:

```yaml
---
Checks: >
  -*,
  bugprone-*,
  performance-*,
  readability-*,
  clang-analyzer-*,
  -readability-magic-numbers,
  -bugprone-easily-swappable-parameters

WarningsAsErrors: ''

HeaderFilterRegex: 'src/.*\.h$'

CheckOptions:
  - key: readability-identifier-naming.FunctionCase
    value: lower_case
  - key: readability-identifier-naming.VariableCase
    value: lower_case
  - key: readability-identifier-naming.MacroDefinitionCase
    value: UPPER_CASE
  - key: readability-function-size.LineThreshold
    value: '100'
```

### Automated via command_hooks

```yaml
:plugins:
  :enabled:
    - command_hooks
    - compile_commands_json_db

:command_hooks:
  :post_build:
    :tools:
      - :executable: clang-tidy
        :arguments:
          - -p build/
          - --checks=bugprone-*,performance-*,clang-analyzer-*
          - "${1}"
```

## Platform-Specific Setup

### Linux

Install LLVM/Clang:
```bash
# Ubuntu/Debian
sudo apt install clang lld llvm

# Fedora
sudo dnf install clang lld llvm

# Specific version
sudo apt install clang-17 lld-17
```

No special Ceedling configuration needed — just set `:executable: clang`.

### macOS

Apple ships Clang as the system compiler (via Xcode Command Line Tools):
```bash
xcode-select --install
# /usr/bin/clang is Apple's Clang (may lag upstream features)
```

For upstream LLVM (latest features, sanitizers):
```bash
brew install llvm
```

Ceedling configuration for Homebrew LLVM:
```yaml
:environment:
  - :path:
    - "/opt/homebrew/opt/llvm/bin"    # Apple Silicon
    - "#{ENV['PATH']}"

:tools_test_compiler:
  :executable: /opt/homebrew/opt/llvm/bin/clang

:tools_test_linker:
  :executable: /opt/homebrew/opt/llvm/bin/clang
```

**Note**: Apple's built-in Clang masquerades as GCC — Ceedling's default GCC config already works with it. The `-DGNU_COMPILER` define handles this.

### Windows

**Option 1: Official LLVM Installer**
- Download from https://releases.llvm.org/
- Installs to `C:\Program Files\LLVM\bin\`

```yaml
:environment:
  - :path:
    - "C:/Program Files/LLVM/bin"
    - "#{ENV['PATH']}"

:tools:
  :test_compiler:
    :executable: "\"C:/Program Files/LLVM/bin/clang.exe\""
    :arguments:
      - -I"${5}"
      - -D"${6}"
      - -DGNU_COMPILER
      - -g
      - -c "${1}"
      - -o "${2}"
      - -MMD
      - -MF "${4}"

:extension:
  :object: .o              # Force .o (Clang on Windows may default to .obj)
```

**Option 2: MSYS2 MinGW Clang**
```bash
pacman -S mingw-w64-x86_64-clang
```

```yaml
:environment:
  - :path:
    - "C:/msys64/mingw64/bin"
    - "#{ENV['PATH']}"

:tools_test_compiler:
  :executable: clang
```

**Option 3: Visual Studio (clang-cl)**

`clang-cl` uses MSVC-compatible flags. Not recommended with Ceedling — Ceedling expects GCC-style flags.

### Windows Notes

- Use escaped quotes for paths with spaces: `"\"C:/Program Files/LLVM/bin/clang.exe\""`
- Avoid test filenames containing "patch" or "setup" (Windows UAC issue)
- Ensure `:extension: :object: .o` is set (prevents `.obj` default)

## Clang Compiler Flags Reference

### Warning Flags (Recommended for Testing)

```
-Wall                               # Standard warnings
-Wextra                             # Additional warnings
-Wpedantic                          # Strict ISO C compliance
-Werror                             # Treat warnings as errors
-Weverything                        # ALL warnings (very noisy, not for CI)

# Commonly suppressed with Ceedling/Unity/CMock:
-Wno-unused-function                # Generated mock functions
-Wno-unused-parameter               # setUp/tearDown params
-Wno-gnu-zero-variadic-macro-arguments
-Wno-language-extension-token
-Wno-missing-field-initializers     # Struct partial init
```

### Standard Selection

```
-std=c99     # C99 (most embedded projects)
-std=c11     # C11 (_Atomic, _Static_assert, anonymous structs)
-std=c17     # C17 (bug fixes only, no new features)
-std=c2x     # C23 draft (latest features)
-std=gnu11   # C11 + GNU extensions (default)
```

### Optimization

```
-O0          # No optimization (fastest compile, best debug)
-O1          # Basic optimization (good for sanitizers)
-O2          # Full optimization (production)
-O3          # Aggressive optimization
-Os          # Optimize for size
-Oz          # Minimize size (Clang-only, more aggressive than -Os)
```

### Debug Information

```
-g           # Standard DWARF debug info
-g0          # No debug info
-glldb       # Optimized for LLDB debugger
-gdwarf-4    # Force DWARF v4 format
-fstandalone-debug    # Full debug info (no type references to other CUs)
```

### Code Generation

```
-fno-omit-frame-pointer    # Required for sanitizer stack traces
-fstack-protector-strong   # Stack buffer overflow protection
-fPIC                      # Position-independent code
-ffunction-sections        # Each function in its own section (for --gc-sections)
-fdata-sections            # Each data item in its own section
```

## Linker Configuration

### Using lld (LLVM Linker)

lld is significantly faster than GNU ld for large projects:

```yaml
:tools:
  :test_linker:
    :executable: clang
    :arguments:
      - -fuse-ld=lld               # Use lld instead of system ld
      - "${1}"
      - "${5}"
      - -o "${2}"
      - "${4}"
```

### Sanitizer Linking

Sanitizer flags MUST appear in both compiler and linker arguments:

```yaml
:flags:
  :test:
    :compile:
      :*:
        - -fsanitize=address,undefined
    :link:
      :*:
        - -fsanitize=address,undefined    # Links sanitizer runtime
```

### Static vs Shared Sanitizer Runtime

```
-shared-libasan              # Use shared ASan library (smaller binaries)
-static-libsan               # Static link all sanitizer runtimes
```

## Troubleshooting

### "unknown warning option '-Wno-...'"

Clang is strict about unknown `-Wno-` flags. Check flag availability:
```bash
clang -Wno-unknown-warning-option -Werror -Wbad-flag -c test.c
```

### Linker errors with sanitizers

Ensure sanitizer flags are in BOTH `:compile` and `:link` sections. Missing from linker = "undefined reference to `__asan_*`".

### Mock compilation warnings

CMock-generated files trigger warnings. Suppress with:
```yaml
:flags:
  :test:
    :compile:
      :*:
        - -Wno-unused-function
        - -Wno-missing-prototypes
```

### macOS "library not found for -lSystem"

When using Homebrew LLVM, you may need:
```bash
export SDKROOT=$(xcrun --show-sdk-path)
```

Or in project.yml:
```yaml
:environment:
  - :sdkroot: "#{`xcrun --show-sdk-path`.strip}"
```

### Windows object file extension

Clang on Windows may produce `.obj` files by default. Force `.o`:
```yaml
:extension:
  :object: .o
```
