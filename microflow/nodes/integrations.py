"""Integration nodes for databases, caches, and object storage."""

import json
import os
import sqlite3
from typing import Any, Dict, Optional

from ..core.task_spec import task

try:
    import psycopg  # type: ignore[import-not-found]
except ImportError:
    psycopg = None

try:
    import redis  # type: ignore[import-not-found]
except ImportError:
    redis = None

try:
    import boto3  # type: ignore[import-not-found]
except ImportError:
    boto3 = None

try:
    from arango import ArangoClient  # type: ignore[import-not-found]
except ImportError:
    ArangoClient = None


_MEMORY_CACHE: Dict[str, Any] = {}


def _normalize_params(params: Any) -> Any:
    if params is None:
        return ()
    return params


def _resolve_dsn(dsn: Optional[str], driver: str) -> str:
    if dsn:
        return dsn

    if driver == "sqlite":
        return os.getenv("SQLITE_DSN", "./data/microflow.db")

    return os.getenv(
        "DATABASE_URL", "postgresql://microflow:microflow@localhost:5432/microflow"
    )


def db_query(
    dsn: Optional[str] = None,
    query: str = "",
    params: Any = None,
    output_key: str = "rows",
    fetch: str = "all",
    driver: str = "sqlite",
    name: Optional[str] = None,
):
    """Execute a read query and return rows."""
    node_name = name or "db_query"

    @task(name=node_name, description=f"DB query ({driver})")
    def _db_query(ctx):
        if not query:
            return {"db_success": False, "db_error": "Query must not be empty"}

        resolved_dsn = _resolve_dsn(dsn, driver)
        resolved_params = _normalize_params(params)

        try:
            if driver == "sqlite":
                with sqlite3.connect(resolved_dsn) as conn:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute(query, resolved_params)

                    if fetch == "one":
                        row = cur.fetchone()
                        rows = [dict(row)] if row else []
                    else:
                        rows = [dict(row) for row in cur.fetchall()]

                return {
                    output_key: rows,
                    "db_success": True,
                    "db_driver": driver,
                    "db_row_count": len(rows),
                    "db_dsn": resolved_dsn,
                }

            if driver == "postgres":
                if psycopg is None:
                    raise ImportError(
                        "psycopg is required for postgres driver. Install with: pip install psycopg[binary]"
                    )

                with psycopg.connect(resolved_dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, resolved_params)

                        if fetch == "one":
                            row = cur.fetchone()
                            columns = [desc[0] for desc in cur.description or []]
                            rows = [dict(zip(columns, row))] if row else []
                        else:
                            records = cur.fetchall()
                            columns = [desc[0] for desc in cur.description or []]
                            rows = [dict(zip(columns, record)) for record in records]

                return {
                    output_key: rows,
                    "db_success": True,
                    "db_driver": driver,
                    "db_row_count": len(rows),
                    "db_dsn": resolved_dsn,
                }

            return {
                "db_success": False,
                "db_error": f"Unsupported driver: {driver}",
            }

        except Exception as e:
            return {
                "db_success": False,
                "db_error": f"DB query error: {e}",
                "db_driver": driver,
            }

    return _db_query


def db_exec(
    dsn: Optional[str] = None,
    query: str = "",
    params: Any = None,
    output_key: str = "db_result",
    driver: str = "sqlite",
    name: Optional[str] = None,
):
    """Execute a write statement and return metadata."""
    node_name = name or "db_exec"

    @task(name=node_name, description=f"DB exec ({driver})")
    def _db_exec(ctx):
        if not query:
            return {"db_success": False, "db_error": "Query must not be empty"}

        resolved_dsn = _resolve_dsn(dsn, driver)
        resolved_params = _normalize_params(params)

        try:
            if driver == "sqlite":
                with sqlite3.connect(resolved_dsn) as conn:
                    cur = conn.cursor()
                    cur.execute(query, resolved_params)
                    conn.commit()
                    result = {
                        "rowcount": cur.rowcount,
                        "lastrowid": cur.lastrowid,
                    }

                return {
                    output_key: result,
                    "db_success": True,
                    "db_driver": driver,
                    "db_dsn": resolved_dsn,
                }

            if driver == "postgres":
                if psycopg is None:
                    raise ImportError(
                        "psycopg is required for postgres driver. Install with: pip install psycopg[binary]"
                    )

                with psycopg.connect(resolved_dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, resolved_params)
                        result = {
                            "rowcount": cur.rowcount,
                        }
                    conn.commit()

                return {
                    output_key: result,
                    "db_success": True,
                    "db_driver": driver,
                    "db_dsn": resolved_dsn,
                }

            return {
                "db_success": False,
                "db_error": f"Unsupported driver: {driver}",
            }

        except Exception as e:
            return {
                "db_success": False,
                "db_error": f"DB exec error: {e}",
                "db_driver": driver,
            }

    return _db_exec


