"""Queue abstractions for workflow job dispatching."""

import json
import os
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Optional, Tuple


@dataclass
class QueueMessage:
    message_id: str
    payload: Dict[str, Any]
    attempts: int


class InMemoryWorkflowQueue:
    """Simple in-memory queue with ACK/NACK semantics."""

    def __init__(self):
        self._pending: Deque[QueueMessage] = deque()
        self._inflight: Dict[str, QueueMessage] = {}
        self._dlq: Deque[QueueMessage] = deque()

    def enqueue(self, payload: Dict[str, Any], message_id: Optional[str] = None) -> str:
        mid = message_id or str(uuid.uuid4())
        self._pending.append(QueueMessage(message_id=mid, payload=payload, attempts=0))
        return mid

    def reserve(self, block_timeout_s: float = 0.0) -> Optional[QueueMessage]:
        if not self._pending and block_timeout_s > 0:
            time.sleep(block_timeout_s)
        if not self._pending:
            return None
        msg = self._pending.popleft()
        msg.attempts += 1
        self._inflight[msg.message_id] = msg
        return msg

    def ack(self, message_id: str) -> bool:
        return self._inflight.pop(message_id, None) is not None

    def nack(self, message_id: str, requeue: bool = True, to_dlq: bool = False) -> bool:
        msg = self._inflight.pop(message_id, None)
        if msg is None:
            return False
        if to_dlq:
            self._dlq.append(msg)
        elif requeue:
            self._pending.append(msg)
        return True

    def dlq_size(self) -> int:
        return len(self._dlq)


_MEMORY_QUEUE_SINGLETON = InMemoryWorkflowQueue()


class RedisWorkflowQueue:
    """Redis Streams queue for reliable workflow dispatching."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        stream: str = "microflow:queue:jobs",
        group: str = "microflow-workers",
        consumer: str = "worker-1",
        dlq_stream: str = "microflow:queue:dlq",
        max_attempts: int = 5,
        client: Optional[Any] = None,
    ):
        if client is None:
            try:
                import redis  # type: ignore[import-not-found]
            except ImportError as exc:
                raise ImportError(
                    "redis is required for RedisWorkflowQueue. Install with: pip install redis"
                ) from exc
            self.client = redis.Redis.from_url(redis_url)
        else:
            self.client = client

        self.stream = stream
        self.group = group
        self.consumer = consumer
        self.dlq_stream = dlq_stream
        self.max_attempts = max_attempts

        # create group if missing
        try:
            self.client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except Exception:
            pass

    def enqueue(self, payload: Dict[str, Any], message_id: Optional[str] = None) -> str:
        msg_id = message_id or "*"
        fields = {
            "payload": json.dumps(payload, default=str),
            "attempts": "0",
        }
        created = self.client.xadd(self.stream, fields, id=msg_id)
        return created.decode("utf-8") if isinstance(created, bytes) else str(created)

    def reserve(self, block_timeout_s: float = 1.0) -> Optional[QueueMessage]:
        block_ms = int(max(0.0, block_timeout_s) * 1000)
        rows = self.client.xreadgroup(
            self.group,
            self.consumer,
            {self.stream: ">"},
            count=1,
            block=block_ms,
        )
        if not rows:
            return None

        _, messages = rows[0]
        if not messages:
            return None

        msg_id, fields = messages[0]
        payload_raw = fields.get(b"payload") or fields.get("payload")
        attempts_raw = fields.get(b"attempts") or fields.get("attempts") or b"0"

        if isinstance(payload_raw, bytes):
            payload_raw = payload_raw.decode("utf-8")
        if isinstance(attempts_raw, bytes):
            attempts_raw = attempts_raw.decode("utf-8")

        payload = json.loads(payload_raw) if payload_raw else {}
        attempts = int(attempts_raw) + 1

        # Persist incremented attempts on the same stream entry by appending metadata entry.
        # Stream entries are immutable; attempts for policy is carried through nack()/dlq logic.
        mid = msg_id.decode("utf-8") if isinstance(msg_id, bytes) else str(msg_id)
        return QueueMessage(message_id=mid, payload=payload, attempts=attempts)

    def ack(self, message_id: str) -> bool:
        acked = self.client.xack(self.stream, self.group, message_id)
        return bool(acked)

    def nack(self, message_id: str, payload: Dict[str, Any], attempts: int) -> bool:
        if attempts >= self.max_attempts:
            self.client.xadd(
                self.dlq_stream,
                {
                    "payload": json.dumps(payload, default=str),
                    "attempts": str(attempts),
                    "source_message_id": message_id,
                },
            )
            self.client.xack(self.stream, self.group, message_id)
            return True

        # Requeue with updated attempts and ack original
        self.client.xadd(
            self.stream,
            {
                "payload": json.dumps(payload, default=str),
                "attempts": str(attempts),
            },
        )
        self.client.xack(self.stream, self.group, message_id)
        return True


def create_workflow_queue_from_env(**overrides: Any) -> Tuple[str, object]:
    """Create queue implementation based on QUEUE_PROVIDER env var.

    Providers:
    - memory (default)
    - redis (only used when explicitly set)
    """
    provider = str(
        overrides.get("provider") or os.getenv("QUEUE_PROVIDER", "memory")
    ).lower()

    if provider == "redis":
        redis_url = str(
            overrides.get("redis_url")
            or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )
        stream = str(
            overrides.get("stream") or os.getenv("QUEUE_STREAM", "microflow:queue:jobs")
        )
        group = str(
            overrides.get("group") or os.getenv("QUEUE_GROUP", "microflow-workers")
        )
        consumer = str(
            overrides.get("consumer") or os.getenv("QUEUE_CONSUMER", "worker-1")
        )
        dlq_stream = str(
            overrides.get("dlq_stream")
            or os.getenv("QUEUE_DLQ_STREAM", "microflow:queue:dlq")
        )
        max_attempts_raw = overrides.get("max_attempts")
        if max_attempts_raw is None:
            max_attempts_raw = os.getenv("QUEUE_MAX_ATTEMPTS", "5")
        max_attempts = int(str(max_attempts_raw))

        queue = RedisWorkflowQueue(
            redis_url=redis_url,
            stream=stream,
            group=group,
            consumer=consumer,
            dlq_stream=dlq_stream,
            max_attempts=max_attempts,
            client=overrides.get("client"),
        )
        return provider, queue

    return "memory", _MEMORY_QUEUE_SINGLETON
