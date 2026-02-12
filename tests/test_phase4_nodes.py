import asyncio

from microflow import task
from microflow.nodes.control_plane import (
    human_approval,
    idempotency_guard,
    metrics_emit,
    queue_consume,
    queue_publish,
    trace_span,
)


def test_metrics_emit_counter_increments():
    node = metrics_emit("jobs_processed", metric_type="counter", output_key="m")

    first = node.spec.fn({})
    second = node.spec.fn({})

    assert first["metric_success"] is True
    assert second["m"]["metric_value"] >= first["m"]["metric_value"]


def test_trace_span_wraps_task_result():
    @task(name="wrapped")
    def wrapped(ctx):
        return {"work_success": True, "x": 1}

    node = trace_span(wrapped, span_name="wrapped_span")
    result = asyncio.run(node.spec.fn({}))

    assert result["trace_success"] is True
    assert result["trace_span"]["span_name"] == "wrapped_span"
    assert result["x"] == 1


def test_human_approval_uses_context_decision():
    node = human_approval(prompt="Deploy to prod?", name="approval_gate")
    approved = node.spec.fn({"approval_decision_approval_gate": "approve"})
    rejected = node.spec.fn({"approval_decision_approval_gate": "reject"})

    assert approved["approval_result"]["approved"] is True
    assert rejected["approval_result"]["approved"] is False


def test_queue_publish_and_consume_memory_provider():
    publish = queue_publish(message_key="payload", provider="memory", output_key="mid")
    consume = queue_consume(provider="memory", output_key="msg")

    pub_result = publish.spec.fn({"payload": {"k": "v"}})
    con_result = consume.spec.fn({})

    assert pub_result["queue_success"] is True
    assert con_result["queue_success"] is True
    assert con_result["msg"]["k"] == "v"


def test_idempotency_guard_blocks_duplicates():
    node = idempotency_guard("job:{job_id}", provider="memory", output_key="idem")

    first = node.spec.fn({"job_id": "abc"})
    second = node.spec.fn({"job_id": "abc"})

    assert first["idempotency_should_process"] is True
    assert second["idempotency_should_process"] is False
