# Conditional Nodes

Conditional nodes allow you to implement branching logic in your workflows, similar to IF/ELSE statements and SWITCH/CASE structures in programming.

## Available Nodes

### if_node

Creates a conditional branch that executes different tasks based on a condition.

**Parameters:**
- `condition_expression` (str): Python expression to evaluate (ctx available)
- `if_true_task` (Task): Task to execute if condition is True
- `if_false_task` (Task, optional): Task to execute if condition is False
- `name` (str, optional): Node name

**Returns:**
- `condition_result`: Boolean result of the condition
- `condition_expression`: The expression that was evaluated
- `branch_taken`: "true" or "false" indicating which branch was executed

**Example:**
```python
from microflow import if_node, task

@task(name="process_high_value")
def process_high_value(ctx):
    return {"processing": "high_value_logic"}

@task(name="process_low_value")
def process_low_value(ctx):
    return {"processing": "low_value_logic"}

# Create conditional node
value_check = if_node(
    condition_expression="ctx.get('amount', 0) > 1000",
    if_true_task=process_high_value,
    if_false_task=process_low_value,
    name="value_check"
)
```

### switch_node

Creates a multi-way branch based on the value of an expression.

**Parameters:**
- `switch_expression` (str): Expression to evaluate for switching
- `cases` (Dict[str, Task]): Dictionary mapping values to tasks
- `default_task` (Task, optional): Task to execute if no case matches
- `name` (str, optional): Node name

**Returns:**
- `switch_value`: The value that was switched on
- `switch_expression`: The expression that was evaluated
- `case_matched`: Which case was matched (or "default")

**Example:**
```python
from microflow import switch_node, task

@task(name="handle_urgent")
def handle_urgent(ctx):
    return {"priority": "urgent_handling"}

@task(name="handle_normal")
def handle_normal(ctx):
    return {"priority": "normal_handling"}

@task(name="handle_low")
def handle_low(ctx):
    return {"priority": "low_handling"}

# Create switch node
priority_router = switch_node(
    switch_expression="ctx.get('priority', 'normal')",
    cases={
        "urgent": handle_urgent,
        "normal": handle_normal,
        "low": handle_low
    },
    name="priority_router"
)
```

### conditional_task

A decorator that adds conditional logic to any task.

**Parameters:**
- `condition` (str): Python expression for the condition
- `execute_if_false` (bool): Whether to execute if condition is False (default: True)

**Example:**
```python
from microflow import conditional_task, task

@conditional_task(condition="ctx.get('user_premium', False)")
@task(name="premium_feature")
def premium_feature(ctx):
    return {"feature": "premium_activated"}

# Only executes if user_premium is True
```

## Convenience Functions

### if_equals

Quick equality check conditional.

**Example:**
```python
from microflow import if_equals

status_check = if_equals(
    key="status",
    value="approved",
    if_true_task=approve_task,
    if_false_task=reject_task
)
```

### if_greater_than

Numeric comparison conditional.

**Example:**
```python
from microflow import if_greater_than

threshold_check = if_greater_than(
    key="score",
    threshold=80,
    if_true_task=pass_task,
    if_false_task=fail_task
)
```

### if_exists

Check if a key exists in context.

**Example:**
```python
from microflow import if_exists

data_check = if_exists(
    key="user_data",
    if_true_task=process_user,
    if_false_task=request_login
)
```

### switch_on_key

Switch based on a context key value.

**Example:**
```python
from microflow import switch_on_key

user_type_router = switch_on_key(
    key="user_type",
    cases={
        "admin": admin_task,
        "user": user_task,
        "guest": guest_task
    }
)
```

## Best Practices

1. **Keep expressions simple**: Use clear, readable expressions in conditions
2. **Handle edge cases**: Always consider what happens with missing data
3. **Use meaningful names**: Name your conditional nodes descriptively
4. **Provide defaults**: Use default tasks in switch nodes for fallback behavior
5. **Test conditions**: Verify your conditional logic with different data scenarios

## Common Patterns

### Data Validation Flow
```python
# Check if required data exists before processing
data_validator = if_exists(
    key="required_field",
    if_true_task=process_data,
    if_false_task=request_data
)
```

### User Permission Flow
```python
# Route based on user permissions
permission_router = switch_on_key(
    key="user_role",
    cases={
        "admin": admin_workflow,
        "moderator": moderator_workflow,
        "user": user_workflow
    },
    default_task=access_denied
)
```

### Error Handling
```python
# Handle different error states
error_handler = switch_on_key(
    key="error_code",
    cases={
        "404": not_found_handler,
        "403": permission_denied_handler,
        "500": server_error_handler
    },
    default_task=generic_error_handler
)
```