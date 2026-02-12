# Integration Nodes

## API

```python
db_query(dsn=None, query='', params=None, output_key='rows', fetch='all', driver='sqlite', name=None)
db_exec(dsn=None, query='', params=None, output_key='db_result', driver='sqlite', name=None)
aql(query, bind_vars=None, url=None, database=None, username=None, password=None, output_key='aql_result', name=None)

cache_get(key, provider='memory', output_key='cache_value', default=None, name=None)
cache_set(key, value_key='data', ttl_s=None, provider='memory', name=None)

s3_read(bucket, key, output_key='object_data', as_text=True, encoding='utf-8', name=None)
s3_write(bucket, key, data_key='data', content_type=None, name=None)
```

## Database

- `driver='sqlite'` works without extra dependencies.
- `driver='postgres'` requires `psycopg`.
- `db_query` returns rows as dictionaries in `output_key`.
- `db_exec` returns metadata in `output_key` (for example rowcount, lastrowid for SQLite).

## Cache

Supported providers:

- `memory` (module-local in-process cache)
- `ctx` (stores values under `ctx['cache']`)
- `redis` (requires `redis` package and `REDIS_URL`)

## ArangoDB AQL

- `aql` executes an AQL query using `python-arango`.
- Connection defaults are loaded from:
  - `ARANGO_URL`
  - `ARANGO_DATABASE`
  - `ARANGO_USERNAME`
  - `ARANGO_PASSWORD`
- You can override each value via function parameters.

## S3 / MinIO

- Requires `boto3`.
- Uses standard AWS env vars and optional custom endpoint via `S3_ENDPOINT_URL` (useful for MinIO).

Common env vars:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `S3_ENDPOINT_URL`

## Example

```python
from microflow import db_exec, db_query, aql, cache_set, cache_get, s3_write

create = db_exec(dsn="./data/app.db", driver="sqlite", query="CREATE TABLE IF NOT EXISTS t (id INTEGER)")
insert = db_exec(dsn="./data/app.db", driver="sqlite", query="INSERT INTO t(id) VALUES (?)", params=(1,))
read = db_query(dsn="./data/app.db", driver="sqlite", query="SELECT id FROM t")

arangodb_rows = aql(
    query="FOR d IN users FILTER d.age >= @min_age RETURN d",
    bind_vars={"min_age": 18},
)

set_cache = cache_set("latest_rows", value_key="rows", provider="memory")
get_cache = cache_get("latest_rows", provider="memory")

write_obj = s3_write("microflow-dev", "exports/rows.json", data_key="rows")
```
