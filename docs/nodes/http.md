# HTTP Request Nodes

HTTP nodes enable your workflows to interact with web APIs, send requests, and process responses. They support all standard HTTP methods and authentication mechanisms.

## Available Nodes

### http_request

The main HTTP request node with full configuration options.

**Parameters:**
- `url` (str): Target URL for the request
- `method` (str): HTTP method (GET, POST, PUT, DELETE, etc.)
- `headers` (Dict[str, str], optional): Request headers
- `data` (Any, optional): Request body data
- `params` (Dict[str, str], optional): URL query parameters
- `auth` (Auth, optional): Authentication object
- `timeout` (float): Request timeout in seconds (default: 30)
- `follow_redirects` (bool): Whether to follow redirects (default: True)
- `output_key` (str): Context key to store response (default: "http_response")
- `name` (str, optional): Node name

**Returns:**
- `http_success`: Boolean indicating if request succeeded
- `http_status_code`: HTTP status code
- `http_response_time`: Response time in seconds
- `[output_key]`: Response data (JSON parsed if possible)
- `http_headers`: Response headers
- `http_error`: Error message if request failed

**Example:**
```python
from microflow import http_request

api_call = http_request(
    url="https://api.example.com/users",
    method="GET",
    headers={"Accept": "application/json"},
    timeout=30,
    output_key="users_data"
)
```

### http_get

Convenience function for GET requests.

**Example:**
```python
from microflow import http_get

fetch_data = http_get(
    url="https://api.example.com/data",
    headers={"Authorization": "Bearer token123"}
)
```

### http_post

Convenience function for POST requests.

**Example:**
```python
from microflow import http_post

create_user = http_post(
    url="https://api.example.com/users",
    data={"name": "John Doe", "email": "john@example.com"},
    headers={"Content-Type": "application/json"}
)
```

### http_put

Convenience function for PUT requests.

**Example:**
```python
from microflow import http_put

update_user = http_put(
    url="https://api.example.com/users/123",
    data={"name": "John Smith"},
    headers={"Content-Type": "application/json"}
)
```

### http_delete

Convenience function for DELETE requests.

**Example:**
```python
from microflow import http_delete

delete_user = http_delete(
    url="https://api.example.com/users/123",
    headers={"Authorization": "Bearer token123"}
)
```

## Authentication

### BearerAuth

For Bearer token authentication (common with APIs).

**Example:**
```python
from microflow import http_get, BearerAuth

auth = BearerAuth("your-api-token-here")

authenticated_request = http_get(
    url="https://api.example.com/protected",
    auth=auth
)
```

### BasicAuth

For HTTP Basic authentication.

**Example:**
```python
from microflow import http_get, BasicAuth

auth = BasicAuth("username", "password")

basic_auth_request = http_get(
    url="https://api.example.com/protected",
    auth=auth
)
```

### APIKeyAuth

For API key authentication (header-based).

**Example:**
```python
from microflow import http_get, APIKeyAuth

auth = APIKeyAuth("X-API-Key", "your-api-key")

api_key_request = http_get(
    url="https://api.example.com/data",
    auth=auth
)
```

## Advanced Features

### webhook_call

Make webhook calls with automatic retry logic.

**Parameters:**
- `webhook_url` (str): Webhook URL
- `payload` (Dict): Data to send
- `secret` (str, optional): Webhook secret for signing
- `max_retries` (int): Maximum retry attempts (default: 3)
- `retry_delay` (float): Delay between retries (default: 1.0)

**Example:**
```python
from microflow import webhook_call

notify_webhook = webhook_call(
    webhook_url="https://hooks.example.com/notify",
    payload={"event": "user_created", "user_id": 123},
    secret="webhook-secret",
    max_retries=3
)
```

### rest_api_call

High-level REST API interaction with automatic JSON handling.

**Parameters:**
- `base_url` (str): API base URL
- `endpoint` (str): API endpoint path
- `method` (str): HTTP method
- `payload` (Dict, optional): Request payload
- `auth` (Auth, optional): Authentication
- `api_version` (str, optional): API version header

**Example:**
```python
from microflow import rest_api_call, BearerAuth

api_call = rest_api_call(
    base_url="https://api.example.com",
    endpoint="/v1/users",
    method="POST",
    payload={"name": "Jane Doe"},
    auth=BearerAuth("token123"),
    api_version="v1"
)
```

## Dynamic URL and Data

You can use context data to build dynamic requests:

```python
from microflow import task, http_post

@task(name="setup_api_call")
def setup_api_call(ctx):
    return {
        "api_url": f"https://api.example.com/users/{ctx.get('user_id')}",
        "user_data": {
            "name": ctx.get("user_name"),
            "email": ctx.get("user_email")
        }
    }

# Use context data in HTTP request
dynamic_request = http_post(
    url="{{ctx.api_url}}",  # Will be resolved at runtime
    data="{{ctx.user_data}}"
)
```

## Error Handling

HTTP nodes provide comprehensive error information:

```python
from microflow import http_get, task

fetch_data = http_get(url="https://api.example.com/data")

@task(name="handle_response")
def handle_response(ctx):
    if ctx.get("http_success"):
        data = ctx.get("http_response")
        return {"processed_data": data}
    else:
        error = ctx.get("http_error")
        status = ctx.get("http_status_code")
        return {"error": f"API call failed: {status} - {error}"}
```

## Common Patterns

### API Pagination
```python
from microflow import http_get, task

@task(name="fetch_all_pages")
async def fetch_all_pages(ctx):
    all_data = []
    page = 1

    while True:
        response = await http_get(
            url=f"https://api.example.com/data?page={page}"
        ).spec.fn(ctx)

        if not response.get("http_success"):
            break

        data = response.get("http_response", {})
        items = data.get("items", [])

        if not items:
            break

        all_data.extend(items)
        page += 1

    return {"all_data": all_data}
```

### API Rate Limiting
```python
from microflow import http_get, delay

# Add delay between API calls
api_call = http_get(url="https://api.example.com/data")
rate_limit_delay = delay(1.0)  # 1 second delay

# Chain them: api_call >> rate_limit_delay >> next_api_call
```

### Conditional API Calls
```python
from microflow import if_node, http_get, http_post

# Only make POST if GET returns specific data
get_user = http_get(url="https://api.example.com/user/123")

update_user = http_post(
    url="https://api.example.com/user/123",
    data={"status": "active"}
)

conditional_update = if_node(
    condition_expression="ctx.get('http_response', {}).get('status') == 'pending'",
    if_true_task=update_user
)

# Chain: get_user >> conditional_update
```

## Best Practices

1. **Use appropriate timeouts**: Set reasonable timeouts based on expected response times
2. **Handle errors gracefully**: Always check `http_success` before processing responses
3. **Use authentication**: Secure your API calls with proper authentication
4. **Respect rate limits**: Add delays between requests when needed
5. **Parse responses carefully**: Check response format before accessing data
6. **Use HTTPS**: Always use secure connections for sensitive data
7. **Log requests**: Use meaningful node names for debugging and monitoring