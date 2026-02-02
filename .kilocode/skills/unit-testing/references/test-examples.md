# Real-World Test Examples

## Table of Contents

1. [UART Driver Tests](#uart-driver-tests)
2. [State Machine Tests](#state-machine-tests)
3. [Sensor Interface Tests](#sensor-interface-tests)
4. [Error Handling Tests](#error-handling-tests)
5. [Hardware Abstraction Layer Tests](#hardware-abstraction-layer-tests)

## UART Driver Tests

### Module Under Test: uart_driver.h

```c
// uart_driver.h
#ifndef UART_DRIVER_H
#define UART_DRIVER_H

#include <stdint.h>
#include <stdbool.h>

typedef enum {
    UART_OK = 0,
    UART_ERROR_INVALID_PARAM = 1,
    UART_ERROR_TIMEOUT = 2,
    UART_ERROR_BUFFER_FULL = 3
} uart_status_t;

void uart_init(uint32_t baud_rate);
uart_status_t uart_send_byte(uint8_t byte);
uart_status_t uart_send_buffer(const uint8_t *buffer, uint16_t length);
bool uart_is_ready(void);
void uart_enable_interrupt(void);

#endif
```

### Test Module: test_uart_driver.c

```c
#include "unity.h"
#include "uart_driver.h"
#include "mock_hal_uart.h"

void setUp(void)
{
    // Reset mock expectations before each test
    mock_hal_uart_Init();
}

void tearDown(void)
{
    // Verify all mock expectations were met
    mock_hal_uart_Verify();
}

// Test Group: Initialization
void test_uart_init_configures_hardware_with_correct_baud_rate(void)
{
    // Arrange
    uint32_t expected_baud = 115200;
    hal_uart_configure_Expect(expected_baud);
    
    // Act
    uart_init(expected_baud);
    
    // Assert: Verified automatically by CMock
}

void test_uart_init_enables_interrupts(void)
{
    // Arrange
    hal_uart_configure_Expect(9600);
    hal_uart_enable_interrupt_Expect();
    
    // Act
    uart_init(9600);
    
    // Assert: Verified automatically
}

// Test Group: Sending Single Byte
void test_uart_send_byte_writes_to_hardware(void)
{
    // Arrange
    uint8_t test_byte = 0x42;
    hal_uart_write_byte_Expect(test_byte);
    hal_uart_write_byte_ExpectAndReturn(UART_OK);
    
    // Act
    uart_status_t status = uart_send_byte(test_byte);
    
    // Assert
    TEST_ASSERT_EQUAL(UART_OK, status);
}

void test_uart_send_byte_returns_error_on_timeout(void)
{
    // Arrange
    hal_uart_write_byte_Expect(0x42);
    hal_uart_write_byte_ExpectAndReturn(UART_ERROR_TIMEOUT);
    
    // Act
    uart_status_t status = uart_send_byte(0x42);
    
    // Assert
    TEST_ASSERT_EQUAL(UART_ERROR_TIMEOUT, status);
}

// Test Group: Sending Buffer
void test_uart_send_buffer_sends_all_bytes(void)
{
    // Arrange
    uint8_t buffer[] = {0x01, 0x02, 0x03};
    uint16_t length = 3;
    
    hal_uart_write_byte_Expect(0x01);
    hal_uart_write_byte_ExpectAndReturn(UART_OK);
    hal_uart_write_byte_Expect(0x02);
    hal_uart_write_byte_ExpectAndReturn(UART_OK);
    hal_uart_write_byte_Expect(0x03);
    hal_uart_write_byte_ExpectAndReturn(UART_OK);
    
    // Act
    uart_status_t status = uart_send_buffer(buffer, length);
    
    // Assert
    TEST_ASSERT_EQUAL(UART_OK, status);
}

void test_uart_send_buffer_stops_on_error(void)
{
    // Arrange
    uint8_t buffer[] = {0x01, 0x02, 0x03};
    uint16_t length = 3;
    
    hal_uart_write_byte_Expect(0x01);
    hal_uart_write_byte_ExpectAndReturn(UART_OK);
    hal_uart_write_byte_Expect(0x02);
    hal_uart_write_byte_ExpectAndReturn(UART_ERROR_BUFFER_FULL);
    // 0x03 should NOT be sent
    
    // Act
    uart_status_t status = uart_send_buffer(buffer, length);
    
    // Assert
    TEST_ASSERT_EQUAL(UART_ERROR_BUFFER_FULL, status);
}

void test_uart_send_buffer_rejects_null_pointer(void)
{
    // Arrange: No hardware calls expected
    
    // Act
    uart_status_t status = uart_send_buffer(NULL, 10);
    
    // Assert
    TEST_ASSERT_EQUAL(UART_ERROR_INVALID_PARAM, status);
}

// Test Group: Status Checking
void test_uart_is_ready_returns_true_when_hardware_ready(void)
{
    // Arrange
    hal_uart_is_ready_ExpectAndReturn(true);
    
    // Act
    bool ready = uart_is_ready();
    
    // Assert
    TEST_ASSERT_TRUE(ready);
}

void test_uart_is_ready_returns_false_when_hardware_busy(void)
{
    // Arrange
    hal_uart_is_ready_ExpectAndReturn(false);
    
    // Act
    bool ready = uart_is_ready();
    
    // Assert
    TEST_ASSERT_FALSE(ready);
}
```

## State Machine Tests

### Module Under Test: led_controller.h

```c
// led_controller.h
typedef enum {
    LED_STATE_OFF,
    LED_STATE_ON,
    LED_STATE_BLINKING,
    LED_STATE_ERROR
} led_state_t;

void led_init(void);
void led_on(void);
void led_off(void);
void led_blink(uint16_t period_ms);
led_state_t led_get_state(void);
void led_handle_error(void);
```

### Test Module: test_led_controller.c

```c
#include "unity.h"
#include "led_controller.h"
#include "mock_hal_gpio.h"
#include "mock_timer.h"

void setUp(void)
{
    led_init();
}

void tearDown(void)
{
    // Verify all expectations
}

// Test Group: Initialization
void test_led_init_sets_gpio_as_output(void)
{
    // Arrange
    hal_gpio_set_direction_Expect(LED_PIN, GPIO_OUTPUT);
    hal_gpio_write_Expect(LED_PIN, GPIO_LOW);
    
    // Act
    led_init();
    
    // Assert: Verified automatically
}

// Test Group: State Transitions
void test_led_transitions_from_off_to_on(void)
{
    // Arrange
    hal_gpio_write_Expect(LED_PIN, GPIO_HIGH);
    
    // Act
    led_on();
    
    // Assert
    TEST_ASSERT_EQUAL(LED_STATE_ON, led_get_state());
}

void test_led_transitions_from_on_to_off(void)
{
    // Arrange
    hal_gpio_write_Expect(LED_PIN, GPIO_HIGH);
    led_on();
    
    hal_gpio_write_Expect(LED_PIN, GPIO_LOW);
    
    // Act
    led_off();
    
    // Assert
    TEST_ASSERT_EQUAL(LED_STATE_OFF, led_get_state());
}

void test_led_transitions_from_on_to_blinking(void)
{
    // Arrange
    hal_gpio_write_Expect(LED_PIN, GPIO_HIGH);
    led_on();
    
    timer_start_Expect(100);  // 100ms period
    
    // Act
    led_blink(100);
    
    // Assert
    TEST_ASSERT_EQUAL(LED_STATE_BLINKING, led_get_state());
}

void test_led_invalid_transition_ignored(void)
{
    // Arrange: LED is OFF
    // No expectations - invalid transition should not call hardware
    
    // Act: Try to turn off when already off
    led_off();
    
    // Assert: Still OFF
    TEST_ASSERT_EQUAL(LED_STATE_OFF, led_get_state());
}

// Test Group: Error Handling
void test_led_enters_error_state_on_hardware_failure(void)
{
    // Arrange
    hal_gpio_write_Expect(LED_PIN, GPIO_HIGH);
    hal_gpio_write_ExpectAndReturn(GPIO_ERROR);
    
    // Act
    led_on();
    
    // Assert
    TEST_ASSERT_EQUAL(LED_STATE_ERROR, led_get_state());
}

void test_led_recovers_from_error_state(void)
{
    // Arrange: LED in error state
    hal_gpio_write_Expect(LED_PIN, GPIO_HIGH);
    hal_gpio_write_ExpectAndReturn(GPIO_ERROR);
    led_on();
    
    // Now recover
    hal_gpio_write_Expect(LED_PIN, GPIO_LOW);
    
    // Act
    led_handle_error();
    
    // Assert
    TEST_ASSERT_EQUAL(LED_STATE_OFF, led_get_state());
}
```

## Sensor Interface Tests

### Module Under Test: temperature_sensor.h

```c
// temperature_sensor.h
typedef struct {
    int16_t temperature;  // In 0.1°C units
    uint8_t status;
} temperature_reading_t;

void temperature_sensor_init(void);
temperature_reading_t temperature_sensor_read(void);
bool temperature_sensor_is_valid(temperature_reading_t reading);
```

### Test Module: test_temperature_sensor.c

```c
#include "unity.h"
#include "temperature_sensor.h"
#include "mock_i2c_driver.h"

void setUp(void)
{
    temperature_sensor_init();
}

void tearDown(void)
{
}

// Test Group: Initialization
void test_temperature_sensor_init_configures_i2c(void)
{
    // Arrange
    i2c_init_Expect(I2C_SPEED_400KHZ);
    
    // Act
    temperature_sensor_init();
    
    // Assert: Verified automatically
}

// Test Group: Reading Sensor
void test_temperature_sensor_reads_valid_temperature(void)
{
    // Arrange
    uint8_t i2c_data[] = {0x18, 0x40};  // 25.0°C in sensor format
    i2c_read_Expect(TEMP_SENSOR_ADDR, 2);
    i2c_read_ReturnThruPtr_data(i2c_data);
    
    // Act
    temperature_reading_t reading = temperature_sensor_read();
    
    // Assert
    TEST_ASSERT_EQUAL(250, reading.temperature);  // 25.0°C
    TEST_ASSERT_TRUE(temperature_sensor_is_valid(reading));
}

void test_temperature_sensor_handles_negative_temperature(void)
{
    // Arrange
    uint8_t i2c_data[] = {0xFF, 0xC0};  // -0.25°C in sensor format
    i2c_read_Expect(TEMP_SENSOR_ADDR, 2);
    i2c_read_ReturnThruPtr_data(i2c_data);
    
    // Act
    temperature_reading_t reading = temperature_sensor_read();
    
    // Assert
    TEST_ASSERT_EQUAL(-3, reading.temperature);  // -0.3°C (rounded)
}

void test_temperature_sensor_detects_communication_error(void)
{
    // Arrange
    i2c_read_Expect(TEMP_SENSOR_ADDR, 2);
    i2c_read_ExpectAndReturn(I2C_ERROR_TIMEOUT);
    
    // Act
    temperature_reading_t reading = temperature_sensor_read();
    
    // Assert
    TEST_ASSERT_FALSE(temperature_sensor_is_valid(reading));
}

// Test Group: Validation
void test_temperature_reading_valid_within_range(void)
{
    // Arrange
    temperature_reading_t reading = {250, STATUS_OK};
    
    // Act & Assert
    TEST_ASSERT_TRUE(temperature_sensor_is_valid(reading));
}

void test_temperature_reading_invalid_out_of_range(void)
{
    // Arrange
    temperature_reading_t reading = {1000, STATUS_OK};  // 100°C - unrealistic
    
    // Act & Assert
    TEST_ASSERT_FALSE(temperature_sensor_is_valid(reading));
}
```

## Error Handling Tests

### Module Under Test: error_handler.h

```c
// error_handler.h
typedef enum {
    ERROR_NONE = 0,
    ERROR_TIMEOUT = 1,
    ERROR_INVALID_STATE = 2,
    ERROR_RESOURCE_BUSY = 3
} error_code_t;

void error_handler_init(void);
void error_handler_report(error_code_t error);
error_code_t error_handler_get_last_error(void);
void error_handler_clear(void);
```

### Test Module: test_error_handler.c

```c
#include "unity.h"
#include "error_handler.h"
#include "mock_logger.h"

void setUp(void)
{
    error_handler_init();
}

void tearDown(void)
{
}

// Test Group: Error Reporting
void test_error_handler_logs_error(void)
{
    // Arrange
    logger_log_error_Expect(ERROR_TIMEOUT);
    
    // Act
    error_handler_report(ERROR_TIMEOUT);
    
    // Assert: Verified automatically
}

void test_error_handler_stores_last_error(void)
{
    // Arrange
    logger_log_error_Expect(ERROR_INVALID_STATE);
    
    // Act
    error_handler_report(ERROR_INVALID_STATE);
    
    // Assert
    TEST_ASSERT_EQUAL(ERROR_INVALID_STATE, error_handler_get_last_error());
}

void test_error_handler_overwrites_previous_error(void)
{
    // Arrange
    logger_log_error_Expect(ERROR_TIMEOUT);
    logger_log_error_Expect(ERROR_RESOURCE_BUSY);
    
    // Act
    error_handler_report(ERROR_TIMEOUT);
    error_handler_report(ERROR_RESOURCE_BUSY);
    
    // Assert
    TEST_ASSERT_EQUAL(ERROR_RESOURCE_BUSY, error_handler_get_last_error());
}

void test_error_handler_clear_resets_error(void)
{
    // Arrange
    logger_log_error_Expect(ERROR_TIMEOUT);
    error_handler_report(ERROR_TIMEOUT);
    
    // Act
    error_handler_clear();
    
    // Assert
    TEST_ASSERT_EQUAL(ERROR_NONE, error_handler_get_last_error());
}

// Test Group: Exception Handling
void test_error_handler_throws_on_critical_error(void)
{
    // Arrange
    logger_log_error_Expect(ERROR_CRITICAL);
    
    // Act & Assert
    CEXCEPTION_T error;
    Try
    {
        error_handler_report(ERROR_CRITICAL);
        TEST_FAIL_MESSAGE("Expected exception");
    }
    Catch(error)
    {
        TEST_ASSERT_EQUAL(ERROR_CRITICAL, error);
    }
}
```

## Hardware Abstraction Layer Tests

### Module Under Test: hal_gpio.h

```c
// hal_gpio.h
typedef enum {
    GPIO_INPUT,
    GPIO_OUTPUT
} gpio_direction_t;

typedef enum {
    GPIO_LOW = 0,
    GPIO_HIGH = 1
} gpio_level_t;

void hal_gpio_set_direction(uint8_t pin, gpio_direction_t direction);
void hal_gpio_write(uint8_t pin, gpio_level_t level);
gpio_level_t hal_gpio_read(uint8_t pin);
```

### Test Module: test_hal_gpio.c

```c
#include "unity.h"
#include "hal_gpio.h"
#include "mock_stm32_gpio.h"

void setUp(void)
{
    // Initialize GPIO subsystem
}

void tearDown(void)
{
}

// Test Group: GPIO Configuration
void test_hal_gpio_set_direction_output(void)
{
    // Arrange
    stm32_gpio_set_mode_Expect(GPIOA, 5, GPIO_MODE_OUTPUT);
    
    // Act
    hal_gpio_set_direction(PA5, GPIO_OUTPUT);
    
    // Assert: Verified automatically
}

void test_hal_gpio_set_direction_input(void)
{
    // Arrange
    stm32_gpio_set_mode_Expect(GPIOB, 3, GPIO_MODE_INPUT);
    
    // Act
    hal_gpio_set_direction(PB3, GPIO_INPUT);
    
    // Assert: Verified automatically
}

// Test Group: GPIO Write
void test_hal_gpio_write_high(void)
{
    // Arrange
    stm32_gpio_set_pin_Expect(GPIOA, 5);
    
    // Act
    hal_gpio_write(PA5, GPIO_HIGH);
    
    // Assert: Verified automatically
}

void test_hal_gpio_write_low(void)
{
    // Arrange
    stm32_gpio_clear_pin_Expect(GPIOA, 5);
    
    // Act
    hal_gpio_write(PA5, GPIO_LOW);
    
    // Assert: Verified automatically
}

// Test Group: GPIO Read
void test_hal_gpio_read_high(void)
{
    // Arrange
    stm32_gpio_read_pin_ExpectAndReturn(GPIOA, 5, 1);
    
    // Act
    gpio_level_t level = hal_gpio_read(PA5);
    
    // Assert
    TEST_ASSERT_EQUAL(GPIO_HIGH, level);
}

void test_hal_gpio_read_low(void)
{
    // Arrange
    stm32_gpio_read_pin_ExpectAndReturn(GPIOA, 5, 0);
    
    // Act
    gpio_level_t level = hal_gpio_read(PA5);
    
    // Assert
    TEST_ASSERT_EQUAL(GPIO_LOW, level);
}
```
