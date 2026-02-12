"""Example: RedisStateStore usage for workflow state persistence."""

import asyncio

from microflow import JSONStateStore, RedisStateStore, Workflow, task


@task(name="prepare")
def prepare(ctx):
    return {"value": 10}


@task(name="compute")
def compute(ctx):
    return {"result": ctx["value"] * 2}


def resolve_store():
    try:
        return RedisStateStore()
    except Exception as e:
        print(f"Redis unavailable, using JSONStateStore fallback: {e}")
        return JSONStateStore("./data")


async def main():
    print("=== Redis State Store Example ===")
    prepare >> compute
    workflow = Workflow([prepare, compute], name="redis_state_store_demo")
    store = resolve_store()

    result = await workflow.run("redis_store_example_001", store, {"source": "example"})
    print("Workflow result:", result)
    print("Run status:", store.get_run_info("redis_store_example_001").get("status"))


if __name__ == "__main__":
    asyncio.run(main())
