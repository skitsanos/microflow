# Utility Nodes

## API

```python
validate_schema(data_key='data', schema=None, schema_path=None, output_key='validated_data', fail_on_error=True, name=None)
template_render(template, variables_key=None, output_key='rendered_text', engine='jinja2', name=None)
batch(data_key='data', size=100, output_key='batches', drop_last=False, name=None)
deduplicate(data_key='data', key_fields=None, hash_expression=None, output_key='unique_data', name=None)
http_pagination(
    url,
    method='GET',
    params=None,
    json_data=None,
    page_param='page',
    start_page=1,
    max_pages=None,
    items_path=None,
    output_key='items',
    headers=None,
    auth=None,
    timeout=30.0,
    follow_redirects=True,
    verify_ssl=True,
    name=None,
)
secret_read(key, provider='env', mount=None, output_key='secret_value', mask_in_ctx=True, name=None)
```

## Notes

- `validate_schema` uses `jsonschema` if installed.
- `template_render` supports `engine='jinja2'` (when installed) and a simple built-in `{{ var.path }}` renderer fallback.
- `http_pagination` increments `page_param` until an empty page is returned or `max_pages` is reached.
- `secret_read` supports `provider='env'` and `provider='ctx'`. With `mask_in_ctx=True`, it stores the real secret under `_<output_key>` and a masked value in `<output_key>`.

## Example

```python
from microflow import batch, deduplicate, template_render

chunk = batch(data_key="records", size=500, output_key="record_batches")
unique = deduplicate(data_key="records", key_fields=["id"], output_key="unique_records")
render = template_render("Processed {{ count }} records", variables_key="vars")
```