def aql(
    query: str,
    bind_vars: Optional[Dict[str, Any]] = None,
    url: Optional[str] = None,
    database: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    output_key: str = "aql_result",
    name: Optional[str] = None,
):
    """Execute an ArangoDB AQL query and return result rows."""
    node_name = name or "aql"

    @task(name=node_name, description="Run ArangoDB AQL query")
    def _aql(ctx):
        if not query.strip():
            return {"aql_success": False, "aql_error": "Query must not be empty"}

        resolved_url = url or os.getenv("ARANGO_URL", "http://localhost:8529")
        resolved_database = database or os.getenv("ARANGO_DATABASE", "_system")
        resolved_username = username or os.getenv("ARANGO_USERNAME", "root")
        resolved_password = password or os.getenv("ARANGO_PASSWORD", "")
        resolved_bind_vars = bind_vars or {}

        try:
            if ArangoClient is None:
                raise ImportError(
                    "python-arango is required for AQL nodes. Install with: pip install python-arango"
                )

            client = ArangoClient(hosts=resolved_url)
            db = client.db(
                resolved_database,
                username=resolved_username,
                password=resolved_password,
            )
            cursor = db.aql.execute(query, bind_vars=resolved_bind_vars)
            rows = list(cursor)

            return {
                output_key: rows,
                "aql_success": True,
                "aql_row_count": len(rows),
                "aql_database": resolved_database,
                "aql_url": resolved_url,
            }
        except Exception as e:
            return {
                "aql_success": False,
                "aql_error": f"AQL query error: {e}",
                "aql_database": resolved_database,
                "aql_url": resolved_url,
            }

    return _aql


def cache_get(
    key: str,
    provider: str = "memory",
    output_key: str = "cache_value",
    default: Any = None,
    name: Optional[str] = None,
):
    """Get a value from cache providers."""
    node_name = name or f"cache_get_{key}"

    @task(name=node_name, description=f"Cache get ({provider})")
    def _cache_get(ctx):
        provider_lower = provider.lower()

        try:
            if provider_lower == "memory":
                value = _MEMORY_CACHE.get(key, default)
            elif provider_lower == "ctx":
                cache_ctx = ctx.get("cache", {})
                value = (
                    cache_ctx.get(key, default)
                    if isinstance(cache_ctx, dict)
                    else default
                )
            elif provider_lower == "redis":
                if redis is None:
                    raise ImportError(
                        "redis is required for provider='redis'. Install with: pip install redis"
                    )
                client = redis.Redis.from_url(
                    os.getenv("REDIS_URL", "redis://localhost:6379/0")
                )
                value = client.get(key)
                if value is None:
                    value = default
                elif isinstance(value, bytes):
                    value = value.decode("utf-8")
            else:
                return {
                    "cache_success": False,
                    "cache_error": f"Unsupported provider: {provider}",
                }

            return {
                output_key: value,
                "cache_success": True,
                "cache_hit": value is not default,
                "cache_provider": provider,
                "cache_key": key,
            }

        except Exception as e:
            return {
                "cache_success": False,
                "cache_error": f"Cache get error: {e}",
                "cache_provider": provider,
            }

    return _cache_get


