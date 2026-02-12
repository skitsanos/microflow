"""Example: queue provider selection with QUEUE_PROVIDER (memory/redis)."""

from microflow import create_workflow_queue_from_env


def main():
    print("=== Queue Provider Example ===")
    provider, queue = create_workflow_queue_from_env()
    print(f"Provider selected: {provider}")

    message_id = queue.enqueue({"workflow_name": "demo", "run_id": "queue_run_001"})
    print(f"Enqueued message: {message_id}")

    msg = queue.reserve(block_timeout_s=0.0)
    if msg is None:
        print("No message available")
        return

    print(f"Reserved message: id={msg.message_id}, payload={msg.payload}, attempts={msg.attempts}")

    if provider == "redis":
        queue.ack(msg.message_id)
    else:
        queue.ack(msg.message_id)

    print("Message acknowledged")


if __name__ == "__main__":
    main()
