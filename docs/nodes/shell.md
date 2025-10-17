# Shell and Process Nodes

Shell nodes allow your workflows to execute system commands, run scripts, and interact with external processes. They provide comprehensive control over command execution and output handling.

## Available Nodes

### shell_command

Execute arbitrary shell commands with full control over execution environment.

**Parameters:**
- `command` (str): Shell command to execute
- `cwd` (str, optional): Working directory for command execution
- `env` (Dict[str, str], optional): Environment variables
- `timeout` (float, optional): Command timeout in seconds
- `capture_output` (bool): Whether to capture stdout/stderr (default: True)
- `shell` (bool): Whether to run command through shell (default: True)
- `output_key` (str): Context key to store output (default: "shell_output")
- `name` (str, optional): Node name

**Returns:**
- `shell_success`: Boolean indicating if command succeeded (exit code 0)
- `shell_exit_code`: Process exit code
- `shell_execution_time`: Execution time in seconds
- `[output_key]`: Command output (stdout)
- `shell_stderr`: Error output (stderr)
- `shell_command`: The command that was executed

**Example:**
```python
from microflow import shell_command

# Simple command execution
list_files = shell_command(
    command="ls -la",
    cwd="/tmp",
    name="list_temp_files"
)

# Command with environment variables
backup_db = shell_command(
    command="pg_dump $DB_NAME > backup.sql",
    env={"DB_NAME": "myapp_production"},
    timeout=300,
    name="backup_database"
)
```

### python_script

Execute Python scripts with automatic virtual environment handling.

**Parameters:**
- `script_path` (str): Path to Python script
- `args` (List[str], optional): Command line arguments
- `venv_path` (str, optional): Virtual environment path
- `python_executable` (str): Python executable (default: "python3")
- `timeout` (float, optional): Script timeout in seconds
- `cwd` (str, optional): Working directory

**Example:**
```python
from microflow import python_script

# Run data processing script
process_data = python_script(
    script_path="./scripts/process_data.py",
    args=["--input", "data.csv", "--output", "processed.csv"],
    venv_path="./.venv",
    timeout=600
)

# Run analysis with specific Python version
analyze_results = python_script(
    script_path="./analysis/analyze.py",
    python_executable="python3.11",
    cwd="./analysis"
)
```

### git_command

Execute Git commands with built-in repository handling.

**Parameters:**
- `git_command` (str): Git subcommand (e.g., "status", "pull", "commit")
- `args` (List[str], optional): Additional arguments
- `repo_path` (str, optional): Repository path (default: current directory)
- `timeout` (float): Command timeout (default: 60)

**Example:**
```python
from microflow import git_command

# Check repository status
git_status = git_command(
    git_command="status",
    args=["--porcelain"],
    repo_path="./my-repo"
)

# Pull latest changes
git_pull = git_command(
    git_command="pull",
    args=["origin", "main"],
    repo_path="./my-repo"
)

# Commit changes
git_commit = git_command(
    git_command="commit",
    args=["-m", "Automated commit from workflow"],
    repo_path="./my-repo"
)
```

### docker_command

Execute Docker commands and manage containers.

**Parameters:**
- `docker_command` (str): Docker subcommand
- `args` (List[str], optional): Additional arguments
- `timeout` (float): Command timeout (default: 300)
- `capture_logs` (bool): Whether to capture container logs (default: True)

**Example:**
```python
from microflow import docker_command

# Build Docker image
build_image = docker_command(
    docker_command="build",
    args=["-t", "myapp:latest", "."],
    timeout=600
)

# Run container
run_container = docker_command(
    docker_command="run",
    args=["-d", "--name", "myapp-instance", "myapp:latest"],
    capture_logs=True
)

# Get container logs
get_logs = docker_command(
    docker_command="logs",
    args=["myapp-instance"]
)
```

## Advanced Usage

### Command Chaining

Chain multiple shell commands together:

```python
from microflow import shell_command, Workflow

# Setup commands
create_directory = shell_command(
    command="mkdir -p /tmp/workflow-data",
    name="create_directory"
)

download_data = shell_command(
    command="curl -o /tmp/workflow-data/data.json https://api.example.com/data",
    name="download_data"
)

process_data = shell_command(
    command="python process.py /tmp/workflow-data/data.json",
    name="process_data"
)

# Chain execution
create_directory >> download_data >> process_data
```

