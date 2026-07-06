from __future__ import annotations

from dataclasses import asdict
import json
from typing import cast

from muscles_data import DataCapability
from muscles_data.catalog import DataAdapterCatalog
from muscles_data.config import DataConfig
from muscles_data.ports import DocumentStorePort
from muscles_data.runtime import DataRuntime
from muscles_data_mongodb import MongoDocumentStoreFactory

from example_data_common import development_approach
from example_data_common.fakes import FakeMongoClient


def run_example() -> dict:
    client = FakeMongoClient()
    catalog = DataAdapterCatalog.with_defaults()
    catalog.register(MongoDocumentStoreFactory(client_factory=lambda _config: client))
    runtime = DataRuntime(
        config=DataConfig.from_raw(
            {"data": {"resources": {"mongo.content": {"type": "mongodb", "url": "mongodb://user:mongo-secret@localhost:27017", "database": "content", "max_limit": 5, "timeout": 1, "native_client": True}}}}
        ),
        catalog=catalog,
    )

    initialized_before = runtime.list_resources()[0]["initialized"]
    store = cast(DocumentStorePort, runtime.require_port("mongo.content", DocumentStorePort))
    upsert = store.upsert_document("profiles", "denis", {"name": "Denis", "role": "developer"})
    found = store.get_document("profiles", "denis")
    store.upsert_document("profiles", "reader", {"name": "Reader", "role": "developer"})
    listed = store.find_documents("profiles", filters={"role": "developer"}, limit=10)
    deleted = store.delete_document("profiles", "reader")
    native = runtime.require_resource("mongo.content", DataCapability.NATIVE_CLIENT).native_client()

    return {
        "approach": development_approach(),
        "initialized_before": initialized_before,
        "upsert": asdict(upsert),
        "found": found,
        "listed_names": [item["name"] for item in listed],
        "deleted": asdict(deleted),
        "native_type": native.__class__.__name__,
        "inspect": runtime.inspect_resource("mongo.content"),
        "doctor": runtime.doctor(),
    }


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
