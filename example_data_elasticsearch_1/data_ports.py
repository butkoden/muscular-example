from __future__ import annotations

from dataclasses import asdict
import json
from typing import cast

from muscles_data import DataCapability
from muscles_data.catalog import DataAdapterCatalog
from muscles_data.config import DataConfig
from muscles_data.ports import SearchIndexPort
from muscles_data.runtime import DataRuntime
from muscles_data_elasticsearch import ElasticsearchSearchFactory

from example_data_common import development_approach
from example_data_common.fakes import FakeElasticsearchClient


def run_example() -> dict:
    client = FakeElasticsearchClient()
    catalog = DataAdapterCatalog.with_defaults()
    catalog.register(ElasticsearchSearchFactory(client_factory=lambda _config: client))
    runtime = DataRuntime(
        config=DataConfig.from_raw(
            {"data": {"resources": {"search.docs": {"type": "elasticsearch", "url": "https://elastic.example", "api_key": "elastic-secret", "index": "docs", "timeout": 1, "native_client": True}}}}
        ),
        catalog=catalog,
    )

    initialized_before = runtime.list_resources()[0]["initialized"]
    search = cast(SearchIndexPort, runtime.require_port("search.docs", SearchIndexPort))
    upsert = search.upsert_documents([{"id": "doc-1", "text": "Muscles data ports", "metadata": {"section": "docs"}}])
    hits = search.search_text("muscles", filters={"section": "docs"}, limit=1, options={"highlight": True})
    deleted = search.delete_documents(filters={"section": "docs"})
    native = runtime.require_resource("search.docs", DataCapability.NATIVE_CLIENT).native_client()

    return {
        "approach": development_approach(),
        "initialized_before": initialized_before,
        "hits": [hit.id for hit in hits],
        "highlights": hits[0].highlights,
        "upsert": asdict(upsert),
        "deleted": asdict(deleted),
        "native_type": native.__class__.__name__,
        "inspect": runtime.inspect_resource("search.docs"),
        "doctor": runtime.doctor(),
    }


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
