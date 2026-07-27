from __future__ import annotations

from dataclasses import asdict
import json
from typing import cast
from uuid import uuid4

from muscles_data.ports import SearchIndexPort
from muscles_data.runtime import DataRuntime
from muscles_data_elasticsearch import ElasticsearchSearchFactory

from example_data_common import development_approach
from example_data_common.runtime import build_runtime, local_endpoint


def run_example() -> dict:
    """Run the SearchIndexPort contract against a live Elasticsearch service."""

    document_id = f"example-{uuid4().hex[:12]}"
    runtime = build_runtime(
        "search.docs",
        {
            "type": "elasticsearch",
            "url": local_endpoint("ELASTICSEARCH_URL"),
            "index": "muscular-example-docs",
            "native_client": False,
        },
        ElasticsearchSearchFactory(),
    )
    try:
        initialized_before = runtime.list_resources()[0]["initialized"]
        search = cast(SearchIndexPort, runtime.require_port("search.docs", SearchIndexPort))
        upsert = search.upsert_documents(
            [{"id": document_id, "title": "Muscles", "text": "Muscles data ports", "metadata": {"section": "examples"}}],
            options={"refresh": "wait_for"},
        )
        hits = search.search_text("muscles", filters={"section": "examples"}, limit=1, options={"highlight": True})
        deleted = search.delete_documents(ids=[document_id], options={"refresh": "wait_for"})

        return {
            "backend": "elasticsearch",
            "approach": development_approach(),
            "initialized_before": initialized_before,
            "document_id": document_id,
            "hits": [hit.id for hit in hits],
            "highlights": hits[0].highlights if hits else {},
            "upsert": asdict(upsert),
            "deleted": asdict(deleted),
            "inspect": runtime.inspect_resource("search.docs"),
            "doctor": runtime.doctor(),
        }
    finally:
        runtime.close()


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
