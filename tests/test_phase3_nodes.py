import asyncio

import pytest

from microflow import task
from microflow.nodes.resilience import retry_policy, circuit_breaker, foreach


def test_retry_policy_retries_and_succeeds():
    state = {"attempts": 0}

    @task(name="flaky")
    def flaky(ctx):
        state["attempts"] += 1
        if state["attempts"] < 3:
            raise RuntimeError("temporary")
        return {"ok": True}

    node = retry_policy(flaky, max_retries=4, initial_delay=0.0)
    result = asyncio.run(node.spec.fn({}))

    assert result["retry_successful"] is True
    assert result["retry_attempts"] == 3
    assert state["attempts"] == 3


def test_retry_policy_custom_retry_on_stops():
    state = {"attempts": 0}

    @task(name="always_fails")
    def always_fails(ctx):
        state["attempts"] += 1
        raise ValueError("stop")

    node = retry_policy(
        always_fails,
        max_retries=5,
        initial_delay=0.0,
        retry_on=lambda exc, result: False,
    )
    result = asyncio.run(node.spec.fn({}))

    assert result["retry_successful"] is False
    assert result["retry_attempts"] == 1
    assert state["attempts"] == 1


def test_circuit_breaker_opens_then_closes_after_recovery():
    state = {"calls": 0}

    @task(name="breaker_target")
    def breaker_target(ctx):
        state["calls"] += 1
        # first two calls fail, then succeed
        if state["calls"] <= 2:
            raise RuntimeError("boom")
        return {"job_success": True}

    node = circuit_breaker(
        breaker_target,
        failure_threshold=2,
        reset_timeout_s=0.0,
        half_open_max_calls=1,
    )

    first = asyncio.run(node.spec.fn({}))
    second = asyncio.run(node.spec.fn({}))
    third = asyncio.run(node.spec.fn({}))

    assert first["circuit_success"] is False
    assert second["circuit_open"] is True
    assert third["circuit_success"] is True
    assert third["circuit_state"] == "closed"


@pytest.mark.asyncio
async def test_foreach_collects_results_and_errors():
    @task(name="per_item")
    def per_item(ctx):
        item = ctx["item"]
        if item == 3:
            raise RuntimeError("bad item")
        return {"value": item * 10}

    node = foreach(per_item, data_key="nums", max_concurrent=2, output_key="out")
    result = await node.spec.fn({"nums": [1, 2, 3, 4]})

    assert result["foreach_success"] is False
    assert result["foreach_total"] == 4
    assert result["foreach_failed"] == 1
    assert [x["value"] for x in result["out"]] == [10, 20, 40]
    assert any(d["error"] for d in result["foreach_details"])
