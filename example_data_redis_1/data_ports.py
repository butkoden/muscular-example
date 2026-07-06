from __future__ import annotations

from dataclasses import asdict
import json
from typing import cast

from muscles_data import DataCapability
from muscles_data.catalog import DataAdapterCatalog
from muscles_data.config import DataConfig
from muscles_data.ports import KeyValuePort, LockPort, StreamPort
from muscles_data.runtime import DataRuntime
from muscles_data_redis import RedisDataFactory

from example_data_common import development_approach
from example_data_common.fakes import FakeRedisClient


def run_example() -> dict:
    client = FakeRedisClient()
    catalog = DataAdapterCatalog.with_defaults()
    catalog.register(RedisDataFactory(client_factory=lambda _config: client))
    runtime = DataRuntime(
        config=DataConfig.from_raw(
            {"data": {"resources": {"cache.default": {"type": "redis", "url": "redis://:redis-secret@localhost:6379/0", "namespace": "demo", "stream_group": "workers", "timeout": 1, "native_client": True}}}}
        ),
        catalog=catalog,
    )

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
    acked = stream.ack("events", read.cursor or "0-0")
    native = runtime.require_resource("cache.default", DataCapability.NATIVE_CLIENT).native_client()

    return {
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
        "native_type": native.__class__.__name__,
        "inspect": runtime.inspect_resource("cache.default"),
        "doctor": runtime.doctor(),
    }


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
