"""File and directory operation nodes"""

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.task_spec import task


def read_file(
    file_path: str,
    encoding: str = "utf-8",
    binary_mode: bool = False,
    name: Optional[str] = None
):
    """
    Read file contents.

    Args:
        file_path: Path to file to read
        encoding: Text encoding (ignored in binary mode)
        binary_mode: Whether to read in binary mode
        name: Node name

    Returns file contents in context:
        - file_content: File contents (string or bytes)
        - file_path: Path that was read
        - file_size: File size in bytes
        - file_exists: Whether file exists
    """
    node_name = name or f"read_{Path(file_path).name}"

    @task(name=node_name, description=f"Read file: {file_path}")
    def _read_file(ctx):
        # Resolve file path from context
        resolved_path = file_path.format(**ctx) if isinstance(file_path, str) else file_path
        path_obj = Path(resolved_path)

        if not path_obj.exists():
            return {
                "file_content": None,
                "file_path": resolved_path,
                "file_size": 0,
                "file_exists": False,
                "file_error": "File not found"
            }

        try:
            if binary_mode:
                with open(path_obj, 'rb') as f:
                    content = f.read()
            else:
                with open(path_obj, 'r', encoding=encoding) as f:
                    content = f.read()

            return {
                "file_content": content,
                "file_path": resolved_path,
                "file_size": path_obj.stat().st_size,
                "file_exists": True
            }

        except Exception as e:
            return {
                "file_content": None,
                "file_path": resolved_path,
                "file_size": 0,
                "file_exists": True,
                "file_error": str(e)
            }

    return _read_file


def write_file(
    file_path: str,
    content: Union[str, bytes],
    encoding: str = "utf-8",
    append_mode: bool = False,
    create_dirs: bool = True,
    name: Optional[str] = None
):
    """
    Write content to file.

    Args:
        file_path: Path to file to write
        content: Content to write (string or bytes)
        encoding: Text encoding (ignored for bytes)
        append_mode: Whether to append instead of overwrite
        create_dirs: Whether to create parent directories
        name: Node name

    Returns write results in context:
        - file_written: Whether write was successful
        - file_path: Path that was written
        - file_size: Size of written content
        - bytes_written: Number of bytes written
    """
    node_name = name or f"write_{Path(file_path).name}"

    @task(name=node_name, description=f"Write file: {file_path}")
    def _write_file(ctx):
        # Resolve file path and content from context
        resolved_path = file_path.format(**ctx) if isinstance(file_path, str) else file_path

        # Resolve content from context if it's a template
        resolved_content = content
        if isinstance(content, str) and "{" in content:
            try:
                resolved_content = content.format(**ctx)
            except KeyError:
                # Content might contain literal braces, leave as-is
                pass

        path_obj = Path(resolved_path)

        try:
            # Create parent directories if needed
            if create_dirs:
                path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            if isinstance(resolved_content, bytes):
                mode = 'ab' if append_mode else 'wb'
                with open(path_obj, mode) as f:
                    bytes_written = f.write(resolved_content)
            else:
                mode = 'a' if append_mode else 'w'
                with open(path_obj, mode, encoding=encoding) as f:
                    bytes_written = f.write(resolved_content)
                    if isinstance(resolved_content, str):
                        bytes_written = len(resolved_content.encode(encoding))

            return {
                "file_written": True,
                "file_path": resolved_path,
                "file_size": path_obj.stat().st_size,
                "bytes_written": bytes_written
            }

        except Exception as e:
            return {
                "file_written": False,
                "file_path": resolved_path,
                "file_size": 0,
                "bytes_written": 0,
                "file_error": str(e)
            }

    return _write_file


def copy_file(
    source_path: str,
    dest_path: str,
    overwrite: bool = True,
    preserve_metadata: bool = True,
    name: Optional[str] = None
):
    """
    Copy a file.

    Args:
        source_path: Source file path
        dest_path: Destination file path
        overwrite: Whether to overwrite existing files
        preserve_metadata: Whether to preserve file metadata
        name: Node name
    """
    node_name = name or "copy_file"

    @task(name=node_name, description=f"Copy {source_path} to {dest_path}")
    def _copy_file(ctx):
        # Resolve paths
        resolved_source = source_path.format(**ctx) if isinstance(source_path, str) else source_path
        resolved_dest = dest_path.format(**ctx) if isinstance(dest_path, str) else dest_path

        source_obj = Path(resolved_source)
        dest_obj = Path(resolved_dest)

        if not source_obj.exists():
            return {
                "copy_success": False,
                "source_path": resolved_source,
                "dest_path": resolved_dest,
                "copy_error": "Source file not found"
            }

        if dest_obj.exists() and not overwrite:
            return {
                "copy_success": False,
                "source_path": resolved_source,
                "dest_path": resolved_dest,
                "copy_error": "Destination exists and overwrite is disabled"
            }

        try:
            # Create destination directory
            dest_obj.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            if preserve_metadata:
                shutil.copy2(source_obj, dest_obj)
            else:
                shutil.copy(source_obj, dest_obj)

            return {
                "copy_success": True,
                "source_path": resolved_source,
                "dest_path": resolved_dest,
                "file_size": dest_obj.stat().st_size
            }

        except Exception as e:
            return {
                "copy_success": False,
                "source_path": resolved_source,
                "dest_path": resolved_dest,
                "copy_error": str(e)
            }

    return _copy_file


