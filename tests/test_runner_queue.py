import asyncio
import json

import pytest

from microflow import Workflow, WorkflowRunner, task
from microflow.queueing import (
    InMemoryWorkflowQueue,
    RedisWorkflowQueue,
    create_workflow_queue_from_env,
)


@pytest.mark.asyncio
async def test_workflow_runner_limits_concurrency():
    active = {"count": 0, "max_seen": 0}

    @task(name="sleepy")
    async def sleepy(ctx):
        active["count"] += 1
        active["max_seen"] = max(active["max_seen"], active["count"])
        await asyncio.sleep(0.05)
        active["count"] -= 1
        return {"done": True}

    wf = Workflow([sleepy], name="wf_limit")
    runner = WorkflowRunner(max_concurrent_workflows=1)

    await asyncio.gather(
        runner.run_workflow(wf, run_id="r1"),
        runner.run_workflow(wf, run_id="r2"),
        runner.run_workflow(wf, run_id="r3"),
    )

    assert active["max_seen"] == 1


def test_queue_provider_defaults_to_memory(monkeypatch):
    monkeypatch.delenv("QUEUE_PROVIDER", raising=False)
    provider, queue = create_workflow_queue_from_env()

    assert provider == "memory"
    assert isinstance(queue, InMemoryWorkflowQueue)


class FakeRedisStreams:
    def __init__(self):
        self.streams = {}
        self.groups = set()

    def xgroup_create(self, stream, group, id="0", mkstream=True):
        self.groups.add((stream, group))
        self.streams.setdefault(stream, [])
        return True

    def xadd(self, stream, fields, id="*"):
        self.streams.setdefault(stream, [])
        next_id = f"{len(self.streams[stream]) + 1}-0" if id == "*" else id
        normalized = {}
        for k, v in fields.items():
            nk = k.encode("utf-8") if isinstance(k, str) else k
            nv = v.encode("utf-8") if isinstance(v, str) else v
            normalized[nk] = nv
        self.streams[stream].append((next_id.encode("utf-8"), normalized))
        return next_id.encode("utf-8")

    def xreadgroup(self, group, consumer, streams, count=1, block=0):
        stream = next(iter(streams.keys()))
        entries = self.streams.get(stream, [])
        if not entries:
            return []
        msg = entries.pop(0)
        return [(stream.encode("utf-8"), [msg])]

    def xack(self, stream, group, message_id):
        return 1


def test_redis_queue_ack_nack_and_dlq():
    fake = FakeRedisStreams()
    queue = RedisWorkflowQueue(
        client=fake,
        stream="q:jobs",
        group="g1",
        consumer="c1",
        dlq_stream="q:dlq",
        max_attempts=2,
    )

    queue.enqueue({"workflow": "demo"})

    msg = queue.reserve(block_timeout_s=0)
    assert msg is not None
    assert msg.payload["workflow"] == "demo"

    # first nack should requeue
    queue.nack(msg.message_id, msg.payload, attempts=1)
    assert len(fake.streams["q:jobs"]) == 1

    msg2 = queue.reserve(block_timeout_s=0)
    assert msg2 is not None
    queue.nack(msg2.message_id, msg2.payload, attempts=2)

    # after max attempts goes to dlq
    assert len(fake.streams["q:dlq"]) == 1
    dlq_payload_raw = fake.streams["q:dlq"][0][1][b"payload"].decode("utf-8")
    assert json.loads(dlq_payload_raw)["workflow"] == "demo"


def test_in_memory_queue_ack_nack():
    q = InMemoryWorkflowQueue()
    mid = q.enqueue({"a": 1})
    msg = q.reserve()
    assert msg and msg.message_id == mid
    assert q.ack(mid) is True

    mid2 = q.enqueue({"a": 2})
    msg2 = q.reserve()
    assert msg2 and msg2.message_id == mid2
    assert q.nack(mid2, to_dlq=True) is True
    assert q.dlq_size() == 1
