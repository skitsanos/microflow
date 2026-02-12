# Control-Plane Nodes

Use these nodes for observability, approvals, queue I/O, and execution safety controls around business tasks. Best practices: keep providers explicit in production, and use stable keys for metrics, idempotency, and approval decisions.

## API

```python
metrics_emit(metric_name, value_key=None, metric_type='counter', labels=None, provider='memory', output_key='metric_result', name=None)
trace_span(wrapped_task, span_name=None, attributes=None, provider='memory', name=None)
human_approval(prompt, approvers=None, timeout_s=None, output_key='approval_result', name=None, default_decision='reject', decision_key='approval_decision')
queue_publish(message_key='data', provider=None, output_key='queue_message_id', queue_kwargs=None, name=None)
queue_consume(provider=None, output_key='queue_message', ack=True, block_timeout_s=0.0, queue_kwargs=None, name=None)
idempotency_guard(key, ttl_s=None, provider='memory', output_key='idempotency', name=None)
```

## Notes

- `metrics_emit` and `trace_span` default to in-memory providers for low overhead.
- `queue_publish`/`queue_consume` use `QUEUE_PROVIDER`; Redis is used only when explicitly configured.
- `human_approval` reads decision from context keys:
  - `approval_decision_<node_name>` (preferred)
  - `approval_decision`
- `idempotency_guard` helps prevent duplicate processing by key.

## Example

```python
from microflow import (
    metrics_emit,
    idempotency_guard,
    queue_publish,
    queue_consume,
)

emit = metrics_emit("workflow_started")
idem = idempotency_guard("run:{run_id}")
publish = queue_publish(message_key="job_payload")
consume = queue_consume()
```
