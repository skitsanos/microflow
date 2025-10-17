# Timing and Delay Nodes

Timing nodes provide control over workflow execution timing, including delays, scheduling, rate limiting, and conditional waiting. They're essential for managing workflow pace and coordinating time-sensitive operations.

## Available Nodes

### delay

Add a simple delay to workflow execution.

**Parameters:**
- `seconds` (float): Number of seconds to delay
- `name` (str, optional): Node name

**Returns:**
- `delay_seconds`: Duration of delay requested
- `delay_start`: Start timestamp
- `delay_end`: End timestamp
- `delay_actual`: Actual delay duration

**Example:**
```python
from microflow import delay

# Simple 5-second delay
wait_5_seconds = delay(5.0)

# Named delay for clarity
processing_delay = delay(
    seconds=2.5,
    name="processing_delay"
)
```

### wait_until

Wait until a specific time before continuing.

**Parameters:**
- `target_time` (str): Target time string
- `time_format` (str): Time format for parsing (default: "%Y-%m-%d %H:%M:%S")
- `timezone` (str, optional): Timezone (None for local)
- `name` (str, optional): Node name

**Returns:**
- `wait_success`: Boolean indicating if wait completed successfully
- `wait_duration`: How long the wait lasted
- `target_time`: The target time that was waited for
- `wait_message`: Status message about the wait

**Example:**
```python
from microflow import wait_until

# Wait until specific date and time
wait_for_midnight = wait_until(
    target_time="2024-01-01 00:00:00",
    name="wait_for_new_year"
)

# Wait until business hours
wait_for_business_hours = wait_until(
    target_time="2024-01-15 09:00:00",
    time_format="%Y-%m-%d %H:%M:%S",
    name="wait_for_business_hours"
)
```

### wait_for_condition

Wait until a condition becomes true, checking periodically.

**Parameters:**
- `condition_expression` (str): Python expression to evaluate (ctx available)
- `check_interval` (float): How often to check condition in seconds (default: 1.0)
- `max_wait_time` (float, optional): Maximum time to wait (None for no limit)
- `name` (str, optional): Node name

**Returns:**
- `condition_met`: Boolean indicating if condition was met
- `wait_duration`: How long the wait lasted
- `condition_checks`: Number of times condition was checked
- `condition_expression`: The expression that was evaluated
- `condition_timeout`: Boolean indicating if wait timed out

**Example:**
```python
from microflow import wait_for_condition, task

@task(name="setup_monitoring")
def setup_monitoring(ctx):
    return {"process_status": "starting"}

# Wait for process to be ready
wait_for_ready = wait_for_condition(
    condition_expression="ctx.get('process_status') == 'ready'",
    check_interval=2.0,
    max_wait_time=60.0,
    name="wait_for_process_ready"
)

# Wait for file to exist
wait_for_file = wait_for_condition(
    condition_expression="ctx.get('file_exists', False)",
    check_interval=5.0,
    max_wait_time=300.0,
    name="wait_for_file_creation"
)
```

### rate_limit

Control the rate of task execution using token bucket algorithm.

**Parameters:**
- `calls_per_second` (float): Maximum calls per second
- `burst_size` (int): Maximum burst size (default: 1)
- `name` (str, optional): Node name

**Returns:**
- `rate_limited`: Boolean indicating if rate limiting was applied
- `tokens_remaining`: Number of tokens remaining in bucket
- `calls_per_second`: The rate limit that was applied
- `wait_time`: Time waited if rate limited

**Example:**
```python
from microflow import rate_limit

# Limit to 2 calls per second
api_rate_limiter = rate_limit(
    calls_per_second=2.0,
    burst_size=5,
    name="api_rate_limit"
)

# Strict rate limiting
database_rate_limiter = rate_limit(
    calls_per_second=0.5,  # One call every 2 seconds
    burst_size=1,
    name="database_rate_limit"
)
```

### schedule_at

Schedule task execution at a specific time.

**Parameters:**
- `schedule_time` (str): When to execute (future time)
- `time_format` (str): Time format for parsing (default: "%Y-%m-%d %H:%M:%S")
- `name` (str, optional): Node name

**Returns:**
- `schedule_success`: Boolean indicating if scheduling succeeded
- `scheduled_time`: The time that was scheduled for
- `actual_execution_time`: When execution actually occurred
- `wait_duration`: How long the wait was

