# Microflow

A lightweight workflow engine for Python that provides deterministic task execution with dependency management, retries, and pluggable state persistence (JSON and Redis). Built with a comprehensive node ecosystem for real-world automation.

## ✨ Features

### Core Engine
- **Pure Python**: No external databases or services required
- **Async/Sync Support**: Mix async and sync tasks seamlessly
- **DAG-based Workflows**: Define task dependencies using simple `>>` operator
- **Retry Logic**: Configurable retries with exponential backoff
- **Pluggable Storage**: JSON file store (default) and Redis state store
- **Parallel Execution**: Automatic parallel execution of independent tasks
- **Context Passing**: Share data between tasks through workflow context
- **Workflow Runner Limits**: Global concurrency guard for workflow execution
- **Queue Abstractions**: In-memory queue by default, Redis queue when enabled
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
- **🔌 Integrations**: DB query/exec, ArangoDB AQL, cache, and S3/MinIO access
- **🛡️ Resilience**: Retry policies, circuit breakers, and foreach fan-out helpers
- **🧰 Utilities**: Schema validation, templating, batching, deduplication, pagination
- **🎛️ Control Plane**: Metrics, tracing, approvals, queue publish/consume, idempotency

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/skitsanos/microflow.git
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

### Redis Storage Backend

```python
from microflow import Workflow, RedisStateStore

store = RedisStateStore(redis_url="redis://localhost:6379/0")
result = await workflow.run("my_run_redis_001", store, {"user": "demo"})
```

### Concurrency Controls

You can cap workflow and task concurrency to control CPU/RAM usage:

- `MICROFLOW_MAX_CONCURRENT_WORKFLOWS`
- `MICROFLOW_MAX_CONCURRENT_TASKS`

Use `WorkflowRunner` for global workflow-level limits:

```python
from microflow import WorkflowRunner

runner = WorkflowRunner(max_concurrent_workflows=4)
result = await runner.run_workflow(workflow, run_id="run_001", store=store)
```

### Queue Provider Selection

Queue backend is selected via `QUEUE_PROVIDER`:

- `memory` (default)
- `redis` (only used when explicitly set)

```python
from microflow import create_workflow_queue_from_env

provider, queue = create_workflow_queue_from_env()
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
    filter_condition="item.get('website') is not None",
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
    to_addresses="admin@company.com",
    subject="User Export Complete",
    body="Exported users to CSV."
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
- **[🔌 Integrations](./docs/nodes/integrations.md)** - DB, cache, S3/MinIO nodes
- **[🛡️ Resilience](./docs/nodes/resilience.md)** - retries, circuit breaking, for-each fan-out
- **[🎛️ Control Plane](./docs/nodes/control-plane.md)** - metrics, tracing, queue, approval, idempotency

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

# Resource-optimized runner and queue demos
task examples:runner
task examples:queue
task examples:redis-store
task examples:resilience

# Run all examples
task examples:all
```

## 📁 Project Structure

```
microflow/
├── microflow/
│   ├── core/              # Core workflow engine
│   │   ├── workflow.py    # Main workflow execution engine
│   │   ├── runner.py      # WorkflowRunner with global concurrency cap
│   │   └── task_spec.py   # Task specification and decorators
│   ├── storage/           # Storage backends
│   │   ├── json_store.py  # JSON file-based state persistence
│   │   └── redis_store.py # Redis-backed state persistence
│   ├── queueing.py        # Queue providers (memory/redis)
│   └── nodes/             # Built-in node library
│       ├── conditional.py      # IF/ELSE, switch nodes
│       ├── http_request.py     # HTTP/API nodes
│       ├── shell.py           # System command nodes
│       ├── file_ops.py        # File operation nodes
│       ├── data_transform.py  # Data processing nodes
│       ├── timing.py          # Timing and delay nodes
│       ├── notifications.py   # Email/Slack notification nodes
│       ├── data_formats.py    # CSV/Excel format nodes
│       ├── utilities.py       # Validation, templating, batching helpers
│       ├── integrations.py    # DB/cache/S3/AQL integrations
│       ├── resilience.py      # Retry/circuit-breaker/foreach nodes
│       ├── control_plane.py   # Metrics/tracing/approval/queue nodes
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
task examples:runner       # Run WorkflowRunner concurrency demo
task examples:queue        # Run queue provider selection demo
task examples:redis-store  # Run RedisStateStore demo
task examples:resilience   # Run resilience nodes demo
task examples:all          # Run all examples

# Utilities
task clean             # Clean up build artifacts
task codex-review      # Run code review (if available)
task deps-up           # Start MinIO/Redis/Postgres for integration work
task deps-down         # Stop local integration dependencies
task deps-ps           # Show dependency container status
task deps-logs         # Tail dependency logs
```

## Local Integration Dependencies

Use Docker Compose to spin local services for integration testing and platform-node development:

```bash
task deps-up
```

Services:
- MinIO (S3-compatible): `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- Redis: `localhost:6379`
- Postgres: `localhost:5432`

Detailed setup: [`docs/development/local-dependencies.md`](./docs/development/local-dependencies.md)

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
from microflow import if_node, conditional_task, retry_policy

# Wrap an existing task with retry policy
reliable_api_call = retry_policy(
    wrapped_task=api_call,
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0
)

# Route between success and fallback branches
route_after_call = if_node("ctx.get('http_success', False)", name="api_route")

@conditional_task(route="true", condition_node="api_route", name="process_fresh")
def process_fresh_data(ctx):
    return {"source": "api"}

@conditional_task(route="false", condition_node="api_route", name="use_cache")
def use_cached_data(ctx):
    return {"source": "cache"}
```

### Parallel Processing
```python
from microflow import parallel_subworkflows

# Process multiple datasets concurrently
parallel_processing = parallel_subworkflows(
    workflows=[
        {"source": data_processor_north, "name": "region_north"},
        {"source": data_processor_south, "name": "region_south"},
        {"source": data_processor_west, "name": "region_west"},
    ],
    max_concurrent=2
)
```

### Conditional Workflows
```python
from microflow import switch_node

# Route based on data characteristics
data_router = switch_node(
    expression="ctx.get('data_type')",
    cases={
        "csv": "csv",
        "json": "json",
        "xml": "xml",
    },
    default_route="default"
)
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/skitsanos/microflow.git
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
- JSON and Redis state persistence backends
- Comprehensive node ecosystem (13 categories, 70+ nodes)
- Async/sync task support
- Retry logic and error handling
- Parallel task execution
- Queue providers (memory + redis via `QUEUE_PROVIDER`)
- Complete documentation

### 🚧 Planned Features
- REST API server
- Web-based workflow designer
- Distributed execution
- Additional durable storage backends beyond JSON/Redis
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
