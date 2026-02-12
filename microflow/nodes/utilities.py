"""Utility nodes for validation, templating, batching, deduplication, pagination, and secrets."""

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from ..core.task_spec import task
from .http_request import HTTPAuth, httpx

try:
    from jsonschema import validate as jsonschema_validate  # type: ignore[import-untyped]
except ImportError:
    jsonschema_validate = None

try:
    from jinja2 import Template as JinjaTemplate  # type: ignore[import-not-found]
except ImportError:
    JinjaTemplate = None


def _get_by_path(data: Any, path: Optional[str]) -> Any:
    """Resolve dot-notation path from dict/list objects."""
    if not path:
        return data

    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if 0 <= idx < len(current) else None
        else:
            return None
        if current is None:
            return None
    return current


def validate_schema(
    data_key: str = "data",
    schema: Optional[Dict[str, Any]] = None,
    schema_path: Optional[str] = None,
    output_key: str = "validated_data",
    fail_on_error: bool = True,
    name: Optional[str] = None,
):
    """Validate context data against a JSON schema."""
    node_name = name or "validate_schema"

    @task(name=node_name, description="Validate data against JSON schema")
    def _validate_schema(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "schema_valid": False,
                "schema_error": f"No data found in context key: {data_key}",
            }

        schema_to_use = schema
        if schema_to_use is None and schema_path:
            try:
                schema_to_use = json.loads(
                    Path(schema_path).read_text(encoding="utf-8")
                )
            except Exception as e:
                msg = f"Failed to load schema from '{schema_path}': {e}"
                if fail_on_error:
                    raise ValueError(msg)
                return {"schema_valid": False, "schema_error": msg}

        if schema_to_use is None:
            msg = "Either 'schema' or 'schema_path' must be provided"
            if fail_on_error:
                raise ValueError(msg)
            return {"schema_valid": False, "schema_error": msg}

        if jsonschema_validate is None:
            msg = "jsonschema is required for validate_schema. Install with: pip install jsonschema"
            if fail_on_error:
                raise ImportError(msg)
            return {"schema_valid": False, "schema_error": msg}

        try:
            jsonschema_validate(instance=data, schema=schema_to_use)
            return {
                output_key: data,
                "schema_valid": True,
                "schema_data_key": data_key,
            }
        except Exception as e:
            msg = f"Schema validation failed: {e}"
            if fail_on_error:
                raise ValueError(msg)
            return {"schema_valid": False, "schema_error": msg}

    return _validate_schema


def template_render(
    template: str,
    variables_key: Optional[str] = None,
    output_key: str = "rendered_text",
    engine: str = "jinja2",
    name: Optional[str] = None,
):
    """Render a text template using context variables."""
    node_name = name or "template_render"

    @task(name=node_name, description="Render text template")
    def _template_render(ctx):
        variables = ctx if variables_key is None else ctx.get(variables_key, {})
        if not isinstance(variables, dict):
            return {
                "render_success": False,
                "render_error": f"variables_key '{variables_key}' must reference a dictionary",
            }

        try:
            if engine == "jinja2":
                if JinjaTemplate is None:
                    raise ImportError(
                        "jinja2 is required for engine='jinja2'. Install with: pip install jinja2"
                    )
                rendered = JinjaTemplate(template).render(**variables, ctx=ctx)
            else:
                # Minimal fallback: replace {{ path.to.value }} from variables first, then ctx.
                def replace_match(match: re.Match[str]) -> str:
                    path = match.group(1).strip()
                    value = _get_by_path(variables, path)
                    if value is None:
                        value = _get_by_path(ctx, path)
                    return "" if value is None else str(value)

                rendered = re.sub(r"\{\{\s*([^{}]+?)\s*\}\}", replace_match, template)

            return {
                output_key: rendered,
                "render_success": True,
                "render_engine": engine,
            }
        except Exception as e:
            return {
                "render_success": False,
                "render_error": f"Template render error: {e}",
                "render_engine": engine,
            }

    return _template_render


def batch(
    data_key: str = "data",
    size: int = 100,
    output_key: str = "batches",
    drop_last: bool = False,
    name: Optional[str] = None,
):
    """Split a list into fixed-size batches."""
    node_name = name or "batch"

    @task(name=node_name, description=f"Batch data into size={size}")
    def _batch(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "batch_success": False,
                "batch_error": f"No data found in context key: {data_key}",
            }
        if not isinstance(data, list):
            return {
                "batch_success": False,
                "batch_error": "Data must be a list",
            }
        if size <= 0:
            return {
                "batch_success": False,
                "batch_error": "Batch size must be greater than 0",
            }

        batches: List[List[Any]] = [
            data[i : i + size] for i in range(0, len(data), size)
        ]
        if drop_last and batches and len(batches[-1]) < size:
            batches = batches[:-1]

        return {
            output_key: batches,
            "batch_success": True,
            "batch_size": size,
            "batch_count": len(batches),
            "item_count": len(data),
            "drop_last": drop_last,
        }

    return _batch


