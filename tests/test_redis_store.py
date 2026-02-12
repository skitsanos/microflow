import json
import time

from microflow import Workflow, task
from microflow.storage.redis_store import RedisStateStore


class FakeRedis:
    def __init__(self):
        self.kv = {}

    def get(self, key):
        return self.kv.get(key)

    def set(self, key, value):
        if isinstance(value, str):
            value = value.encode("utf-8")
        self.kv[key] = value
        return True

    def delete(self, key):
        if key in self.kv:
            del self.kv[key]
            return 1
        return 0

    def scan_iter(self, match=None):
        if not match or match == "*":
            for k in list(self.kv.keys()):
                yield k
            return

        # support prefix pattern like "prefix:*"
        if match.endswith("*"):
            prefix = match[:-1]
            for k in list(self.kv.keys()):
                if k.startswith(prefix):
                    yield k
        else:
            for k in list(self.kv.keys()):
                if k == match:
                    yield k


def test_redis_state_store_crud_and_listing():
    store = RedisStateStore(client=FakeRedis(), key_prefix="mf:runs")

    store.init_run("run1", {"a": 1})
    info = store.get_run_info("run1")
    assert info["status"] == "running"
    assert info["ctx"]["a"] == 1

    store.update_ctx("run1", {"b": 2})
    assert store.get_ctx("run1")["b"] == 2

    store.upsert_task("run1", "t1", status="success", attempt=1)
    task_data = store.get_task("run1", "t1")
    assert task_data["status"] == "success"

    store.set_run_status("run1", "success")
    success_runs = store.list_runs(status="success")
    assert len(success_runs) == 1
    assert success_runs[0]["id"] == "run1"

    assert store.delete_run("run1") is True
    assert store.delete_run("run1") is False


def test_redis_state_store_cleanup_old_runs():
    fake = FakeRedis()
    store = RedisStateStore(client=fake, key_prefix="mf:runs")

    old = {
        "id": "old",
        "status": "success",
        "started": time.time() - (40 * 24 * 60 * 60),
        "finished": None,
        "ctx": {},
        "tasks": {},
    }
    new = {
        "id": "new",
        "status": "success",
        "started": time.time(),
        "finished": None,
        "ctx": {},
        "tasks": {},
    }

    fake.set("mf:runs:old", json.dumps(old))
    fake.set("mf:runs:new", json.dumps(new))

    deleted = store.cleanup_old_runs(days=30)
    assert deleted == 1
    ids = [run["id"] for run in store.list_runs()]
    assert ids == ["new"]


def test_workflow_runs_with_redis_state_store():
    @task(name="step1")
    def step1(ctx):
        return {"x": 10}

    @task(name="step2")
    def step2(ctx):
        return {"y": ctx["x"] + 5}

    step1 >> step2

    workflow = Workflow([step1, step2], name="redis_store_test")
    store = RedisStateStore(client=FakeRedis(), key_prefix="mf:runs")

    result = __import__("asyncio").run(workflow.run("run-redis", store, {"z": 1}))

    assert result["x"] == 10
    assert result["y"] == 15
    run_info = store.get_run_info("run-redis")
    assert run_info["status"] == "success"
