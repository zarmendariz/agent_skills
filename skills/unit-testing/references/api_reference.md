# Unity / CMock / CException API Reference

Complete API reference for the ThrowTheSwitch embedded C testing ecosystem.

## Table of Contents

1. [Unity Assertions](#unity-assertions)
2. [Unity Configuration](#unity-configuration)
3. [Unity Test Runners](#unity-test-runners)
4. [CMock Generated Functions](#cmock-generated-functions)
5. [CMock Plugins](#cmock-plugins)
6. [CMock Configuration](#cmock-configuration)
7. [CException API](#cexception-api)
8. [CException Configuration](#cexception-configuration)

## Unity Assertions

All assertions support a `_MESSAGE` suffix: `TEST_ASSERT_EQUAL_INT_MESSAGE(exp, act, "msg")`

### Control Flow

```c
TEST_FAIL()                     // Immediately fail
TEST_FAIL_MESSAGE("msg")        // Fail with message
TEST_PASS()                     // Abort test, count as pass
TEST_PASS_MESSAGE("msg")
TEST_IGNORE()                   // Mark test as ignored
TEST_IGNORE_MESSAGE("msg")
TEST_MESSAGE("msg")             // Print info without ending test
```

### Boolean

```c
TEST_ASSERT(condition)
TEST_ASSERT_TRUE(condition)
TEST_ASSERT_FALSE(condition)
TEST_ASSERT_UNLESS(condition)       // Alias for FALSE
TEST_ASSERT_NULL(pointer)
TEST_ASSERT_NOT_NULL(pointer)
TEST_ASSERT_EMPTY(pointer)          // *pointer == 0
TEST_ASSERT_NOT_EMPTY(pointer)      // *pointer != 0
```

### Integer Equality

```c
// Signed (decimal display)
TEST_ASSERT_EQUAL_INT(expected, actual)
TEST_ASSERT_EQUAL_INT8(expected, actual)
TEST_ASSERT_EQUAL_INT16(expected, actual)
TEST_ASSERT_EQUAL_INT32(expected, actual)
TEST_ASSERT_EQUAL_INT64(expected, actual)

// Unsigned (decimal display)
TEST_ASSERT_EQUAL_UINT(expected, actual)
TEST_ASSERT_EQUAL_UINT8(expected, actual)
TEST_ASSERT_EQUAL_UINT16(expected, actual)
TEST_ASSERT_EQUAL_UINT32(expected, actual)
TEST_ASSERT_EQUAL_UINT64(expected, actual)

// Hex display
TEST_ASSERT_EQUAL_HEX(expected, actual)
TEST_ASSERT_EQUAL_HEX8(expected, actual)
TEST_ASSERT_EQUAL_HEX16(expected, actual)
TEST_ASSERT_EQUAL_HEX32(expected, actual)
TEST_ASSERT_EQUAL_HEX64(expected, actual)

// Character (printable chars, otherwise hex)
TEST_ASSERT_EQUAL_CHAR(expected, actual)

// Shorthand (behavior set by UNITY_SHORTHAND_AS_*)
TEST_ASSERT_EQUAL(expected, actual)
TEST_ASSERT_NOT_EQUAL(expected, actual)
```

### Inequality

```c
TEST_ASSERT_NOT_EQUAL_INT(threshold, actual)
TEST_ASSERT_NOT_EQUAL_UINT(threshold, actual)
// ...and all INT8/INT16/INT32/INT64/UINT8/UINT16/UINT32/UINT64 variants
```

### Comparison (Greater/Less Than)

Available for all integer sizes (INT, INT8..INT64, UINT, UINT8..UINT64, HEX8..HEX64, CHAR):

```c
TEST_ASSERT_GREATER_THAN(threshold, actual)
TEST_ASSERT_GREATER_THAN_INT(threshold, actual)
TEST_ASSERT_GREATER_THAN_INT8(threshold, actual)
// ...etc for all sizes

TEST_ASSERT_GREATER_OR_EQUAL(threshold, actual)
TEST_ASSERT_LESS_THAN(threshold, actual)
TEST_ASSERT_LESS_OR_EQUAL(threshold, actual)
// ...with all size variants
```

### Range (Within)

Asserts `|actual - expected| <= delta`:

```c
TEST_ASSERT_INT_WITHIN(delta, expected, actual)
TEST_ASSERT_INT8_WITHIN(delta, expected, actual)
TEST_ASSERT_INT16_WITHIN(delta, expected, actual)
TEST_ASSERT_INT32_WITHIN(delta, expected, actual)
TEST_ASSERT_INT64_WITHIN(delta, expected, actual)
TEST_ASSERT_UINT_WITHIN(delta, expected, actual)
TEST_ASSERT_UINT8_WITHIN(delta, expected, actual)
TEST_ASSERT_UINT16_WITHIN(delta, expected, actual)
TEST_ASSERT_UINT32_WITHIN(delta, expected, actual)
TEST_ASSERT_UINT64_WITHIN(delta, expected, actual)
TEST_ASSERT_HEX_WITHIN(delta, expected, actual)
TEST_ASSERT_HEX8_WITHIN(delta, expected, actual)
TEST_ASSERT_HEX16_WITHIN(delta, expected, actual)
TEST_ASSERT_HEX32_WITHIN(delta, expected, actual)
TEST_ASSERT_HEX64_WITHIN(delta, expected, actual)
TEST_ASSERT_CHAR_WITHIN(delta, expected, actual)
```

### Bitwise

```c
TEST_ASSERT_BITS(mask, expected, actual)    // Compare masked bits only
TEST_ASSERT_BITS_HIGH(mask, actual)         // All masked bits are set
TEST_ASSERT_BITS_LOW(mask, actual)          // All masked bits are clear
TEST_ASSERT_BIT_HIGH(bit, actual)           // Bit N (0-31) is set
TEST_ASSERT_BIT_LOW(bit, actual)            // Bit N (0-31) is clear
```

### String, Pointer, Memory

```c
TEST_ASSERT_EQUAL_STRING(expected, actual)
TEST_ASSERT_EQUAL_STRING_LEN(expected, actual, len)
TEST_ASSERT_EQUAL_PTR(expected, actual)
TEST_ASSERT_EQUAL_MEMORY(expected, actual, len)     // Raw byte compare
```

### Array Assertions

All take `(expected_array, actual_array, num_elements)`:

```c
TEST_ASSERT_EQUAL_INT_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_INT8_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_INT16_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_INT32_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_INT64_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_UINT_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_UINT8_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_UINT16_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_UINT32_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_UINT64_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_HEX_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_HEX8_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_HEX16_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_HEX32_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_HEX64_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_CHAR_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_PTR_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_STRING_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_MEMORY_ARRAY(expected, actual, len, num_elements)
TEST_ASSERT_EQUAL_FLOAT_ARRAY(expected, actual, num_elements)
TEST_ASSERT_EQUAL_DOUBLE_ARRAY(expected, actual, num_elements)
```

### Array Range Assertions

```c
TEST_ASSERT_INT_ARRAY_WITHIN(delta, expected, actual, num_elements)
TEST_ASSERT_UINT_ARRAY_WITHIN(delta, expected, actual, num_elements)
// ...all size variants...
TEST_ASSERT_FLOAT_ARRAY_WITHIN(delta, expected, actual, num_elements)
TEST_ASSERT_DOUBLE_ARRAY_WITHIN(delta, expected, actual, num_elements)
```

### Each-Equal (Array vs Single Value)

Compare every element against one expected value:

```c
TEST_ASSERT_EACH_EQUAL_INT(expected, actual_array, num_elements)
TEST_ASSERT_EACH_EQUAL_UINT(expected, actual_array, num_elements)
// ...all size variants...
TEST_ASSERT_EACH_EQUAL_PTR(expected, actual_array, num_elements)
TEST_ASSERT_EACH_EQUAL_STRING(expected, actual_array, num_elements)
TEST_ASSERT_EACH_EQUAL_MEMORY(expected, actual_array, len, num_elements)
```

### Float Assertions (requires UNITY_INCLUDE_FLOAT)

```c
TEST_ASSERT_FLOAT_WITHIN(delta, expected, actual)
TEST_ASSERT_FLOAT_NOT_WITHIN(delta, expected, actual)
TEST_ASSERT_EQUAL_FLOAT(expected, actual)       // delta = expected * 0.00001f
TEST_ASSERT_NOT_EQUAL_FLOAT(expected, actual)
TEST_ASSERT_LESS_THAN_FLOAT(threshold, actual)
TEST_ASSERT_GREATER_THAN_FLOAT(threshold, actual)
TEST_ASSERT_LESS_OR_EQUAL_FLOAT(threshold, actual)
TEST_ASSERT_GREATER_OR_EQUAL_FLOAT(threshold, actual)

TEST_ASSERT_FLOAT_IS_INF(actual)
TEST_ASSERT_FLOAT_IS_NEG_INF(actual)
TEST_ASSERT_FLOAT_IS_NAN(actual)
TEST_ASSERT_FLOAT_IS_DETERMINATE(actual)        // Not INF, not NAN
TEST_ASSERT_FLOAT_IS_NOT_INF(actual)
TEST_ASSERT_FLOAT_IS_NOT_NEG_INF(actual)
TEST_ASSERT_FLOAT_IS_NOT_NAN(actual)
TEST_ASSERT_FLOAT_IS_NOT_DETERMINATE(actual)
```

### Double Assertions (requires UNITY_INCLUDE_DOUBLE)

Mirror of float assertions with `DOUBLE` prefix. Default delta = expected * 1e-12.

```c
TEST_ASSERT_DOUBLE_WITHIN(delta, expected, actual)
TEST_ASSERT_DOUBLE_NOT_WITHIN(delta, expected, actual)
TEST_ASSERT_EQUAL_DOUBLE(expected, actual)
TEST_ASSERT_NOT_EQUAL_DOUBLE(expected, actual)
TEST_ASSERT_LESS_THAN_DOUBLE(threshold, actual)
TEST_ASSERT_GREATER_THAN_DOUBLE(threshold, actual)
TEST_ASSERT_LESS_OR_EQUAL_DOUBLE(threshold, actual)
TEST_ASSERT_GREATER_OR_EQUAL_DOUBLE(threshold, actual)

TEST_ASSERT_DOUBLE_IS_INF(actual)
TEST_ASSERT_DOUBLE_IS_NEG_INF(actual)
TEST_ASSERT_DOUBLE_IS_NAN(actual)
TEST_ASSERT_DOUBLE_IS_DETERMINATE(actual)
TEST_ASSERT_DOUBLE_IS_NOT_INF(actual)
TEST_ASSERT_DOUBLE_IS_NOT_NEG_INF(actual)
TEST_ASSERT_DOUBLE_IS_NOT_NAN(actual)
TEST_ASSERT_DOUBLE_IS_NOT_DETERMINATE(actual)
```

## Unity Configuration

All via `#define` (in `unity_config.h` or compiler flags):

### Integer Width

```c
#define UNITY_INT_WIDTH      32      // Bits in int (16, 32)
#define UNITY_LONG_WIDTH     32      // Bits in long (16, 32)
#define UNITY_POINTER_WIDTH  32      // Bits in pointer (16, 32, 64)
#define UNITY_SUPPORT_64            // Force 64-bit support
```

### Float/Double

```c
#define UNITY_INCLUDE_FLOAT         // Enable float assertions
#define UNITY_EXCLUDE_FLOAT         // Disable float assertions
#define UNITY_INCLUDE_DOUBLE        // Enable double assertions
#define UNITY_EXCLUDE_DOUBLE        // Disable double assertions
#define UNITY_FLOAT_PRECISION  0.00001f  // Default delta multiplier
#define UNITY_DOUBLE_PRECISION 1e-12     // Default delta multiplier
#define UNITY_FLOAT_TYPE       float     // Override float type
#define UNITY_DOUBLE_TYPE      double    // Override double type
#define UNITY_EXCLUDE_FLOAT_PRINT       // Save code space
```

### Output Customization

```c
#define UNITY_OUTPUT_CHAR(a)    RS232_putc(a)   // Custom character output
#define UNITY_OUTPUT_FLUSH()    RS232_flush()
#define UNITY_OUTPUT_START()    RS232_config(115200,1,8,0)
#define UNITY_OUTPUT_COMPLETE() RS232_close()
#define UNITY_USE_FLUSH_STDOUT          // Flush stdout after each line
#define UNITY_OUTPUT_COLOR              // ANSI color output
#define UNITY_INCLUDE_PRINT_FORMATTED   // Enable TEST_PRINTF()
```

### IDE Integration

```c
#define UNITY_OUTPUT_FOR_ECLIPSE
#define UNITY_OUTPUT_FOR_IAR_WORKBENCH
#define UNITY_OUTPUT_FOR_QT_CREATOR
```

### Execution Timing

```c
#define UNITY_INCLUDE_EXEC_TIME         // Report per-test time (ms)
#define UNITY_CLOCK_MS  my_timer_fn     // Millisecond timer function
```

### Parameterized Tests

```c
#define UNITY_SUPPORT_TEST_CASES        // Enable TEST_CASE, TEST_RANGE, TEST_MATRIX
```

### Shorthand Behavior

```c
#define UNITY_SHORTHAND_AS_INT          // Cast to int (historical default)
#define UNITY_SHORTHAND_AS_MEM          // Byte-by-byte memory compare
#define UNITY_SHORTHAND_AS_RAW          // Use == directly
#define UNITY_SHORTHAND_AS_NONE         // Disallow shorthand
```

### Standard Header Control

```c
#define UNITY_EXCLUDE_STDINT_H          // Skip stdint.h
#define UNITY_EXCLUDE_LIMITS_H          // Skip limits.h
#define UNITY_EXCLUDE_STDDEF_H          // Provide own NULL
#define UNITY_EXCLUDE_SETJMP            // Disable setjmp (no CMock)
```

### Memory Optimization

```c
#define UNITY_EXCLUDE_DETAILS           // Strip scratchpad (tiny targets)
#define UNITY_PTR_ATTRIBUTE __attribute__((far))  // Near/far pointer
```

## Unity Test Runners

### Manual Runner

```c
#include "unity.h"

void setUp(void)    { /* before each test */ }
void tearDown(void) { /* after each test  */ }

void test_something(void) {
    TEST_ASSERT_EQUAL_INT(42, compute());
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_something);
    return UNITY_END();  // Returns failure count
}
```

### Auto-Generated Runner (Ceedling)

Ceedling automatically generates runners. No manual `main()` needed — just write test functions prefixed with `test_`.

### Unity Fixture (Test Groups)

```c
#include "unity_fixture.h"

TEST_GROUP(MyGroup);

TEST_SETUP(MyGroup) { /* before each test in group */ }
TEST_TEAR_DOWN(MyGroup) { /* after each test in group */ }

TEST(MyGroup, DescriptionOfTest) {
    TEST_ASSERT_EQUAL_INT(1, my_func());
}

TEST_GROUP_RUNNER(MyGroup) {
    RUN_TEST_CASE(MyGroup, DescriptionOfTest);
}

int main(int argc, const char* argv[]) {
    return UnityMain(argc, argv, runAllTests);
}

void runAllTests(void) {
    RUN_TEST_GROUP(MyGroup);
}
```

## CMock Generated Functions

### Always Available (No Plugin Required)

```c
// For: void func(int a, int b)
void func_Expect(int a, int b);

// For: int func(int a, int b)
void func_ExpectAndReturn(int a, int b, int to_return);
```

### Plugin: :expect_any_args

```c
void func_ExpectAnyArgs(void);
void func_ExpectAnyArgsAndReturn(int retval);
```

### Plugin: :array

```c
// depth = number of array elements to compare (0 = pointer compare)
void func_ExpectWithArray(uint8_t* data, int data_depth, int size, int other);
void func_ExpectWithArrayAndReturn(uint8_t* data, int data_depth, int size, int other, int retval);
```

### Plugin: :ignore

```c
void func_Ignore(void);                    // Ignore all calls
void func_IgnoreAndReturn(int retval);     // Ignore, return value (queued)
void func_StopIgnore(void);               // Cancel ignore, restore Expect
```

### Plugin: :ignore_stateless

Same signatures as `:ignore` but `IgnoreAndReturn` always returns the last-set value (not queued).

### Plugin: :ignore_arg

Used after `_Expect` to selectively skip argument validation:

```c
// For: void func(int a, char* b, int c)
void func_IgnoreArg_a(void);
void func_IgnoreArg_b(void);
void func_IgnoreArg_c(void);
```

### Plugin: :return_thru_ptr

For pointer parameters:

```c
// For: BOOL divide(uint num, uint den, uint* result)
void divide_ReturnThruPtr_result(uint* val);
void divide_ReturnArrayThruPtr_result(uint* val, int len);
void divide_ReturnMemThruPtr_result(uint* val, size_t size);
```

### Plugin: :callback

```c
// Callback signature: int (*)(int a, int b, int NumCalls)
void func_AddCallback(CMOCK_func_CALLBACK cb);   // Check args, then call
void func_Stub(CMOCK_func_CALLBACK cb);           // Skip checks, call directly
```

### Plugin: :cexception

```c
void func_ExpectAndThrow(int a, int b, CEXCEPTION_T error);
```

### Complete Reference Table

| Suffix | Plugin | Description |
|--------|--------|-------------|
| `_Expect` | (always) | Expect void-return call with args |
| `_ExpectAndReturn` | (always) | Expect value-return call |
| `_ExpectAnyArgs` | `:expect_any_args` | Expect call, any args |
| `_ExpectAnyArgsAndReturn` | `:expect_any_args` | Expect call, any args, return |
| `_ExpectWithArray` | `:array` | Expect with array depth |
| `_ExpectWithArrayAndReturn` | `:array` | Expect with array depth, return |
| `_ExpectAndThrow` | `:cexception` | Expect and throw exception |
| `_Ignore` | `:ignore` | Ignore all calls |
| `_IgnoreAndReturn` | `:ignore` | Ignore, queue return values |
| `_StopIgnore` | `:ignore` | Cancel ignore |
| `_IgnoreArg_<param>` | `:ignore_arg` | Ignore specific arg after Expect |
| `_ReturnThruPtr_<param>` | `:return_thru_ptr` | Write value through pointer |
| `_ReturnArrayThruPtr_<param>` | `:return_thru_ptr` | Write array through pointer |
| `_ReturnMemThruPtr_<param>` | `:return_thru_ptr` | Write raw bytes through pointer |
| `_AddCallback` | `:callback` | Callback after arg check |
| `_Stub` | `:callback` | Callback, bypass arg check |

## CMock Plugins

### Available Plugins

```yaml
:cmock:
  :plugins:
    - :ignore              # _Ignore, _IgnoreAndReturn, _StopIgnore
    - :ignore_stateless    # Stateless variant of :ignore (cannot use both)
    - :ignore_arg          # _IgnoreArg_<param>
    - :expect_any_args     # _ExpectAnyArgs, _ExpectAnyArgsAndReturn
    - :return_thru_ptr     # _ReturnThruPtr_<param>, _ReturnArrayThruPtr_<param>
    - :array               # _ExpectWithArray, _ExpectWithArrayAndReturn
    - :cexception          # _ExpectAndThrow (requires CException)
    - :callback            # _AddCallback, _Stub
```

### Recommended Plugin Set

```yaml
:cmock:
  :plugins:
    - :ignore
    - :ignore_arg
    - :expect_any_args
    - :return_thru_ptr
    - :callback
    - :cexception
```

## CMock Configuration

### YAML Options (in project.yml under `:cmock:`)

| Option | Default | Description |
|--------|---------|-------------|
| `:mock_prefix` | `Mock` | Prefix for mock filenames |
| `:mock_suffix` | `""` | Suffix for mock filenames |
| `:mock_path` | `mocks` | Output directory for mocks |
| `:when_no_prototypes` | `:warn` | `:warn`, `:ignore`, `:error` |
| `:enforce_strict_ordering` | `false` | Enforce cross-function call order |
| `:fail_on_unexpected_calls` | `true` | Fail on unconfigured mock calls |
| `:memcmp_if_unknown` | `true` | memcmp for unknown types |
| `:when_ptr` | `:smart` | `:compare_ptr`, `:compare_data`, `:smart` |
| `:treat_externs` | `:exclude` | Include/exclude extern functions |
| `:treat_inlines` | `:exclude` | Include/exclude inline functions |
| `:callback_include_count` | `true` | NumCalls param in callbacks |
| `:callback_after_arg_check` | `false` | Callback timing |
| `:verbosity` | `2` | 0=errors, 1=+warnings, 2=normal, 3=verbose |

### Type Mapping (`:treat_as`)

Maps custom types to Unity assertion display format:

```yaml
:cmock:
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
    'char*': STRING
```

### Header Parsing Options

```yaml
:cmock:
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
```

### C-Level Memory Configuration

```c
#define CMOCK_MEM_STATIC           // Fixed pool (default)
#define CMOCK_MEM_DYNAMIC          // Heap allocation
#define CMOCK_MEM_SIZE   32768     // Pool size in bytes
#define CMOCK_MEM_ALIGN  2         // 0=none, 1=16bit, 2=32bit, 3=64bit
```

## CException API

### Core Syntax

```c
#include "CException.h"

CEXCEPTION_T e;
Try {
    // Protected code — Throw jumps to Catch
    riskyOperation();
}
Catch(e) {
    // Handle exception
    // e contains the exception ID
}
```

### Functions/Macros

```c
Throw(exception_id)          // Jump to nearest Catch block
ExitTry()                    // Exit Try cleanly (no exception)
```

### Nested Exceptions

```c
CEXCEPTION_T outer;
Try {
    CEXCEPTION_T inner;
    Try {
        DoRiskyThing();
    }
    Catch(inner) {
        if (inner == FATAL) Throw(inner);  // Re-throw to outer
        Recover();
    }
}
Catch(outer) {
    HandleFatal(outer);
}
```

### Integration with Unity

```c
void test_function_throws_on_bad_input(void) {
    CEXCEPTION_T e;
    Try {
        function_under_test(NULL);
        TEST_FAIL_MESSAGE("Expected exception");
    }
    Catch(e) {
        TEST_ASSERT_EQUAL_HEX32(ERR_INVALID_INPUT, e);
    }
}
```

## CException Configuration

All via `#define`:

```c
#define CEXCEPTION_T              unsigned int  // Exception type
#define CEXCEPTION_NONE           (0x5A5A5A5A)  // "No exception" sentinel
#define CEXCEPTION_NUM_ID         (1)           // Task count (RTOS)
#define CEXCEPTION_GET_ID         (0)           // Current task ID
#define CEXCEPTION_NO_CATCH_HANDLER(id)         // Uncaught handler
#define CEXCEPTION_USE_CONFIG_FILE              // Load CExceptionConfig.h

// Hooks (all default empty):
#define CEXCEPTION_HOOK_START_TRY
#define CEXCEPTION_HOOK_HAPPY_TRY
#define CEXCEPTION_HOOK_AFTER_TRY
#define CEXCEPTION_HOOK_START_CATCH
```

### RTOS Configuration Example

```c
#define CEXCEPTION_NUM_ID    OS_NUM_TASKS
#define CEXCEPTION_GET_ID    OS_GetCurrentTaskId()
#define CEXCEPTION_T         uint16_t
```

### Limitations

1. **No `return`/`goto` inside `Try`** — corrupts the exception frame stack
2. **`volatile` for modified locals** — variables modified in Try and read in Catch must be `volatile`
3. **No automatic cleanup** — `malloc`'d memory must be manually freed in Catch
4. **Single exception ID only** — no stack traces, no exception chaining
5. **No `finally` block** — use `CEXCEPTION_HOOK_AFTER_TRY` for cleanup logic
