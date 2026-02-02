---
name: unit-testing
description: Comprehensive guide for unit testing embedded C code using Unity, CMock, and CException with Ceedling integration. Use when creating new test modules, test groups, individual unit tests, configuring test runners, setting up mocks for hardware dependencies, or implementing best practices for embedded software testing. Includes context-aware guidance for both Ceedling-based and manual test-runner approaches.
---

# Embedded C Unit Testing

## Overview

This skill provides comprehensive guidance for unit testing embedded C code using the Unity testing framework, CMock for mocking, CException for exception handling, and Ceedling as the build automation tool. It covers creating test modules, organizing test groups, writing individual tests, configuring mocks for hardware dependencies, and best practices specific to embedded systems.

## Core Concepts

### The Testing Stack

- **Unity**: Lightweight C testing framework designed for embedded systems
- **CMock**: Automatic mock generation for C functions and dependencies
- **CException**: Exception handling framework for C (optional but recommended)
- **Ceedling**: Build automation tool that orchestrates Unity, CMock, and CException

### Test Organization Hierarchy

```
Project
├── test/
│   ├── test_module_a.c          # Test module for module_a
│   ├── test_module_b.c          # Test module for module_b
│   └── support/
│       └── test_types.h         # Shared test types and helpers
├── src/
│   ├── module_a.c
│   ├── module_a.h
│   ├── module_b.c
│   └── module_b.h
└── project.yml                  # Ceedling configuration
```

## Workflow Decision Tree

**Starting point:** What do you need to do?

