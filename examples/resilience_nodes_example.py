"""Example: retry_policy, circuit_breaker, and foreach nodes."""

import asyncio

from microflow import Workflow, circuit_breaker, foreach, retry_policy, task


@task(name="flaky_api")
def flaky_api(ctx):
    item = ctx["item"]
    if item == 3:
        raise RuntimeError("transient error for item=3")
    return {"task_success": True, "value": item * 10}


async def main():
    print("=== Resilience Nodes Example ===")
    wrapped = retry_policy(flaky_api, max_retries=2, initial_delay=0.0)
    safe = circuit_breaker(wrapped, failure_threshold=3, reset_timeout_s=5.0)
    fanout = foreach(safe, data_key="numbers", item_key="item", max_concurrent=2)

    workflow = Workflow([fanout], name="resilience_demo")
    result = await workflow.run(
        "resilience_example_001",
        initial_ctx={"numbers": [1, 2, 3, 4]},
    )

    print("foreach_success:", result.get("foreach_success"))
    print("foreach_succeeded:", result.get("foreach_succeeded"))
    print("foreach_failed:", result.get("foreach_failed"))
    print("results:", result.get("foreach_results"))


if __name__ == "__main__":
    asyncio.run(main())
