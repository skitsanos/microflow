# Microflow Nodes Documentation

Welcome to the comprehensive documentation for Microflow nodes! This directory contains detailed guides for all available node types in the Microflow workflow engine.

## Node Categories

### 🔀 [Conditional Nodes](./conditional.md)
Control workflow branching and decision-making logic.

**Key Nodes:**
- `if_node` - Conditional branching based on expressions
- `switch_node` - Multi-way branching like switch/case statements
- `conditional_task` - Decorator for conditional task execution
- Convenience functions: `if_equals`, `if_greater_than`, `if_exists`, `switch_on_key`

**Use Cases:** Data validation, user permission routing, error handling, feature flags

---

### 🌐 [HTTP Request Nodes](./http.md)
Interact with web APIs and external services.

**Key Nodes:**
- `http_request` - Full-featured HTTP client with authentication
- `http_get`, `http_post`, `http_put`, `http_delete` - Convenience methods
- `webhook_call` - Webhook calls with retry logic
- `rest_api_call` - High-level REST API interaction

**Authentication:** `BearerAuth`, `BasicAuth`, `APIKeyAuth`

**Use Cases:** API integration, data fetching, webhook notifications, microservice communication

---

### 💻 [Shell and Process Nodes](./shell.md)
Execute system commands and interact with external processes.

**Key Nodes:**
- `shell_command` - Execute arbitrary shell commands
- `python_script` - Run Python scripts with virtual environment support
- `git_command` - Git operations with repository handling
- `docker_command` - Docker container management

**Use Cases:** System administration, deployment automation, file processing, CI/CD pipelines

---

### 📁 [File Operation Nodes](./file-operations.md)
Comprehensive filesystem operations for data management.

**Key Nodes:**
- `read_file`, `write_file` - File I/O operations
- `copy_file`, `move_file` - File manipulation
- `list_directory` - Directory listing with filtering

**Use Cases:** Log processing, configuration management, data archiving, file-based workflows

---

### 🔄 [Data Transformation Nodes](./data-transformation.md)
Process and manipulate data structures within workflows.

**Key Nodes:**
- `data_transform` - Apply custom transformations using Python expressions
- `data_filter` - Filter lists based on conditions
- `select_fields`, `rename_fields` - Field manipulation for dictionaries
- `json_parse`, `json_stringify` - JSON data handling

**Use Cases:** Data cleaning, ETL operations, API response processing, data validation

---

### ⏱️ [Timing and Delay Nodes](./timing.md)
Control workflow execution timing and scheduling.

**Key Nodes:**
- `delay`, `wait_until` - Time-based delays and scheduling
- `wait_for_condition` - Conditional waiting with polling
- `rate_limit` - Control execution rate using token bucket algorithm
- `timeout_wrapper`, `retry_with_backoff` - Task reliability features

**Use Cases:** API rate limiting, scheduled workflows, polling operations, retry logic

---

### 📧 [Notification Nodes](./notifications.md)
Send alerts and messages through various channels.

**Key Nodes:**
- `send_email` - Rich HTML/text emails with attachments
- `slack_notification` - Slack messages with Block Kit support
- `simple_email` - Quick email notifications

**Use Cases:** Workflow status alerts, error notifications, reporting, stakeholder communication

---

### 📊 [Data Format Nodes](./data-formats.md)
Convert between different file formats (CSV, Excel, JSON).

**Key Nodes:**
- `csv_read`, `csv_write` - CSV file operations
- `excel_read`, `excel_write` - Excel file operations (requires pandas/openpyxl)
- `csv_to_json`, `json_to_csv`, `excel_to_json` - Format conversions

**Use Cases:** Data import/export, report generation, format standardization, spreadsheet processing

---

### 🔗 [Subworkflow Nodes](./subworkflow.md)
Compose and reuse workflows within other workflows.

**Key Nodes:**
- `subworkflow` - Execute workflows as single nodes
- `parallel_subworkflows` - Execute multiple workflows in parallel
- `workflow_chain` - Chain workflows in sequence
- `WorkflowLoader`, `load_workflow_from_file` - Dynamic workflow loading

**Use Cases:** Workflow composition, code reusability, parallel processing, modular design

---

## Quick Start Guide

### Basic Node Usage

```python
from microflow import Workflow, task, http_get, data_filter, send_email

# Fetch data from API
fetch_users = http_get(
    url="https://api.example.com/users",
    output_key="users_data"
)

# Filter active users
filter_active = data_filter(
    filter_expression="item.get('status') == 'active'",
    data_key="users_data",
    output_key="active_users"
)

# Send notification
notify_admin = send_email(
    to="admin@company.com",
    subject="Active Users Report",
    body="Found {{len(ctx.active_users)}} active users."
)

# Chain nodes together
fetch_users >> filter_active >> notify_admin

# Create and run workflow
workflow = Workflow([fetch_users, filter_active, notify_admin])
```

### Node Chaining

Nodes can be chained using the `>>` operator to create dependencies:

```python
node_a >> node_b >> node_c  # Sequential execution
node_a >> node_b            # node_b waits for node_a
node_a >> node_c            # node_c also waits for node_a (parallel branches)
```

### Context Usage

Nodes share data through the workflow context:

```python
@task(name="setup_data")
def setup_data(ctx):
    return {"user_id": 123, "email": "user@example.com"}

# Use context data in subsequent nodes
fetch_profile = http_get(
    url="https://api.example.com/users/{{ctx.user_id}}",
    output_key="profile_data"
)

send_welcome = send_email(
    to="{{ctx.email}}",
    subject="Welcome!",
    body="Welcome {{ctx.profile_data.name}}!"
)

setup_data >> fetch_profile >> send_welcome
```