def move_file(
    source_path: str,
    dest_path: str,
    overwrite: bool = True,
    name: Optional[str] = None
):
    """
    Move/rename a file.

    Args:
        source_path: Source file path
        dest_path: Destination file path
        overwrite: Whether to overwrite existing files
        name: Node name
    """
    node_name = name or "move_file"

    @task(name=node_name, description=f"Move {source_path} to {dest_path}")
    def _move_file(ctx):
        # Resolve paths
        resolved_source = source_path.format(**ctx) if isinstance(source_path, str) else source_path
        resolved_dest = dest_path.format(**ctx) if isinstance(dest_path, str) else dest_path

        source_obj = Path(resolved_source)
        dest_obj = Path(resolved_dest)

        if not source_obj.exists():
            return {
                "move_success": False,
                "source_path": resolved_source,
                "dest_path": resolved_dest,
                "move_error": "Source file not found"
            }

        if dest_obj.exists() and not overwrite:
            return {
                "move_success": False,
                "source_path": resolved_source,
                "dest_path": resolved_dest,
                "move_error": "Destination exists and overwrite is disabled"
            }

        try:
            # Create destination directory
            dest_obj.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(source_obj, dest_obj)

            return {
                "move_success": True,
                "source_path": resolved_source,
                "dest_path": resolved_dest,
                "file_size": dest_obj.stat().st_size
            }

        except Exception as e:
            return {
                "move_success": False,
                "source_path": resolved_source,
                "dest_path": resolved_dest,
                "move_error": str(e)
            }

    return _move_file


def delete_file(
    file_path: str,
    missing_ok: bool = True,
    name: Optional[str] = None
):
    """
    Delete a file.

    Args:
        file_path: Path to file to delete
        missing_ok: Whether to ignore missing files
        name: Node name
    """
    node_name = name or "delete_file"

    @task(name=node_name, description=f"Delete file: {file_path}")
    def _delete_file(ctx):
        # Resolve path
        resolved_path = file_path.format(**ctx) if isinstance(file_path, str) else file_path
        path_obj = Path(resolved_path)

        if not path_obj.exists():
            if missing_ok:
                return {
                    "delete_success": True,
                    "file_path": resolved_path,
                    "delete_message": "File did not exist"
                }
            else:
                return {
                    "delete_success": False,
                    "file_path": resolved_path,
                    "delete_error": "File not found"
                }

        try:
            path_obj.unlink()
            return {
                "delete_success": True,
                "file_path": resolved_path
            }

        except Exception as e:
            return {
                "delete_success": False,
                "file_path": resolved_path,
                "delete_error": str(e)
            }

    return _delete_file


def list_directory(
    dir_path: str,
    pattern: str = "*",
    recursive: bool = False,
    include_hidden: bool = False,
    file_info: bool = True,
    name: Optional[str] = None
):
    """
    List directory contents.

    Args:
        dir_path: Directory path to list
        pattern: File pattern to match (glob style)
        recursive: Whether to search recursively
        include_hidden: Whether to include hidden files
        file_info: Whether to include file size, modification time, etc.
        name: Node name

    Returns directory listing in context:
        - dir_files: List of file information
        - dir_count: Number of files found
        - dir_path: Directory that was listed
    """
    node_name = name or "list_directory"

    @task(name=node_name, description=f"List directory: {dir_path}")
    def _list_directory(ctx):
        # Resolve directory path
        resolved_path = dir_path.format(**ctx) if isinstance(dir_path, str) else dir_path
        path_obj = Path(resolved_path)

        if not path_obj.exists():
            return {
                "dir_files": [],
                "dir_count": 0,
                "dir_path": resolved_path,
                "dir_error": "Directory not found"
            }

        if not path_obj.is_dir():
            return {
                "dir_files": [],
                "dir_count": 0,
                "dir_path": resolved_path,
                "dir_error": "Path is not a directory"
            }

        try:
            files = []

            # Get file list
            if recursive:
                glob_pattern = f"**/{pattern}" if pattern != "*" else "**/*"
                file_paths = path_obj.glob(glob_pattern)
            else:
                file_paths = path_obj.glob(pattern)

            for file_path in file_paths:
                # Skip hidden files if not requested
                if not include_hidden and file_path.name.startswith('.'):
                    continue

                file_data = {
                    "name": file_path.name,
                    "path": str(file_path),
                    "relative_path": str(file_path.relative_to(path_obj)),
                    "is_file": file_path.is_file(),
                    "is_dir": file_path.is_dir()
                }

                if file_info and file_path.exists():
                    stat = file_path.stat()
                    file_data.update({
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "permissions": oct(stat.st_mode)[-3:]
                    })

                files.append(file_data)

            # Sort by name
            files.sort(key=lambda x: x["name"])

            return {
                "dir_files": files,
                "dir_count": len(files),
                "dir_path": resolved_path
            }

        except Exception as e:
            return {
                "dir_files": [],
                "dir_count": 0,
                "dir_path": resolved_path,
                "dir_error": str(e)
            }

    return _list_directory


