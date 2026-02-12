"""Resilience nodes for retries, circuit breaking, and per-item execution."""

import asyncio
import time
from typing import Any, Callable, Dict, Optional

from ..core.task_spec import Task, task


def _result_indicates_success(result: Any) -> bool:
    """Infer success from dict payloads with *_success flags."""
    if not isinstance(result, dict):
        return True

    success_flags = [
        v for k, v in result.items() if k.endswith("_success") and isinstance(v, bool)
    ]
    if not success_flags:
        return True
    return all(success_flags)


def retry_policy(
    wrapped_task: Task,
    retry_on: Optional[Callable[[Optional[Exception], Any], bool]] = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    name: Optional[str] = None,
):
    """Retry a task with policy-driven retry decisions."""
    node_name = name or f"retry_policy_{wrapped_task.spec.name}"

    @task(name=node_name, description=f"Retry policy for {wrapped_task.spec.name}")
    async def _retry_policy(ctx):
        last_error: Optional[Exception] = None
        last_result: Any = None
        attempts = 0
        total_duration = 0.0

        while attempts <= max_retries:
            attempts += 1
            start_time = time.time()

            try:
                result = wrapped_task.spec.fn(ctx)
                if asyncio.iscoroutine(result):
                    result = await result

                total_duration += time.time() - start_time
                should_retry = False
                if retry_on is not None:
                    should_retry = bool(retry_on(None, result))

                if not should_retry:
                    if isinstance(result, dict):
                        result.update(
                            {
                                "retry_successful": True,
                                "retry_attempts": attempts,
                                "total_retry_duration": total_duration,
                            }
                        )
                        return result

                    return {
                        "wrapped_result": result,
                        "retry_successful": True,
                        "retry_attempts": attempts,
                        "total_retry_duration": total_duration,
                    }

                last_result = result

            except Exception as e:
                total_duration += time.time() - start_time
                last_error = e
                should_retry = retry_on(e, None) if retry_on is not None else True
                if not should_retry:
                    break

            if attempts > max_retries:
                break

            delay = min(initial_delay * (backoff_factor ** (attempts - 1)), max_delay)
            await asyncio.sleep(delay)
            total_duration += delay

        return {
            "retry_successful": False,
            "retry_attempts": attempts,
            "total_retry_duration": total_duration,
            "last_error": str(last_error) if last_error else None,
            "last_result": last_result,
            "max_retries": max_retries,
        }

    return _retry_policy


def circuit_breaker(
    wrapped_task: Task,
    failure_threshold: int = 5,
    reset_timeout_s: float = 60.0,
    half_open_max_calls: int = 1,
    name: Optional[str] = None,
):
    """Wrap a task with a stateful circuit breaker."""
    node_name = name or f"circuit_breaker_{wrapped_task.spec.name}"

    state: Dict[str, Any] = {
        "mode": "closed",  # closed | open | half_open
        "failure_count": 0,
        "opened_at": None,
        "half_open_calls": 0,
    }

    @task(name=node_name, description=f"Circuit breaker for {wrapped_task.spec.name}")
    async def _circuit_breaker(ctx):
        now = time.time()

        if state["mode"] == "open":
            opened_at = state["opened_at"] or now
            if (now - opened_at) < reset_timeout_s:
                return {
                    "circuit_success": False,
                    "circuit_open": True,
                    "circuit_state": "open",
                    "circuit_failure_count": state["failure_count"],
                }

            state["mode"] = "half_open"
            state["half_open_calls"] = 0

        if (
            state["mode"] == "half_open"
            and state["half_open_calls"] >= half_open_max_calls
        ):
            return {
                "circuit_success": False,
                "circuit_open": True,
                "circuit_state": "half_open",
                "circuit_failure_count": state["failure_count"],
            }

        try:
            if state["mode"] == "half_open":
                state["half_open_calls"] += 1

            result = wrapped_task.spec.fn(ctx)
            if asyncio.iscoroutine(result):
                result = await result

            success = _result_indicates_success(result)
            if not success:
                raise RuntimeError("Wrapped task returned unsuccessful result")

            # success path closes breaker
            state["mode"] = "closed"
            state["failure_count"] = 0
            state["opened_at"] = None
            state["half_open_calls"] = 0

            if isinstance(result, dict):
                result.update(
                    {
                        "circuit_success": True,
                        "circuit_open": False,
                        "circuit_state": "closed",
                        "circuit_failure_count": 0,
                    }
                )
                return result

            return {
                "wrapped_result": result,
                "circuit_success": True,
                "circuit_open": False,
                "circuit_state": "closed",
                "circuit_failure_count": 0,
            }

        except Exception as e:
            state["failure_count"] += 1
            if state["failure_count"] >= failure_threshold:
                state["mode"] = "open"
                state["opened_at"] = time.time()

            return {
                "circuit_success": False,
                "circuit_open": state["mode"] == "open",
                "circuit_state": state["mode"],
                "circuit_failure_count": state["failure_count"],
                "circuit_error": str(e),
            }

    return _circuit_breaker


def foreach(
    wrapped_task: Task,
    data_key: str = "data",
    item_key: str = "item",
    max_concurrent: int = 5,
    output_key: str = "foreach_results",
    name: Optional[str] = None,
):
    """Execute a task for each item in a list with bounded concurrency."""
    node_name = name or f"foreach_{wrapped_task.spec.name}"

    @task(name=node_name, description=f"For-each wrapper for {wrapped_task.spec.name}")
    async def _foreach(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "foreach_success": False,
                "foreach_error": f"No data found in context key: {data_key}",
            }
        if not isinstance(data, list):
            return {
                "foreach_success": False,
                "foreach_error": "Data must be a list",
            }
        if max_concurrent <= 0:
            return {
                "foreach_success": False,
                "foreach_error": "max_concurrent must be greater than 0",
            }

        semaphore = asyncio.Semaphore(max_concurrent)
        details = []

        async def run_item(index: int, item: Any) -> Dict[str, Any]:
            async with semaphore:
                item_ctx = dict(ctx)
                item_ctx[item_key] = item
                item_ctx["_foreach_index"] = index

                try:
                    result = wrapped_task.spec.fn(item_ctx)
                    if asyncio.iscoroutine(result):
                        result = await result
                    return {
                        "index": index,
                        "item": item,
                        "success": True,
                        "result": result,
                        "error": None,
                    }
                except Exception as e:
                    return {
                        "index": index,
                        "item": item,
                        "success": False,
                        "result": None,
                        "error": str(e),
                    }

        details = await asyncio.gather(
            *[run_item(i, item) for i, item in enumerate(data)]
        )

        successful = [d for d in details if d["success"]]
        failed = [d for d in details if not d["success"]]
        results = [d["result"] for d in successful]

        return {
            output_key: results,
            "foreach_details": details,
            "foreach_success": len(failed) == 0,
            "foreach_total": len(details),
            "foreach_succeeded": len(successful),
            "foreach_failed": len(failed),
            "foreach_item_key": item_key,
        }

    return _foreach
