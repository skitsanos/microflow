# File Operation Nodes

## API

```python
read_file(file_path, encoding='utf-8', binary_mode=False, name=None)
write_file(file_path, content, encoding='utf-8', append_mode=False, create_dirs=True, name=None)
copy_file(source_path, dest_path, overwrite=True, preserve_metadata=True, name=None)
move_file(source_path, dest_path, overwrite=True, name=None)
delete_file(file_path, missing_ok=True, name=None)
list_directory(dir_path, pattern='*', recursive=False, include_hidden=False, file_info=True, name=None)
create_directory(dir_path, parents=True, exist_ok=True, name=None)
watch_file(file_path, check_interval=1.0, timeout=None, wait_for_creation=False, name=None)
read_json_file(file_path, **kwargs)
write_json_file(file_path, data_key='json_data', indent=2, **kwargs)
```

## Behavior

Common return keys include `*_success`, `*_error`, and operation-specific metadata.

Examples:

- `read_file` returns `file_content`, `file_path`, `file_size`, `file_exists`.
- `write_file` returns `file_written`, `file_path`, `bytes_written`, `append_mode`.
- `list_directory` returns `directory_items`, `item_count`, and path metadata.

## Example

```python
from microflow.nodes.file_ops import read_file, write_file

read_input = read_file("./input.txt")
write_output = write_file("./output.txt", content="processed")
```
