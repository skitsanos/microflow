# Timing Nodes

## API

```python
delay(seconds, name=None)
wait_until(target_time, time_format='%Y-%m-%d %H:%M:%S', timezone=None, name=None)
wait_for_condition(condition_expression, check_interval=1.0, max_wait_time=None, name=None)
timeout_wrapper(wrapped_task, timeout_seconds, name=None)
rate_limit(calls_per_second, burst_size=1, name=None)
schedule_at(schedule_time, time_format='%Y-%m-%d %H:%M:%S', name=None)
retry_with_backoff(wrapped_task, max_retries=3, initial_delay=1.0, backoff_factor=2.0, max_delay=60.0, name=None)
measure_execution_time(wrapped_task, name=None)
sleep(seconds)
wait_seconds(seconds)
wait_minutes(minutes)
wait_hours(hours)
daily_schedule(hour, minute=0, second=0)
timeout_after(seconds)
```

## Behavior

- `delay`, `wait_until`, and `wait_for_condition` block asynchronously and write timing metadata to context.
- `timeout_wrapper`, `retry_with_backoff`, and `measure_execution_time` wrap existing tasks.
- Convenience aliases: `sleep`, `wait_seconds`, `wait_minutes`, `wait_hours`.

## Example

```python
from microflow import delay, wait_for_condition, rate_limit

pause = delay(2.0)
wait_ready = wait_for_condition("ctx.get('ready') is True", check_interval=1.0, max_wait_time=30.0)
limit = rate_limit(2.0, burst_size=5)
```
