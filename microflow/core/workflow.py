"""Core workflow engine implementation"""

import asyncio
import json
import time
import traceback
import uuid
from typing import Any, Dict, List, Optional, Set

from .task_spec import Task
from ..storage.json_store import JSONStateStore


class Workflow:
    """A workflow composed of tasks with dependencies"""

    def __init__(self, tasks: List[Task], name: str = ""):
        self.tasks = tasks
        self.name = name or f"workflow_{uuid.uuid4().hex[:8]}"

    def topo_sort(self) -> List[Task]:
        """Topological sort using Kahn's algorithm"""
        # Create a copy of upstream dependencies for each task
        incoming = {task: set(task.upstream) for task in self.tasks}
        ready = [task for task in self.tasks if not incoming[task]]
        order = []

        while ready:
            current = ready.pop()
            order.append(current)

            # Remove this task from its downstream tasks' incoming edges
            for downstream_task in list(current.downstream):
                incoming[downstream_task].discard(current)
                if not incoming[downstream_task]:
                    ready.append(downstream_task)

        if len(order) != len(self.tasks):
            cycle_tasks = [task for task in self.tasks if task not in order]
            raise RuntimeError(
                f"Cycle detected in workflow. Tasks in cycle: {cycle_tasks}"
            )

        return order

    async def _run_task(
        self, store: JSONStateStore, run_id: str, task: Task, ctx: Dict[str, Any]
    ) -> None:
        """Execute a single task with retries and error handling"""
        spec = task.spec
        attempt = 0

        while True:
            attempt += 1
            store.upsert_task(
                run_id,
                spec.name,
                status="running",
                attempt=attempt,
                input=json.dumps(ctx, default=str),
                output=None,
                error=None,
                started=time.time(),
                finished=None,
            )

            try:
                # Execute the task function
                result = spec.fn(ctx)

                # Handle async functions
                if asyncio.iscoroutine(result):
                    if spec.timeout_s:
                        result = await asyncio.wait_for(result, timeout=spec.timeout_s)
                    else:
                        result = await result

                # Merge result into context if it's a dict
                if isinstance(result, dict):
                    ctx.update(result)
                    store.update_ctx(run_id, result)

                # Mark task as successful
                store.upsert_task(
                    run_id,
                    spec.name,
                    status="success",
                    attempt=attempt,
                    output=json.dumps(result, default=str),
                    error=None,
                    finished=time.time(),
                )
                return

            except Exception as e:
                error_msg = "".join(
                    traceback.format_exception(type(e), e, e.__traceback__)
                )
                store.upsert_task(
                    run_id,
                    spec.name,
                    status="error",
                    attempt=attempt,
                    output=None,
                    error=error_msg,
                    finished=time.time(),
                )

                # Check if we should retry
                if attempt > spec.max_retries:
                    raise

                # Apply backoff before retry
                if spec.backoff_s > 0:
                    backoff_time = spec.backoff_s * (
                        2 ** (attempt - 1)
                    )  # Exponential backoff
                    await asyncio.sleep(backoff_time)

    async def run(
        self,
        run_id: Optional[str] = None,
        store: Optional[JSONStateStore] = None,
        initial_ctx: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the workflow"""
        if run_id is None:
            run_id = f"{self.name}_{uuid.uuid4().hex[:8]}"

        if store is None:
            store = JSONStateStore()

        if initial_ctx is None:
            initial_ctx = {}

        # Initialize the run
        store.init_run(run_id, initial_ctx)

        try:
            # Get topological order
            ordered_tasks = self.topo_sort()

            # Track which tasks have completed successfully
            completed_tasks: Set[Task] = set()
            remaining_tasks = set(ordered_tasks)
            ctx = store.get_ctx(run_id)

            # Add storage instance to context for sub-workflows
            ctx["_microflow_store"] = store

            while remaining_tasks:
                # Find tasks whose dependencies are all satisfied
                ready_tasks = [
                    task
                    for task in remaining_tasks
                    if all(
                        upstream_task in completed_tasks
                        for upstream_task in task.upstream
                    )
                ]

                if not ready_tasks:
                    store.set_run_status(run_id, "stalled")
                    raise RuntimeError(
                        "No runnable tasks; upstream failures or circular dependencies"
                    )

                # Execute ready tasks in parallel
                try:
                    await asyncio.gather(
                        *[
                            self._run_task(store, run_id, task, ctx)
                            for task in ready_tasks
                        ]
                    )

                    # Mark tasks as completed and remove from remaining
                    completed_tasks.update(ready_tasks)
                    for task in ready_tasks:
                        remaining_tasks.remove(task)

                except Exception:
                    store.set_run_status(run_id, "failed")
                    raise

            # All tasks completed successfully
            store.set_run_status(run_id, "success")
            return store.get_ctx(run_id)

        except Exception:
            if store.get_run_info(run_id)["status"] != "failed":
                store.set_run_status(run_id, "failed")
            raise

    def visualize(self) -> str:
        """Generate a simple text visualization of the workflow DAG"""
        lines = [f"Workflow: {self.name}"]
        lines.append("=" * 40)

        for task in self.tasks:
            deps = [t.spec.name for t in task.upstream]
            deps_str = f" (depends on: {', '.join(deps)})" if deps else ""
            lines.append(f"- {task.spec.name}{deps_str}")

        return "\n".join(lines)
