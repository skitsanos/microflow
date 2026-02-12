# Conditional Nodes

## API

```python
if_node(condition, name=None, true_route='true', false_route='false')
switch_node(expression, cases, default_route='default', name=None)
conditional_task(route, condition_node=None, **task_kwargs)
if_equals(key, value, name=None)
if_greater_than(key, value, name=None)
if_exists(key, name=None)
switch_on_key(key, cases, default_route='default', name=None)
```

## Behavior

- `if_node` evaluates `condition` (string expression with `ctx` or callable) and writes route metadata:
  - `_route_<node_name>`
  - `_condition_result_<node_name>`
- `switch_node` evaluates `expression` and writes:
  - `_route_<node_name>`
  - `_switch_value_<node_name>`
  - `_matched_case_<node_name>`
- `conditional_task` wraps a task so it only runs when the selected route matches.

## Example

```python
from microflow import Workflow, if_node, conditional_task, task

branch = if_node("ctx.get('score', 0) >= 80", name="score_check")

@conditional_task(route="true", condition_node="score_check")
@task(name="passed")
def passed(ctx):
    return {"result": "pass"}

@conditional_task(route="false", condition_node="score_check")
@task(name="failed")
def failed(ctx):
    return {"result": "fail"}

branch >> passed
branch >> failed
workflow = Workflow([branch, passed, failed])
```
