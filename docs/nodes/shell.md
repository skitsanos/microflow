# Shell and Process Nodes

## API

```python
shell_command(command, shell=True, cwd=None, env=None, capture_output=True, timeout=None, check_return_code=True, name=None, max_retries=0, backoff_s=1.0)
python_script(script_path, args=None, python_executable='python', venv_path=None, **kwargs)
git_command(git_args, repo_path=None, **kwargs)
docker_command(docker_args, **kwargs)
npm_command(npm_args, project_path=None, **kwargs)
curl_request(url, method='GET', headers=None, data=None, output_file=None, follow_redirects=True, **kwargs)
background_process(command, pidfile=None, name=None, **kwargs)
kill_process(pid=None, pidfile=None, signal=15, name=None)
run_script(script_path, **kwargs)
make_executable(file_path, **kwargs)
create_directory(dir_path, **kwargs)
remove_directory(dir_path, **kwargs)
archive_files(source_path, archive_path, **kwargs)
extract_archive(archive_path, dest_path, **kwargs)
```

## Behavior

`shell_command` is the base primitive and returns keys such as:

- `shell_stdout`
- `shell_stderr`
- `shell_returncode`
- `shell_success`
- `shell_command`

Other helpers are thin wrappers over `shell_command`.

## Example

```python
from microflow import shell_command

check_git = shell_command(["git", "status", "--short"], shell=False)
```
