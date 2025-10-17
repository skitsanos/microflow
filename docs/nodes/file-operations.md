# File Operation Nodes

File operation nodes enable your workflows to interact with the filesystem, performing common operations like reading, writing, copying, and moving files.

## Available Nodes

### read_file

Read content from a file and store it in the workflow context.

**Parameters:**
- `file_path` (str): Path to the file to read
- `encoding` (str): File encoding (default: "utf-8")
- `binary_mode` (bool): Whether to read in binary mode (default: False)
- `output_key` (str): Context key to store content (default: "file_content")
- `name` (str, optional): Node name

**Returns:**
- `file_success`: Boolean indicating if operation succeeded
- `file_size`: File size in bytes
- `file_path`: Path of the file that was read
- `[output_key]`: File content (string or bytes)
- `file_error`: Error message if operation failed

**Example:**
```python
from microflow import read_file

# Read text file
read_config = read_file(
    file_path="./config/settings.json",
    output_key="config_data",
    name="read_configuration"
)

# Read binary file
read_image = read_file(
    file_path="./images/logo.png",
    binary_mode=True,
    output_key="image_data",
    name="read_logo"
)
```

### write_file

Write content to a file from the workflow context.

**Parameters:**
- `content_key` (str): Context key containing content to write (default: "file_content")
- `file_path` (str): Path where to write the file
- `encoding` (str): File encoding (default: "utf-8")
- `binary_mode` (bool): Whether to write in binary mode (default: False)
- `create_dirs` (bool): Whether to create parent directories (default: True)
- `append_mode` (bool): Whether to append to existing file (default: False)
- `name` (str, optional): Node name

**Returns:**
- `file_success`: Boolean indicating if operation succeeded
- `file_size`: Size of written content in bytes
- `file_path`: Path where file was written
- `file_created`: Boolean indicating if file was newly created
- `file_error`: Error message if operation failed

**Example:**
```python
from microflow import write_file, task

@task(name="generate_report")
def generate_report(ctx):
    data = ctx.get("processed_data", [])
    report = f"Report generated with {len(data)} items"
    return {"report_content": report}

# Write report to file
save_report = write_file(
    content_key="report_content",
    file_path="./reports/daily_report.txt",
    name="save_daily_report"
)

generate_report >> save_report
```

### copy_file

Copy a file from source to destination.

**Parameters:**
- `source_path` (str): Source file path
- `destination_path` (str): Destination file path
- `create_dirs` (bool): Whether to create destination directories (default: True)
- `overwrite` (bool): Whether to overwrite existing files (default: True)
- `preserve_metadata` (bool): Whether to preserve file metadata (default: True)
- `name` (str, optional): Node name

**Returns:**
- `file_success`: Boolean indicating if operation succeeded
- `source_path`: Source file path
- `destination_path`: Destination file path
- `file_size`: Size of copied file
- `file_exists_before`: Whether destination file existed before copy
- `file_error`: Error message if operation failed

**Example:**
```python
from microflow import copy_file

# Backup configuration file
backup_config = copy_file(
    source_path="./config/production.json",
    destination_path="./backups/production_backup.json",
    name="backup_configuration"
)

# Copy with metadata preservation
archive_logs = copy_file(
    source_path="/var/log/app.log",
    destination_path="/archive/app_log_backup.log",
    preserve_metadata=True,
    name="archive_application_logs"
)
```

### move_file

Move or rename a file from source to destination.

**Parameters:**
- `source_path` (str): Source file path
- `destination_path` (str): Destination file path
- `create_dirs` (bool): Whether to create destination directories (default: True)
- `overwrite` (bool): Whether to overwrite existing files (default: False)
- `name` (str, optional): Node name

**Returns:**
- `file_success`: Boolean indicating if operation succeeded
- `source_path`: Original source file path
- `destination_path`: New destination file path
- `file_size`: Size of moved file
- `file_exists_before`: Whether destination file existed before move
- `file_error`: Error message if operation failed

**Example:**
```python
from microflow import move_file

# Move processed file to archive
archive_processed = move_file(
    source_path="./processing/data.csv",
    destination_path="./archive/processed_data.csv",
    name="archive_processed_data"
)

# Rename file
rename_temp = move_file(
    source_path="./temp/temp_file.txt",
    destination_path="./temp/final_file.txt",
    name="rename_temp_file"
)
```

### list_directory

List contents of a directory with filtering options.

**Parameters:**
- `directory_path` (str): Directory path to list
- `pattern` (str, optional): Glob pattern to filter files (e.g., "*.txt")
- `recursive` (bool): Whether to list recursively (default: False)
- `include_dirs` (bool): Whether to include directories (default: True)
- `include_files` (bool): Whether to include files (default: True)
- `output_key` (str): Context key to store file list (default: "directory_contents")
- `name` (str, optional): Node name

**Returns:**
- `file_success`: Boolean indicating if operation succeeded
- `directory_path`: Path that was listed
- `file_count`: Number of files found
- `directory_count`: Number of directories found
- `[output_key]`: List of file/directory information
- `file_error`: Error message if operation failed

**Example:**
```python
from microflow import list_directory

# List all files in directory
list_logs = list_directory(
    directory_path="/var/log",
    pattern="*.log",
    output_key="log_files",
    name="list_log_files"
)

# Recursive directory listing
list_all_python = list_directory(
    directory_path="./src",
    pattern="*.py",
    recursive=True,
    include_dirs=False,
    output_key="python_files",
    name="find_python_files"
)
```

