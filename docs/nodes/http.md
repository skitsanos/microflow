# HTTP Request Nodes

Use these nodes to call external HTTP APIs with retries, auth, and configurable response parsing. Best practices: set explicit timeouts and retry policy per endpoint, and validate response status/body before merging into context.

## API

```python
http_request(
    url,
    method='GET',
    headers=None,
    params=None,
    json_data=None,
    form_data=None,
    auth=None,
    timeout=30.0,
    follow_redirects=True,
    verify_ssl=True,
    response_format='json',
    name=None,
    max_retries=0,
    backoff_s=1.0,
)

http_get(url, **kwargs)
http_post(url, json_data=None, **kwargs)
http_put(url, json_data=None, **kwargs)
http_delete(url, **kwargs)
webhook_call(webhook_url, payload_keys=None, **kwargs)
rest_api_call(base_url, endpoint, method='GET', auth=None, **kwargs)
```

## Authentication Helpers

```python
BearerAuth(token)
BasicAuth(username, password)
APIKeyAuth(api_key, header_name='X-API-Key')
```

## Behavior

`http_request` writes:

- `http_status_code`
- `http_headers`
- `http_data` (parsed by `response_format`)
- `http_success`
- `http_url`

`json_data` can be:

- a dict (with optional `"ctx.<key>"` value expansion), or
- a callable receiving `ctx` and returning a dict.

## Example

```python
from microflow import http_post, webhook_call, BearerAuth

create = http_post(
    "https://api.example.com/users",
    json_data={"name": "ctx.user_name"},
    auth=BearerAuth("token"),
)

notify = webhook_call(
    "https://hooks.example.com/event",
    payload_keys=["user_id", "status"],
)
```
