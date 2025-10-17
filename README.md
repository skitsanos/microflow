# Microflow

A lightweight, powerful workflow engine for Python that provides deterministic task execution with dependency management, retries, and JSON file-based state persistence. Built with a comprehensive node ecosystem for real-world automation.

## ✨ Features

### Core Engine
- **Pure Python**: No external databases or services required
- **Async/Sync Support**: Mix async and sync tasks seamlessly
- **DAG-based Workflows**: Define task dependencies using simple `>>` operator
- **Retry Logic**: Configurable retries with exponential backoff
- **JSON Storage**: Human-readable state persistence using JSON files
- **Parallel Execution**: Automatic parallel execution of independent tasks
- **Context Passing**: Share data between tasks through workflow context
- **Modular Design**: Clean separation of concerns for easy extension

### Rich Node Ecosystem
- **🔀 Conditional Nodes**: IF/ELSE logic, switch statements, conditional task execution
- **🌐 HTTP Nodes**: REST API calls, webhook integration, authentication support
- **💻 Shell Nodes**: System commands, Python scripts, Git operations, Docker management
- **📁 File Operations**: Read/write files, directory operations, file manipulation
- **🔄 Data Transformation**: JSON processing, data filtering, field selection/renaming
- **⏱️ Timing Nodes**: Delays, scheduling, rate limiting, timeout handling
- **📧 Notifications**: Email alerts, Slack integration, multi-channel messaging
- **📊 Data Formats**: CSV/Excel operations, format conversion, data import/export
- **🔗 Subworkflows**: Workflow composition, parallel execution, dynamic loading

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/microflow.git
cd microflow

# Setup with Task (recommended)
task setup

# Or manually:
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Basic Workflow Example

```python
import asyncio
from microflow import Workflow, task, JSONStateStore

@task(max_retries=2, backoff_s=0.5)
async def fetch_data(ctx):
    return {"items": [1, 2, 3, 4, 5]}

@task()
def transform_data(ctx):
    total = sum(ctx["items"])
    return {"total": total}

@task()
async def notify(ctx):
    print(f"Total: {ctx['total']}")
    return {"notified": True}

# Build workflow DAG
fetch_data >> transform_data >> notify

# Execute workflow
workflow = Workflow([fetch_data, transform_data, notify])
store = JSONStateStore("./data")

result = await workflow.run("my_run_001", store, {"user": "demo"})
```

### Using Built-in Nodes

```python
import asyncio
from microflow import (
    Workflow, JSONStateStore,
    http_get, data_filter, send_email, csv_write
)

# Fetch data from API
fetch_users = http_get(
    url="https://jsonplaceholder.typicode.com/users",
    output_key="users"
)

# Filter active users
filter_active = data_filter(
    filter_expression="item.get('website') is not None",
    data_key="users",
    output_key="active_users"
)

# Export to CSV
export_csv = csv_write(
    data_key="active_users",
    file_path="./output/active_users.csv"
)

# Send notification
notify_complete = send_email(
    to="admin@company.com",
    subject="User Export Complete",
    body="Exported {{len(ctx.active_users)}} active users to CSV."
)

# Chain the workflow
fetch_users >> filter_active >> export_csv >> notify_complete

# Execute
workflow = Workflow([fetch_users, filter_active, export_csv, notify_complete])
store = JSONStateStore("./data")

async def main():
    result = await workflow.run("user_export_001", store)
    print("Workflow completed!")

asyncio.run(main())
```

## 📖 Documentation

### Node Reference
Comprehensive documentation for all built-in nodes:

- **[📚 Complete Node Documentation](./docs/nodes/README.md)** - Overview and quick reference
- **[🔀 Conditional Nodes](./docs/nodes/conditional.md)** - IF/ELSE, switch logic
- **[🌐 HTTP Nodes](./docs/nodes/http.md)** - API calls, webhooks, authentication
- **[💻 Shell Nodes](./docs/nodes/shell.md)** - System commands, scripts
- **[📁 File Operations](./docs/nodes/file-operations.md)** - File I/O, directory operations
- **[🔄 Data Transformation](./docs/nodes/data-transformation.md)** - Data processing, filtering
- **[⏱️ Timing Nodes](./docs/nodes/timing.md)** - Delays, scheduling, rate limiting
- **[📧 Notifications](./docs/nodes/notifications.md)** - Email, Slack alerts
- **[📊 Data Formats](./docs/nodes/data-formats.md)** - CSV/Excel conversion
- **[🔗 Subworkflows](./docs/nodes/subworkflow.md)** - Workflow composition

### Examples
Run example workflows to see Microflow in action:

```bash
# Basic workflow example
task examples:basic

# HTTP and API integration
task examples:api

# Data processing pipeline
task examples:data-formats

# Extended nodes demonstration
task examples:extended

# Run all examples
task examples:all
```

## 📁 Project Structure

