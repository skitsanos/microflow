import importlib
from pathlib import Path

integrations = importlib.import_module("microflow.nodes.integrations")


def test_db_exec_and_query_sqlite(tmp_path: Path):
    db_path = tmp_path / "test.db"

    create = integrations.db_exec(
        dsn=str(db_path),
        driver="sqlite",
        query="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)",
    )
    created = create.spec.fn({})
    assert created["db_success"] is True

    insert = integrations.db_exec(
        dsn=str(db_path),
        driver="sqlite",
        query="INSERT INTO users(name) VALUES (?)",
        params=("Alice",),
    )
    inserted = insert.spec.fn({})
    assert inserted["db_success"] is True
    assert inserted["db_result"]["rowcount"] == 1

    select = integrations.db_query(
        dsn=str(db_path),
        driver="sqlite",
        query="SELECT id, name FROM users",
        output_key="rows",
    )
    queried = select.spec.fn({})
    assert queried["db_success"] is True
    assert queried["db_row_count"] == 1
    assert queried["rows"][0]["name"] == "Alice"


def test_cache_memory_set_get():
    setter = integrations.cache_set("key1", value_key="payload", provider="memory")
    set_result = setter.spec.fn({"payload": {"v": 1}})
    assert set_result["cache_success"] is True

    getter = integrations.cache_get("key1", provider="memory", output_key="val")
    get_result = getter.spec.fn({})
    assert get_result["cache_success"] is True
    assert get_result["val"] == {"v": 1}


def test_aql_uses_env_defaults(monkeypatch):
    monkeypatch.setenv("ARANGO_URL", "http://arangodb.test:8529")
    monkeypatch.setenv("ARANGO_DATABASE", "mydb")
    monkeypatch.setenv("ARANGO_USERNAME", "user1")
    monkeypatch.setenv("ARANGO_PASSWORD", "pass1")

    state = {}

    class FakeAQL:
        @staticmethod
        def execute(query, bind_vars):
            state["query"] = query
            state["bind_vars"] = bind_vars
            return [{"id": "a"}, {"id": "b"}]

    class FakeDB:
        aql = FakeAQL()

    class FakeArangoClient:
        def __init__(self, hosts):
            state["hosts"] = hosts

        def db(self, database, username, password):
            state["database"] = database
            state["username"] = username
            state["password"] = password
            return FakeDB()

    monkeypatch.setattr(integrations, "ArangoClient", FakeArangoClient)

    node = integrations.aql(
        query="FOR doc IN users FILTER doc.age >= @min_age RETURN doc",
        bind_vars={"min_age": 21},
        output_key="rows",
    )
    result = node.spec.fn({})

    assert result["aql_success"] is True
    assert result["aql_row_count"] == 2
    assert result["rows"][0]["id"] == "a"
    assert state["hosts"] == "http://arangodb.test:8529"
    assert state["database"] == "mydb"
    assert state["username"] == "user1"
    assert state["password"] == "pass1"
    assert state["bind_vars"] == {"min_age": 21}


def test_s3_write_and_read_with_fake_boto3(monkeypatch):
    storage = {}

    class FakeBody:
        def __init__(self, data: bytes):
            self._data = data

        def read(self):
            return self._data

    class FakeS3Client:
        def put_object(self, Bucket, Key, Body, **kwargs):
            storage[(Bucket, Key)] = Body
            return {"ETag": "etag-1"}

        def get_object(self, Bucket, Key):
            body = storage[(Bucket, Key)]
            return {
                "Body": FakeBody(body),
                "ETag": "etag-1",
                "ContentLength": len(body),
                "ContentType": "text/plain",
            }

    class FakeBoto3:
        @staticmethod
        def client(name, **kwargs):
            assert name == "s3"
            return FakeS3Client()

    monkeypatch.setattr(integrations, "boto3", FakeBoto3)

    writer = integrations.s3_write("bucket-a", "path/file.txt", data_key="payload")
    wrote = writer.spec.fn({"payload": "hello"})
    assert wrote["s3_success"] is True
    assert wrote["s3_bytes_written"] == 5

    reader = integrations.s3_read("bucket-a", "path/file.txt", output_key="data")
    read = reader.spec.fn({})
    assert read["s3_success"] is True
    assert read["data"] == "hello"