1. **Setting up a new project?** → See [Ceedling Configuration](#ceedling-configuration)
2. **Creating a new test module?** → See [Creating Test Modules](#creating-test-modules)
3. **Adding tests to existing module?** → See [Test Groups and Individual Tests](#test-groups-and-individual-tests)
4. **Mocking hardware/external dependencies?** → See [CMock Best Practices](#cmock-best-practices)
5. **Handling errors and exceptions?** → See [CException Integration](#cexception-integration)
6. **Running tests?** → See [Running Tests](#running-tests)

## Ceedling Configuration

### Initial Setup

Create a `project.yml` file in your project root:

```yaml
---
:project:
  :name: my_embedded_project
  :build_root: build/
  :release_build: false

:environment:
  :path:
    - /usr/bin
    - /usr/local/bin

:extension:
  :executable: .out

:paths:
  :test:
    - test/**
  :source:
    - src/**
  :support:
    - test/support/**
  :libraries: []

:defines:
  :test:
    - TEST
    - UNITY_INCLUDE_PRINT_FORMATTED

:cmock:
  :mock_prefix: mock_
  :when_no_prototypes: :warn
  :enforce_strict_ordering: true
  :plugins:
    - :cexception
  :treat_as:
    uint8: HEX8
    uint16: HEX16
    uint32: HEX32

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
      - -pedantic
      - -std=c99
      - -I"${3}"

:plugins:
  :load_paths:
    - vendor/ceedling/plugins
  :enabled:
    - stdout_pretty_tests_report
    - module_generator
```

### Key Configuration Sections

- **`:cmock:`** - Controls mock generation behavior
  - `:mock_prefix:` - Prefix for generated mock functions (default: `mock_`)
  - `:enforce_strict_ordering:` - Require mocked calls in exact order
  - `:plugins:` - Enable CException support for exception handling

- **`:cexception:`** - Exception handling configuration
  - `:enabled:` - Enable exception support in tests

- **`:unity:`** - Unity framework settings
  - `:use_exceptions:` - Enable exception handling in Unity

## Creating Test Modules

### Step 1: Generate Test Module Structure

Use Ceedling's module generator:

```bash
ceedling module:create[module_name]
```

This creates:
- `src/module_name.c` - Implementation
- `src/module_name.h` - Header
- `test/test_module_name.c` - Test file

### Step 2: Basic Test Module Template

```c
#include "unity.h"
#include "module_name.h"
#include "mock_dependencies.h"  // If mocking external functions

void setUp(void)
{
    // Called before each test
    // Initialize test fixtures, reset state
}

void tearDown(void)
{
    // Called after each test
    // Clean up resources, verify mock expectations
}

// Test groups and individual tests go here
```

### Step 3: Add Test Groups

See [Test Groups and Individual Tests](#test-groups-and-individual-tests) section below.

## Test Groups and Individual Tests

### Organizing Tests with Groups

Group related tests using descriptive function names:

```c
// Test group: Initialization tests
void test_module_init_sets_default_state(void)
{
    module_init();
    TEST_ASSERT_EQUAL(STATE_IDLE, module_get_state());
}

void test_module_init_clears_error_flags(void)
{
    module_init();
    TEST_ASSERT_EQUAL(0, module_get_errors());
}

// Test group: State machine tests
void test_state_transition_from_idle_to_active(void)
{
    module_init();
    module_start();
    TEST_ASSERT_EQUAL(STATE_ACTIVE, module_get_state());
}

void test_state_transition_invalid_from_idle(void)
{
    module_init();
    module_stop();  // Invalid transition
    TEST_ASSERT_EQUAL(STATE_IDLE, module_get_state());
}
```

### Naming Convention

Use descriptive names following this pattern:

```
test_<function_name>_<scenario>_<expected_result>
```

Examples:
- `test_calculate_sum_with_positive_numbers_returns_correct_result`
- `test_uart_send_with_full_buffer_returns_error`
- `test_timer_interrupt_increments_counter`

### Individual Test Structure

```c
void test_function_name(void)
{
    // Arrange: Set up test conditions
    int input = 5;
    int expected = 10;

    // Act: Call the function under test
    int result = function_under_test(input);

    // Assert: Verify the result
    TEST_ASSERT_EQUAL(expected, result);
}
```

### Common Unity Assertions

```c
TEST_ASSERT_EQUAL(expected, actual)
TEST_ASSERT_NOT_EQUAL(not_expected, actual)
TEST_ASSERT_TRUE(condition)
TEST_ASSERT_FALSE(condition)
TEST_ASSERT_NULL(pointer)
TEST_ASSERT_NOT_NULL(pointer)
TEST_ASSERT_EQUAL_STRING(expected_string, actual_string)
TEST_ASSERT_EQUAL_MEMORY(expected_mem, actual_mem, size)
TEST_ASSERT_EQUAL_HEX8(expected, actual)
TEST_ASSERT_EQUAL_HEX16(expected, actual)
TEST_ASSERT_EQUAL_HEX32(expected, actual)
TEST_ASSERT_FLOAT_WITHIN(delta, expected, actual)
```

## CMock Best Practices

### When to Mock

Mock external dependencies:
- Hardware interfaces (GPIO, UART, SPI, I2C)
- External libraries
- System calls
- Functions from other modules (for isolation)

### Generating Mocks

Ceedling automatically generates mocks for headers listed in test files:

```c
#include "unity.h"
#include "module_under_test.h"
#include "mock_hardware_driver.h"  // Ceedling generates mock_hardware_driver.c/h
```

### Mock Function Patterns

#### 1. Expect a Function to Be Called

```c
void test_module_calls_hardware_init(void)
{
    // Arrange: Expect hardware_init to be called exactly once
    hardware_init_Expect();

    // Act
    module_init();

    // Assert: Verified automatically by CMock
}
```

#### 2. Expect Function with Specific Arguments

```c
void test_module_sends_correct_data_to_uart(void)
{
    // Arrange: Expect uart_send with specific data
    uart_send_Expect(0x42);

    // Act
    module_send_command(0x42);

    // Assert: Verified automatically
}
```

#### 3. Return Values from Mocked Functions

```c
void test_module_handles_sensor_reading(void)
{
    // Arrange: Mock sensor_read to return specific value
    sensor_read_ExpectAndReturn(42);

    // Act
    int result = module_process_sensor();

    // Assert
    TEST_ASSERT_EQUAL(42, result);
}
```

#### 4. Callback Functions (Complex Behavior)

```c
void test_module_processes_interrupt_data(void)
{
    // Arrange: Set up callback to simulate interrupt behavior
    void interrupt_callback(uint8_t data)
    {
        // Simulate interrupt processing
    }

    interrupt_handler_StubWithCallback(interrupt_callback);

    // Act
    module_handle_interrupt();

    // Assert
    TEST_ASSERT_EQUAL(PROCESSED, module_get_status());
}
```

#### 5. Verify Call Order (Strict Ordering)

With `:enforce_strict_ordering: true` in `project.yml`:

```c
void test_initialization_sequence(void)
{
    // Arrange: Expect calls in specific order
    hardware_reset_Expect();
    hardware_configure_Expect();
    hardware_enable_Expect();

    // Act
    module_init();

    // Assert: Calls must occur in exact order
}
```

### Mock Configuration in project.yml

```yaml
:cmock:
  :mock_prefix: mock_
  :when_no_prototypes: :warn
  :enforce_strict_ordering: true
  :treat_as:
    uint8: HEX8
    uint16: HEX16
    uint32: HEX32
  :plugins:
    - :cexception
```

## CException Integration

### Enabling Exception Handling

In `project.yml`:

```yaml
:cexception:
  :enabled: true

:unity:
  :use_exceptions: true

:cmock:
  :plugins:
    - :cexception
```

### Testing Exception Scenarios

#### 1. Testing Code That Throws Exceptions

```c
void test_module_throws_on_invalid_input(void)
{
    // Arrange
    CEXCEPTION_T error_code;

    // Act & Assert
    Try
    {
        module_process(NULL);  // Should throw
        TEST_FAIL_MESSAGE("Expected exception not thrown");
    }
    Catch(error_code)
    {
        TEST_ASSERT_EQUAL(ERROR_INVALID_INPUT, error_code);
    }
}
```

#### 2. Testing Exception Propagation

```c
void test_exception_propagates_from_dependency(void)
{
    // Arrange: Mock dependency to throw exception
    dependency_function_ExpectAndThrow(EXCEPTION_TIMEOUT);

    // Act & Assert
    CEXCEPTION_T error_code;
    Try
    {
        module_call_dependency();
        TEST_FAIL_MESSAGE("Expected exception not thrown");
    }
    Catch(error_code)
    {
        TEST_ASSERT_EQUAL(EXCEPTION_TIMEOUT, error_code);
    }
}
```

#### 3. Testing Exception Handling

```c
void test_module_recovers_from_exception(void)
{
    // Arrange
    module_init();

    // Act: Trigger exception and verify recovery
    CEXCEPTION_T error_code;
    Try
    {
        module_process_risky_operation();
    }
    Catch(error_code)
    {
        module_recover_from_error(error_code);
    }

    // Assert: Module is in valid state
    TEST_ASSERT_EQUAL(STATE_READY, module_get_state());
}
```

## Running Tests

### Using Ceedling

```bash
# Run all tests
ceedling test:all

# Run tests for specific module
ceedling test:module_name

# Run with verbose output
ceedling test:all --verbose

# Generate coverage report
ceedling clobber test:all gcov:all utils:gcov

# Run specific test file
ceedling test:test_module_name
```

### Test Execution Flow

1. **Compilation**: Ceedling compiles test files with mocks
2. **Linking**: Links test executable with Unity framework
3. **Execution**: Runs test executable
4. **Reporting**: Generates test report with pass/fail status

### Interpreting Test Output

```
test/test_module_a.c:42:test_function_returns_correct_value PASS
test/test_module_a.c:50:test_function_handles_error PASS
test/test_module_b.c:15:test_state_machine_transition FAIL
  Expected 5 but was 3

-----------------------
3 Tests 2 Passed 1 Failed
```

## Best Practices for Embedded Testing

### 1. Test Isolation

- Each test should be independent
- Use `setUp()` and `tearDown()` for initialization/cleanup
- Mock all external dependencies
- Avoid shared state between tests

### 2. Hardware Abstraction

Create hardware abstraction layers (HAL) to enable testing:

```c
// hal_gpio.h
void hal_gpio_set(uint8_t pin, uint8_t state);
uint8_t hal_gpio_get(uint8_t pin);

// In tests, mock hal_gpio functions
#include "mock_hal_gpio.h"
```

### 3. Testable Code Patterns

**Avoid:**
```c
void process_sensor(void)
{
    int value = read_adc();  // Hard to test - direct hardware access
    if (value > THRESHOLD) {
        set_output_pin();
    }
}
```

**Prefer:**
```c
void process_sensor(int sensor_value)  // Accept as parameter
{
    if (sensor_value > THRESHOLD) {
        set_output_pin();
    }
}

// In tests
void test_process_sensor_sets_output_when_above_threshold(void)
{
    set_output_pin_Expect();
    process_sensor(THRESHOLD + 1);
}
```

### 4. Test Coverage

- Aim for >80% code coverage
- Test happy paths, error cases, and edge cases
- Use Ceedling's gcov integration for coverage reports

```bash
ceedling clobber test:all gcov:all utils:gcov
```

### 5. Fixture Management

```c
void setUp(void)
{
    // Initialize module state
    module_init();

    // Reset mock expectations
    mock_dependency_Init();
}

void tearDown(void)
{
    // Verify all mock expectations were met
    mock_dependency_Verify();

    // Clean up resources
    module_cleanup();
}
```

## Reference Documentation

For detailed information on specific topics, see:

- **[Ceedling Configuration](references/ceedling-configuration.md)** - Comprehensive Ceedling settings and options
- **[CMock Advanced Patterns](references/cmock-patterns.md)** - Complex mocking scenarios and patterns
- **[Test Examples](references/test-examples.md)** - Real-world test examples for common embedded scenarios
- **[Troubleshooting](references/troubleshooting.md)** - Common issues and solutions

## Quick Reference

### Test Module Creation Checklist

- [ ] Create test file: `test/test_module_name.c`
- [ ] Include Unity header: `#include "unity.h"`
- [ ] Include module under test: `#include "module_name.h"`
- [ ] Include mocks for dependencies: `#include "mock_*.h"`
- [ ] Implement `setUp()` function
- [ ] Implement `tearDown()` function
- [ ] Write test functions following naming convention
- [ ] Run tests: `ceedling test:module_name`

### Mock Setup Checklist

- [ ] Identify external dependencies
- [ ] Add mock includes to test file
- [ ] Configure CMock in `project.yml`
- [ ] Use `*_Expect()` for function calls
- [ ] Use `*_ExpectAndReturn()` for return values
- [ ] Use `*_ExpectAndThrow()` for exceptions
- [ ] Verify mock expectations in `tearDown()`

### Exception Handling Checklist

- [ ] Enable CException in `project.yml`
- [ ] Use `Try/Catch` blocks in tests
- [ ] Mock functions to throw with `*_ExpectAndThrow()`
- [ ] Verify exception codes with `TEST_ASSERT_EQUAL()`
- [ ] Test recovery paths after exceptions
