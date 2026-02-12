import importlib
import sys

import pytest

from microflow import Workflow
from microflow.nodes.data_transform import rename_fields, select_fields
from microflow.nodes.http_request import webhook_call
from microflow.nodes.subworkflow import WorkflowLoader


@pytest.mark.asyncio
async def test_webhook_call_supports_callable_json_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        headers = {"content-type": "application/json"}
        text = '{"ok": true}'
        content = b'{"ok": true}'
        url = "https://example.test/webhook"

        def json(self):
            return {"ok": True}

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def request(self, **kwargs):
            captured.update(kwargs)
            return FakeResponse()

    fake_httpx = type("FakeHTTPX", (), {"AsyncClient": FakeAsyncClient})

    http_request_module = importlib.import_module("microflow.nodes.http_request")

    monkeypatch.setattr(http_request_module, "httpx", fake_httpx)

    node = webhook_call("https://example.test/webhook", payload_keys=["user_id", "event"])
    result = await node.spec.fn({"user_id": 42, "event": "created", "_private": "ignore"})

    assert captured["json"] == {"user_id": 42, "event": "created"}
    assert result["http_success"] is True
    assert result["http_status_code"] == 200


def test_workflow_loader_can_import_module(tmp_path, monkeypatch):
    module_name = "temp_microflow_workflow"
    module_file = tmp_path / f"{module_name}.py"

    module_file.write_text(
        "from microflow import Workflow, task\n"
        "@task(name='noop')\n"
        "def noop(ctx):\n"
        "    return {'ok': True}\n"
        "def create_workflow():\n"
        "    return Workflow([noop], name='tmp')\n",
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    sys.modules.pop(module_name, None)

    loaded = WorkflowLoader.load_from_module(module_name)

    assert isinstance(loaded, Workflow)
    assert loaded.tasks[0].spec.name == "noop"


def test_select_and_rename_fields_default_optionals():
    select_task = select_fields(data_key="users")
    renamed_task = rename_fields(data_key="users")

    selected = select_task.spec.fn({"users": [{"id": 1, "name": "Alice"}]})
    renamed = renamed_task.spec.fn({"users": [{"id": 1, "name": "Alice"}]})

    assert selected["transform_success"] is True
    assert selected["selected_data"] == [{}]
    assert renamed["transform_success"] is True
    assert renamed["renamed_data"] == [{"id": 1, "name": "Alice"}]
