"""Timer and delay nodes for workflow timing control"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..core.task_spec import task


def delay(
    seconds: float,
    name: Optional[str] = None
):
    """
    Add a delay to the workflow.

    Args:
        seconds: Number of seconds to delay
        name: Node name

    Returns delay information in context:
        - delay_seconds: Duration of delay
        - delay_start: Start timestamp
        - delay_end: End timestamp
    """
    node_name = name or f"delay_{seconds}s"

    @task(name=node_name, description=f"Delay for {seconds} seconds")
    async def _delay(ctx):
        start_time = time.time()

        await asyncio.sleep(seconds)

        end_time = time.time()

        return {
            "delay_seconds": seconds,
            "delay_start": start_time,
            "delay_end": end_time,
            "delay_actual": end_time - start_time
        }

    return _delay


def wait_until(
    target_time: str,
    time_format: str = "%Y-%m-%d %H:%M:%S",
    timezone: Optional[str] = None,
    name: Optional[str] = None
):
    """
    Wait until a specific time.

    Args:
        target_time: Target time string
        time_format: Time format for parsing
        timezone: Timezone (None for local)
        name: Node name
    """
    node_name = name or f"wait_until_{target_time}"

    @task(name=node_name, description=f"Wait until {target_time}")
    async def _wait_until(ctx):
        try:
            # Parse target time
            target_dt = datetime.strptime(target_time, time_format)
            current_dt = datetime.now()

            if target_dt <= current_dt:
                return {
                    "wait_success": True,
                    "wait_duration": 0,
                    "target_time": target_time,
                    "wait_message": "Target time already passed"
                }

            # Calculate wait duration
            wait_duration = (target_dt - current_dt).total_seconds()

            start_time = time.time()
            await asyncio.sleep(wait_duration)
            end_time = time.time()

            return {
                "wait_success": True,
                "wait_duration": wait_duration,
                "actual_duration": end_time - start_time,
                "target_time": target_time,
                "start_time": start_time,
                "end_time": end_time
            }

        except ValueError as e:
            return {
                "wait_success": False,
                "wait_error": f"Time parsing error: {e}",
                "target_time": target_time,
                "time_format": time_format
            }

    return _wait_until


def wait_for_condition(
    condition_expression: str,
    check_interval: float = 1.0,
    max_wait_time: Optional[float] = None,
    name: Optional[str] = None
):
    """
    Wait until a condition becomes true.

    Args:
        condition_expression: Python expression to evaluate (ctx available)
        check_interval: How often to check condition (seconds)
        max_wait_time: Maximum time to wait (None for no limit)
        name: Node name
    """
    node_name = name or f"wait_for_condition"

    @task(name=node_name, timeout_s=max_wait_time,
          description=f"Wait for condition: {condition_expression}")
    async def _wait_for_condition(ctx):
        start_time = time.time()
        checks = 0

        while True:
            checks += 1

            try:
                # Evaluate condition
                eval_context = {
                    'ctx': ctx,
                    '__builtins__': {}
                }

                if eval(condition_expression, eval_context):
                    end_time = time.time()
                    return {
                        "condition_met": True,
                        "wait_duration": end_time - start_time,
                        "condition_checks": checks,
                        "condition_expression": condition_expression
                    }

            except Exception as e:
                return {
                    "condition_met": False,
                    "condition_error": f"Condition evaluation error: {e}",
                    "condition_expression": condition_expression,
                    "condition_checks": checks
                }

            # Check timeout
            if max_wait_time and (time.time() - start_time) >= max_wait_time:
                return {
                    "condition_met": False,
                    "condition_timeout": True,
                    "wait_duration": time.time() - start_time,
                    "condition_checks": checks,
                    "condition_expression": condition_expression
                }

            await asyncio.sleep(check_interval)

    return _wait_for_condition


def timeout_wrapper(
    wrapped_task,
    timeout_seconds: float,
    name: Optional[str] = None
):
    """
    Wrap a task with a timeout.

    Args:
        wrapped_task: Task to wrap with timeout
        timeout_seconds: Timeout in seconds
        name: Node name
    """
    node_name = name or f"timeout_{wrapped_task.spec.name}"

    @task(name=node_name, description=f"Timeout wrapper for {wrapped_task.spec.name}")
    async def _timeout_wrapper(ctx):
        start_time = time.time()

        try:
            # Execute wrapped task with timeout
            result = await asyncio.wait_for(
                wrapped_task.spec.fn(ctx) if asyncio.iscoroutinefunction(wrapped_task.spec.fn)
                else asyncio.to_thread(wrapped_task.spec.fn, ctx),
                timeout=timeout_seconds
            )

            end_time = time.time()

            # Merge results and add timeout info
            if isinstance(result, dict):
                result.update({
                    "timeout_applied": True,
                    "timeout_seconds": timeout_seconds,
                    "execution_time": end_time - start_time,
                    "timed_out": False
                })
                return result
            else:
                return {
                    "wrapped_result": result,
                    "timeout_applied": True,
                    "timeout_seconds": timeout_seconds,
                    "execution_time": end_time - start_time,
                    "timed_out": False
                }

        except asyncio.TimeoutError:
            end_time = time.time()
            return {
                "timeout_applied": True,
                "timeout_seconds": timeout_seconds,
                "execution_time": end_time - start_time,
                "timed_out": True,
                "timeout_error": f"Task timed out after {timeout_seconds} seconds"
            }

    return _timeout_wrapper


def rate_limit(
    calls_per_second: float,
    burst_size: int = 1,
    name: Optional[str] = None
):
    """
    Rate limit task execution using token bucket algorithm.

    Args:
        calls_per_second: Maximum calls per second
        burst_size: Maximum burst size
        name: Node name
    """
    node_name = name or f"rate_limit_{calls_per_second}cps"

    # Shared state for rate limiting (in real implementation, would use Redis or similar)
    _bucket_state = {
        "tokens": burst_size,
        "last_update": time.time()
    }

    @task(name=node_name, description=f"Rate limit: {calls_per_second} calls/sec")
    async def _rate_limit(ctx):
        current_time = time.time()

        # Add tokens based on time elapsed
        time_passed = current_time - _bucket_state["last_update"]
        tokens_to_add = time_passed * calls_per_second
        _bucket_state["tokens"] = min(burst_size, _bucket_state["tokens"] + tokens_to_add)
        _bucket_state["last_update"] = current_time

        if _bucket_state["tokens"] >= 1:
            # Consume token and proceed
            _bucket_state["tokens"] -= 1
            return {
                "rate_limited": False,
                "tokens_remaining": _bucket_state["tokens"],
                "calls_per_second": calls_per_second
            }
        else:
            # Need to wait for next token
            wait_time = (1 - _bucket_state["tokens"]) / calls_per_second
            await asyncio.sleep(wait_time)

            _bucket_state["tokens"] = 0
            _bucket_state["last_update"] = time.time()

            return {
                "rate_limited": True,
                "wait_time": wait_time,
                "tokens_remaining": 0,
                "calls_per_second": calls_per_second
            }

    return _rate_limit


def schedule_at(
    schedule_time: str,
    time_format: str = "%Y-%m-%d %H:%M:%S",
    name: Optional[str] = None
):
    """
    Schedule task execution at specific time.

    Args:
        schedule_time: When to execute (future time)
        time_format: Time format for parsing
        name: Node name
    """
    node_name = name or f"schedule_at_{schedule_time}"

    @task(name=node_name, description=f"Schedule for {schedule_time}")
    async def _schedule_at(ctx):
        try:
            # Parse schedule time
            target_dt = datetime.strptime(schedule_time, time_format)
            current_dt = datetime.now()

            if target_dt <= current_dt:
                return {
                    "schedule_success": False,
                    "schedule_error": "Schedule time is in the past",
                    "schedule_time": schedule_time
                }

            # Calculate wait duration
            wait_duration = (target_dt - current_dt).total_seconds()

            # Wait until scheduled time
            await asyncio.sleep(wait_duration)

            return {
                "schedule_success": True,
                "scheduled_time": schedule_time,
                "actual_execution_time": datetime.now().strftime(time_format),
                "wait_duration": wait_duration
            }

        except ValueError as e:
            return {
                "schedule_success": False,
                "schedule_error": f"Time parsing error: {e}",
                "schedule_time": schedule_time,
                "time_format": time_format
            }

    return _schedule_at


def retry_with_backoff(
    wrapped_task,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    name: Optional[str] = None
):
    """
    Retry a task with exponential backoff.

    Args:
        wrapped_task: Task to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay between retries
        backoff_factor: Multiplier for delay after each retry
        max_delay: Maximum delay between retries
        name: Node name
    """
    node_name = name or f"retry_{wrapped_task.spec.name}"

    @task(name=node_name, description=f"Retry wrapper for {wrapped_task.spec.name}")
    async def _retry_with_backoff(ctx):
        last_error = None
        total_duration = 0

        for attempt in range(max_retries + 1):
            start_time = time.time()

            try:
                # Execute wrapped task
                if asyncio.iscoroutinefunction(wrapped_task.spec.fn):
                    result = await wrapped_task.spec.fn(ctx)
                else:
                    result = wrapped_task.spec.fn(ctx)

                execution_time = time.time() - start_time
                total_duration += execution_time

                # Success - add retry info to result
                if isinstance(result, dict):
                    result.update({
                        "retry_attempt": attempt + 1,
                        "retry_successful": True,
                        "total_retry_duration": total_duration
                    })
                    return result
                else:
                    return {
                        "wrapped_result": result,
                        "retry_attempt": attempt + 1,
                        "retry_successful": True,
                        "total_retry_duration": total_duration
                    }

            except Exception as e:
                execution_time = time.time() - start_time
                total_duration += execution_time
                last_error = e

                if attempt < max_retries:
                    # Calculate delay for next attempt
                    delay = min(initial_delay * (backoff_factor ** attempt), max_delay)
                    await asyncio.sleep(delay)
                    total_duration += delay

        # All retries failed
        return {
            "retry_successful": False,
            "retry_attempts": max_retries + 1,
            "total_retry_duration": total_duration,
            "last_error": str(last_error),
            "max_retries": max_retries
        }

    return _retry_with_backoff


def measure_execution_time(
    wrapped_task,
    name: Optional[str] = None
):
    """
    Measure execution time of a task.

    Args:
        wrapped_task: Task to measure
        name: Node name
    """
    node_name = name or f"measure_{wrapped_task.spec.name}"

    @task(name=node_name, description=f"Measure execution time for {wrapped_task.spec.name}")
    async def _measure_execution_time(ctx):
        start_time = time.time()

        try:
            # Execute wrapped task
            if asyncio.iscoroutinefunction(wrapped_task.spec.fn):
                result = await wrapped_task.spec.fn(ctx)
            else:
                result = wrapped_task.spec.fn(ctx)

            end_time = time.time()
            execution_time = end_time - start_time

            # Add timing info to result
            if isinstance(result, dict):
                result.update({
                    "execution_time": execution_time,
                    "start_time": start_time,
                    "end_time": end_time,
                    "timing_measured": True
                })
                return result
            else:
                return {
                    "wrapped_result": result,
                    "execution_time": execution_time,
                    "start_time": start_time,
                    "end_time": end_time,
                    "timing_measured": True
                }

        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time

            return {
                "execution_time": execution_time,
                "start_time": start_time,
                "end_time": end_time,
                "timing_measured": True,
                "execution_error": str(e)
            }

    return _measure_execution_time


# Convenience functions for common timing patterns
def sleep(seconds: float):
    """Simple sleep function"""
    return delay(seconds, name=f"sleep_{seconds}s")


def wait_seconds(seconds: float):
    """Alias for delay"""
    return delay(seconds, name=f"wait_{seconds}s")


def wait_minutes(minutes: float):
    """Wait for specified minutes"""
    return delay(minutes * 60, name=f"wait_{minutes}min")


def wait_hours(hours: float):
    """Wait for specified hours"""
    return delay(hours * 3600, name=f"wait_{hours}hr")


def daily_schedule(hour: int, minute: int = 0, second: int = 0):
    """Schedule for daily execution at specified time"""
    now = datetime.now()
    target_time = now.replace(hour=hour, minute=minute, second=second, microsecond=0)

    # If time has passed today, schedule for tomorrow
    if target_time <= now:
        target_time += timedelta(days=1)

    return schedule_at(
        target_time.strftime("%Y-%m-%d %H:%M:%S"),
        name=f"daily_{hour:02d}_{minute:02d}"
    )


def timeout_after(seconds: float):
    """Create a timeout node that fails after specified seconds"""
    @task(name=f"timeout_after_{seconds}s", description=f"Timeout after {seconds} seconds")
    async def _timeout_after(ctx):
        await asyncio.sleep(seconds)
        raise TimeoutError(f"Workflow timed out after {seconds} seconds")

    return _timeout_after