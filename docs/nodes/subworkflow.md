# Subworkflow Nodes

Subworkflow nodes enable workflow composition and reusability by allowing you to embed workflows within other workflows. They support parallel execution, workflow chaining, and dynamic workflow loading.

## Available Nodes

### subworkflow

Execute a complete workflow as a single node within another workflow.

**Parameters:**
- `workflow` (Workflow): The workflow to execute as a subworkflow
- `initial_context` (Dict[str, Any], optional): Initial context for the subworkflow
- `context_mapping` (Dict[str, str], optional): Map parent context keys to subworkflow context
- `output_mapping` (Dict[str, str], optional): Map subworkflow results back to parent context
- `timeout_seconds` (float, optional): Timeout for subworkflow execution
- `name` (str, optional): Node name

**Returns:**
- `subworkflow_success`: Boolean indicating if subworkflow completed successfully
- `subworkflow_duration`: Execution time of the subworkflow
- `subworkflow_name`: Name of the executed subworkflow
- `subworkflow_result`: Final context from subworkflow execution
- `subworkflow_error`: Error message if subworkflow failed

**Example:**
```python
from microflow import subworkflow, Workflow, task

# Create a reusable data processing subworkflow
@task(name="validate_data")
def validate_data(ctx):
    data = ctx.get("input_data", [])
    valid_items = [item for item in data if item.get("id")]
    return {"validated_data": valid_items}

@task(name="transform_data")
def transform_data(ctx):
    data = ctx.get("validated_data", [])
    transformed = [{"id": item["id"], "processed": True} for item in data]
    return {"processed_data": transformed}

# Create subworkflow
data_processing_workflow = Workflow(
    [validate_data, transform_data],
    name="data_processing"
)

validate_data >> transform_data

# Use as subworkflow in main workflow
process_user_data = subworkflow(
    workflow=data_processing_workflow,
    context_mapping={"user_data": "input_data"},
    output_mapping={"processed_data": "processed_users"},
    name="process_user_data_sub"
)
```

### parallel_subworkflows

Execute multiple workflows in parallel and collect their results.

**Parameters:**
- `workflows` (List[Workflow]): List of workflows to execute in parallel
- `context_for_each` (List[Dict[str, Any]], optional): Individual contexts for each workflow
- `shared_context` (Dict[str, Any], optional): Context shared by all workflows
- `max_concurrent` (int, optional): Maximum number of concurrent workflows
- `timeout_seconds` (float, optional): Timeout for all workflows
- `name` (str, optional): Node name

**Returns:**
- `parallel_success`: Boolean indicating if all workflows completed successfully
- `parallel_duration`: Total execution time
- `parallel_results`: List of results from each workflow
- `successful_count`: Number of workflows that completed successfully
- `failed_count`: Number of workflows that failed
- `parallel_errors`: List of errors from failed workflows

**Example:**
```python
from microflow import parallel_subworkflows, Workflow, task

# Create multiple processing workflows
@task(name="process_region_data")
def process_region_data(ctx):
    region = ctx.get("region", "unknown")
    data = ctx.get("data", [])
    processed = f"Processed {len(data)} items for {region}"
    return {"region_result": processed}

# Create workflows for different regions
region_workflow = Workflow([process_region_data], name="region_processing")

# Execute in parallel for different regions
parallel_processing = parallel_subworkflows(
    workflows=[region_workflow, region_workflow, region_workflow],
    context_for_each=[
        {"region": "North", "data": [1, 2, 3]},
        {"region": "South", "data": [4, 5, 6, 7]},
        {"region": "West", "data": [8, 9]}
    ],
    max_concurrent=2,
    name="parallel_region_processing"
)
```

### workflow_chain

Chain multiple workflows in sequence, passing results between them.

**Parameters:**
- `workflows` (List[Workflow]): List of workflows to execute in sequence
- `context_passthrough` (bool): Whether to pass context between workflows (default: True)
- `output_keys` (List[str], optional): Specific keys to pass between workflows
- `timeout_seconds` (float, optional): Total timeout for the chain
- `name` (str, optional): Node name

