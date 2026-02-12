"""Control-plane and observability nodes."""

import asyncio
import os
import time
from typing import Any, Dict, Optional

from ..core.task_spec import Task, task
from ..queueing import create_workflow_queue_from_env

_MEMORY_METRICS: Dict[str, Dict[str, Any]] = {}
_MEMORY_TRACES = []
_MEMORY_IDEMPOTENCY: Dict[str, Optional[float]] = {}


def _safe_numeric(value: Any, default: float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _metric_key(metric_name: str, labels: Optional[Dict[str, Any]]) -> str:
    if not labels:
        return metric_name
    normalized = ",".join(f"{k}={labels[k]}" for k in sorted(labels.keys()))
    return f"{metric_name}|{normalized}"


def metrics_emit(
    metric_name: str,
    value_key: Optional[str] = None,
    metric_type: str = "counter",
    labels: Optional[Dict[str, Any]] = None,
    provider: str = "memory",
    output_key: str = "metric_result",
    name: Optional[str] = None,
):
    """Emit metrics to configured provider (memory currently supported)."""
    node_name = name or f"metrics_emit_{metric_name}"

    @task(name=node_name, description=f"Emit metric '{metric_name}'")
    def _metrics_emit(ctx):
        if provider != "memory":
            return {
                "metric_success": False,
                "metric_error": f"Unsupported provider: {provider}",
            }

        metric_key = _metric_key(metric_name, labels)
        metric = _MEMORY_METRICS.setdefault(
            metric_key,
            {
                "name": metric_name,
                "labels": labels or {},
                "type": metric_type,
                "value": 0.0,
                "count": 0,
                "sum": 0.0,
            },
        )

        value = _safe_numeric(ctx.get(value_key) if value_key else None, 1.0)

        if metric_type == "counter":
            metric["value"] += value
        elif metric_type == "gauge":
            metric["value"] = value
        elif metric_type == "timer":
            metric["count"] += 1
            metric["sum"] += value
            metric["value"] = (
                metric["sum"] / metric["count"] if metric["count"] else 0.0
            )
        else:
            return {
                "metric_success": False,
                "metric_error": f"Unsupported metric_type: {metric_type}",
            }

        return {
            output_key: {
                "metric_name": metric_name,
                "metric_type": metric_type,
                "metric_value": metric["value"],
                "labels": labels or {},
            },
            "metric_success": True,
            "metric_provider": provider,
        }

    return _metrics_emit


def trace_span(
    wrapped_task: Task,
    span_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    provider: str = "memory",
    name: Optional[str] = None,
):
    """Wrap a task with tracing span metadata."""
    span_label = span_name or wrapped_task.spec.name
    node_name = name or f"trace_span_{wrapped_task.spec.name}"

    @task(name=node_name, description=f"Trace span for {wrapped_task.spec.name}")
    async def _trace_span(ctx):
        start = time.time()
        error = None
        wrapped_result: Any = None

        try:
            wrapped_result = wrapped_task.spec.fn(ctx)
            if asyncio.iscoroutine(wrapped_result):
                wrapped_result = await wrapped_result
            success = True
        except Exception as e:
            success = False
            error = str(e)

        end = time.time()
        span = {
            "span_name": span_label,
            "start_time": start,
            "end_time": end,
            "duration_s": end - start,
            "success": success,
            "error": error,
            "attributes": attributes or {},
        }

        if provider == "memory":
            _MEMORY_TRACES.append(span)
        else:
            return {
                "trace_success": False,
                "trace_error": f"Unsupported provider: {provider}",
            }

        if isinstance(wrapped_result, dict):
            wrapped_result.update(
                {
                    "trace_success": success,
                    "trace_span": span,
                    "trace_provider": provider,
                }
            )
            return wrapped_result

        return {
            "wrapped_result": wrapped_result,
            "trace_success": success,
            "trace_span": span,
            "trace_provider": provider,
        }

    return _trace_span


def _resolve_decision(raw: Any) -> Optional[bool]:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in {"approve", "approved", "yes", "y", "true", "1"}:
            return True
        if lowered in {"reject", "rejected", "no", "n", "false", "0"}:
            return False
    return None


def human_approval(
    prompt: str,
    approvers: Optional[list] = None,
    timeout_s: Optional[float] = None,
    output_key: str = "approval_result",
    name: Optional[str] = None,
    default_decision: str = "reject",
    decision_key: str = "approval_decision",
):
    """Evaluate approval decision from context keys."""
    node_name = name or "human_approval"

    @task(name=node_name, description="Human approval gate")
    def _human_approval(ctx):
        raw_decision = ctx.get(f"{decision_key}_{node_name}", ctx.get(decision_key))
        parsed = _resolve_decision(raw_decision)

        if parsed is None:
            parsed = default_decision.strip().lower() in {
                "approve",
                "approved",
                "yes",
                "y",
                "true",
                "1",
            }
            status = "defaulted"
        else:
            status = "provided"

        result = {
            "prompt": prompt,
            "approvers": approvers or [],
            "approved": parsed,
            "decision": "approve" if parsed else "reject",
            "status": status,
            "timeout_s": timeout_s,
        }

        return {
            output_key: result,
            "approval_success": True,
            "approval_required": parsed is False,
        }

    return _human_approval


def queue_publish(
    message_key: str = "data",
    provider: Optional[str] = None,
    output_key: str = "queue_message_id",
    queue_kwargs: Optional[Dict[str, Any]] = None,
    name: Optional[str] = None,
):
    """Publish a workflow job/message to configured queue provider."""
    node_name = name or "queue_publish"

    @task(name=node_name, description="Publish message to queue")
    def _queue_publish(ctx):
        payload = ctx.get(message_key)
        if payload is None:
            return {
                "queue_success": False,
                "queue_error": f"No data found in context key: {message_key}",
            }

        if not isinstance(payload, dict):
            payload = {"value": payload}

        queue_provider, queue = create_workflow_queue_from_env(
            provider=provider,
            **(queue_kwargs or {}),
        )
        message_id = queue.enqueue(payload)

        return {
            output_key: message_id,
            "queue_success": True,
            "queue_provider": queue_provider,
        }

    return _queue_publish


def queue_consume(
    provider: Optional[str] = None,
    output_key: str = "queue_message",
    ack: bool = True,
    block_timeout_s: float = 0.0,
    queue_kwargs: Optional[Dict[str, Any]] = None,
    name: Optional[str] = None,
):
    """Consume one message from configured queue provider."""
    node_name = name or "queue_consume"

    @task(name=node_name, description="Consume message from queue")
    def _queue_consume(ctx):
        queue_provider, queue = create_workflow_queue_from_env(
            provider=provider,
            **(queue_kwargs or {}),
        )

        msg = queue.reserve(block_timeout_s=block_timeout_s)
        if msg is None:
            return {
                output_key: None,
                "queue_success": True,
                "queue_empty": True,
                "queue_provider": queue_provider,
            }

        if ack:
            queue.ack(msg.message_id)

        return {
            output_key: msg.payload,
            "queue_success": True,
            "queue_empty": False,
            "queue_provider": queue_provider,
            "queue_message_id": msg.message_id,
            "queue_attempts": msg.attempts,
            "queue_acked": ack,
        }

    return _queue_consume


def idempotency_guard(
    key: str,
    ttl_s: Optional[int] = None,
    provider: str = "memory",
    output_key: str = "idempotency",
    name: Optional[str] = None,
):
    """Guard against duplicate processing by key."""
    node_name = name or "idempotency_guard"

    @task(name=node_name, description=f"Idempotency guard for key '{key}'")
    def _idempotency_guard(ctx):
        try:
            resolved_key = key.format(**ctx)
        except Exception:
            resolved_key = key

        now = time.time()

        if provider == "memory":
            expires_at = _MEMORY_IDEMPOTENCY.get(resolved_key)
            if expires_at is not None and expires_at > now:
                duplicate = True
            elif expires_at is None and resolved_key in _MEMORY_IDEMPOTENCY:
                duplicate = True
            else:
                duplicate = False

            if not duplicate:
                _MEMORY_IDEMPOTENCY[resolved_key] = (now + ttl_s) if ttl_s else None

        elif provider == "redis":
            try:
                import redis  # type: ignore[import-not-found]
            except ImportError:
                return {
                    "idempotency_success": False,
                    "idempotency_error": "redis is required for provider='redis'",
                }

            client = redis.Redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0")
            )
            redis_key = f"microflow:idempotency:{resolved_key}"
            if ttl_s:
                was_set = client.set(redis_key, "1", ex=ttl_s, nx=True)
            else:
                was_set = client.set(redis_key, "1", nx=True)
            duplicate = not bool(was_set)

        else:
            return {
                "idempotency_success": False,
                "idempotency_error": f"Unsupported provider: {provider}",
            }

        result = {
            "key": resolved_key,
            "duplicate": duplicate,
            "should_process": not duplicate,
            "provider": provider,
            "ttl_s": ttl_s,
        }

        return {
            output_key: result,
            "idempotency_success": True,
            "idempotency_duplicate": duplicate,
            "idempotency_should_process": not duplicate,
        }

    return _idempotency_guard
