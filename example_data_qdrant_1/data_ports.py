from __future__ import annotations

from dataclasses import asdict
import json
from typing import cast
from uuid import uuid4

from muscles_data.ports import VectorSearchPort
from muscles_data.runtime import DataRuntime
from muscles_data_qdrant import QdrantVectorFactory

from example_data_common import development_approach
from example_data_common.runtime import build_runtime, local_endpoint


def run_example() -> dict:
    """Run vector write/search/delete operations against a live Qdrant service."""

    document_id = f"example-{uuid4().hex[:12]}"
    second_id = f"example-{uuid4().hex[:12]}"
    runtime = build_runtime(
        "vector.docs",
        {
            "type": "qdrant",
            "url": local_endpoint("QDRANT_URL"),
            "collection": "muscular-example-vectors",
            "vector_size": 3,
            "distance": "cosine",
            "payload_indexes": ["section"],
            "native_client": False,
        },
        QdrantVectorFactory(),
    )
    try:
        initialized_before = runtime.list_resources()[0]["initialized"]
        vector = cast(VectorSearchPort, runtime.require_port("vector.docs", VectorSearchPort))
        upsert = vector.upsert_vectors(
            [
                {"id": document_id, "vector": [1.0, 0.0, 0.0], "payload": {"section": "examples"}},
                {"id": second_id, "vector": [0.0, 1.0, 0.0], "payload": {"section": "other"}},
            ],
            options={"wait": True},
        )
        hits = vector.search_vectors([1.0, 0.0, 0.0], filters={"section": "examples"}, limit=1)
        deleted = vector.delete_vectors(ids=[document_id, second_id], options={"wait": True})

        return {
            "backend": "qdrant",
            "approach": development_approach(),
            "initialized_before": initialized_before,
            "document_id": document_id,
            "hits": [hit.id for hit in hits],
            "upsert": asdict(upsert),
            "deleted": asdict(deleted),
            "inspect": runtime.inspect_resource("vector.docs"),
            "doctor": runtime.doctor(),
        }
    finally:
        runtime.close()


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