**Returns:**
- `chain_success`: Boolean indicating if all workflows in chain completed
- `chain_duration`: Total execution time for the chain
- `chain_results`: List of results from each workflow in the chain
- `chain_final_context`: Final context after all workflows
- `chain_errors`: List of errors from any failed workflows

**Example:**
```python
from microflow import workflow_chain, Workflow, task

# First workflow: data collection
@task(name="collect_data")
def collect_data(ctx):
    return {"raw_data": [1, 2, 3, 4, 5]}

collection_workflow = Workflow([collect_data], name="data_collection")

# Second workflow: data processing
@task(name="process_collected")
def process_collected(ctx):
    raw_data = ctx.get("raw_data", [])
    processed = [x * 2 for x in raw_data]
    return {"processed_data": processed}

processing_workflow = Workflow([process_collected], name="data_processing")

# Third workflow: data export
@task(name="export_processed")
def export_processed(ctx):
    data = ctx.get("processed_data", [])
    return {"export_result": f"Exported {len(data)} items"}

export_workflow = Workflow([export_processed], name="data_export")

# Chain workflows together
data_pipeline = workflow_chain(
    workflows=[collection_workflow, processing_workflow, export_workflow],
    context_passthrough=True,
    name="complete_data_pipeline"
)
```

## Dynamic Workflow Loading

### WorkflowLoader

Load workflows dynamically from configuration or files.

**Example:**
```python
from microflow import WorkflowLoader, task

# Create workflow loader
loader = WorkflowLoader()

# Register workflow factories
@loader.register("data_validation")
def create_validation_workflow(config):
    @task(name="validate")
    def validate(ctx):
        return {"validated": True}

    return Workflow([validate], name="validation")

# Load workflow dynamically
@task(name="load_dynamic_workflow")
def load_dynamic_workflow(ctx):
    workflow_type = ctx.get("workflow_type", "data_validation")
    config = ctx.get("workflow_config", {})

    workflow = loader.create_workflow(workflow_type, config)
    return {"loaded_workflow": workflow}
```

### load_workflow_from_file

Load workflow definitions from configuration files.

**Parameters:**
- `file_path` (str): Path to workflow configuration file
- `workflow_format` (str): File format ("json", "yaml", "python")
- `name` (str, optional): Node name

**Example:**
```python
from microflow import load_workflow_from_file

# Load workflow from JSON configuration
load_config_workflow = load_workflow_from_file(
    file_path="./workflows/data_processing.json",
    workflow_format="json",
    name="load_config_workflow"
)

# Load workflow from Python file
load_python_workflow = load_workflow_from_file(
    file_path="./workflows/custom_workflow.py",
    workflow_format="python",
    name="load_python_workflow"
)
```

## Advanced Usage Patterns

### Conditional Subworkflows

Execute different subworkflows based on conditions:

```python
from microflow import subworkflow, if_node, task, Workflow

# Create different processing workflows
@task(name="simple_processing")
def simple_processing(ctx):
    return {"result": "simple_processed"}

@task(name="complex_processing")
def complex_processing(ctx):
    return {"result": "complex_processed"}

simple_workflow = Workflow([simple_processing], name="simple")
complex_workflow = Workflow([complex_processing], name="complex")

# Conditional subworkflow execution
simple_sub = subworkflow(
    workflow=simple_workflow,
    name="simple_subworkflow"
)

complex_sub = subworkflow(
    workflow=complex_workflow,
    name="complex_subworkflow"
)

@task(name="determine_complexity")
def determine_complexity(ctx):
    data_size = len(ctx.get("input_data", []))
    return {"is_complex": data_size > 100}

# Use conditional node to choose subworkflow
conditional_processing = if_node(
    condition_expression="ctx.get('is_complex', False)",
    if_true_task=complex_sub,
    if_false_task=simple_sub,
    name="choose_processing_type"
)

determine_complexity >> conditional_processing
```

