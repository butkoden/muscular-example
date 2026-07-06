from __future__ import annotations

from dataclasses import asdict
import json
from typing import cast

from muscles_data.catalog import DataAdapterCatalog
from muscles_data.config import DataConfig
from muscles_data.ports import VectorSearchPort
from muscles_data.runtime import DataRuntime
from muscles_data_qdrant import QdrantVectorFactory

from example_data_common import development_approach
from example_data_common.fakes import FakeQdrantClient, FakeQdrantModels


def run_example() -> dict:
    client = FakeQdrantClient()
    catalog = DataAdapterCatalog.with_defaults()
    catalog.register(QdrantVectorFactory(client_factory=lambda _config: client, models_provider=lambda: FakeQdrantModels))
    runtime = DataRuntime(
        config=DataConfig.from_raw(
            {"data": {"resources": {"vector.docs": {"type": "qdrant", "url": "https://qdrant.example", "api_key": "qdrant-secret", "collection": "docs", "timeout": 1}}}}
        ),
        catalog=catalog,
    )

    vector = cast(VectorSearchPort, runtime.require_port("vector.docs", VectorSearchPort))
    upsert = vector.upsert_vectors([
        {"id": "doc-1", "vector": [0.9, 0.1], "payload": {"section": "docs"}},
        {"id": "doc-2", "vector": [0.1, 0.9], "payload": {"section": "notes"}},
    ])
    hits = [hit.id for hit in vector.search_vectors([1.0, 0.0], filters={"section": "docs"}, limit=1)]
    deleted_by_id = vector.delete_vectors(ids=["doc-2"])
    deleted_by_filter = vector.delete_vectors(filters={"section": "notes"})

    return {
        "approach": development_approach(),
        "hits": hits,
        "upsert": asdict(upsert),
        "deleted_by_id": asdict(deleted_by_id),
        "deleted_by_filter": asdict(deleted_by_filter),
        "inspect": runtime.inspect_resource("vector.docs"),
        "doctor": runtime.doctor(),
    }


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
