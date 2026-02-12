"""HTTP Request node for making web API calls"""

from typing import Any, Callable, Dict, Optional, Union
from urllib.parse import urljoin

from ..core.task_spec import task

httpx: Any = None
try:
    import httpx
except ImportError:
    pass


class HTTPAuth:
    """Base class for HTTP authentication"""

    pass


class BearerAuth(HTTPAuth):
    """Bearer token authentication"""

    def __init__(self, token: str):
        self.token = token

    def apply(self, headers: Dict[str, str]):
        headers["Authorization"] = f"Bearer {self.token}"


class BasicAuth(HTTPAuth):
    """Basic authentication"""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def apply(self, headers: Dict[str, str]):
        import base64

        credentials = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()
        headers["Authorization"] = f"Basic {credentials}"


class APIKeyAuth(HTTPAuth):
    """API Key authentication"""

    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        self.api_key = api_key
        self.header_name = header_name

    def apply(self, headers: Dict[str, str]):
        headers[self.header_name] = self.api_key


def http_request(
    url: Union[str, Callable[[Dict[str, Any]], str]],
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[
        Union[Dict[str, Any], Callable[[Dict[str, Any]], Dict[str, Any]]]
    ] = None,
    form_data: Optional[Dict[str, Any]] = None,
    auth: Optional[HTTPAuth] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    response_format: str = "json",  # "json", "text", "raw"
    name: Optional[str] = None,
    max_retries: int = 0,
    backoff_s: float = 1.0,
):
    """
    Create an HTTP request node.

    Args:
        url: Target URL or function that returns URL from context
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: Additional headers to send
        params: Query parameters
        json_data: JSON payload for request body
        form_data: Form data for request body
        auth: Authentication handler
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow redirects
        verify_ssl: Whether to verify SSL certificates
        response_format: How to parse response ("json", "text", "raw")
        name: Node name
        max_retries: Number of retry attempts
        backoff_s: Backoff time between retries

    Returns HTTP response data in context with keys:
        - http_status_code: Response status code
        - http_headers: Response headers
        - http_data: Parsed response data
        - http_success: Boolean indicating if request was successful
    """
    if httpx is None:
        raise ImportError(
            "httpx is required for HTTP requests. Install with: pip install httpx"
        )

    node_name = (
        name or f"http_{method.lower()}_{url if isinstance(url, str) else 'dynamic'}"
    )

    @task(
        name=node_name,
        max_retries=max_retries,
        backoff_s=backoff_s,
        description=f"HTTP {method} request",
    )
    async def _http_request(ctx):
        # Resolve URL
        if callable(url):
            request_url = url(ctx)
        else:
            request_url = url

        # Build headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        # Apply authentication
        if auth:
            auth.apply(request_headers)

        # Resolve dynamic parameters from context
        resolved_params = {}
        if params:
            for key, value in params.items():
                if isinstance(value, str) and value.startswith("ctx."):
                    # Extract value from context: "ctx.user_id" -> ctx["user_id"]
                    ctx_key = value[4:]
                    resolved_params[key] = ctx.get(ctx_key)
                else:
                    resolved_params[key] = value

        # Resolve JSON payload (supports dict values sourced from context or a builder callable)
        resolved_json = None
        if json_data:
            if callable(json_data):
                resolved_json = json_data(ctx)
            else:
                resolved_json = {}
                for key, value in json_data.items():
                    if isinstance(value, str) and value.startswith("ctx."):
                        ctx_key = value[4:]
                        resolved_json[key] = ctx.get(ctx_key)
                    else:
                        resolved_json[key] = value

        # Make the request
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=follow_redirects, verify=verify_ssl
        ) as client:

            response = await client.request(
                method=method.upper(),
                url=request_url,
                headers=request_headers,
                params=resolved_params,
                json=resolved_json,
                data=form_data,
            )

            # Parse response based on format
            response_data = None
            try:
                if response_format == "json":
                    response_data = response.json()
                elif response_format == "text":
                    response_data = response.text
                else:  # raw
                    response_data = response.content
            except Exception as e:
                response_data = {"parse_error": str(e), "raw_content": response.text}

            # Check if request was successful
            is_success = 200 <= response.status_code < 300

            return {
                "http_status_code": response.status_code,
                "http_headers": dict(response.headers),
                "http_data": response_data,
                "http_success": is_success,
                "http_url": str(response.url),
            }

    return _http_request


# Convenience functions for common HTTP patterns
def http_get(url: str, **kwargs):
    """Create a GET request node"""
    return http_request(url, method="GET", **kwargs)


def http_post(
    url: Union[str, Callable[[Dict[str, Any]], str]],
    json_data: Optional[
        Union[Dict[str, Any], Callable[[Dict[str, Any]], Dict[str, Any]]]
    ] = None,
    **kwargs,
):
    """Create a POST request node"""
    return http_request(url, method="POST", json_data=json_data, **kwargs)


def http_put(
    url: Union[str, Callable[[Dict[str, Any]], str]],
    json_data: Optional[
        Union[Dict[str, Any], Callable[[Dict[str, Any]], Dict[str, Any]]]
    ] = None,
    **kwargs,
):
    """Create a PUT request node"""
    return http_request(url, method="PUT", json_data=json_data, **kwargs)


def http_delete(url: str, **kwargs):
    """Create a DELETE request node"""
    return http_request(url, method="DELETE", **kwargs)


def webhook_call(
    webhook_url: Union[str, Callable[[Dict[str, Any]], str]],
    payload_keys: Optional[list] = None,
    **kwargs,
):
    """
    Create a webhook call node that sends context data as JSON payload.

    Args:
        webhook_url: Webhook endpoint URL
        payload_keys: List of context keys to include in payload (all if None)
    """

    def build_payload(ctx):
        if payload_keys:
            return {key: ctx.get(key) for key in payload_keys}
        else:
            # Send all non-private context data (not starting with _)
            return {k: v for k, v in ctx.items() if not k.startswith("_")}

    return http_post(
        webhook_url,
        json_data=lambda ctx: build_payload(ctx),
        name="webhook_call",
        **kwargs,
    )


def rest_api_call(
    base_url: str,
    endpoint: str,
    method: str = "GET",
    auth: Optional[HTTPAuth] = None,
    **kwargs,
):
    """
    Create a REST API call node.

    Args:
        base_url: Base API URL
        endpoint: API endpoint path
        method: HTTP method
        auth: Authentication handler
    """
    full_url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))
    return http_request(full_url, method=method, auth=auth, **kwargs)
