# Microflow

A lightweight workflow engine for Python that provides deterministic task execution with dependency management, retries, and JSON file-based state persistence.

## Features

- **Pure Python**: No external databases or services required
- **Async/Sync Support**: Mix async and sync tasks seamlessly
- **DAG-based Workflows**: Define task dependencies using simple `>>` operator
- **Retry Logic**: Configurable retries with exponential backoff
- **JSON Storage**: Human-readable state persistence using JSON files
- **Parallel Execution**: Automatic parallel execution of independent tasks
- **Context Passing**: Share data between tasks through workflow context
- **Modular Design**: Clean separation of concerns for easy extension

## Quick Start

### Setup

```bash
# Create virtual environment and install dependencies
task venv
task install

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Basic Example

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

## Project Structure

```
microflow/
├── microflow/
│   ├── core/           # Core workflow engine
│   ├── storage/        # Storage backends (JSON, future: Redis, etc.)
│   ├── api/           # REST API (planned)
│   ├── scheduler/     # Task scheduling (planned)
│   └── tasks/         # Built-in task types (planned)
├── examples/          # Example workflows
├── tests/            # Test suite
└── data/             # Runtime data (JSON files)
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

## Available Tasks

Use the Taskfile for common operations:

```bash
task venv          # Create virtual environment
task install       # Install dependencies
task test          # Run tests
task lint          # Check code style
task format        # Format code
task run           # Start API server (planned)
task example       # Run example workflow
task clean         # Clean up build artifacts
```

## Development

```bash
# Setup development environment
task venv
task install
task dev-install

# Run tests
task test

# Format and lint code
task format
task lint

# Run example
task example
```

## License

MIT License