**Example:**
```python
from microflow import schedule_at

# Schedule for specific time
morning_report = schedule_at(
    schedule_time="2024-01-15 08:00:00",
    name="morning_report_schedule"
)

# Schedule with custom format
backup_schedule = schedule_at(
    schedule_time="15/01/2024 02:00",
    time_format="%d/%m/%Y %H:%M",
    name="nightly_backup"
)
```

## Advanced Features

### timeout_wrapper

Wrap any task with a timeout.

**Parameters:**
- `wrapped_task` (Task): Task to wrap with timeout
- `timeout_seconds` (float): Timeout in seconds
- `name` (str, optional): Node name

**Returns:**
- `timeout_applied`: Boolean indicating timeout was set
- `timeout_seconds`: The timeout duration
- `execution_time`: Actual execution time
- `timed_out`: Boolean indicating if task timed out
- `wrapped_result`: Result from wrapped task (if successful)

**Example:**
```python
from microflow import timeout_wrapper, shell_command

# Create a long-running task
long_process = shell_command(
    command="sleep 30",
    name="long_running_process"
)

# Wrap with 10-second timeout
timed_process = timeout_wrapper(
    wrapped_task=long_process,
    timeout_seconds=10.0,
    name="timed_long_process"
)
```

### retry_with_backoff

Retry a task with exponential backoff on failure.

**Parameters:**
- `wrapped_task` (Task): Task to retry
- `max_retries` (int): Maximum number of retries (default: 3)
- `initial_delay` (float): Initial delay between retries (default: 1.0)
- `backoff_factor` (float): Multiplier for delay after each retry (default: 2.0)
- `max_delay` (float): Maximum delay between retries (default: 60.0)
- `name` (str, optional): Node name

**Returns:**
- `retry_successful`: Boolean indicating if task eventually succeeded
- `retry_attempts`: Number of attempts made
- `total_retry_duration`: Total time spent retrying
- `last_error`: Error from final attempt (if failed)

**Example:**
```python
from microflow import retry_with_backoff, http_get

# Create unreliable HTTP request
api_call = http_get(
    url="https://unreliable-api.example.com/data",
    name="unreliable_api"
)

# Add retry logic
reliable_api_call = retry_with_backoff(
    wrapped_task=api_call,
    max_retries=5,
    initial_delay=1.0,
    backoff_factor=2.0,
    max_delay=30.0,
    name="reliable_api_call"
)
```

### measure_execution_time

Measure and report execution time of any task.

**Parameters:**
- `wrapped_task` (Task): Task to measure
- `name` (str, optional): Node name

**Returns:**
- `execution_time`: Time taken to execute task
- `start_time`: When execution started
- `end_time`: When execution finished
- `timing_measured`: Boolean indicating timing was captured
- `wrapped_result`: Result from wrapped task

**Example:**
```python
from microflow import measure_execution_time, data_transform

# Create data processing task
process_data = data_transform(
    transform_expression="{'processed': True, **item}",
    data_key="input_data"
)

# Measure its execution time
timed_processing = measure_execution_time(
    wrapped_task=process_data,
    name="measure_data_processing"
)
```

## Convenience Functions

### sleep

Simple sleep function (alias for delay).

```python
from microflow import sleep

# Sleep for 3 seconds
pause = sleep(3.0)
```

### wait_seconds, wait_minutes, wait_hours

Convenience functions for common delay durations.

```python
from microflow import wait_seconds, wait_minutes, wait_hours

short_pause = wait_seconds(30)      # 30 seconds
medium_pause = wait_minutes(5)      # 5 minutes
long_pause = wait_hours(2)          # 2 hours
```

### daily_schedule

Schedule for daily execution at specified time.

**Parameters:**
- `hour` (int): Hour of day (0-23)
- `minute` (int): Minute of hour (0-59, default: 0)
- `second` (int): Second of minute (0-59, default: 0)

```python
from microflow import daily_schedule

# Schedule for 8:30 AM daily
morning_task = daily_schedule(
    hour=8,
    minute=30,
    second=0
)

# Schedule for midnight
midnight_task = daily_schedule(hour=0)
```

### timeout_after

Create a timeout node that fails after specified seconds.

