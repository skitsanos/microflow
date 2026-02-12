# Microflow Node Docs (Code-Aligned)

This documentation reflects the current APIs in `microflow/nodes/*.py`.

## Categories

- [Conditional](./conditional.md)
- [HTTP](./http.md)
- [Shell and Process](./shell.md)
- [File Operations](./file-operations.md)
- [Data Transformation](./data-transformation.md)
- [Timing](./timing.md)
- [Notifications](./notifications.md)
- [Data Formats](./data-formats.md)
- [Subworkflows](./subworkflow.md)
- [Utilities](./utilities.md)
- [Integrations](./integrations.md)

## Notes

- Most functions return a `Task` object produced by the `@task` decorator.
- Nodes communicate through the shared workflow context (`ctx`) and return dictionaries that are merged into `ctx`.
- `microflow.__init__` exports a curated subset of helpers. Some additional helpers are available from module paths (for example `microflow.nodes.shell`).

## Quick Example

```python
from microflow import Workflow, http_get, data_filter

fetch = http_get("https://example.com/api")
filter_items = data_filter("item.get('active') is True", data_key="http_data", output_key="active")

fetch >> filter_items
workflow = Workflow([fetch, filter_items])
```
