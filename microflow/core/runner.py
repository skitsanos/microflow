"""Workflow runner with global concurrency limits."""

import asyncio
import os
from typing import Any, Dict, Optional

from .workflow import Workflow
from ..storage.json_store import JSONStateStore


class WorkflowRunner:
    """Run workflows with a process-wide concurrency cap."""

    def __init__(self, max_concurrent_workflows: Optional[int] = None):
        if max_concurrent_workflows is None:
            env_cap = os.getenv("MICROFLOW_MAX_CONCURRENT_WORKFLOWS")
            if env_cap:
                try:
                    max_concurrent_workflows = max(1, int(env_cap))
                except ValueError:
                    max_concurrent_workflows = max(1, os.cpu_count() or 1)
            else:
                max_concurrent_workflows = max(1, os.cpu_count() or 1)

        self.max_concurrent_workflows = max(1, int(max_concurrent_workflows))
        self._semaphore = asyncio.Semaphore(self.max_concurrent_workflows)

    async def run_workflow(
        self,
        workflow: Workflow,
        run_id: Optional[str] = None,
        store: Optional[JSONStateStore] = None,
        initial_ctx: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a single workflow under the global concurrency guard."""
        async with self._semaphore:
            return await workflow.run(
                run_id=run_id, store=store, initial_ctx=initial_ctx
            )