def cache_set(
    key: str,
    value_key: str = "data",
    ttl_s: Optional[int] = None,
    provider: str = "memory",
    name: Optional[str] = None,
):
    """Set a value in cache providers."""
    node_name = name or f"cache_set_{key}"

    @task(name=node_name, description=f"Cache set ({provider})")
    def _cache_set(ctx):
        value = ctx.get(value_key)
        if value is None:
            return {
                "cache_success": False,
                "cache_error": f"No value found in context key: {value_key}",
            }

        provider_lower = provider.lower()

        try:
            if provider_lower == "memory":
                _MEMORY_CACHE[key] = value
            elif provider_lower == "ctx":
                cache_ctx = ctx.get("cache")
                if not isinstance(cache_ctx, dict):
                    cache_ctx = {}
                    ctx["cache"] = cache_ctx
                cache_ctx[key] = value
            elif provider_lower == "redis":
                if redis is None:
                    raise ImportError(
                        "redis is required for provider='redis'. Install with: pip install redis"
                    )
                client = redis.Redis.from_url(
                    os.getenv("REDIS_URL", "redis://localhost:6379/0")
                )
                payload = (
                    value
                    if isinstance(value, (str, bytes))
                    else json.dumps(value, default=str)
                )
                if ttl_s is not None:
                    client.setex(key, ttl_s, payload)
                else:
                    client.set(key, payload)
            else:
                return {
                    "cache_success": False,
                    "cache_error": f"Unsupported provider: {provider}",
                }

            return {
                "cache_success": True,
                "cache_provider": provider,
                "cache_key": key,
                "cache_ttl_s": ttl_s,
            }

        except Exception as e:
            return {
                "cache_success": False,
                "cache_error": f"Cache set error: {e}",
                "cache_provider": provider,
            }

    return _cache_set


def _build_s3_client() -> Any:
    if boto3 is None:
        raise ImportError(
            "boto3 is required for S3 nodes. Install with: pip install boto3"
        )

    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    region_name = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    kwargs: Dict[str, Any] = {"region_name": region_name}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key

    return boto3.client("s3", **kwargs)


def s3_read(
    bucket: str,
    key: str,
    output_key: str = "object_data",
    as_text: bool = True,
    encoding: str = "utf-8",
    name: Optional[str] = None,
):
    """Read an object from S3-compatible storage."""
    node_name = name or f"s3_read_{bucket}_{key}"

    @task(name=node_name, description=f"S3 read: s3://{bucket}/{key}")
    def _s3_read(ctx):
        try:
            client = _build_s3_client()
            response = client.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read()
            data = body.decode(encoding) if as_text else body

            return {
                output_key: data,
                "s3_success": True,
                "s3_bucket": bucket,
                "s3_key": key,
                "s3_content_type": response.get("ContentType"),
                "s3_etag": response.get("ETag"),
                "s3_content_length": response.get("ContentLength", len(body)),
            }
        except Exception as e:
            return {
                "s3_success": False,
                "s3_error": f"S3 read error: {e}",
                "s3_bucket": bucket,
                "s3_key": key,
            }

    return _s3_read


def s3_write(
    bucket: str,
    key: str,
    data_key: str = "data",
    content_type: Optional[str] = None,
    name: Optional[str] = None,
):
    """Write an object to S3-compatible storage."""
    node_name = name or f"s3_write_{bucket}_{key}"

    @task(name=node_name, description=f"S3 write: s3://{bucket}/{key}")
    def _s3_write(ctx):
        value = ctx.get(data_key)
        if value is None:
            return {
                "s3_success": False,
                "s3_error": f"No data found in context key: {data_key}",
                "s3_bucket": bucket,
                "s3_key": key,
            }

        if isinstance(value, bytes):
            payload = value
        elif isinstance(value, str):
            payload = value.encode("utf-8")
        else:
            payload = json.dumps(value, default=str).encode("utf-8")

        try:
            client = _build_s3_client()
            put_kwargs: Dict[str, Any] = {
                "Bucket": bucket,
                "Key": key,
                "Body": payload,
            }
            if content_type:
                put_kwargs["ContentType"] = content_type

            response = client.put_object(**put_kwargs)

            return {
                "s3_success": True,
                "s3_bucket": bucket,
                "s3_key": key,
                "s3_etag": response.get("ETag"),
                "s3_bytes_written": len(payload),
            }
        except Exception as e:
            return {
                "s3_success": False,
                "s3_error": f"S3 write error: {e}",
                "s3_bucket": bucket,
                "s3_key": key,
            }

    return _s3_write
