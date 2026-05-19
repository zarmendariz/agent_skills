# Ceedling Configuration Reference

Ceedling 1.0.0 (released 2025-01-01) — Ruby/Rake-based automated build and test system for C.

## Table of Contents

1. [Project Configuration](#project-configuration)
2. [Paths Configuration](#paths-configuration)
3. [Defines Configuration](#defines-configuration)
4. [Flags Configuration](#flags-configuration)
5. [Tools Configuration](#tools-configuration)
6. [Switching to Clang](#switching-to-clang)
7. [Environment and Extensions](#environment-and-extensions)
8. [CMock Configuration](#cmock-configuration)
9. [CException Configuration](#cexception-configuration)
10. [Libraries Configuration](#libraries-configuration)
11. [Plugins](#plugins)
12. [Mixins](#mixins)
13. [Commands Reference](#commands-reference)
14. [Complete Examples](#complete-examples)

## Project Configuration

```yaml
:project:
  :build_root: build/                 # Required: build output directory
  :which_ceedling: gem                # 'gem' (default) or path to local ceedling
  :use_mocks: TRUE                    # Enable CMock mock generation (default: FALSE)
  :use_exceptions: FALSE              # Enable CException (default: FALSE)
  :use_test_preprocessor: :none       # :none, :mocks, :tests, :all
  :use_backtrace: :simple             # :none, :simple (default), :gdb
  :use_decorators: :auto              # :auto, :all, :none (emoji/color in output)
  :test_file_prefix: test_            # Prefix for test file discovery
  :release_build: FALSE               # Enable release build target
  :compile_threads: :auto             # Parallel compilation (integer or :auto)
  :test_threads: :auto                # Parallel test execution
  :default_tasks:
    - test:all                        # Tasks when no argument given
```

| Setting | Purpose | Default |
|---------|---------|---------|
| `:build_root:` | Build artifact directory | Required |
| `:use_mocks:` | Enable CMock | `FALSE` |
| `:use_exceptions:` | Enable CException | `FALSE` |
| `:use_test_preprocessor:` | Macro expansion before scanning | `:none` |
| `:compile_threads:` | Parallel compile workers | `1` |
| `:test_threads:` | Parallel test runners | `1` |
| `:release_build:` | Enable `ceedling release` | `FALSE` |

### Test Build and Release Build

```yaml
:test_build:
  :use_assembly: FALSE
  :graceful_fail: true              # Exit 0 even on test failures (useful for CI)

:release_build:
  :output: MyApp.out                # Release artifact name
  :use_assembly: FALSE
  :artifacts:
    - build/release/out/MyApp.map   # Extra files to preserve
```

## Paths Configuration

**IMPORTANT (1.0.0 breaking change)**: `:include` paths are no longer auto-merged from `:source`. You must explicitly list all header search paths.

```yaml
:paths:
  :test:
    - +:test/**                     # Recursive (+ prefix is decorative)
    - -:test/support                # Exclude from test collection
  :source:
    - src/**
    - lib/module_a/**
  :include:                         # REQUIRED — explicit header search paths
    - src/**
    - include/**
    - /usr/local/include/third_party
  :support:
    - test/support
  :libraries:
    - third_party/libs              # -L search paths for linker
```

### Glob Syntax

| Pattern | Meaning |
|---------|---------|
| `/**` | All subdirectories recursively (includes parent) |
| `/*` | Direct subdirectories only |
| `?` | Single character wildcard |
| `{a,b}` | Alternatives |
| `-:path` | Subtract/exclude a path |
| `+:path` | Additive (default, decorative) |

## Defines Configuration

### Simple (all test executables)

```yaml
:defines:
  :test:
    - TEST
    - UNITY_INCLUDE_EXEC_TIME
  :release:
    - NDEBUG
    - PRODUCT_VERSION=42
```

### Advanced Per-Test Matchers (1.0.0)

```yaml
:defines:
  :test:
    :*:                             # Wildcard: ALL test executables
      - TEST
      - ASSERT_LEVEL=2
    :Comms:                         # Substring match
      - COMMS_MODULE_ENABLED
    :/test_(uart|spi)/:             # Regex match
      - SERIAL_BUS_TEST
    :test_comm_startup.c:           # Exact file match
      - STARTUP_TEST_ONLY
    :hardware/test_startup:         # Path-qualified match
      - HARDWARE_VARIANT=1
  :preprocess:                      # Symbols for preprocessing step
    :*:
      - TEST
      - PREPROCESS_ONLY_DEFINE
  :use_test_definition: TRUE        # test_FooBar.c → -D_TEST_FOOBAR_
```

Symbols are **cumulative** — multiple matching matchers each contribute their defines.

## Flags Configuration

Compiler and linker flags, separate from tool definitions. Structure: `context → operation → flags`.

### Simple (applies to all)

```yaml
:flags:
  :test:
    :compile:
      - -std=c11
      - -Wall
      - -Wextra
    :link:
      - -lm
  :release:
    :compile:
      - -std=c11
      - -O2
    :link:
      - -lm
      - -pthread
```

### Advanced Per-Test Matchers

```yaml
:flags:
  :test:
    :compile:
      :*:                           # All test executables
        - -std=c11
        - -Wall
      :Model:                       # Substring match
        - -Wextra
      :/test_(uart|spi)/:           # Regex match
        - -DSERIAL_TEST
    :link:
      :TestBigModule:
        - -Wl,--whole-archive
        - -lfull_lib
```

**NOTE**: Simple list and matcher formats cannot be mixed for the same operation.

## Tools Configuration

The `:tools:` section defines the toolchain. Each tool has an executable and arguments with placeholder variables.

### Placeholder Variables

| Placeholder | Compiler | Linker |
|------------|----------|--------|
| `${1}` | Source file | Object files list |
| `${2}` | Output object | Output binary |
| `${3}` | (unused) | Map file (unused) |
| `${4}` | Dependency file | Library flags (-l) |
| `${5}` | Include paths | Library paths (-L) |
| `${6}` | Define symbols | — |

### Default GCC Tool Configuration

```yaml
:tools:
  :test_compiler:
    :executable: gcc
    :arguments:
      - -I"${5}"                    # Include paths (one -I per path)
      - -D"${6}"                    # Defines (one -D per symbol)
      - -DGNU_COMPILER             # Ceedling compatibility define
      - -g                          # Debug symbols
      - -c "${1}"                   # Source file
      - -o "${2}"                   # Output object
      - -MMD                        # Generate dependency file
      - -MF "${4}"                  # Dependency file path

  :test_linker:
    :executable: gcc
    :arguments:
      - "${1}"                      # Object files
      - "${5}"                      # Library search paths
      - -o "${2}"                   # Output executable
      - "${4}"                      # Library flags

  :test_fixture:
    :executable: "${1}"             # Run the test executable directly

  :release_compiler:
    :executable: gcc
    :arguments:
      - -I"${5}"
      - -D"${6}"
      - -O2
      - -c "${1}"
      - -o "${2}"
      - -MMD
      - -MF "${4}"

  :release_linker:
    :executable: gcc
    :arguments:
      - "${1}"
      - "${5}"
      - -o "${2}"
      - "${4}"
```

### Full Tool Definition Format

```yaml
:tools:
  :test_compiler:
    :executable: gcc                # Must be in PATH or fully qualified
    :name: 'my test compiler'      # Optional human-readable name
    :arguments:
      - -I"${5}"
      - -D"${6}"
      - -g
      - -Wall
      - -c "${1}"
      - -o "${2}"
      - -MMD
      - -MF "${4}"
    :stderr_redirect: :none        # :none, :auto, :win, :unix, :tcsh
    :optional: false               # If true, skip tool validation
```

### Tool Shortcut Overrides

Replace only the executable while keeping default arguments:

```yaml
:tools_test_compiler:
  :executable: clang

:tools_test_linker:
  :executable: clang
```

## Switching to Clang

### Complete Clang Toolchain Configuration

```yaml
:tools:
  :test_compiler:
    :executable: clang
    :arguments:
      - -I"${5}"
      - -D"${6}"
      - -DGNU_COMPILER             # Keep for CMock/Unity compatibility
      - -g
      - -std=c11
      - -Wall
      - -Wextra
      - -Wno-unused-function       # Suppress warnings on generated mock functions
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
      - -Wall
      - -Wextra
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

### Minimal Swap (Shortcut Method)

```yaml
:tools_test_compiler:
  :executable: clang

:tools_test_linker:
  :executable: clang

:tools_release_compiler:
  :executable: clang

:tools_release_linker:
  :executable: clang
```

### Clang with AddressSanitizer

```yaml
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

### Clang with UndefinedBehaviorSanitizer

```yaml
:flags:
  :test:
    :compile:
      :*:
        - -fsanitize=undefined
        - -fno-sanitize-recover=all
        - -g
    :link:
      :*:
        - -fsanitize=undefined
```

### Combined ASan + UBSan

```yaml
:flags:
  :test:
    :compile:
      :*:
        - -fsanitize=address,undefined
        - -fno-omit-frame-pointer
        - -O1
        - -g
    :link:
      :*:
        - -fsanitize=address,undefined
```

### Clang on Windows

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
  :object: .o                       # Force .o (Clang on Windows may default to .obj)
```

### Clang on macOS (Homebrew LLVM)

```yaml
:environment:
  - :path:
    - "/opt/homebrew/opt/llvm/bin"   # ARM Macs
    - "#{ENV['PATH']}"

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
```

### Preprocessing Note

Ceedling's preprocessing tools (for mock generation) are tightly coupled to GCC output format. The preprocessor should remain GCC/cpp even when using Clang for compilation. Use `:use_test_preprocessor: :mocks` to limit preprocessing scope.

### GCC vs Clang Warning Flag Differences

| Category | GCC | Clang |
|----------|-----|-------|
| Basic | `-Wall -Wextra` | Same (Clang may warn more aggressively) |
| All possible | N/A | `-Weverything` (Clang-only, very noisy) |
| GNU extensions | N/A | `-Wno-gnu-*` to suppress |
| Zero variadic macros | N/A | `-Wno-gnu-zero-variadic-macro-arguments` |
| Color diagnostics | `-fdiagnostics-color` | `-fcolor-diagnostics` |

## Environment and Extensions

### Environment Variables

```yaml
:environment:
  # Ordered list (not hash) — evaluated top to bottom
  - :license_server: gizmo.intranet
  - :path:
    - /opt/local/llvm/bin           # Prepend to PATH
    - "#{ENV['PATH']}"              # Must quote because of '#'
  - :var1: hello
  - :var2: "#{ENV['VAR1']} world"   # Use previously set var
```

### File Extensions

```yaml
:extension:
  :header: .h
  :source: .c
  :assembly: .s
  :object: .o
  :executable: .out                 # .exe on Windows
  :testpass: .pass
  :testfail: .fail
  :dependencies: .d
```

## CMock Configuration

```yaml
:cmock:
  :mock_prefix: mock_
  :mock_suffix: ""
  :mock_path: mocks/
  :when_no_prototypes: :warn        # :warn, :ignore, :error
  :enforce_strict_ordering: true
  :fail_on_unexpected_calls: true
  :memcmp_if_unknown: true
  :when_ptr: :smart                 # :compare_ptr, :compare_data, :smart
  :verbosity: 2                     # 0=errors, 1=+warnings, 2=normal, 3=verbose

  :treat_as:
    uint8_t: HEX8
    uint16_t: HEX16
    uint32_t: HEX32
    int8_t: INT8
    int16_t: INT16
    int32_t: INT32
    bool: INT
    float: FLOAT
    double: FLOAT

  :treat_externs: :exclude          # :include or :exclude extern functions
  :treat_inlines: :exclude          # :include or :exclude inline functions

  :strippables:
    - '(?:__attribute__\s*\(+.*?\)+)'
  :attributes:
    - __ramfunc
    - __irq
    - __fiq
    - register
    - extern
  :c_calling_conventions:
    - __stdcall
    - __cdecl
    - __fastcall

  :callback_include_count: true     # Include NumCalls param in callbacks
  :callback_after_arg_check: false  # false = _Stub bypasses arg checks

  :plugins:
    - :ignore
    - :ignore_arg
    - :expect_any_args
    - :return_thru_ptr
    - :array
    - :cexception
    - :callback

  :unity_helper_path: []            # Paths to custom UNITY_TEST_ASSERT_EQUAL_* headers

  :includes: []
  :includes_h_pre_orig_header: []
  :includes_h_post_orig_header: []
  :includes_c_pre_header: []
  :includes_c_post_header: []
```

### CMock C-Level Defines

```c
#define CMOCK_MEM_STATIC              // Fixed-size pool (default)
#define CMOCK_MEM_DYNAMIC             // Heap-allocated chunks
#define CMOCK_MEM_SIZE     (32768)    // Pool size in bytes
#define CMOCK_MEM_ALIGN    2          // 0=none, 1=uint16, 2=uint32, 3=uint64
#define CMOCK_MEM_PTR_AS_INT unsigned long
#define CMOCK_MEM_INDEX_TYPE size_t
```

## CException Configuration

Enable in project.yml:

```yaml
:project:
  :use_exceptions: TRUE
```

### C-Level Configuration Defines

```c
#define CEXCEPTION_T             unsigned int  // Exception ID type
#define CEXCEPTION_NONE          (0x5A5A5A5A)  // "No exception" sentinel
#define CEXCEPTION_NUM_ID        (1)           // Number of tasks (RTOS)
#define CEXCEPTION_GET_ID        (0)           // Current task ID expression
#define CEXCEPTION_NO_CATCH_HANDLER(id)        // Handler for uncaught throws

// Hooks (all default empty):
#define CEXCEPTION_HOOK_START_TRY
#define CEXCEPTION_HOOK_HAPPY_TRY
#define CEXCEPTION_HOOK_AFTER_TRY
#define CEXCEPTION_HOOK_START_CATCH

#define CEXCEPTION_USE_CONFIG_FILE             // Include CExceptionConfig.h
```

## Libraries Configuration

```yaml
:paths:
  :libraries:
    - third_party/lib               # -L search paths

:libraries:
  :system:                          # Both test and release
    - m                             # -lm
    - pthread                       # -lpthread
  :test:
    - test/stub_comm.a              # Test-only library
  :release:
    - release/comms.a               # Production library
  :flag: "-l${1}"                   # Library flag format
  :path_flag: "-L ${1}"             # Path flag format
  :placement: :end                  # :start or :end in link command
```

## Plugins

### Built-in Plugins (1.0.0 names)

| Plugin | Purpose |
|--------|---------|
| `report_tests_pretty_stdout` | Formatted test results (recommended) |
| `report_tests_ide_stdout` | IDE-friendly clickable output |
| `report_tests_gtestlike_stdout` | Google Test-style output |
| `report_tests_teamcity_stdout` | TeamCity CI messages |
| `report_tests_log_factory` | JSON/JUnit/HTML report files |
| `report_tests_raw_output_log` | Raw executable output log |
| `report_build_warnings_log` | Compiler warnings log |
| `gcov` | GCC code coverage |
| `module_generator` | Create src/header/test triplets |
| `compile_commands_json_db` | `compile_commands.json` for clangd/LSP |
| `command_hooks` | Hook scripts to build events |
| `dependencies` | External library management |
| `fff` | FFF fake functions (alternative to CMock) |

### Plugin Configuration

```yaml
:plugins:
  :load_paths:
    - project/plugins               # Custom plugin directories
  :enabled:
    - report_tests_pretty_stdout
    - module_generator
    - gcov
    - compile_commands_json_db

:gcov:
  :summaries: TRUE
  :report_task: FALSE
  :utilities:
    - gcovr
  :reports:
    - HtmlBasic
  :gcovr:
    :html_medium_threshold: 75
    :html_high_threshold: 90

:report_tests_log_factory:
  :reports:
    - json
    - junit
    - html

:module_generator:
  :project_root: ./
  :source_root: src/
  :inc_root: include/
  :test_root: test/
  :naming: :snake                   # :bumpy, :camel, :caps, :snake
```

## Mixins

Composable YAML configurations (1.0.0 feature). Mixins are deep-merged into base config.

```yaml
# In project.yml:
:mixins:
  :enabled:
    - clang_toolchain               # Finds clang_toolchain.yml in load_paths
    - ci_settings.yml               # Direct filepath
  :load_paths:
    - project/mixins
```

### Usage

```bash
ceedling --mixin=mixins/clang.yml test:all
ceedling --mixin=mixins/clang.yml --mixin=mixins/asan.yml test:all

# Via environment:
CEEDLING_MIXIN_1=mixins/clang.yml ceedling test:all
```

### Multi-Toolchain Pattern

```
project/
├── project.yml              # Base config (GCC default)
└── mixins/
    ├── clang.yml            # Override tools for Clang
    ├── cross_arm.yml        # ARM cross-compilation
    ├── asan.yml             # AddressSanitizer
    └── ci.yml               # CI-specific settings
```

## Commands Reference

### Application Commands

```bash
ceedling version                              # Show versions
ceedling new my_project                       # Create project skeleton
ceedling new my_project --local               # With vendored Ceedling
ceedling examples                             # List example projects
ceedling example temp_sensor                  # Extract example
ceedling dumpconfig                           # Show resolved configuration
ceedling environment                          # Show environment variables
```

### Build Tasks

```bash
ceedling test:all                             # Run all tests
ceedling test:foo                             # Run tests for module 'foo'
ceedling "test:pattern[Init]"                 # Tests matching pattern
ceedling "test:path[drivers/uart]"            # Tests in path
ceedling test:foo --test-case=configure       # Filter test cases
ceedling test:foo --exclude_test_case=slow    # Exclude test cases

ceedling release                              # Build release artifact

ceedling gcov:all                             # Run with coverage
ceedling gcov:foo                             # Coverage for module

ceedling 'module:create[foo]'                 # Create module triplet
ceedling 'module:destroy[foo]'                # Remove module

ceedling clean                                # Delete compiled artifacts
ceedling clobber                              # Delete all generated files

ceedling files:test                           # List test files
ceedling files:source                         # List source files
ceedling paths:include                        # List include paths
```

### Verbosity and Options

```bash
ceedling --verbosity=obnoxious test:all       # Maximum verbosity
ceedling --verbosity=errors test:all          # Errors only
# Options: silent, errors, warnings, normal (default), obnoxious, debug

ceedling --log test:all                       # Log to file
ceedling --project=other.yml test:all         # Custom project file
```

## Complete Examples

### Minimal project.yml

```yaml
---
:project:
  :build_root: build/
  :use_mocks: TRUE

:paths:
  :source:
    - src/**
  :test:
    - test/**
  :include:
    - src/**
```

### Clang + Sanitizers + Coverage

```yaml
---
:project:
  :build_root: build/
  :use_mocks: TRUE
  :use_exceptions: TRUE
  :use_test_preprocessor: :mocks
  :compile_threads: :auto
  :test_threads: :auto

:paths:
  :test:
    - test/**
  :source:
    - src/**
  :include:
    - src/**
    - include/**
  :support:
    - test/support

:defines:
  :test:
    - TEST
    - UNITY_INCLUDE_EXEC_TIME
  :release:
    - NDEBUG

:flags:
  :test:
    :compile:
      :*:
        - -std=c11
        - -Wall
        - -Wextra
        - -Wpedantic
        - -Wno-unused-parameter
        - -fsanitize=address,undefined
        - -fno-omit-frame-pointer
        - -O1
        - -g
    :link:
      :*:
        - -fsanitize=address,undefined

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

:cmock:
  :mock_prefix: mock_
  :enforce_strict_ordering: true
  :plugins:
    - :ignore
    - :ignore_arg
    - :return_thru_ptr
    - :callback
    - :cexception

:plugins:
  :enabled:
    - report_tests_pretty_stdout
    - module_generator
    - gcov
    - compile_commands_json_db
```

### Cross-Compilation (Host Tests + ARM Release)

```yaml
---
:project:
  :build_root: build/
  :release_build: TRUE
  :use_mocks: TRUE

:paths:
  :source:
    - src/**
  :test:
    - test/**
  :include:
    - src/**
    - include/**
  :support:
    - test/support

:defines:
  :test:
    - TEST
    - HOST_TEST_BUILD
  :release:
    - STM32F407xx
    - USE_HAL_DRIVER

:flags:
  :test:
    :compile:
      - -std=c99
      - -Wall
      - -Wextra
  :release:
    :compile:
      - -std=c99

# Test builds use default GCC (host); release uses ARM toolchain
:tools:
  :release_compiler:
    :executable: arm-none-eabi-gcc
    :arguments:
      - -I"${5}"
      - -D"${6}"
      - -mcpu=cortex-m4
      - -mthumb
      - -mfloat-abi=hard
      - -mfpu=fpv4-sp-d16
      - -Os
      - -ffunction-sections
      - -fdata-sections
      - -c "${1}"
      - -o "${2}"
      - -MMD
      - -MF "${4}"

  :release_linker:
    :executable: arm-none-eabi-gcc
    :arguments:
      - -mcpu=cortex-m4
      - -mthumb
      - -mfloat-abi=hard
      - -mfpu=fpv4-sp-d16
      - -T platform/stm32f4.ld
      - -Wl,-Map="${3}",--cref
      - -Wl,--gc-sections
      - "${1}"
      - "${5}"
      - -o "${2}"
      - "${4}"

:release_build:
  :output: firmware.elf

:plugins:
  :enabled:
    - report_tests_pretty_stdout
    - module_generator
```
