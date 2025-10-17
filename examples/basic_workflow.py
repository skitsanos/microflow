"""Basic workflow example demonstrating microflow features"""

import asyncio
import random
from microflow import Workflow, task, JSONStateStore


@task(name="fetch_data", max_retries=2, backoff_s=0.5, description="Fetch data from external source")
async def fetch_data(ctx):
    """Simulate fetching data from an external API"""
    print(f"Fetching data...")

    # Simulate network delay
    await asyncio.sleep(1)

    # Simulate occasional failures for retry demonstration
    if random.random() < 0.3:
        raise Exception("Network timeout")

    # Return data that will be merged into context
    return {
        "items": [1, 2, 3, 4, 5],
        "source": "external_api",
        "fetch_time": "2024-01-01T10:00:00Z"
    }


@task(name="transform_data", description="Transform and validate the fetched data")
def transform_data(ctx):
    """Transform the fetched data"""
    print(f"Transforming {len(ctx['items'])} items...")

    items = ctx["items"]
    total = sum(items)
    average = total / len(items)

    return {
        "total": total,
        "average": average,
        "item_count": len(items),
        "processed": True
    }


@task(name="branch_high", description="Handle high value scenarios")
async def branch_high(ctx):
    """Branch for high values"""
    if ctx["total"] >= 10:
        print(f"High value path: total={ctx['total']}")
        await asyncio.sleep(0.5)  # Simulate processing
        return {"path": "high_value", "bonus": 100}


@task(name="branch_low", description="Handle low value scenarios")
async def branch_low(ctx):
    """Branch for low values"""
    if ctx["total"] < 10:
        print(f"Low value path: total={ctx['total']}")
        await asyncio.sleep(0.3)  # Simulate processing
        return {"path": "low_value", "discount": 0.1}


@task(name="notify", max_retries=1, description="Send notification")
async def notify(ctx):
    """Send notification about the results"""
    path = ctx.get("path", "unknown")
    total = ctx.get("total", 0)

    print(f"Sending notification: path={path}, total={total}")

    # Simulate notification service
    await asyncio.sleep(0.2)

    return {
        "notification_sent": True,
        "notification_id": f"notif_{random.randint(1000, 9999)}"
    }


@task(name="audit_log", description="Log workflow completion")
def audit_log(ctx):
    """Log the workflow execution for audit purposes"""
    print("Writing audit log...")

    return {
        "audit_logged": True,
        "audit_id": f"audit_{random.randint(10000, 99999)}"
    }


def create_workflow():
    """Create and configure the workflow DAG"""

    # Build the DAG using the >> operator
    fetch_data >> transform_data
    transform_data >> branch_high
    transform_data >> branch_low
    branch_high >> notify
    branch_low >> notify
    notify >> audit_log

    # Create workflow with all tasks
    tasks = [fetch_data, transform_data, branch_high, branch_low, notify, audit_log]
    workflow = Workflow(tasks, name="basic_example")

    return workflow


async def main():
    """Run the example workflow"""
    print("=== Microflow Basic Example ===\n")

    # Create workflow
    workflow = create_workflow()

    # Print workflow structure
    print(workflow.visualize())
    print()

    # Create storage
    store = JSONStateStore("./data")

    # Run workflow
    try:
        print("Starting workflow execution...\n")

        final_ctx = await workflow.run(
            run_id="basic_example_001",
            store=store,
            initial_ctx={"user_id": "demo_user", "timestamp": "2024-01-01T10:00:00Z"}
        )

        print("\n=== Workflow Completed Successfully! ===")
        print("Final context:")
        for key, value in final_ctx.items():
            print(f"  {key}: {value}")

        # Show run information
        print("\n=== Run Information ===")
        run_info = store.get_run_info("basic_example_001")
        print(f"Run ID: {run_info['id']}")
        print(f"Status: {run_info['status']}")
        print(f"Started: {run_info['started']}")
        print(f"Finished: {run_info['finished']}")

        print("\n=== Task Results ===")
        for task_name, task_info in run_info['tasks'].items():
            print(f"{task_name}: {task_info['status']} (attempt {task_info['attempt']})")

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")

        # Show error details
        run_info = store.get_run_info("basic_example_001")
        print("\n=== Error Details ===")
        for task_name, task_info in run_info['tasks'].items():
            if task_info['status'] == 'error':
                print(f"Task {task_name} failed:")
                print(f"  Error: {task_info['error']}")


if __name__ == "__main__":
    asyncio.run(main())