from __future__ import annotations

from dataclasses import asdict
import json
from typing import cast
from uuid import uuid4

from muscles_data.ports import DocumentStorePort
from muscles_data_mongodb import MongoDocumentStoreFactory

from example_data_common import development_approach
from example_data_common.runtime import build_runtime, local_endpoint


def run_example() -> dict:
    """Run document operations against a live MongoDB service."""

    collection = f"profiles_{uuid4().hex[:12]}"
    runtime = build_runtime(
        "mongo.content",
        {
            "type": "mongodb",
            "url": local_endpoint("MONGODB_URL"),
            "database": "muscular_example",
            "max_limit": 10,
            "native_client": False,
        },
        MongoDocumentStoreFactory(),
    )
    try:
        initialized_before = runtime.list_resources()[0]["initialized"]
        store = cast(DocumentStorePort, runtime.require_port("mongo.content", DocumentStorePort))
        upsert = store.upsert_document(collection, "denis", {"name": "Denis", "role": "developer"})
        found = store.get_document(collection, "denis")
        store.upsert_document(collection, "reader", {"name": "Reader", "role": "developer"})
        listed = store.find_documents(collection, filters={"role": "developer"}, limit=10)
        deleted = store.delete_document(collection, "reader")
        store.delete_document(collection, "denis")

        return {
            "backend": "mongodb",
            "approach": development_approach(),
            "initialized_before": initialized_before,
            "upsert": asdict(upsert),
            "found": dict(found or {}),
            "listed_names": sorted(str(item["name"]) for item in listed),
            "deleted": asdict(deleted),
            "inspect": runtime.inspect_resource("mongo.content"),
            "doctor": runtime.doctor(),
        }
    finally:
        runtime.close()


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