## Advanced Usage

### File Processing Pipeline

Create a complete file processing workflow:

```python
from microflow import read_file, write_file, task, Workflow

@task(name="process_data")
def process_data(ctx):
    content = ctx.get("file_content", "")
    # Process the content
    processed = content.upper()
    return {"processed_content": processed}

# Build pipeline
read_input = read_file(
    file_path="./input/data.txt",
    output_key="file_content"
)

write_output = write_file(
    content_key="processed_content",
    file_path="./output/processed_data.txt"
)

# Chain operations
read_input >> process_data >> write_output
```

### Conditional File Operations

Perform operations based on file existence or content:

```python
from microflow import list_directory, copy_file, if_node, task

check_backups = list_directory(
    directory_path="./backups",
    pattern="backup_*.sql",
    output_key="backup_files"
)

@task(name="need_backup")
def need_backup(ctx):
    backup_files = ctx.get("backup_files", [])
    return {"needs_backup": len(backup_files) == 0}

create_backup = copy_file(
    source_path="./data/database.db",
    destination_path="./backups/backup_latest.db"
)

conditional_backup = if_node(
    condition_expression="ctx.get('needs_backup', False)",
    if_true_task=create_backup,
    name="backup_if_needed"
)

check_backups >> need_backup >> conditional_backup
```

### Batch File Operations

Process multiple files using directory listing:

```python
from microflow import list_directory, task

list_images = list_directory(
    directory_path="./images",
    pattern="*.jpg",
    output_key="image_files"
)

@task(name="process_images")
def process_images(ctx):
    images = ctx.get("image_files", [])
    processed_count = 0

    for image_info in images:
        file_path = image_info.get("path")
        # Process each image
        print(f"Processing {file_path}")
        processed_count += 1

    return {"processed_images": processed_count}

list_images >> process_images
```

### Dynamic File Paths

Use context data to build dynamic file paths:

```python
from microflow import task, write_file
from datetime import datetime

@task(name="prepare_output")
def prepare_output(ctx):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.txt"
    return {
        "output_filename": filename,
        "report_data": "Generated report content"
    }

save_timestamped_report = write_file(
    content_key="report_data",
    file_path="./reports/{{ctx.output_filename}}",
    name="save_timestamped_report"
)
```

## File Format Handling

### JSON Files
```python
from microflow import read_file, write_file, task
import json

read_json_config = read_file(
    file_path="./config.json",
    output_key="json_content"
)

@task(name="parse_json")
def parse_json(ctx):
    content = ctx.get("json_content", "{}")
    data = json.loads(content)
    return {"config_data": data}

@task(name="generate_json")
def generate_json(ctx):
    data = {"updated": True, "timestamp": "2024-01-01"}
    content = json.dumps(data, indent=2)
    return {"json_output": content}

write_json_config = write_file(
    content_key="json_output",
    file_path="./updated_config.json"
)
```

### CSV Files
```python
from microflow import read_file, write_file, task
import csv
from io import StringIO

read_csv_data = read_file(
    file_path="./data.csv",
    output_key="csv_content"
)

@task(name="process_csv")
def process_csv(ctx):
    content = ctx.get("csv_content", "")
    reader = csv.DictReader(StringIO(content))
    processed_rows = []

    for row in reader:
        # Process each row
        processed_rows.append(row)

    return {"processed_data": processed_rows}
```

## Error Handling

File operations provide comprehensive error information:

```python
from microflow import read_file, task

read_config = read_file(
    file_path="./config/app.json",
    output_key="config_content"
)

@task(name="handle_file_result")
def handle_file_result(ctx):
    if ctx.get("file_success"):
        content = ctx.get("config_content")
        return {"status": "success", "content_length": len(content)}
    else:
        error = ctx.get("file_error")
        return {"status": "error", "message": error}

read_config >> handle_file_result
```

## Security Considerations

### Path Validation
```python
from microflow import task
import os

@task(name="validate_path")
def validate_path(ctx):
    file_path = ctx.get("user_file_path", "")

    # Validate path is within allowed directory
    allowed_dir = "/safe/directory"
    real_path = os.path.realpath(file_path)

    if not real_path.startswith(allowed_dir):
        raise ValueError("Path not allowed")

    return {"safe_path": real_path}
```

### File Size Limits
```python
from microflow import read_file, task

@task(name="check_file_size")
def check_file_size(ctx):
    file_size = ctx.get("file_size", 0)
    max_size = 10 * 1024 * 1024  # 10MB

    if file_size > max_size:
        return {"size_ok": False, "error": "File too large"}

    return {"size_ok": True}
```

## Best Practices

1. **Handle errors gracefully**: Always check `file_success` before processing results
2. **Use absolute paths**: Avoid relative paths when possible for consistency
3. **Validate inputs**: Check file paths and content for security
4. **Set appropriate permissions**: Be mindful of file permissions when creating files
5. **Use binary mode for non-text**: Use `binary_mode=True` for images, executables, etc.
6. **Create directories**: Use `create_dirs=True` to avoid path errors
7. **Handle large files**: Consider memory usage when reading large files
8. **Use appropriate encoding**: Specify correct encoding for text files
9. **Clean up temporary files**: Remove temporary files after processing
10. **Monitor disk space**: Be aware of available disk space for write operations