def create_directory(
    dir_path: str,
    parents: bool = True,
    exist_ok: bool = True,
    name: Optional[str] = None
):
    """
    Create a directory.

    Args:
        dir_path: Directory path to create
        parents: Whether to create parent directories
        exist_ok: Whether to ignore if directory already exists
        name: Node name
    """
    node_name = name or "create_directory"

    @task(name=node_name, description=f"Create directory: {dir_path}")
    def _create_directory(ctx):
        # Resolve path
        resolved_path = dir_path.format(**ctx) if isinstance(dir_path, str) else dir_path
        path_obj = Path(resolved_path)

        try:
            path_obj.mkdir(parents=parents, exist_ok=exist_ok)
            return {
                "dir_created": True,
                "dir_path": resolved_path,
                "dir_existed": path_obj.exists()
            }

        except Exception as e:
            return {
                "dir_created": False,
                "dir_path": resolved_path,
                "dir_error": str(e)
            }

    return _create_directory


def watch_file(
    file_path: str,
    check_interval: float = 1.0,
    timeout: Optional[float] = None,
    wait_for_creation: bool = False,
    name: Optional[str] = None
):
    """
    Watch a file for changes.

    Args:
        file_path: File path to watch
        check_interval: How often to check for changes (seconds)
        timeout: Maximum time to wait (None for no timeout)
        wait_for_creation: Wait for file to be created if it doesn't exist
        name: Node name
    """
    node_name = name or f"watch_{Path(file_path).name}"

    @task(name=node_name, timeout_s=timeout, description=f"Watch file: {file_path}")
    async def _watch_file(ctx):
        # Resolve path
        resolved_path = file_path.format(**ctx) if isinstance(file_path, str) else file_path
        path_obj = Path(resolved_path)

        if not path_obj.exists() and not wait_for_creation:
            return {
                "watch_success": False,
                "file_path": resolved_path,
                "watch_error": "File not found"
            }

        try:
            start_time = asyncio.get_event_loop().time()
            last_mtime = path_obj.stat().st_mtime if path_obj.exists() else 0

            while True:
                await asyncio.sleep(check_interval)

                # Check timeout
                if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                    return {
                        "watch_success": False,
                        "file_path": resolved_path,
                        "watch_error": "Timeout waiting for file change"
                    }

                # Check if file exists now
                if not path_obj.exists():
                    if wait_for_creation:
                        continue
                    else:
                        return {
                            "watch_success": False,
                            "file_path": resolved_path,
                            "watch_error": "File was deleted"
                        }

                # Check for changes
                current_mtime = path_obj.stat().st_mtime
                if current_mtime > last_mtime:
                    return {
                        "watch_success": True,
                        "file_path": resolved_path,
                        "file_changed": True,
                        "last_modified": current_mtime,
                        "watch_duration": asyncio.get_event_loop().time() - start_time
                    }

        except Exception as e:
            return {
                "watch_success": False,
                "file_path": resolved_path,
                "watch_error": str(e)
            }

    return _watch_file


# Convenience functions for common file operations
def read_json_file(file_path: str, **kwargs):
    """Read and parse JSON file"""
    read_task = read_file(file_path, **kwargs)

    @task(name=f"read_json_{Path(file_path).stem}", description=f"Read JSON: {file_path}")
    def _read_json_file(ctx):
        # First read the file
        result = read_task.spec.fn(ctx)

        if not result.get("file_exists") or result.get("file_error"):
            return result

        try:
            # Parse JSON
            json_data = json.loads(result["file_content"])
            result["json_data"] = json_data
            result["json_parsed"] = True
            return result

        except json.JSONDecodeError as e:
            result["json_data"] = None
            result["json_parsed"] = False
            result["json_error"] = str(e)
            return result

    return _read_json_file


def write_json_file(file_path: str, data_key: str = "json_data", indent: int = 2, **kwargs):
    """Write data as JSON file"""
    @task(name=f"write_json_{Path(file_path).stem}", description=f"Write JSON: {file_path}")
    def _write_json_file(ctx):
        # Get data from context
        data = ctx.get(data_key)
        if data is None:
            return {
                "file_written": False,
                "file_path": file_path,
                "file_error": f"No data found in context key: {data_key}"
            }

        try:
            # Convert to JSON
            json_content = json.dumps(data, indent=indent, ensure_ascii=False)

            # Write file
            write_task = write_file(file_path, json_content, **kwargs)
            return write_task.spec.fn(ctx)

        except (TypeError, ValueError) as e:
            return {
                "file_written": False,
                "file_path": file_path,
                "file_error": f"JSON serialization error: {e}"
            }

    return _write_json_file