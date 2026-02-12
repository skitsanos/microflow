"""Shell/Process execution nodes for running external commands"""

import asyncio
import os
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.task_spec import task


def shell_command(
    command: Union[str, List[str]],
    shell: bool = True,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
    timeout: Optional[float] = None,
    check_return_code: bool = True,
    name: Optional[str] = None,
    max_retries: int = 0,
    backoff_s: float = 1.0,
):
    """
    Execute a shell command or external process.

    Args:
        command: Command to execute (string or list of arguments)
        shell: Whether to execute through shell
        cwd: Working directory for command execution
        env: Environment variables (merged with current environment)
        capture_output: Whether to capture stdout/stderr
        timeout: Command timeout in seconds
        check_return_code: Whether to raise exception on non-zero exit code
        name: Node name
        max_retries: Number of retry attempts
        backoff_s: Backoff time between retries

    Returns command execution results in context:
        - shell_stdout: Standard output
        - shell_stderr: Standard error
        - shell_returncode: Exit code
        - shell_success: Boolean indicating success
        - shell_command: The executed command
    """
    node_name = name or f"shell_{command[:20] if isinstance(command, str) else 'cmd'}"

    @task(
        name=node_name,
        max_retries=max_retries,
        backoff_s=backoff_s,
        timeout_s=timeout,
        description=f"Execute: {command}",
    )
    async def _shell_command(ctx):
        # Resolve dynamic values from context
        resolved_command = command
        if isinstance(command, str):
            # Replace context variables: "echo {{user_id}}" -> "echo user123"
            resolved_command = command.format(**ctx)
        elif isinstance(command, list):
            resolved_command = [
                arg.format(**ctx) if isinstance(arg, str) else arg for arg in command
            ]

        # Resolve working directory
        resolved_cwd = cwd
        if cwd and isinstance(cwd, str):
            resolved_cwd = cwd.format(**ctx)

        # Merge environment variables
        resolved_env = os.environ.copy()
        if env:
            for key, value in env.items():
                if isinstance(value, str):
                    resolved_env[key] = value.format(**ctx)
                else:
                    resolved_env[key] = str(value)

        try:
            # Execute the command
            if shell and isinstance(resolved_command, str):
                # Shell execution
                process = await asyncio.create_subprocess_shell(
                    resolved_command,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    cwd=resolved_cwd,
                    env=resolved_env,
                )
            else:
                # Direct execution
                if isinstance(resolved_command, str):
                    resolved_command = shlex.split(resolved_command)

                process = await asyncio.create_subprocess_exec(
                    *resolved_command,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    cwd=resolved_cwd,
                    env=resolved_env,
                )

            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            # Decode output
            stdout_text = stdout.decode("utf-8") if stdout else ""
            stderr_text = stderr.decode("utf-8") if stderr else ""

            # Check return code
            if check_return_code and process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode, resolved_command, stdout_text, stderr_text
                )

            return {
                "shell_stdout": stdout_text,
                "shell_stderr": stderr_text,
                "shell_returncode": process.returncode,
                "shell_success": process.returncode == 0,
                "shell_command": resolved_command,
            }

        except asyncio.TimeoutError:
            if process:
                process.kill()
                await process.wait()
            raise TimeoutError(
                f"Command timed out after {timeout} seconds: {resolved_command}"
            )

        except subprocess.CalledProcessError as e:
            return {
                "shell_stdout": e.stdout if e.stdout else "",
                "shell_stderr": e.stderr if e.stderr else "",
                "shell_returncode": e.returncode,
                "shell_success": False,
                "shell_command": resolved_command,
                "shell_error": str(e),
            }

    return _shell_command


def python_script(
    script_path: str,
    args: Optional[List[str]] = None,
    python_executable: str = "python",
    venv_path: Optional[str] = None,
    **kwargs,
):
    """
    Execute a Python script.

    Args:
        script_path: Path to Python script
        args: Command line arguments for the script
        python_executable: Python interpreter to use
        venv_path: Path to virtual environment (will activate before execution)
        **kwargs: Additional arguments for shell_command
    """
    # Build command
    if venv_path:
        # Activate virtual environment and run script
        venv_python = os.path.join(venv_path, "bin", "python")
        if os.name == "nt":  # Windows
            venv_python = os.path.join(venv_path, "Scripts", "python.exe")
        command = [venv_python, script_path]
    else:
        command = [python_executable, script_path]

    if args:
        command.extend(args)

    return shell_command(
        command=command,
        shell=False,
        name=kwargs.pop("name", f"python_{Path(script_path).stem}"),
        **kwargs,
    )


def git_command(git_args: List[str], repo_path: Optional[str] = None, **kwargs):
    """
    Execute a git command.

    Args:
        git_args: Git command arguments (e.g., ["status", "--porcelain"])
        repo_path: Repository path (current directory if None)
        **kwargs: Additional arguments for shell_command
    """
    command = ["git"] + git_args

    return shell_command(
        command=command,
        shell=False,
        cwd=repo_path,
        name=kwargs.pop("name", f"git_{git_args[0] if git_args else 'cmd'}"),
        **kwargs,
    )


def docker_command(docker_args: List[str], **kwargs):
    """
    Execute a Docker command.

    Args:
        docker_args: Docker command arguments (e.g., ["ps", "-a"])
        **kwargs: Additional arguments for shell_command
    """
    command = ["docker"] + docker_args

    return shell_command(
        command=command,
        shell=False,
        name=kwargs.pop("name", f"docker_{docker_args[0] if docker_args else 'cmd'}"),
        **kwargs,
    )


