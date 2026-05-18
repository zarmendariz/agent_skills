# Troubleshooting Guide

## Table of Contents

1. [Ceedling Issues](#ceedling-issues)
2. [Mock Generation Issues](#mock-generation-issues)
3. [Test Compilation Issues](#test-compilation-issues)
4. [Test Execution Issues](#test-execution-issues)
5. [Assertion Failures](#assertion-failures)
6. [Performance Issues](#performance-issues)

## Ceedling Issues

### Issue: "project.yml not found"

**Symptom**: Error when running `ceedling test:all`

**Cause**: Ceedling cannot find `project.yml` in current directory

**Solution**:
```bash
# Verify project.yml exists
ls -la project.yml

# Run from project root
cd /path/to/project
ceedling test:all

# Or specify project file
ceedling -p /path/to/project.yml test:all
```

### Issue: "Ceedling command not found"

**Symptom**: `ceedling: command not found`

**Cause**: Ceedling not installed or not in PATH

**Solution**:
```bash
# Install Ceedling (requires Ruby)
gem install ceedling

# Verify installation
ceedling version

# Or use bundler
bundle exec ceedling test:all
```

### Issue: "Build directory permission denied"

**Symptom**: Error creating build artifacts

**Cause**: Insufficient permissions on build directory

**Solution**:
```bash
# Check permissions
ls -la build/

# Fix permissions
chmod -R 755 build/

# Or remove and let Ceedling recreate
rm -rf build/
ceedling test:all
```

## Mock Generation Issues

### Issue: "Mock generation failed"

**Symptom**: CMock fails to generate mock files

**Cause**: Invalid function prototypes or syntax errors in header files

**Solution**:
```c
// Wrong: Missing return type
void function_name(int param);

// Correct: Explicit return type
int function_name(int param);

// Wrong: Incomplete parameter list
void function_name();

// Correct: Explicit void parameter
void function_name(void);
```

### Issue: "when_no_prototypes: warn" warnings

**Symptom**: CMock warnings about missing prototypes

**Cause**: Function declarations missing from header files

**Solution**:

In `project.yml`:
```yaml
:cmock:
  :when_no_prototypes: :error  # Fail on missing prototypes
```

Then fix header files:
```c
// hal_gpio.h
#ifndef HAL_GPIO_H
#define HAL_GPIO_H

// Add missing prototypes
void hal_gpio_init(void);
void hal_gpio_set_pin(uint8_t pin);
void hal_gpio_clear_pin(uint8_t pin);

#endif
```

### Issue: "Undefined reference to mock_*"

**Symptom**: Linker error for mock functions

**Cause**: Mock header not included in test file

**Solution**:
```c
// test_module.c
#include "unity.h"
#include "module_under_test.h"
#include "mock_dependency.h"  // Add this!

void test_something(void)
{
    dependency_function_Expect();
    module_under_test();
}
```

### Issue: "Mock function not called as expected"

**Symptom**: Test fails with "Expected call not made"

**Cause**: Function name mismatch or incorrect mock prefix

**Solution**:

Check `project.yml`:
```yaml
:cmock:
  :mock_prefix: mock_  # Verify prefix
```

Verify function name:
```c
// If header has: void uart_send(uint8_t byte);
// Mock function is: uart_send_Expect(byte);
// NOT: uart_send_byte_Expect(byte);

uart_send_Expect(0x42);  // Correct
uart_send_byte_Expect(0x42);  // Wrong!
```

## Test Compilation Issues

### Issue: "Undefined reference to function"

**Symptom**: Linker error for production code

**Cause**: Source file not included in build

**Solution**:

In `project.yml`:
```yaml
:paths:
  :source:
    - src/**
    - src/drivers/**  # Add missing path
```

Or verify file exists:
```bash
find src -name "*.c" | grep function_name
```

### Issue: "Conflicting types for function"

**Symptom**: Compilation error about type mismatch

**Cause**: Function declared differently in header and source

**Solution**:
```c
// module.h
int calculate(int a, int b);

// module.c
int calculate(int a, int b)  // Must match header exactly
{
    return a + b;
}

// Wrong:
float calculate(int a, int b)  // Type mismatch!
{
    return a + b;
}
```

### Issue: "Include file not found"

**Symptom**: Compilation error about missing header

**Cause**: Include path not configured

**Solution**:

In `project.yml`:
```yaml
:paths:
  :support:
    - test/support/**
    - vendor/unity/src/**  # Add missing path
```

Or use absolute paths:
```c
#include "unity.h"
#include "module.h"
#include "mock_dependency.h"
```

### Issue: "Redefinition of function"

**Symptom**: Compilation error about duplicate definitions

**Cause**: Header guard missing or multiple includes

**Solution**:
```c
// module.h
#ifndef MODULE_H
#define MODULE_H

void function(void);

#endif  // MODULE_H
```

## Test Execution Issues

### Issue: "Segmentation fault"

**Symptom**: Test crashes with segfault

**Cause**: Null pointer dereference or memory corruption

**Solution**:
```c
// Wrong: Dereferencing null pointer
void test_function(void)
{
    int *ptr = NULL;
    int value = *ptr;  // Segfault!
}

// Correct: Check for null
void test_function(void)
{
    int *ptr = NULL;
    TEST_ASSERT_NULL(ptr);
}
```

### Issue: "Test hangs/infinite loop"

**Symptom**: Test never completes

**Cause**: Infinite loop in code or mock

**Solution**:
```bash
# Run with timeout
timeout 5 ceedling test:module_name

# Or add watchdog in test
void test_with_timeout(void)
{
    // Set timeout
    TEST_IGNORE_MESSAGE("Timeout protection needed");
}
```

### Issue: "Mock expectation not met"

**Symptom**: Test fails with "Expected call not made"

**Cause**: Function not called or called with wrong arguments

**Solution**:
```c
// Wrong: Expectation set but function not called
void test_function(void)
{
    hardware_init_Expect();
    // module_init() not called!
}

// Correct: Call the function
void test_function(void)
{
    hardware_init_Expect();
    module_init();  // Now it's called
}
```

### Issue: "Unexpected call to mock function"

**Symptom**: Test fails with "Unexpected call"

**Cause**: Function called but not expected

**Solution**:
```c
// Wrong: Function called but not expected
void test_function(void)
{
    module_process();  // Calls hardware_init internally
    // But hardware_init_Expect() not set!
}

// Correct: Set expectation
void test_function(void)
{
    hardware_init_Expect();
    module_process();
}
```

## Assertion Failures

### Issue: "Expected X but was Y"

**Symptom**: Assertion fails with value mismatch

**Cause**: Function returns unexpected value

**Solution**:
```c
// Debug: Print actual value
void test_calculate(void)
{
    int result = calculate(5, 3);
    printf("Result: %d\n", result);  // See actual value
    TEST_ASSERT_EQUAL(8, result);
}

// Or use better assertion
TEST_ASSERT_EQUAL_INT(8, result);
TEST_ASSERT_EQUAL_HEX(0x08, result);
```

### Issue: "Pointer comparison failed"

**Symptom**: Pointer assertion fails unexpectedly

**Cause**: Comparing different pointer values

**Solution**:
```c
// Wrong: Different pointers
void test_buffer(void)
{
    uint8_t buffer1[] = {1, 2, 3};
    uint8_t buffer2[] = {1, 2, 3};
    TEST_ASSERT_EQUAL_PTR(buffer1, buffer2);  // Fails!
}

// Correct: Compare memory content
void test_buffer(void)
{
    uint8_t buffer1[] = {1, 2, 3};
    uint8_t buffer2[] = {1, 2, 3};
    TEST_ASSERT_EQUAL_MEMORY(buffer1, buffer2, 3);
}
```

### Issue: "String comparison failed"

**Symptom**: String assertion fails

**Cause**: String content mismatch

**Solution**:
```c
// Wrong: Using EQUAL for strings
void test_string(void)
{
    char *result = get_string();
    TEST_ASSERT_EQUAL("hello", result);  // Wrong!
}

// Correct: Use string comparison
void test_string(void)
{
    char *result = get_string();
    TEST_ASSERT_EQUAL_STRING("hello", result);
}
```

### Issue: "Float comparison failed"

**Symptom**: Float assertion fails due to precision

**Cause**: Floating point precision issues

**Solution**:
```c
// Wrong: Exact float comparison
void test_calculate_float(void)
{
    float result = calculate_pi();
    TEST_ASSERT_EQUAL(3.14159, result);  // May fail!
}

// Correct: Use delta for float comparison
void test_calculate_float(void)
{
    float result = calculate_pi();
    TEST_ASSERT_FLOAT_WITHIN(0.0001, 3.14159, result);
}
```

## Performance Issues

### Issue: "Tests run very slowly"

**Symptom**: Test execution takes too long

**Cause**: Inefficient code or excessive mocking

**Solution**:
```bash
# Profile test execution
time ceedling test:all

# Run specific test
ceedling test:module_name

# Check for slow setUp/tearDown
void setUp(void)
{
    // Minimize initialization
    // Avoid file I/O, network calls
}
```

### Issue: "Build artifacts too large"

**Symptom**: Build directory grows excessively

**Cause**: Debug symbols or optimization settings

**Solution**:

In `project.yml`:
```yaml
:tools:
  :test_compiler:
    :arguments:
      - -g0  # No debug symbols
      - -Os  # Optimize for size
```

Or clean build:
```bash
ceedling clobber
ceedling test:all
```

### Issue: "Memory usage too high"

**Symptom**: Tests consume excessive memory

**Cause**: Large buffers or memory leaks in tests

**Solution**:
```c
// Wrong: Large static buffer
void test_function(void)
{
    uint8_t large_buffer[10000];  // Too much!
}

// Correct: Use smaller buffer
void test_function(void)
{
    uint8_t small_buffer[100];
}

// Or use dynamic allocation
void test_function(void)
{
    uint8_t *buffer = malloc(100);
    // ... test code ...
    free(buffer);
}
```

## Quick Diagnostic Checklist

- [ ] Verify `project.yml` exists and is valid YAML
- [ ] Check all include paths in `project.yml`
- [ ] Verify mock headers are included in test files
- [ ] Check function prototypes match between header and source
- [ ] Verify mock expectations are set before function calls
- [ ] Check for typos in mock function names
- [ ] Verify test file naming follows convention (`test_*.c`)
- [ ] Check for infinite loops or blocking calls
- [ ] Verify memory is properly allocated/freed
- [ ] Check compiler warnings and errors
