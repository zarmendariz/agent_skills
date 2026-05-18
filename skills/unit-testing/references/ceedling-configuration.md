# Ceedling Configuration Reference

## Table of Contents

1. [Project Configuration](#project-configuration)
2. [Paths Configuration](#paths-configuration)
3. [CMock Configuration](#cmock-configuration)
4. [CException Configuration](#cexception-configuration)
5. [Unity Configuration](#unity-configuration)
6. [Compiler Configuration](#compiler-configuration)
7. [Plugins Configuration](#plugins-configuration)
8. [Complete Example](#complete-example)

## Project Configuration

### Basic Project Settings

```yaml
:project:
  :name: my_embedded_project
  :build_root: build/
  :release_build: false
  :test_file_prefix: test_
```

| Setting | Purpose | Default |
|---------|---------|---------|
| `:name:` | Project name (used in reports) | Required |
| `:build_root:` | Directory for build artifacts | `build/` |
| `:release_build:` | Enable release build configuration | `false` |
| `:test_file_prefix:` | Prefix for test files | `test_` |

## Paths Configuration

### Directory Structure

```yaml
:paths:
  :test:
    - test/**
    - test/unit/**
  :source:
    - src/**
    - src/drivers/**
  :support:
    - test/support/**
  :libraries:
    - vendor/lib/**
```

| Path | Purpose |
|------|---------|
| `:test:` | Test source files (glob patterns) |
| `:source:` | Production source files |
| `:support:` | Test support files (helpers, fixtures) |
| `:libraries:` | External libraries |

### Glob Pattern Examples

```yaml
:paths:
  :test:
    - test/unit/**           # All files in unit subdirectory
    - test/integration/*.c   # Only .c files in integration
  :source:
    - src/**                 # All files in src
    - src/hal/*.c            # Only .c files in hal
```

## CMock Configuration

### Basic CMock Settings

```yaml
:cmock:
  :mock_prefix: mock_
  :when_no_prototypes: :warn
  :enforce_strict_ordering: true
  :treat_as:
    uint8: HEX8
    uint16: HEX16
    uint32: HEX32
    bool: UINT8
  :plugins:
    - :cexception
```

### CMock Options Reference

| Option | Values | Purpose |
|--------|--------|---------|
| `:mock_prefix:` | string | Prefix for generated mock functions |
| `:when_no_prototypes:` | `:warn`, `:ignore`, `:error` | Behavior when function prototypes missing |
| `:enforce_strict_ordering:` | `true`, `false` | Require mocked calls in exact order |
| `:allow_always_return:` | `true`, `false` | Allow `*_AlwaysReturn()` for mocks |
| `:allow_expect_only:` | `true`, `false` | Allow `*_ExpectOnly()` without return |
| `:allow_expect_calls:` | `true`, `false` | Allow `*_ExpectCalls()` for call counts |

### Type Mapping

```yaml
:cmock:
  :treat_as:
    uint8: HEX8          # Display as hex in test output
    uint16: HEX16
    uint32: HEX32
    int8: INT8
    int16: INT16
    int32: INT32
    bool: UINT8
    status_t: INT
    handle_t: PTR
```

### Plugin Configuration

```yaml
:cmock:
  :plugins:
    - :cexception        # Enable exception handling
    - :ignore_arg        # Allow ignoring specific arguments
    - :return_thru_ptr   # Return values through pointers
```

## CException Configuration

### Enable Exception Handling

```yaml
:cexception:
  :enabled: true
```

### Exception Codes

Define custom exception codes in a header file:

```c
// exception_codes.h
#define EXCEPTION_INVALID_INPUT    1
#define EXCEPTION_TIMEOUT          2
#define EXCEPTION_BUFFER_OVERFLOW  3
#define EXCEPTION_HARDWARE_ERROR   4
```

Then reference in tests:

```c
#include "exception_codes.h"

void test_throws_on_invalid_input(void)
{
    CEXCEPTION_T error;
    Try
    {
        function_under_test(NULL);
        TEST_FAIL_MESSAGE("Expected exception");
    }
    Catch(error)
    {
        TEST_ASSERT_EQUAL(EXCEPTION_INVALID_INPUT, error);
    }
}
```

## Unity Configuration

### Unity Framework Settings

```yaml
:unity:
  :use_exceptions: true
  :verbose: true
  :color: true
```

| Setting | Purpose |
|---------|---------|
| `:use_exceptions:` | Enable exception support |
| `:verbose:` | Verbose test output |
| `:color:` | Colored test output |

## Compiler Configuration

### GCC Configuration Example

```yaml
:tools:
  :test_compiler:
    :executable: gcc
    :arguments:
      - -c
      - "${1}"
      - -o "${2}"
      - -Wall
      - -Wextra
      - -pedantic
      - -std=c99
      - -I"${3}"
      - -DTEST
      - -DDEBUG
      - -g
      - -O0
  
  :test_linker:
    :executable: gcc
    :arguments:
      - "${1}"
      - -o "${2}"
      - -lm
```

### Compiler Flags Explained

| Flag | Purpose |
|------|---------|
| `-Wall` | Enable all warnings |
| `-Wextra` | Enable extra warnings |
| `-pedantic` | Strict C standard compliance |
| `-std=c99` | Use C99 standard |
| `-I"${3}"` | Include paths |
| `-DTEST` | Define TEST macro |
| `-g` | Include debug symbols |
| `-O0` | No optimization (for testing) |

## Plugins Configuration

### Available Plugins

```yaml
:plugins:
  :load_paths:
    - vendor/ceedling/plugins
  :enabled:
    - stdout_pretty_tests_report
    - module_generator
    - gcov
```

### Plugin Descriptions

| Plugin | Purpose |
|--------|---------|
| `stdout_pretty_tests_report` | Pretty-printed test output |
| `module_generator` | Generate test module templates |
| `gcov` | Code coverage analysis |
| `xml_tests_report` | XML test report generation |

## Complete Example

### Minimal project.yml

```yaml
---
:project:
  :name: embedded_project
  :build_root: build/

:paths:
  :test:
    - test/**
  :source:
    - src/**
  :support:
    - test/support/**

:defines:
  :test:
    - TEST

:cmock:
  :mock_prefix: mock_
  :enforce_strict_ordering: true
  :plugins:
    - :cexception

:cexception:
  :enabled: true

:unity:
  :use_exceptions: true

:tools:
  :test_compiler:
    :executable: gcc
    :arguments:
      - -c
      - "${1}"
      - -o "${2}"
      - -Wall
      - -Wextra
      - -std=c99
      - -I"${3}"

:plugins:
  :enabled:
    - stdout_pretty_tests_report
```

### Production-Ready project.yml

```yaml
---
:project:
  :name: stm32_firmware
  :build_root: build/
  :release_build: false
  :test_file_prefix: test_

:environment:
  :path:
    - /usr/bin
    - /usr/local/bin
    - /opt/gcc-arm/bin

:extension:
  :executable: .elf

:paths:
  :test:
    - test/unit/**
    - test/integration/**
  :source:
    - src/**
    - src/hal/**
    - src/drivers/**
  :support:
    - test/support/**
    - test/fixtures/**
  :libraries:
    - vendor/cmsis/**

:defines:
  :test:
    - TEST
    - UNITY_INCLUDE_PRINT_FORMATTED
    - DEBUG
    - STM32L476xx
  :release:
    - NDEBUG
    - STM32L476xx

:cmock:
  :mock_prefix: mock_
  :when_no_prototypes: :warn
  :enforce_strict_ordering: true
  :allow_expect_only: true
  :treat_as:
    uint8_t: HEX8
    uint16_t: HEX16
    uint32_t: HEX32
    int8_t: INT8
    int16_t: INT16
    int32_t: INT32
    bool: UINT8
    HAL_StatusTypeDef: INT
  :plugins:
    - :cexception
    - :ignore_arg
    - :return_thru_ptr

:cexception:
  :enabled: true

:unity:
  :use_exceptions: true
  :verbose: true
  :color: true

:tools:
  :test_compiler:
    :executable: arm-none-eabi-gcc
    :arguments:
      - -c
      - "${1}"
      - -o "${2}"
      - -mcpu=cortex-m4
      - -mthumb
      - -Wall
      - -Wextra
      - -pedantic
      - -std=c99
      - -I"${3}"
      - -ffunction-sections
      - -fdata-sections
  
  :test_linker:
    :executable: arm-none-eabi-gcc
    :arguments:
      - "${1}"
      - -o "${2}"
      - -mcpu=cortex-m4
      - -mthumb
      - -Wl,--gc-sections
      - -lm

:plugins:
  :load_paths:
    - vendor/ceedling/plugins
  :enabled:
    - stdout_pretty_tests_report
    - module_generator
    - gcov
    - xml_tests_report
```

## Troubleshooting Configuration

### Mock Generation Issues

**Problem**: "when_no_prototypes" warnings

```yaml
:cmock:
  :when_no_prototypes: :error  # Fail on missing prototypes
```

**Problem**: Strict ordering conflicts

```yaml
:cmock:
  :enforce_strict_ordering: false  # Allow any order
```

### Compiler Issues

**Problem**: Include path errors

```yaml
:paths:
  :support:
    - test/support/**
    - vendor/unity/src/**
```

**Problem**: Undefined reference errors

```yaml
:tools:
  :test_linker:
    :arguments:
      - "${1}"
      - -o "${2}"
      - -lm  # Link math library
      - -lpthread  # Link pthread if needed
```