### Dynamic Commands

Use context data to build dynamic commands:

```python
from microflow import task, shell_command

@task(name="setup_backup")
def setup_backup(ctx):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "backup_filename": f"backup_{timestamp}.tar.gz",
        "source_directory": ctx.get("data_directory", "/data")
    }

# Use dynamic data in command
backup_data = shell_command(
    command="tar -czf {{ctx.backup_filename}} {{ctx.source_directory}}",
    name="backup_data"
)
```

### Conditional Execution

Execute commands based on previous results:

```python
from microflow import shell_command, if_node

check_space = shell_command(
    command="df -h / | tail -1 | awk '{print $5}' | sed 's/%//'",
    output_key="disk_usage",
    name="check_disk_space"
)

cleanup_logs = shell_command(
    command="find /var/log -name '*.log' -mtime +7 -delete",
    name="cleanup_old_logs"
)

# Only cleanup if disk usage > 80%
conditional_cleanup = if_node(
    condition_expression="int(ctx.get('shell_output', '0').strip()) > 80",
    if_true_task=cleanup_logs,
    name="conditional_cleanup"
)

check_space >> conditional_cleanup
```

## Error Handling

Shell nodes provide comprehensive error information:

```python
from microflow import shell_command, task

risky_command = shell_command(
    command="some-command-that-might-fail",
    name="risky_operation"
)

@task(name="handle_result")
def handle_result(ctx):
    if ctx.get("shell_success"):
        output = ctx.get("shell_output")
        return {"result": "success", "output": output}
    else:
        exit_code = ctx.get("shell_exit_code")
        error = ctx.get("shell_stderr")
        return {
            "result": "failed",
            "exit_code": exit_code,
            "error": error
        }

risky_command >> handle_result
```

## Security Considerations

### Input Validation
```python
from microflow import task, shell_command

@task(name="validate_input")
def validate_input(ctx):
    filename = ctx.get("filename", "")
    # Validate filename to prevent injection
    if not filename.replace("_", "").replace("-", "").replace(".", "").isalnum():
        raise ValueError("Invalid filename")
    return {"safe_filename": filename}

safe_command = shell_command(
    command="ls -la {{ctx.safe_filename}}",
    name="safe_file_listing"
)
```

### Environment Isolation
```python
from microflow import shell_command

# Use restricted environment
secure_command = shell_command(
    command="python script.py",
    env={
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "PYTHONPATH": "/safe/python/path"
    },
    cwd="/safe/working/directory"
)
```

## Common Patterns

### System Monitoring
```python
from microflow import shell_command

# Check system health
check_memory = shell_command(
    command="free -m | grep Mem | awk '{print $3/$2 * 100.0}'",
    output_key="memory_usage",
    name="check_memory"
)

check_cpu = shell_command(
    command="top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1",
    output_key="cpu_usage",
    name="check_cpu"
)
```

### File Processing
```python
from microflow import shell_command

# Process log files
compress_logs = shell_command(
    command="gzip /var/log/app/*.log",
    name="compress_logs"
)

archive_logs = shell_command(
    command="mv /var/log/app/*.gz /archive/",
    name="archive_logs"
)

compress_logs >> archive_logs
```

### Deployment Pipeline
```python
from microflow import shell_command, git_command

# Deployment workflow
git_pull = git_command(
    git_command="pull",
    args=["origin", "main"]
)

run_tests = shell_command(
    command="npm test",
    timeout=300
)

build_app = shell_command(
    command="npm run build",
    timeout=600
)

deploy_app = shell_command(
    command="./deploy.sh production",
    timeout=900
)

# Chain deployment steps
git_pull >> run_tests >> build_app >> deploy_app
```

## Best Practices

1. **Use timeouts**: Always set appropriate timeouts for long-running commands
2. **Validate inputs**: Sanitize any user inputs used in commands
3. **Handle errors**: Check `shell_success` and process error output
4. **Use absolute paths**: Avoid relative paths in commands when possible
5. **Set working directory**: Use `cwd` parameter for context-dependent commands
6. **Limit environment**: Use restricted environment variables for security
7. **Log commands**: Use descriptive node names for debugging
8. **Test commands**: Verify commands work in your target environment
9. **Use proper quoting**: Escape special characters in command arguments
10. **Monitor resources**: Be aware of CPU/memory usage for intensive commands