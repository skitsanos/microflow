"""Example: resource-aware workflow execution using WorkflowRunner limits."""

import asyncio
import time

from microflow import Workflow, WorkflowRunner, task


@task(name="io_step")
async def io_step(ctx):
    await asyncio.sleep(0.1)
    return {"done": True, "started_at": time.time()}


def build_workflow() -> Workflow:
    return Workflow([io_step], name="resource_optimized_demo", max_concurrent_tasks=1)


async def main():
    print("=== Resource Optimized Runner Example ===")
    runner = WorkflowRunner(max_concurrent_workflows=2)

    workflows = [build_workflow() for _ in range(5)]
    results = await asyncio.gather(
        *[
            runner.run_workflow(workflow, run_id=f"runner_example_{idx}")
            for idx, workflow in enumerate(workflows, start=1)
        ]
    )

    print(f"Completed {len(results)} workflows with global cap=2 and task cap=1")
    print("Sample result:", results[0])


if __name__ == "__main__":
    asyncio.run(main())