```python
from microflow import timeout_after

# Fail if workflow takes longer than 5 minutes
workflow_timeout = timeout_after(300)
```

## Common Patterns

### API Rate Limiting
```python
from microflow import rate_limit, http_get, Workflow

# Rate-limited API calls
rate_limiter = rate_limit(calls_per_second=2.0)

api_call_1 = http_get(url="https://api.example.com/data1")
api_call_2 = http_get(url="https://api.example.com/data2")
api_call_3 = http_get(url="https://api.example.com/data3")

# Chain with rate limiting between calls
api_call_1 >> rate_limiter >> api_call_2 >> rate_limiter >> api_call_3
```

### Scheduled Workflows
```python
from microflow import schedule_at, task

@task(name="backup_data")
def backup_data(ctx):
    return {"backup": "completed", "timestamp": "2024-01-15"}

# Schedule backup for 2 AM
nightly_backup = schedule_at(
    schedule_time="2024-01-16 02:00:00",
    name="schedule_backup"
)

nightly_backup >> backup_data
```

### Polling with Timeout
```python
from microflow import wait_for_condition, timeout_wrapper, task

@task(name="check_service_status")
def check_service_status(ctx):
    # Simulate checking service status
    return {"service_ready": True}

# Wait for service with timeout
wait_for_service = wait_for_condition(
    condition_expression="ctx.get('service_ready', False)",
    check_interval=5.0,
    name="wait_for_service"
)

timed_wait = timeout_wrapper(
    wrapped_task=wait_for_service,
    timeout_seconds=300.0,  # 5 minute timeout
    name="timed_service_wait"
)

check_service_status >> timed_wait
```

### Retry with Custom Logic
```python
from microflow import retry_with_backoff, task, http_get

@task(name="check_retry_condition")
def check_retry_condition(ctx):
    http_status = ctx.get("http_status_code", 0)
    # Only retry on server errors (5xx)
    should_retry = 500 <= http_status < 600
    return {"should_retry": should_retry}

api_call = http_get(url="https://api.example.com/data")

retry_api = retry_with_backoff(
    wrapped_task=api_call,
    max_retries=3,
    initial_delay=2.0,
    name="retry_api_call"
)

api_call >> check_retry_condition >> retry_api
```

### Performance Monitoring
```python
from microflow import measure_execution_time, task

@task(name="heavy_computation")
def heavy_computation(ctx):
    # Simulate heavy processing
    import time
    time.sleep(2)
    return {"result": "computed"}

# Measure performance
timed_computation = measure_execution_time(
    wrapped_task=heavy_computation,
    name="measure_heavy_computation"
)

@task(name="log_performance")
def log_performance(ctx):
    execution_time = ctx.get("execution_time", 0)
    print(f"Computation took {execution_time:.2f} seconds")
    return {"logged": True}

timed_computation >> log_performance
```

## Error Handling

Timing nodes provide comprehensive error information:

```python
from microflow import wait_for_condition, task

wait_task = wait_for_condition(
    condition_expression="ctx.get('ready', False)",
    check_interval=1.0,
    max_wait_time=30.0
)

@task(name="handle_wait_result")
def handle_wait_result(ctx):
    if ctx.get("condition_met"):
        return {"status": "success", "message": "Condition was met"}
    elif ctx.get("condition_timeout"):
        return {"status": "timeout", "message": "Wait timed out"}
    else:
        error = ctx.get("condition_error")
        return {"status": "error", "message": f"Wait failed: {error}"}

wait_task >> handle_wait_result
```

## Best Practices

1. **Use appropriate timeouts**: Set reasonable timeouts to prevent hanging workflows
2. **Handle timeouts gracefully**: Always check timeout flags and handle accordingly
3. **Choose proper intervals**: Use appropriate check intervals for polling operations
4. **Rate limit external calls**: Respect API rate limits with rate limiting nodes
5. **Monitor execution time**: Use timing measurement for performance optimization
6. **Plan for failures**: Use retry logic for unreliable operations
7. **Schedule wisely**: Consider system load when scheduling workflows
8. **Use delays sparingly**: Avoid unnecessary delays that slow down workflows
9. **Test timing logic**: Verify timing behavior in different environments
10. **Document timing requirements**: Clearly specify timing constraints and expectations