# Resilience Nodes

## API

```python
retry_policy(
    wrapped_task,
    retry_on=None,
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0,
    max_delay=60.0,
    name=None,
)

circuit_breaker(
    wrapped_task,
    failure_threshold=5,
    reset_timeout_s=60.0,
    half_open_max_calls=1,
    name=None,
)

foreach(
    wrapped_task,
    data_key='data',
    item_key='item',
    max_concurrent=5,
    output_key='foreach_results',
    name=None,
)
```

## Notes

- `retry_policy` retries by exception by default.
- Provide `retry_on(exc, result) -> bool` for custom retry logic.
- `circuit_breaker` opens after `failure_threshold` failures and transitions to half-open after `reset_timeout_s`.
- `foreach` runs a task per item with bounded concurrency and returns both aggregated results and per-item details.

## Example

```python
from microflow import task, retry_policy, circuit_breaker, foreach

@task(name="call_api")
def call_api(ctx):
    return {"http_success": True, "payload": ctx["item"]}

safe = circuit_breaker(call_api, failure_threshold=3, reset_timeout_s=30)
retriable = retry_policy(safe, max_retries=2, initial_delay=0.5)
per_item = foreach(retriable, data_key="items", max_concurrent=4)
```