### Error Recovery with Subworkflows

Implement error recovery using fallback subworkflows:

```python
from microflow import subworkflow, task, Workflow

# Primary workflow that might fail
@task(name="risky_operation")
def risky_operation(ctx):
    # Simulate potential failure
    if ctx.get("simulate_failure", False):
        raise Exception("Simulated failure")
    return {"primary_result": "success"}

primary_workflow = Workflow([risky_operation], name="primary")

# Fallback workflow
@task(name="fallback_operation")
def fallback_operation(ctx):
    return {"fallback_result": "recovered"}

fallback_workflow = Workflow([fallback_operation], name="fallback")

# Execute with fallback
primary_sub = subworkflow(
    workflow=primary_workflow,
    name="primary_subworkflow"
)

fallback_sub = subworkflow(
    workflow=fallback_workflow,
    name="fallback_subworkflow"
)

@task(name="check_primary_success")
def check_primary_success(ctx):
    return {"primary_failed": not ctx.get("subworkflow_success", False)}

# Chain with fallback
recovery_flow = if_node(
    condition_expression="ctx.get('primary_failed', False)",
    if_true_task=fallback_sub,
    name="recovery_if_needed"
)

primary_sub >> check_primary_success >> recovery_flow
```

### Map-Reduce Pattern

Implement map-reduce operations using parallel subworkflows:

```python
from microflow import parallel_subworkflows, task, Workflow

# Map phase: process chunks in parallel
@task(name="process_chunk")
def process_chunk(ctx):
    chunk = ctx.get("data_chunk", [])
    chunk_sum = sum(chunk)
    return {"chunk_result": chunk_sum}

chunk_workflow = Workflow([process_chunk], name="chunk_processing")

@task(name="map_phase")
def map_phase(ctx):
    data = ctx.get("input_data", [])
    chunk_size = 10
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

    contexts = [{"data_chunk": chunk} for chunk in chunks]
    workflows = [chunk_workflow for _ in chunks]

    return {"chunk_contexts": contexts, "chunk_workflows": workflows}

# Parallel processing
parallel_map = parallel_subworkflows(
    workflows="{{ctx.chunk_workflows}}",
    context_for_each="{{ctx.chunk_contexts}}",
    name="parallel_map_processing"
)

# Reduce phase: combine results
@task(name="reduce_phase")
def reduce_phase(ctx):
    results = ctx.get("parallel_results", [])
    chunk_sums = [result.get("chunk_result", 0) for result in results]
    total_sum = sum(chunk_sums)
    return {"final_result": total_sum}

map_phase >> parallel_map >> reduce_phase
```

### Workflow Factory Pattern

Create workflows dynamically based on configuration:

```python
from microflow import task, Workflow, subworkflow

class WorkflowFactory:
    @staticmethod
    def create_processing_workflow(workflow_type: str, config: dict):
        if workflow_type == "data_validation":
            return WorkflowFactory._create_validation_workflow(config)
        elif workflow_type == "data_transformation":
            return WorkflowFactory._create_transformation_workflow(config)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

    @staticmethod
    def _create_validation_workflow(config):
        @task(name="validate_fields")
        def validate_fields(ctx):
            required_fields = config.get("required_fields", [])
            data = ctx.get("input_data", [])
            valid_items = [
                item for item in data
                if all(field in item for field in required_fields)
            ]
            return {"validated_data": valid_items}

        return Workflow([validate_fields], name="field_validation")

    @staticmethod
    def _create_transformation_workflow(config):
        @task(name="transform_data")
        def transform_data(ctx):
            transformations = config.get("transformations", {})
            data = ctx.get("input_data", [])
            # Apply transformations
            return {"transformed_data": data}

        return Workflow([transform_data], name="data_transformation")

@task(name="create_dynamic_workflow")
def create_dynamic_workflow(ctx):
    workflow_config = ctx.get("workflow_config", {})
    workflow_type = workflow_config.get("type", "data_validation")

    workflow = WorkflowFactory.create_processing_workflow(
        workflow_type,
        workflow_config
    )

    return {"dynamic_workflow": workflow}

# Use dynamic workflow
dynamic_sub = subworkflow(
    workflow="{{ctx.dynamic_workflow}}",
    name="dynamic_subworkflow"
)

create_dynamic_workflow >> dynamic_sub
```

