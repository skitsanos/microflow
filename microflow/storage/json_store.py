"""JSON file-based state storage for workflows"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import RLock


class JSONStateStore:
    """File-based state store using JSON files"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.runs_dir = self.data_dir / "runs"
        self.runs_dir.mkdir(exist_ok=True)
        self._lock = RLock()

    def _run_file(self, run_id: str) -> Path:
        """Get the JSON file path for a workflow run"""
        return self.runs_dir / f"{run_id}.json"

    def _load_run_data(self, run_id: str) -> Dict[str, Any]:
        """Load run data from JSON file"""
        run_file = self._run_file(run_id)
        if not run_file.exists():
            return {
                "id": run_id,
                "status": "pending",
                "started": None,
                "finished": None,
                "ctx": {},
                "tasks": {}
            }

        try:
            with open(run_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Return default structure if file is corrupted
            return {
                "id": run_id,
                "status": "pending",
                "started": None,
                "finished": None,
                "ctx": {},
                "tasks": {}
            }

    def _save_run_data(self, run_id: str, data: Dict[str, Any]) -> None:
        """Save run data to JSON file"""
        run_file = self._run_file(run_id)
        with self._lock:
            # Atomic write using temporary file
            temp_file = run_file.with_suffix('.tmp')
            try:
                with open(temp_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                temp_file.replace(run_file)
            except Exception:
                if temp_file.exists():
                    temp_file.unlink()
                raise

    def init_run(self, run_id: str, ctx: Dict[str, Any]) -> None:
        """Initialize a new workflow run"""
        data = {
            "id": run_id,
            "status": "running",
            "started": time.time(),
            "finished": None,
            "ctx": ctx,
            "tasks": {}
        }
        self._save_run_data(run_id, data)

    def set_run_status(self, run_id: str, status: str) -> None:
        """Update workflow run status"""
        data = self._load_run_data(run_id)
        data["status"] = status
        if status in ["success", "failed", "stalled"]:
            data["finished"] = time.time()
        self._save_run_data(run_id, data)

    def get_ctx(self, run_id: str) -> Dict[str, Any]:
        """Get workflow context"""
        data = self._load_run_data(run_id)
        return data.get("ctx", {})

    def update_ctx(self, run_id: str, ctx_update: Dict[str, Any]) -> None:
        """Update workflow context"""
        with self._lock:
            data = self._load_run_data(run_id)
            data["ctx"].update(ctx_update)
            self._save_run_data(run_id, data)

    def upsert_task(self, run_id: str, name: str, **kwargs) -> None:
        """Insert or update task state"""
        with self._lock:
            data = self._load_run_data(run_id)

            if name not in data["tasks"]:
                data["tasks"][name] = {}

            # Update task data
            task_data = data["tasks"][name]
            for key, value in kwargs.items():
                if value is not None:
                    task_data[key] = value

            self._save_run_data(run_id, data)

    def get_task(self, run_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Get task state"""
        data = self._load_run_data(run_id)
        return data["tasks"].get(name)

    def get_run_info(self, run_id: str) -> Dict[str, Any]:
        """Get complete run information"""
        return self._load_run_data(run_id)

    def list_runs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all workflow runs, optionally filtered by status"""
        runs = []

        for run_file in self.runs_dir.glob("*.json"):
            try:
                with open(run_file, 'r') as f:
                    data = json.load(f)
                    if status is None or data.get("status") == status:
                        runs.append(data)
            except (json.JSONDecodeError, IOError):
                continue

        # Sort by started time, newest first
        runs.sort(key=lambda x: x.get("started", 0), reverse=True)
        return runs

    def delete_run(self, run_id: str) -> bool:
        """Delete a workflow run"""
        run_file = self._run_file(run_id)
        if run_file.exists():
            run_file.unlink()
            return True
        return False

    def cleanup_old_runs(self, days: int = 30) -> int:
        """Clean up runs older than specified days"""
        cutoff = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0

        for run_file in self.runs_dir.glob("*.json"):
            try:
                with open(run_file, 'r') as f:
                    data = json.load(f)
                    started = data.get("started", 0)
                    if started < cutoff:
                        run_file.unlink()
                        deleted_count += 1
            except (json.JSONDecodeError, IOError):
                continue

        return deleted_count