import importlib

import pytest


utilities = importlib.import_module("microflow.nodes.utilities")


def test_validate_schema_success_with_mock_validator(monkeypatch):
    def fake_validate(instance, schema):
        if instance.get("id") is None:
            raise ValueError("id required")

    monkeypatch.setattr(utilities, "jsonschema_validate", fake_validate)

    node = utilities.validate_schema(
        data_key="payload",
        schema={"type": "object"},
        output_key="validated",
        fail_on_error=False,
    )
    result = node.spec.fn({"payload": {"id": 123}})

    assert result["schema_valid"] is True
    assert result["validated"]["id"] == 123


def test_template_render_simple_engine():
    node = utilities.template_render(
        "Hello {{ user.name }} from {{ city }}",
        variables_key="vars",
        engine="simple",
        output_key="text",
    )
    result = node.spec.fn({"vars": {"user": {"name": "Alice"}, "city": "Boston"}})

    assert result["render_success"] is True
    assert result["text"] == "Hello Alice from Boston"


def test_batch_and_deduplicate_nodes():
    batch_node = utilities.batch(data_key="items", size=2, output_key="chunks")
    batch_result = batch_node.spec.fn({"items": [1, 2, 3, 4, 5]})

    assert batch_result["batch_success"] is True
    assert batch_result["chunks"] == [[1, 2], [3, 4], [5]]

    dedupe_node = utilities.deduplicate(
        data_key="items",
        key_fields=["id"],
        output_key="unique_items",
    )
    dedupe_result = dedupe_node.spec.fn(
        {
            "items": [
                {"id": 1, "name": "A"},
                {"id": 1, "name": "A2"},
                {"id": 2, "name": "B"},
            ]
        }
    )

    assert dedupe_result["deduplicate_success"] is True
    assert dedupe_result["unique_count"] == 2
    assert [x["id"] for x in dedupe_result["unique_items"]] == [1, 2]


@pytest.mark.asyncio
async def test_http_pagination_collects_all_pages(monkeypatch):
    pages = {
        1: {"items": [{"id": 1}, {"id": 2}]},
        2: {"items": [{"id": 3}]},
        3: {"items": []},
    }

    class FakeResponse:
        def __init__(self, payload):
            self.status_code = 200
            self._payload = payload

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def request(self, **kwargs):
            page = kwargs["params"]["page"]
            return FakeResponse(pages[page])

    fake_httpx = type("FakeHTTPX", (), {"AsyncClient": FakeAsyncClient})
    monkeypatch.setattr(utilities, "httpx", fake_httpx)

    node = utilities.http_pagination(
        url="https://example.test/api",
        items_path="items",
        output_key="all_items",
    )

    result = await node.spec.fn({})

    assert result["pagination_success"] is True
    assert result["pages_fetched"] == 2
    assert [item["id"] for item in result["all_items"]] == [1, 2, 3]


def test_secret_read_from_env(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "secret-token")

    masked_node = utilities.secret_read("API_TOKEN", output_key="token", mask_in_ctx=True)
    masked_result = masked_node.spec.fn({})

    assert masked_result["secret_found"] is True
    assert masked_result["token"] == "***"
    assert masked_result["_token"] == "secret-token"

    plain_node = utilities.secret_read("API_TOKEN", output_key="token", mask_in_ctx=False)
    plain_result = plain_node.spec.fn({})

    assert plain_result["secret_found"] is True
    assert plain_result["token"] == "secret-token"
