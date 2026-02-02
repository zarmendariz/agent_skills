# CMock Advanced Patterns

## Table of Contents

1. [Basic Mocking Patterns](#basic-mocking-patterns)
2. [Argument Matching](#argument-matching)
3. [Return Value Patterns](#return-value-patterns)
4. [Callback and Stub Patterns](#callback-and-stub-patterns)
5. [Complex Scenarios](#complex-scenarios)
6. [Common Pitfalls](#common-pitfalls)

## Basic Mocking Patterns

### Pattern 1: Simple Function Call Expectation

**Scenario**: Verify a function is called exactly once

```c
void test_module_initializes_hardware(void)
{
    // Arrange
    hardware_init_Expect();
    
    // Act
    module_init();
    
    // Assert: Automatically verified by CMock
}
```

**Generated mock function**: `hardware_init_Expect()`
- Expects exactly one call
- Fails test if not called or called multiple times

### Pattern 2: Function Call with Return Value

**Scenario**: Mock function returns a specific value

```c
void test_module_reads_sensor_value(void)
{
    // Arrange
    sensor_read_ExpectAndReturn(42);
    
    // Act
    int value = module_get_sensor_reading();
    
    // Assert
    TEST_ASSERT_EQUAL(42, value);
}
```

**Generated mock functions**:
- `sensor_read_ExpectAndReturn(return_value)` - Expect call and return value
- `sensor_read_IgnoreAndReturn(return_value)` - Ignore calls, always return value

### Pattern 3: Multiple Calls with Different Returns

**Scenario**: Function called multiple times with different return values

```c
void test_module_reads_multiple_sensor_values(void)
{
    // Arrange: Set up sequence of return values
    sensor_read_ExpectAndReturn(10);
    sensor_read_ExpectAndReturn(20);
    sensor_read_ExpectAndReturn(30);
    
    // Act
    int v1 = module_get_sensor_reading();
    int v2 = module_get_sensor_reading();
    int v3 = module_get_sensor_reading();
    
    // Assert
    TEST_ASSERT_EQUAL(10, v1);
    TEST_ASSERT_EQUAL(20, v2);
    TEST_ASSERT_EQUAL(30, v3);
}
```

## Argument Matching

### Pattern 1: Exact Argument Matching

**Scenario**: Verify function called with specific arguments

```c
void test_uart_sends_correct_byte(void)
{
    // Arrange: Expect uart_send with exact value 0x42
    uart_send_Expect(0x42);
    
    // Act
    module_send_command(0x42);
    
    // Assert: Verified automatically
}
```

**Generated mock function**: `uart_send_Expect(expected_arg)`

### Pattern 2: Ignore Specific Arguments

**Scenario**: Don't care about specific argument values

```c
void test_gpio_set_called_with_any_value(void)
{
    // Arrange: Expect gpio_set with pin 5, any value
    gpio_set_Expect(5, IGNORE_ARG);
    
    // Act
    module_toggle_led();
    
    // Assert: Verified automatically
}
```

**Generated mock function**: `gpio_set_Expect(pin, IGNORE_ARG)`

### Pattern 3: Pointer Arguments

**Scenario**: Verify function called with pointer to specific data

```c
void test_process_buffer_with_specific_data(void)
{
    // Arrange
    uint8_t expected_data[] = {0x01, 0x02, 0x03};
    process_buffer_Expect(expected_data);
    
    // Act
    module_send_data(expected_data);
    
    // Assert: Verified automatically
}
```

### Pattern 4: Ignore Pointer Arguments

**Scenario**: Don't care about pointer value

```c
void test_process_any_buffer(void)
{
    // Arrange: Expect process_buffer with any pointer
    process_buffer_Expect(IGNORE_ARG);
    
    // Act
    uint8_t data[] = {0x01, 0x02};
    module_send_data(data);
    
    // Assert: Verified automatically
}
```

### Pattern 5: Pointer to Specific Memory

**Scenario**: Verify pointer points to specific memory location

```c
void test_process_specific_buffer_address(void)
{
    // Arrange
    uint8_t buffer[10];
    process_buffer_Expect((uint8_t*)&buffer);
    
    // Act
    module_process_buffer(buffer);
    
    // Assert: Verified automatically
}
```

## Return Value Patterns

### Pattern 1: Return Value Through Pointer

**Scenario**: Function returns value through output parameter

```c
// Function signature
void sensor_read(uint16_t *value);

// Test
void test_sensor_read_returns_value_through_pointer(void)
{
    // Arrange
    uint16_t expected_value = 1234;
    uint16_t actual_value;
    sensor_read_ExpectAndReturn(&actual_value);
    sensor_read_ReturnThruPtr_value(&expected_value);
    
    // Act
    sensor_read(&actual_value);
    
    // Assert
    TEST_ASSERT_EQUAL(expected_value, actual_value);
}
```

**Generated mock functions**:
- `sensor_read_ExpectAndReturn(pointer)`
- `sensor_read_ReturnThruPtr_value(value_pointer)`

### Pattern 2: Multiple Output Parameters

**Scenario**: Function returns multiple values through pointers

```c
// Function signature
void get_sensor_data(uint16_t *temperature, uint16_t *humidity);

// Test
void test_get_sensor_data_returns_multiple_values(void)
{
    // Arrange
    uint16_t temp = 25;
    uint16_t humidity = 60;
    uint16_t actual_temp, actual_humidity;
    
    get_sensor_data_Expect(&actual_temp, &actual_humidity);
    get_sensor_data_ReturnThruPtr_temperature(&temp);
    get_sensor_data_ReturnThruPtr_humidity(&humidity);
    
    // Act
    get_sensor_data(&actual_temp, &actual_humidity);
    
    // Assert
    TEST_ASSERT_EQUAL(25, actual_temp);
    TEST_ASSERT_EQUAL(60, actual_humidity);
}
```

### Pattern 3: Always Return (Ignore Call Count)

**Scenario**: Function can be called any number of times

```c
void test_module_with_optional_logging(void)
{
    // Arrange: log_message can be called any number of times
    log_message_IgnoreAndReturn(0);
    
    // Act
    module_process();  // May call log_message 0, 1, or more times
    
    // Assert: No verification of call count
}
```

**Generated mock function**: `log_message_IgnoreAndReturn(return_value)`

## Callback and Stub Patterns

### Pattern 1: Callback Function

**Scenario**: Mock function executes custom code

```c
// Interrupt handler that calls callback
void interrupt_handler_Callback(void (*callback)(uint8_t))
{
    callback(0x42);  // Simulate interrupt with data
}

void test_module_handles_interrupt_data(void)
{
    // Arrange: Define callback behavior
    void interrupt_callback(uint8_t data)
    {
        TEST_ASSERT_EQUAL(0x42, data);
    }
    
    interrupt_handler_StubWithCallback(interrupt_callback);
    
    // Act
    module_register_interrupt_handler();
    
    // Assert: Callback was executed with correct data
}
```

**Generated mock function**: `interrupt_handler_StubWithCallback(callback_function)`

### Pattern 2: Callback with State

**Scenario**: Callback modifies test state

```c
static int callback_call_count = 0;

void test_callback_called_multiple_times(void)
{
    // Arrange
    void counting_callback(void)
    {
        callback_call_count++;
    }
    
    process_Expect();
    process_StubWithCallback(counting_callback);
    
    // Act
    module_process();
    module_process();
    module_process();
    
    // Assert
    TEST_ASSERT_EQUAL(3, callback_call_count);
}
```

### Pattern 3: Callback with Arguments

**Scenario**: Callback receives and processes arguments

```c
static uint8_t received_data[10];
static int received_length = 0;

void data_callback(const uint8_t *data, int length)
{
    memcpy(received_data, data, length);
    received_length = length;
}

void test_callback_receives_data(void)
{
    // Arrange
    uart_receive_StubWithCallback(data_callback);
    
    // Act
    module_receive_data();
    
    // Assert
    TEST_ASSERT_EQUAL(5, received_length);
    TEST_ASSERT_EQUAL_MEMORY(expected_data, received_data, 5);
}
```

## Complex Scenarios

### Scenario 1: Strict Call Ordering

**Configuration** (in project.yml):
```yaml
:cmock:
  :enforce_strict_ordering: true
```

**Test**:
```c
void test_initialization_sequence_must_be_exact(void)
{
    // Arrange: Calls must occur in this exact order
    hardware_reset_Expect();
    hardware_configure_Expect();
    hardware_enable_Expect();
    
    // Act
    module_init();
    
    // Assert: If calls occur in different order, test fails
}
```

### Scenario 2: Conditional Mocking

**Scenario**: Different mock behavior based on input

```c
void test_error_handling_with_conditional_mocks(void)
{
    // Arrange: First call succeeds, second fails
    sensor_read_ExpectAndReturn(42);
    sensor_read_ExpectAndReturn(-1);  // Error code
    
    // Act
    int value1 = module_read_sensor();
    int value2 = module_read_sensor();
    
    // Assert
    TEST_ASSERT_EQUAL(42, value1);
    TEST_ASSERT_EQUAL(-1, value2);
}
```

### Scenario 3: Mock with Exception

**Scenario**: Mock function throws exception

```c
void test_exception_from_mocked_function(void)
{
    // Arrange
    sensor_read_ExpectAndThrow(EXCEPTION_TIMEOUT);
    
    // Act & Assert
    CEXCEPTION_T error;
    Try
    {
        module_read_sensor();
        TEST_FAIL_MESSAGE("Expected exception");
    }
    Catch(error)
    {
        TEST_ASSERT_EQUAL(EXCEPTION_TIMEOUT, error);
    }
}
```

### Scenario 4: Partial Mocking (Some Calls Ignored)

**Scenario**: Mock some calls, ignore others

```c
void test_module_with_optional_calls(void)
{
    // Arrange
    optional_function_IgnoreAndReturn(0);  // Can be called any number of times
    required_function_Expect();              // Must be called exactly once
    
    // Act
    module_process();
    
    // Assert: required_function verified, optional_function ignored
}
```

### Scenario 5: Memory Verification

**Scenario**: Verify function called with specific memory content

```c
void test_buffer_content_verification(void)
{
    // Arrange
    uint8_t expected_buffer[] = {0x01, 0x02, 0x03, 0x04};
    process_buffer_Expect(expected_buffer);
    
    // Act
    uint8_t actual_buffer[] = {0x01, 0x02, 0x03, 0x04};
    module_send_buffer(actual_buffer);
    
    // Assert: Verified automatically by CMock
}
```

## Common Pitfalls

### Pitfall 1: Forgetting to Expect Calls

**Wrong**:
```c
void test_module_calls_function(void)
{
    // Missing: hardware_init_Expect();
    
    module_init();
    
    // Test passes even if hardware_init not called!
}
```

**Correct**:
```c
void test_module_calls_function(void)
{
    hardware_init_Expect();
    
    module_init();
    
    // Test fails if hardware_init not called
}
```

### Pitfall 2: Wrong Argument Type

**Wrong**:
```c
void test_uart_send(void)
{
    uart_send_Expect(0x42);  // Expects uint8_t
    
    module_send((uint16_t)0x42);  // Sends uint16_t
    
    // May not match correctly
}
```

**Correct**:
```c
void test_uart_send(void)
{
    uart_send_Expect((uint8_t)0x42);  // Explicit type
    
    module_send((uint8_t)0x42);
}
```

### Pitfall 3: Pointer Comparison Issues

**Wrong**:
```c
void test_process_buffer(void)
{
    uint8_t buffer[] = {0x01, 0x02};
    process_buffer_Expect(buffer);
    
    uint8_t other_buffer[] = {0x01, 0x02};
    module_process(other_buffer);  // Different pointer!
    
    // Test fails - different memory addresses
}
```

**Correct**:
```c
void test_process_buffer(void)
{
    uint8_t buffer[] = {0x01, 0x02};
    process_buffer_Expect(buffer);
    
    module_process(buffer);  // Same pointer
}
```

### Pitfall 4: Unverified Mock Expectations

**Wrong**:
```c
void test_module_calls_function(void)
{
    hardware_init_Expect();
    
    // module_init() not called - expectation never verified
    
    // Test passes even though function wasn't called!
}
```

**Correct**:
```c
void test_module_calls_function(void)
{
    hardware_init_Expect();
    
    module_init();  // Actually call the function
    
    // Test fails if hardware_init not called
}
```

### Pitfall 5: Mixing Expect and Ignore

**Wrong**:
```c
void test_mixed_expectations(void)
{
    function_a_Expect();
    function_b_IgnoreAndReturn(0);
    function_a_Expect();  // Conflicting expectations!
    
    module_process();
}
```

**Correct**:
```c
void test_mixed_expectations(void)
{
    function_a_Expect();
    function_a_Expect();  // Consistent expectations
    function_b_IgnoreAndReturn(0);
    
    module_process();
}
```

## Best Practices

1. **One assertion per test** - Keep tests focused
2. **Clear mock expectations** - Use descriptive names
3. **Verify call order** - Use strict ordering when needed
4. **Test error paths** - Mock functions to return errors
5. **Use callbacks for complex behavior** - Simulate real interactions
6. **Document mock behavior** - Comment why mocks are needed
7. **Keep mocks simple** - Complex mocks indicate design issues
