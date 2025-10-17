"""Sub-workflow execution node"""

import asyncio
import importlib.util
import os
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..core.task_spec import task
from ..core.workflow import Workflow
from ..storage.json_store import JSONStateStore


class WorkflowLoader:
    """Utility for loading workflows from files or modules"""

    @staticmethod
    def load_from_file(file_path: str) -> Workflow:
        """Load a workflow from a Python file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")

        # Load the module
        spec = importlib.util.spec_from_file_location("workflow_module", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load workflow from {file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for a workflow creation function
        if hasattr(module, 'create_workflow'):
            return module.create_workflow()
        elif hasattr(module, 'workflow'):
            return module.workflow
        else:
            raise AttributeError(f"Workflow file {file_path} must define 'create_workflow()' function or 'workflow' variable")

    @staticmethod
    def load_from_module(module_path: str, workflow_name: str = "workflow") -> Workflow:
        """Load a workflow from an importable module"""
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, 'create_workflow'):
                return module.create_workflow()
            elif hasattr(module, workflow_name):
                return getattr(module, workflow_name)
            else:
                raise AttributeError(f"Module {module_path} must define 'create_workflow()' function or '{workflow_name}' variable")
        except ImportError as e:
            raise ImportError(f"Could not import module {module_path}: {e}")


def subworkflow(
    workflow_source: Union[str, Workflow, Callable[[], Workflow]],
    context_mapping: Optional[Dict[str, str]] = None,
    input_keys: Optional[List[str]] = None,
    output_keys: Optional[List[str]] = None,
    name: Optional[str] = None,
    inherit_store: bool = True,
    timeout_s: Optional[float] = None,
    max_retries: int = 0,
    backoff_s: float = 1.0
):
    """
    Create a sub-workflow execution node.

    Args:
        workflow_source: Source of the workflow:
            - String path to Python file containing workflow
            - Workflow instance
            - Callable that returns a workflow instance
        context_mapping: Map parent context keys to child context keys
            e.g., {"user_id": "current_user", "data": "input_data"}
        input_keys: List of context keys to pass to sub-workflow (all if None)
        output_keys: List of context keys to extract from sub-workflow result (all if None)
        name: Node name
        inherit_store: Whether child workflow uses same storage as parent
        timeout_s: Sub-workflow execution timeout
        max_retries: Number of retry attempts
        backoff_s: Backoff time between retries

    Returns sub-workflow results in context with keys:
        - subworkflow_success: Boolean indicating if sub-workflow succeeded
        - subworkflow_run_id: Child workflow run ID
        - subworkflow_result: Sub-workflow final context
        - (plus any output_keys specified)
    """
    node_name = name or f"subworkflow_{uuid.uuid4().hex[:8]}"

    @task(name=node_name, max_retries=max_retries, backoff_s=backoff_s,
          timeout_s=timeout_s, description="Execute sub-workflow")
    async def _subworkflow(ctx):
        # Load the workflow
        if isinstance(workflow_source, Workflow):
            child_workflow = workflow_source
        elif callable(workflow_source):
            child_workflow = workflow_source()
        elif isinstance(workflow_source, str):
            child_workflow = WorkflowLoader.load_from_file(workflow_source)
        else:
            raise ValueError(f"Invalid workflow_source type: {type(workflow_source)}")

        # Prepare child context
        child_ctx = {}

        if input_keys:
            # Only pass specified keys
            for key in input_keys:
                if key in ctx:
                    child_ctx[key] = ctx[key]
        else:
            # Pass all non-private context data
            child_ctx = {k: v for k, v in ctx.items() if not k.startswith("_")}

        # Apply context mapping
        if context_mapping:
            mapped_ctx = {}
            for parent_key, child_key in context_mapping.items():
                if parent_key in child_ctx:
                    mapped_ctx[child_key] = child_ctx[parent_key]
                    if child_key != parent_key:
                        del child_ctx[parent_key]
            child_ctx.update(mapped_ctx)

        # Set up storage for child workflow
        if inherit_store:
            # Use the same storage instance as parent
            # We'll need to pass this from the parent workflow execution
            child_store = ctx.get("_microflow_store")
            if child_store is None:
                child_store = JSONStateStore()
        else:
            child_store = JSONStateStore()

        # Generate unique run ID for child
        child_run_id = f"{node_name}_{uuid.uuid4().hex[:8]}"

        try:
            # Execute child workflow
            child_result = await child_workflow.run(
                run_id=child_run_id,
                store=child_store,
                initial_ctx=child_ctx
            )

            # Extract output data
            output_data = {}
            if output_keys:
                # Only extract specified keys
                for key in output_keys:
                    if key in child_result:
                        output_data[key] = child_result[key]
            else:
                # Extract all non-private data
                output_data = {k: v for k, v in child_result.items() if not k.startswith("_")}

            # Return results
            result = {
                "subworkflow_success": True,
                "subworkflow_run_id": child_run_id,
                "subworkflow_result": child_result
            }
            result.update(output_data)

            return result

        except Exception as e:
            return {
                "subworkflow_success": False,
                "subworkflow_run_id": child_run_id,
                "subworkflow_error": str(e),
                "subworkflow_result": None
            }

    return _subworkflow


def parallel_subworkflows(
    workflows: List[Dict[str, Any]],
    name: Optional[str] = None,
    max_concurrent: int = 5,
    timeout_s: Optional[float] = None
):
    """
    Execute multiple sub-workflows in parallel.

    Args:
        workflows: List of workflow configurations, each with:
            - source: Workflow source (file path, instance, or callable)
            - context_mapping: Optional context mapping
            - input_keys: Optional input keys filter
            - output_keys: Optional output keys filter
            - name: Optional workflow name
        name: Node name
        max_concurrent: Maximum number of concurrent sub-workflows
        timeout_s: Total timeout for all sub-workflows

    Returns:
        - parallel_results: List of results from each sub-workflow
        - parallel_success: Boolean indicating if all succeeded
        - parallel_summary: Summary statistics
    """
    node_name = name or "parallel_subworkflows"

    @task(name=node_name, timeout_s=timeout_s, description="Execute parallel sub-workflows")
    async def _parallel_subworkflows(ctx):
        # Create sub-workflow tasks
        subworkflow_tasks = []
        for i, wf_config in enumerate(workflows):
            sub_name = wf_config.get('name', f"parallel_{i}")
            sub_task = subworkflow(
                workflow_source=wf_config['source'],
                context_mapping=wf_config.get('context_mapping'),
                input_keys=wf_config.get('input_keys'),
                output_keys=wf_config.get('output_keys'),
                name=sub_name
            )
            subworkflow_tasks.append(sub_task.spec.fn(ctx))

        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(task):
            async with semaphore:
                return await task

        # Run all sub-workflows
        results = await asyncio.gather(
            *[run_with_semaphore(task) for task in subworkflow_tasks],
            return_exceptions=True
        )

        # Process results
        successful_results = []
        failed_results = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "index": i,
                    "error": str(result),
                    "workflow": workflows[i].get('name', f"parallel_{i}")
                })
            elif result.get('subworkflow_success', False):
                successful_results.append(result)
            else:
                failed_results.append({
                    "index": i,
                    "error": result.get('subworkflow_error', 'Unknown error'),
                    "workflow": workflows[i].get('name', f"parallel_{i}")
                })

        return {
            "parallel_results": results,
            "parallel_success": len(failed_results) == 0,
            "parallel_summary": {
                "total": len(workflows),
                "successful": len(successful_results),
                "failed": len(failed_results),
                "success_rate": len(successful_results) / len(workflows)
            },
            "parallel_successful": successful_results,
            "parallel_failed": failed_results
        }

    return _parallel_subworkflows


# Convenience functions
def load_workflow_from_file(file_path: str):
    """Load a workflow from a file for use in subworkflow nodes"""
    return lambda: WorkflowLoader.load_from_file(file_path)


def workflow_chain(*workflow_sources, context_keys: Optional[List[str]] = None):
    """
    Create a chain of sub-workflows that execute sequentially.

    Args:
        *workflow_sources: Workflow sources in execution order
        context_keys: Keys to pass between workflows in the chain
    """
    tasks = []
    for i, source in enumerate(workflow_sources):
        sub_task = subworkflow(
            workflow_source=source,
            input_keys=context_keys,
            output_keys=context_keys,
            name=f"chain_step_{i}"
        )
        tasks.append(sub_task)

    # Chain them together
    for i in range(len(tasks) - 1):
        tasks[i] >> tasks[i + 1]

    return tasks