```
microflow/
├── microflow/
│   ├── core/              # Core workflow engine
│   │   ├── workflow.py    # Main workflow execution engine
│   │   └── task_spec.py   # Task specification and decorators
│   ├── storage/           # Storage backends
│   │   └── json_store.py  # JSON file-based state persistence
│   └── nodes/             # Built-in node library
│       ├── conditional.py      # IF/ELSE, switch nodes
│       ├── http_request.py     # HTTP/API nodes
│       ├── shell.py           # System command nodes
│       ├── file_ops.py        # File operation nodes
│       ├── data_transform.py  # Data processing nodes
│       ├── timing.py          # Timing and delay nodes
│       ├── notifications.py   # Email/Slack notification nodes
│       ├── data_formats.py    # CSV/Excel format nodes
│       └── subworkflow.py     # Workflow composition nodes
├── docs/
│   └── nodes/            # Comprehensive node documentation
├── examples/             # Example workflows and demos
├── tests/               # Test suite
└── data/                # Runtime workflow state (JSON files)
```

## Task Decorator Options

```python
@task(
    name="custom_name",           # Task name (defaults to function name)
    max_retries=3,               # Number of retry attempts
    backoff_s=1.0,               # Base backoff time in seconds
    timeout_s=30.0,              # Task timeout
    tags={"critical", "data"},    # Task tags for filtering
    description="Process data"    # Human-readable description
)
```

## Workflow Context

Tasks can read from and write to a shared context dictionary:

```python
@task()
def task_a(ctx):
    # Read from context
    user_id = ctx.get("user_id")

    # Write to context (return dict to merge)
    return {"processed_data": [1, 2, 3]}

@task()
def task_b(ctx):
    # Access data from task_a
    data = ctx["processed_data"]
    return {"result": sum(data)}
```

## Storage

Workflow state is persisted as JSON files in the data directory:

```
data/
└── runs/
    ├── my_run_001.json
    ├── my_run_002.json
    └── ...
```

Each run file contains complete workflow state including task status, inputs, outputs, and errors.

## 🛠️ Development Commands

Use the Taskfile for common operations:

```bash
# Environment Setup
task setup             # Complete project setup
task venv              # Create virtual environment
task install           # Install dependencies
task dev-install       # Install in development mode

# Code Quality
task test              # Run tests
task lint              # Check code style
task format            # Format code with black
task check             # Run all checks (lint + test)

# Examples
task examples:basic        # Run basic workflow example
task examples:api          # Run API integration example
task examples:data-formats # Run CSV/Excel demo
task examples:extended     # Run extended nodes demo
task examples:all          # Run all examples

# Utilities
task clean             # Clean up build artifacts
task codex-review      # Run code review (if available)
```

## 🎯 Use Cases

Microflow excels at automating complex workflows:

### Data Processing Pipelines
```python
# ETL workflow with validation and notifications
extract_data >> validate_schema >> transform_data >> load_database >> send_report
```

### API Integration & Monitoring
```python
# Monitor API health and alert on issues
check_api_health >> analyze_response >> conditional_alert >> update_dashboard
```

### System Administration
```python
# Automated backup and cleanup
backup_database >> compress_files >> upload_to_cloud >> cleanup_local >> notify_admins
```

### Business Process Automation
```python
# Invoice processing workflow
read_invoices >> validate_data >> update_accounting >> send_notifications >> archive_files
```

## 🔄 Common Patterns

### Error Handling with Fallbacks
```python
from microflow import if_node, retry_with_backoff

# Retry failed operations
reliable_api_call = retry_with_backoff(
    wrapped_task=api_call,
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0
)

# Fallback to alternative on failure
fallback_flow = if_node(
    condition_expression="not ctx.get('api_success', False)",
    if_true_task=use_cached_data,
    if_false_task=process_fresh_data
)
```

### Parallel Processing
```python
from microflow import parallel_subworkflows

# Process multiple datasets concurrently
parallel_processing = parallel_subworkflows(
    workflows=[data_processor] * 3,
    context_for_each=[
        {"dataset": "region_north"},
        {"dataset": "region_south"},
        {"dataset": "region_west"}
    ],
    max_concurrent=2
)
```

### Conditional Workflows
```python
from microflow import switch_node

# Route based on data characteristics
data_router = switch_node(
    switch_expression="ctx.get('data_type')",
    cases={
        "csv": csv_processor,
        "json": json_processor,
        "xml": xml_processor
    },
    default_task=generic_processor
)
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/your-username/microflow.git
cd microflow

# Setup development environment
task setup
task dev-install

# Run tests to ensure everything works
task test

# Check code quality
task lint
task format
```

### Adding New Nodes
1. Create your node in `microflow/nodes/`
2. Add comprehensive documentation in `docs/nodes/`
3. Include examples and tests
4. Update `microflow/__init__.py` exports
5. Add examples to demonstrate usage

### Running Tests
```bash
# Run all tests
task test

# Run specific test file
python -m pytest tests/test_specific.py -v

# Run with coverage
python -m pytest --cov=microflow tests/
```

## 📊 Status

**Current Version**: 0.1.0 (Active Development)

### ✅ Completed Features
- Core workflow engine with DAG execution
- JSON-based state persistence
- Comprehensive node ecosystem (9 categories, 50+ nodes)
- Async/sync task support
- Retry logic and error handling
- Parallel task execution
- Complete documentation

### 🚧 Planned Features
- REST API server
- Web-based workflow designer
- Distributed execution
- Additional storage backends (Redis, PostgreSQL)
- Workflow scheduling and cron-like triggers
- Monitoring and metrics dashboard

## 📄 License

MIT License

Copyright (c) 2024 Microflow Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.