## Context Management

### Context Isolation

Isolate context between parent and child workflows:

```python
from microflow import subworkflow, task, Workflow

@task(name="sensitive_operation")
def sensitive_operation(ctx):
    # This workflow should not see parent secrets
    return {"result": "processed"}

isolated_workflow = Workflow([sensitive_operation], name="isolated")

# Execute with isolated context
isolated_sub = subworkflow(
    workflow=isolated_workflow,
    initial_context={"safe_data": "value"},  # Only provide safe data
    context_mapping={},  # Don't map any parent context
    output_mapping={"result": "isolated_result"},  # Only map safe outputs
    name="isolated_execution"
)
```

### Context Transformation

Transform context data between workflows:

```python
from microflow import task, subworkflow, Workflow

@task(name="transform_context")
def transform_context(ctx):
    # Transform parent context for child workflow
    parent_data = ctx.get("parent_format_data", {})
    child_data = {
        "id": parent_data.get("identifier"),
        "name": parent_data.get("title"),
        "value": parent_data.get("amount", 0)
    }
    return {"child_format_data": child_data}

@task(name="process_child_data")
def process_child_data(ctx):
    data = ctx.get("child_format_data", {})
    return {"processed": True, "child_result": data}

child_workflow = Workflow([process_child_data], name="child")

# Transform and execute
transformed_sub = subworkflow(
    workflow=child_workflow,
    context_mapping={"child_format_data": "child_format_data"},
    output_mapping={"child_result": "final_result"},
    name="transformed_subworkflow"
)

transform_context >> transformed_sub
```

## Error Handling

Subworkflow nodes provide comprehensive error information:

```python
from microflow import subworkflow, task, Workflow

@task(name="potentially_failing_task")
def potentially_failing_task(ctx):
    if ctx.get("should_fail", False):
        raise Exception("Deliberate failure")
    return {"success": True}

risky_workflow = Workflow([potentially_failing_task], name="risky")

risky_sub = subworkflow(
    workflow=risky_workflow,
    timeout_seconds=30,
    name="risky_subworkflow"
)

@task(name="handle_subworkflow_result")
def handle_subworkflow_result(ctx):
    if ctx.get("subworkflow_success"):
        result = ctx.get("subworkflow_result", {})
        return {"status": "success", "message": "Subworkflow completed"}
    else:
        error = ctx.get("subworkflow_error", "Unknown error")
        duration = ctx.get("subworkflow_duration", 0)
        return {
            "status": "failed",
            "error": error,
            "duration": duration,
            "recovery_action": "retry_with_different_params"
        }

risky_sub >> handle_subworkflow_result
```

## Best Practices

1. **Design for reusability**: Create subworkflows that can be reused across different contexts
2. **Manage context carefully**: Be explicit about what context is passed to subworkflows
3. **Handle timeouts**: Set appropriate timeouts for subworkflow execution
4. **Error propagation**: Decide how errors should propagate from subworkflows to parent
5. **Resource management**: Consider resource usage when running parallel subworkflows
6. **Logging and monitoring**: Ensure subworkflow execution is properly logged
7. **Version compatibility**: Maintain compatibility when sharing subworkflows
8. **Security boundaries**: Use context isolation for sensitive operations
9. **Performance optimization**: Consider the overhead of subworkflow execution
10. **Testing strategies**: Test subworkflows both independently and as part of larger workflows