def npm_command(npm_args: List[str], project_path: Optional[str] = None, **kwargs):
    """
    Execute an npm command.

    Args:
        npm_args: npm command arguments (e.g., ["install", "--production"])
        project_path: Project directory path
        **kwargs: Additional arguments for shell_command
    """
    command = ["npm"] + npm_args

    return shell_command(
        command=command,
        shell=False,
        cwd=project_path,
        name=kwargs.pop("name", f"npm_{npm_args[0] if npm_args else 'cmd'}"),
        **kwargs,
    )


def curl_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[str] = None,
    output_file: Optional[str] = None,
    follow_redirects: bool = True,
    **kwargs,
):
    """
    Make HTTP request using curl.

    Args:
        url: Request URL
        method: HTTP method
        headers: HTTP headers
        data: Request body data
        output_file: File to save response to
        follow_redirects: Whether to follow redirects
        **kwargs: Additional arguments for shell_command
    """
    command = ["curl"]

    # Add options
    if method != "GET":
        command.extend(["-X", method])

    if headers:
        for key, value in headers.items():
            command.extend(["-H", f"{key}: {value}"])

    if data:
        command.extend(["-d", data])

    if output_file:
        command.extend(["-o", output_file])

    if follow_redirects:
        command.append("-L")

    # Add URL
    command.append(url)

    return shell_command(
        command=command,
        shell=False,
        name=kwargs.pop("name", f"curl_{method.lower()}"),
        **kwargs,
    )


def background_process(
    command: Union[str, List[str]],
    pidfile: Optional[str] = None,
    name: Optional[str] = None,
    **kwargs,
):
    """
    Start a background process.

    Args:
        command: Command to execute in background
        pidfile: File to store process ID
        name: Node name
        **kwargs: Additional arguments for shell_command
    """
    node_name = name or "background_process"

    @task(name=node_name, description=f"Start background: {command}")
    async def _background_process(ctx):
        # Resolve command
        resolved_command = command
        if isinstance(command, str):
            resolved_command = command.format(**ctx)
        elif isinstance(command, list):
            resolved_command = [
                arg.format(**ctx) if isinstance(arg, str) else arg for arg in command
            ]

        try:
            # Start background process
            if isinstance(resolved_command, str):
                process = await asyncio.create_subprocess_shell(
                    resolved_command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *resolved_command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            # Save PID if requested
            if pidfile:
                with open(pidfile, "w") as f:
                    f.write(str(process.pid))

            return {
                "background_pid": process.pid,
                "background_command": resolved_command,
                "background_started": True,
                "background_pidfile": pidfile,
            }

        except Exception as e:
            return {
                "background_pid": None,
                "background_command": resolved_command,
                "background_started": False,
                "background_error": str(e),
            }

    return _background_process


def kill_process(
    pid: Optional[int] = None,
    pidfile: Optional[str] = None,
    signal: int = 15,  # SIGTERM
    name: Optional[str] = None,
):
    """
    Kill a process by PID or PID file.

    Args:
        pid: Process ID to kill
        pidfile: File containing process ID
        signal: Signal to send (default: SIGTERM)
        name: Node name
    """
    node_name = name or "kill_process"

    @task(name=node_name, description="Kill process")
    async def _kill_process(ctx):
        target_pid = pid

        # Read PID from file if not provided directly
        if target_pid is None and pidfile:
            try:
                with open(pidfile, "r") as f:
                    target_pid = int(f.read().strip())
            except (FileNotFoundError, ValueError) as e:
                return {
                    "kill_success": False,
                    "kill_error": f"Could not read PID from {pidfile}: {e}",
                }

        if target_pid is None:
            return {"kill_success": False, "kill_error": "No PID provided"}

        try:
            os.kill(target_pid, signal)

            # Clean up PID file if it exists
            if pidfile and os.path.exists(pidfile):
                os.remove(pidfile)

            return {"kill_success": True, "kill_pid": target_pid, "kill_signal": signal}

        except ProcessLookupError:
            return {
                "kill_success": False,
                "kill_error": f"Process {target_pid} not found",
            }
        except PermissionError:
            return {
                "kill_success": False,
                "kill_error": f"Permission denied to kill process {target_pid}",
            }
        except Exception as e:
            return {"kill_success": False, "kill_error": str(e)}

    return _kill_process


# Convenience functions for common shell operations
def run_script(script_path: str, **kwargs):
    """Run a shell script"""
    return shell_command(
        f"bash {script_path}", name=f"script_{Path(script_path).stem}", **kwargs
    )


def make_executable(file_path: str, **kwargs):
    """Make a file executable"""
    return shell_command(f"chmod +x {file_path}", name="make_executable", **kwargs)


def create_directory(dir_path: str, **kwargs):
    """Create a directory"""
    return shell_command(f"mkdir -p {dir_path}", name="create_directory", **kwargs)


def remove_directory(dir_path: str, **kwargs):
    """Remove a directory"""
    return shell_command(f"rm -rf {dir_path}", name="remove_directory", **kwargs)


def archive_files(source_path: str, archive_path: str, **kwargs):
    """Create tar.gz archive"""
    return shell_command(
        f"tar -czf {archive_path} -C {Path(source_path).parent} {Path(source_path).name}",
        name="archive_files",
        **kwargs,
    )


def extract_archive(archive_path: str, dest_path: str, **kwargs):
    """Extract tar.gz archive"""
    return shell_command(
        f"tar -xzf {archive_path} -C {dest_path}", name="extract_archive", **kwargs
    )
