# Local Integration Dependencies

Use Docker Compose to run services needed for integration tests and upcoming nodes.

## Services

- MinIO (S3-compatible API): `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- Redis: `localhost:6379`
- Postgres: `localhost:5432`

## Start

```bash
task deps-up
```

## Stop

```bash
task deps-down
```

## Check Status

```bash
task deps-ps
```

## Tail Logs

```bash
task deps-logs
```

## Configuration

Default values are in `.env.example`. If `.env` exists, `task deps-*` commands load it automatically.

For MinIO, a development bucket is auto-created at startup:

- `MINIO_TEST_BUCKET` (default: `microflow-dev`)