## Node Development Patterns

### Error Handling Pattern

```python
from microflow import http_get, if_node, send_email

api_call = http_get(url="https://api.example.com/data")

error_notification = send_email(
    to="admin@company.com",
    subject="API Error",
    body="API call failed: {{ctx.http_error}}"
)

# Only send notification if API call fails
error_check = if_node(
    condition_expression="not ctx.get('http_success', False)",
    if_true_task=error_notification
)

api_call >> error_check
```

### Retry Pattern

```python
from microflow import retry_with_backoff, http_get

unreliable_api = http_get(url="https://unreliable-api.example.com/data")

reliable_api = retry_with_backoff(
    wrapped_task=unreliable_api,
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0
)
```

### Parallel Processing Pattern

```python
from microflow import parallel_subworkflows, Workflow

# Create processing workflow
process_workflow = Workflow([process_data_task])

# Process multiple datasets in parallel
parallel_processing = parallel_subworkflows(
    workflows=[process_workflow] * 3,
    context_for_each=[
        {"dataset": "dataset_1"},
        {"dataset": "dataset_2"},
        {"dataset": "dataset_3"}
    ],
    max_concurrent=2
)
```

## Best Practices

### 1. Node Naming
Use descriptive names for better workflow visualization:
```python
fetch_user_data = http_get(url="...", name="fetch_user_data")
validate_user_email = data_filter(expression="...", name="validate_user_email")
```

### 2. Error Handling
Always check success flags and handle errors appropriately:
```python
@task(name="handle_api_result")
def handle_api_result(ctx):
    if ctx.get("http_success"):
        return {"status": "success", "data": ctx.get("http_response")}
    else:
        return {"status": "error", "message": ctx.get("http_error")}
```

### 3. Context Management
Keep context keys consistent and well-documented:
```python
# Good: Clear, consistent naming
setup_user_data >> fetch_user_profile >> process_user_info

# Bad: Inconsistent naming
setup_data >> get_profile >> handle_stuff
```

### 4. Resource Management
Be mindful of resource usage, especially for file operations and external calls:
```python
# Use timeouts for external calls
api_call = http_get(url="...", timeout=30)

# Clean up temporary files
cleanup_temp = shell_command(command="rm -f /tmp/workflow_*")
```

### 5. Security
Handle sensitive data carefully:
```python
# Use environment variables for credentials
secure_api = http_get(
    url="https://api.example.com/data",
    auth=BearerAuth(os.getenv("API_TOKEN"))
)

# Validate file paths
@task(name="validate_path")
def validate_path(ctx):
    path = ctx.get("file_path")
    if not path.startswith("/safe/directory/"):
        raise ValueError("Unsafe file path")
    return {"validated_path": path}
```

## Common Workflows

### ETL Pipeline
```python
# Extract
extract_data = csv_read(file_path="./input/data.csv")

# Transform
clean_data = data_filter(expression="item.get('status') == 'valid'")
transform_data = data_transform(expression="{'id': item['id'], 'name': item['name'].upper()}")

# Load
load_data = csv_write(data_key="transformed_data", file_path="./output/cleaned.csv")

extract_data >> clean_data >> transform_data >> load_data
```

### API Integration Workflow
```python
# Authenticate
auth_call = http_post(url="https://api.example.com/auth", data={"key": "secret"})

# Fetch data with token
fetch_data = http_get(
    url="https://api.example.com/data",
    headers={"Authorization": "Bearer {{ctx.access_token}}"}
)

# Process and notify
process_data = data_transform(expression="{'processed': True, **item}")
notify_complete = slack_notification(message="Data processing complete!")

auth_call >> fetch_data >> process_data >> notify_complete
```

### Monitoring Workflow
```python
# Check system health
check_cpu = shell_command(command="top -bn1 | grep 'Cpu(s)'", output_key="cpu_usage")
check_memory = shell_command(command="free -m", output_key="memory_usage")
check_disk = shell_command(command="df -h /", output_key="disk_usage")

# Alert if issues found
cpu_alert = if_node(
    condition_expression="'high' in ctx.get('cpu_usage', '').lower()",
    if_true_task=send_email(to="admin@company.com", subject="High CPU Alert")
)

check_cpu >> cpu_alert
check_memory >> memory_alert  # Similar pattern for memory
check_disk >> disk_alert      # Similar pattern for disk
```

## Node Reference Quick Links

- **[Conditional Nodes](./conditional.md)** - `if_node`, `switch_node`, conditional logic
- **[HTTP Nodes](./http.md)** - `http_request`, `http_get`, API integration
- **[Shell Nodes](./shell.md)** - `shell_command`, `python_script`, system operations
- **[File Nodes](./file-operations.md)** - `read_file`, `write_file`, filesystem operations
- **[Data Transform Nodes](./data-transformation.md)** - `data_transform`, `data_filter`, data processing
- **[Timing Nodes](./timing.md)** - `delay`, `wait_for_condition`, scheduling
- **[Notification Nodes](./notifications.md)** - `send_email`, `slack_notification`, alerts
- **[Data Format Nodes](./data-formats.md)** - `csv_read`, `excel_write`, format conversion
- **[Subworkflow Nodes](./subworkflow.md)** - `subworkflow`, workflow composition

For detailed examples and advanced usage patterns, refer to the individual node documentation files.