"""Redis-backed state storage for workflows."""

import json
import time
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional

try:
    import redis  # type: ignore[import-not-found]
except ImportError:
    redis = None


class RedisStateStore:
    """Redis state store using one JSON blob per run."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "microflow:runs",
        client: Optional[Any] = None,
    ):
        if client is None:
            if redis is None:
                raise ImportError(
                    "redis is required for RedisStateStore. Install with: pip install redis"
                )
            self.client = redis.Redis.from_url(redis_url)
        else:
            self.client = client

        self.key_prefix = key_prefix.rstrip(":")
        self._lock = RLock()

    def _run_key(self, run_id: str) -> str:
        return f"{self.key_prefix}:{run_id}"

    def _run_pattern(self) -> str:
        return f"{self.key_prefix}:*"

    def _decode(self, raw: Any) -> Optional[str]:
        if raw is None:
            return None
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        return str(raw)

    def _default_run_data(self, run_id: str) -> Dict[str, Any]:
        return {
            "id": run_id,
            "status": "pending",
            "started": None,
            "finished": None,
            "ctx": {},
            "tasks": {},
        }

    def _load_run_data(self, run_id: str) -> Dict[str, Any]:
        raw = self._decode(self.client.get(self._run_key(run_id)))
        if raw is None:
            return self._default_run_data(run_id)

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
            return self._default_run_data(run_id)
        except (json.JSONDecodeError, TypeError, ValueError):
            return self._default_run_data(run_id)

    def _save_run_data(self, run_id: str, data: Dict[str, Any]) -> None:
        payload = json.dumps(data, default=str)
        self.client.set(self._run_key(run_id), payload)

    def init_run(self, run_id: str, ctx: Dict[str, Any]) -> None:
        data = {
            "id": run_id,
            "status": "running",
            "started": time.time(),
            "finished": None,
            "ctx": ctx,
            "tasks": {},
        }
        self._save_run_data(run_id, data)

    def set_run_status(self, run_id: str, status: str) -> None:
        data = self._load_run_data(run_id)
        data["status"] = status
        if status in ["success", "failed", "stalled"]:
            data["finished"] = time.time()
        self._save_run_data(run_id, data)

    def get_ctx(self, run_id: str) -> Dict[str, Any]:
        return self._load_run_data(run_id).get("ctx", {})

    def update_ctx(self, run_id: str, ctx_update: Dict[str, Any]) -> None:
        with self._lock:
            data = self._load_run_data(run_id)
            data.setdefault("ctx", {})
            data["ctx"].update(ctx_update)
            self._save_run_data(run_id, data)

    def upsert_task(self, run_id: str, name: str, **kwargs) -> None:
        with self._lock:
            data = self._load_run_data(run_id)
            data.setdefault("tasks", {})
            data["tasks"].setdefault(name, {})

            task_data = data["tasks"][name]
            for key, value in kwargs.items():
                if value is not None:
                    task_data[key] = value

            self._save_run_data(run_id, data)

    def get_task(self, run_id: str, name: str) -> Optional[Dict[str, Any]]:
        return self._load_run_data(run_id).get("tasks", {}).get(name)

    def get_run_info(self, run_id: str) -> Dict[str, Any]:
        return self._load_run_data(run_id)

    def _iter_run_keys(self) -> Iterable[str]:
        keys = self.client.scan_iter(match=self._run_pattern())
        for key in keys:
            decoded = self._decode(key)
            if decoded:
                yield decoded

    def list_runs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        runs: List[Dict[str, Any]] = []
        for key in self._iter_run_keys():
            raw = self._decode(self.client.get(key))
            if raw is None:
                continue
            try:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    continue
                if status is None or data.get("status") == status:
                    runs.append(data)
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

        runs.sort(key=lambda x: x.get("started", 0) or 0, reverse=True)
        return runs

    def delete_run(self, run_id: str) -> bool:
        return bool(self.client.delete(self._run_key(run_id)))

    def cleanup_old_runs(self, days: int = 30) -> int:
        cutoff = time.time() - (days * 24 * 60 * 60)
        deleted = 0

        for key in self._iter_run_keys():
            raw = self._decode(self.client.get(key))
            if raw is None:
                continue
            try:
                data = json.loads(raw)
                started = data.get("started", 0) if isinstance(data, dict) else 0
                if started and started < cutoff:
                    deleted += int(self.client.delete(key))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

        return deleted