def deduplicate(
    data_key: str = "data",
    key_fields: Optional[Sequence[str]] = None,
    hash_expression: Optional[str] = None,
    output_key: str = "unique_data",
    name: Optional[str] = None,
):
    """Deduplicate items in a list using key fields, expression, or full item hash."""
    node_name = name or "deduplicate"

    @task(name=node_name, description="Deduplicate list items")
    def _deduplicate(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "deduplicate_success": False,
                "deduplicate_error": f"No data found in context key: {data_key}",
            }
        if not isinstance(data, list):
            return {
                "deduplicate_success": False,
                "deduplicate_error": "Data must be a list",
            }

        seen = set()
        unique_items = []

        try:
            for item in data:
                if hash_expression:
                    fingerprint = eval(
                        hash_expression,
                        {"item": item, "ctx": ctx, "__builtins__": {}},
                    )
                elif key_fields:
                    if isinstance(item, dict):
                        fingerprint = tuple(item.get(field) for field in key_fields)
                    else:
                        fingerprint = tuple(
                            getattr(item, field, None) for field in key_fields
                        )
                else:
                    fingerprint = json.dumps(item, sort_keys=True, default=str)

                if fingerprint in seen:
                    continue

                seen.add(fingerprint)
                unique_items.append(item)

            return {
                output_key: unique_items,
                "deduplicate_success": True,
                "original_count": len(data),
                "unique_count": len(unique_items),
                "removed_count": len(data) - len(unique_items),
            }
        except Exception as e:
            return {
                "deduplicate_success": False,
                "deduplicate_error": f"Deduplicate error: {e}",
            }

    return _deduplicate


def http_pagination(
    url: Union[str, Callable[[Dict[str, Any]], str]],
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    page_param: str = "page",
    start_page: int = 1,
    max_pages: Optional[int] = None,
    items_path: Optional[str] = None,
    output_key: str = "items",
    headers: Optional[Dict[str, str]] = None,
    auth: Optional[HTTPAuth] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    name: Optional[str] = None,
):
    """Fetch paginated API data by incrementing a page parameter until exhausted."""
    if httpx is None:
        raise ImportError(
            "httpx is required for HTTP pagination. Install with: pip install httpx"
        )

    node_name = name or "http_pagination"

    @task(name=node_name, description=f"Paginated HTTP {method} request")
    async def _http_pagination(ctx):
        request_url = url(ctx) if callable(url) else url
        request_headers = dict(headers or {})
        if auth:
            auth.apply(request_headers)

        base_params = dict(params or {})
        aggregated: List[Any] = []
        current_page = start_page
        pages_fetched = 0

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=follow_redirects,
            verify=verify_ssl,
        ) as client:
            while True:
                if max_pages is not None and pages_fetched >= max_pages:
                    break

                page_params = dict(base_params)
                page_params[page_param] = current_page

                response = await client.request(
                    method=method.upper(),
                    url=request_url,
                    headers=request_headers,
                    params=page_params,
                    json=json_data,
                )

                if not (200 <= response.status_code < 300):
                    return {
                        "pagination_success": False,
                        "pagination_error": (
                            f"Page {current_page} failed with status {response.status_code}"
                        ),
                        "http_status_code": response.status_code,
                        "pages_fetched": pages_fetched,
                        output_key: aggregated,
                    }

                payload = response.json()
                page_items = _get_by_path(payload, items_path)
                if page_items is None:
                    page_items = payload

                if isinstance(page_items, list):
                    items_to_add = page_items
                else:
                    items_to_add = [page_items]

                if not items_to_add:
                    break

                aggregated.extend(items_to_add)
                pages_fetched += 1
                current_page += 1

        return {
            output_key: aggregated,
            "pagination_success": True,
            "pages_fetched": pages_fetched,
            "item_count": len(aggregated),
            "start_page": start_page,
            "page_param": page_param,
        }

    return _http_pagination


def secret_read(
    key: str,
    provider: str = "env",
    mount: Optional[str] = None,
    output_key: str = "secret_value",
    mask_in_ctx: bool = True,
    name: Optional[str] = None,
):
    """Read a secret from supported providers (currently env and ctx)."""
    node_name = name or f"secret_read_{key}"

    @task(name=node_name, description=f"Read secret '{key}' from {provider}")
    def _secret_read(ctx):
        value = None
        provider_lower = provider.lower()

        if provider_lower == "env":
            value = os.getenv(key)
        elif provider_lower == "ctx":
            source = ctx.get(mount, {}) if mount else ctx
            if isinstance(source, dict):
                value = source.get(key)
        else:
            return {
                "secret_found": False,
                "secret_error": f"Unsupported provider: {provider}",
                "secret_provider": provider,
            }

        if value is None:
            return {
                "secret_found": False,
                "secret_error": f"Secret not found for key: {key}",
                "secret_provider": provider,
            }

        result: Dict[str, Any] = {
            "secret_found": True,
            "secret_provider": provider,
            "secret_key": key,
            "secret_masked": mask_in_ctx,
        }

        if mask_in_ctx:
            result[output_key] = "***"
            result[f"_{output_key}"] = value
        else:
            result[output_key] = value

        return result

    return _secret_read
