# Subworkflow Nodes

Use these nodes to compose reusable workflow modules and execute them sequentially or in parallel. Best practices: define clear input/output contracts between parent and child workflows, and cap concurrency to match available resources.

## API

```python
subworkflow(
    workflow_source,
    context_mapping=None,
    input_keys=None,
    output_keys=None,
    name=None,
    inherit_store=True,
    timeout_s=None,
    max_retries=0,
    backoff_s=1.0,
)

parallel_subworkflows(workflows, name=None, max_concurrent=5, timeout_s=None)
load_workflow_from_file(file_path)
workflow_chain(*workflow_sources, context_keys=None)
```

## WorkflowLoader

```python
WorkflowLoader.load_from_file(file_path)
WorkflowLoader.load_from_module(module_path, workflow_name='workflow')
```

`load_from_file` expects the Python file to expose either:

- `create_workflow()` function, or
- `workflow` variable.

## Behavior

- `subworkflow` accepts a workflow source as:
  - workflow instance,
  - callable returning a workflow,
  - path to workflow Python file.
- It returns keys including:
  - `subworkflow_success`
  - `subworkflow_run_id`
  - `subworkflow_result`
  - `subworkflow_error` on failure

## Example

```python
from microflow import subworkflow, Workflow
from myflows.user_flow import create_workflow

child = subworkflow(
    workflow_source=create_workflow,
    input_keys=["user_id"],
    output_keys=["user_profile"],
    name="profile_subflow",
)
```
