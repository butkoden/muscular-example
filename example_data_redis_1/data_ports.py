from __future__ import annotations

from dataclasses import asdict
import json
from typing import cast
from uuid import uuid4

from muscles_data.ports import KeyValuePort, LockPort, StreamPort
from muscles_data_redis import RedisDataFactory

from example_data_common import development_approach
from example_data_common.runtime import build_runtime, local_endpoint


def run_example() -> dict:
    """Run key-value, lock and stream operations against a live Redis service."""

    suffix = uuid4().hex[:12]
    namespace = f"muscular-example:{suffix}"
    runtime = build_runtime(
        "cache.default",
        {
            "type": "redis",
            "url": local_endpoint("REDIS_URL"),
            "namespace": namespace,
            "stream_group": f"group-{suffix}",
            "consumer": f"consumer-{suffix}",
            "native_client": False,
        },
        RedisDataFactory(),
    )
    try:
        initialized_before = runtime.list_resources()[0]["initialized"]
        cache = cast(KeyValuePort, runtime.require_port("cache.default", KeyValuePort))
        cache_write = cache.set("cursor", b"page-2", ttl_seconds=60)
        cache_value = cache.get("cursor")
        cache_exists = cache.exists("cursor")

        lock = cast(LockPort, runtime.require_port("cache.default", LockPort))
        handle = lock.acquire_lock("sync", ttl_seconds=30)
        lock_release = lock.release_lock(handle)

        stream = cast(StreamPort, runtime.require_port("cache.default", StreamPort))
        published = stream.publish("events", {"kind": "cursor.updated"})
        read = stream.read("events", limit=10)
        message_id = read.messages[0]["id"] if read.messages else ""
        acked = stream.ack("events", message_id)

        return {
            "backend": "redis",
            "approach": development_approach(),
            "initialized_before": initialized_before,
            "cache_write": asdict(cache_write),
            "cache_value": cache_value.decode("utf-8") if cache_value else None,
            "cache_exists": cache_exists,
            "lock_acquired": handle is not None,
            "lock_release": asdict(lock_release),
            "stream_publish": asdict(published),
            "stream_messages": read.messages,
            "stream_ack": asdict(acked),
            "inspect": runtime.inspect_resource("cache.default"),
            "doctor": runtime.doctor(),
        }
    finally:
        runtime.close()


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
