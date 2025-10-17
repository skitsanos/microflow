"""Conditional execution nodes (IF and SWITCH)"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Union
from ..core.task_spec import task


def if_node(
    condition: Union[str, Callable[[Dict[str, Any]], bool]],
    name: Optional[str] = None,
    true_route: str = "true",
    false_route: str = "false"
):
    """
    Create an IF node that evaluates a condition and sets routing information.

    Args:
        condition: Either a string expression to evaluate or a callable that takes context and returns bool
        name: Node name (defaults to "if_condition")
        true_route: Route name for true condition (default: "true")
        false_route: Route name for false condition (default: "false")

    Usage:
        # Using string expression
        if_check = if_node("ctx['value'] > 10", "check_value")

        # Using callable
        if_check = if_node(lambda ctx: ctx.get('status') == 'active', "check_status")

        # Route downstream tasks
        @conditional_task(route="true")
        def handle_true(ctx): ...

        @conditional_task(route="false")
        def handle_false(ctx): ...

        if_check >> handle_true
        if_check >> handle_false
    """
    node_name = name or "if_condition"

    @task(name=node_name, description=f"IF condition: {condition}")
    def _if_node(ctx):
        try:
            if isinstance(condition, str):
                # Evaluate string expression safely
                result = eval(condition, {"ctx": ctx, "__builtins__": {}})
            else:
                # Call function with context
                result = condition(ctx)

            route = true_route if result else false_route

            return {
                f"_route_{node_name}": route,
                f"_condition_result_{node_name}": result
            }

        except Exception as e:
            return {
                f"_route_{node_name}": false_route,
                f"_condition_result_{node_name}": False,
                f"_condition_error_{node_name}": str(e)
            }

    return _if_node


def switch_node(
    expression: Union[str, Callable[[Dict[str, Any]], Any]],
    cases: Dict[Any, str],
    default_route: str = "default",
    name: Optional[str] = None
):
    """
    Create a SWITCH node that evaluates an expression and routes based on value matching.

    Args:
        expression: String expression or callable that returns a value to match
        cases: Dictionary mapping values to route names
        default_route: Route name when no case matches (default: "default")
        name: Node name (defaults to "switch_expression")

    Usage:
        switch_status = switch_node(
            "ctx['status']",
            {
                'pending': 'handle_pending',
                'approved': 'handle_approved',
                'rejected': 'handle_rejected'
            },
            default_route='handle_unknown'
        )

        @conditional_task(route="handle_pending")
        def process_pending(ctx): ...

        @conditional_task(route="handle_approved")
        def process_approved(ctx): ...
    """
    node_name = name or "switch_expression"

    @task(name=node_name, description=f"SWITCH on: {expression}")
    def _switch_node(ctx):
        try:
            if isinstance(expression, str):
                # Evaluate string expression safely
                value = eval(expression, {"ctx": ctx, "__builtins__": {}})
            else:
                # Call function with context
                value = expression(ctx)

            route = cases.get(value, default_route)

            return {
                f"_route_{node_name}": route,
                f"_switch_value_{node_name}": value,
                f"_matched_case_{node_name}": value in cases
            }

        except Exception as e:
            return {
                f"_route_{node_name}": default_route,
                f"_switch_value_{node_name}": None,
                f"_switch_error_{node_name}": str(e)
            }

    return _switch_node


def conditional_task(
    route: str,
    condition_node: Optional[str] = None,
    **task_kwargs
):
    """
    Decorator for tasks that should only execute when a specific route is active.

    Args:
        route: The route name this task should execute for
        condition_node: Name of the condition node to check (auto-detected if not provided)
        **task_kwargs: Additional arguments for the task decorator

    Usage:
        if_check = if_node("ctx['value'] > 10", "check_value")

        @conditional_task(route="true", condition_node="check_value")
        def handle_high_value(ctx):
            return {"message": "High value detected"}

        @conditional_task(route="false", condition_node="check_value")
        def handle_low_value(ctx):
            return {"message": "Low value detected"}
    """
    def decorator(func):
        # Check if func is already a Task
        if hasattr(func, 'spec'):
            original_task = func
            original_fn = func.spec.fn
        else:
            original_task = task(**task_kwargs)(func)
            original_fn = original_task.spec.fn

        async def conditional_wrapper(ctx):
            # Find the route information in context
            route_key = None
            if condition_node:
                route_key = f"_route_{condition_node}"
            else:
                # Auto-detect by looking for any route key
                for key in ctx.keys():
                    if key.startswith("_route_"):
                        route_key = key
                        break

            if route_key and ctx.get(route_key) == route:
                # Route matches, execute the task
                if asyncio.iscoroutinefunction(original_fn):
                    return await original_fn(ctx)
                else:
                    return original_fn(ctx)
            else:
                # Route doesn't match, skip execution
                return {"_skipped": True, "_reason": f"Route {route} not active"}

        # Create new task with conditional wrapper
        new_spec = original_task.spec
        new_spec.fn = conditional_wrapper

        return original_task

    return decorator


# Convenience functions for common patterns
def if_equals(key: str, value: Any, name: Optional[str] = None):
    """Create an IF node that checks if a context key equals a specific value"""
    return if_node(f"ctx.get('{key}') == {repr(value)}", name or f"if_{key}_equals_{value}")


def if_greater_than(key: str, value: Union[int, float], name: Optional[str] = None):
    """Create an IF node that checks if a context key is greater than a value"""
    return if_node(f"ctx.get('{key}', 0) > {value}", name or f"if_{key}_gt_{value}")


def if_exists(key: str, name: Optional[str] = None):
    """Create an IF node that checks if a context key exists and is truthy"""
    return if_node(f"bool(ctx.get('{key}'))", name or f"if_{key}_exists")


def switch_on_key(key: str, cases: Dict[Any, str], default_route: str = "default", name: Optional[str] = None):
    """Create a SWITCH node that switches on a context key value"""
    return switch_node(f"ctx.get('{key}')", cases, default_route, name or f"switch_on_{key}")