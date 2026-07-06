from __future__ import annotations

import json
from types import SimpleNamespace

from muscles import ActionDispatcher
from muscles_data import init_package
from muscles_data.errors import DataCapabilityError
from muscles_data.ports import KeyValuePort, ObjectStorePort, SearchIndexPort, VectorSearchPort


DEVELOPMENT_APPROACH = {
    "contract": "The example uses named resources and typed ports instead of backend clients.",
    "use_case": "Data operations live in run_data_ports_example(), away from the web adapter.",
    "adapter": "The WSGI route only renders the use-case result; data access goes through muscles-data.",
}


def development_approach() -> dict:
    return dict(DEVELOPMENT_APPROACH)


def run_data_ports_example() -> dict:
    """Show typed ports, capability mismatch and safe diagnostics on fake resources."""

    # RU: Конфиг описывает ресурсы, но adapters создаются лениво.
    # EN: Config declares resources, but adapters are initialized lazily.
    app = SimpleNamespace()
    runtime = init_package(
        app,
        {
            "data": {
                "resources": {
                    "vector.docs": {"type": "memory_vector"},
                    "search.docs": {"type": "memory_search"},
                    "cache.default": {"type": "memory_kv", "token": "local-demo-token"},
                    "objects.docs": {"type": "memory_object"},
                }
            }
        },
    )

    # RU: Основной путь — typed ports. Здесь нет импортов Qdrant/Redis/S3.
    # EN: The primary path is typed ports. There are no backend SDK imports here.
    vector = runtime.require_port("vector.docs", VectorSearchPort)
    vector.upsert_vectors([
        {"id": "doc-1", "vector": [1.0, 0.0], "payload": {"title": "Data ports"}},
        {"id": "doc-2", "vector": [0.0, 1.0], "payload": {"title": "Other"}},
    ])
    vector_hits = [hit.id for hit in vector.search_vectors([0.9, 0.1], limit=1)]

    search = runtime.require_port("search.docs", SearchIndexPort)
    search.upsert_documents([
        {"id": "doc-1", "text": "Muscles data ports keep framework code backend-neutral."},
        {"id": "doc-2", "text": "Other note."},
    ])
    search_hits = [hit.id for hit in search.search_text("backend-neutral")]

    cache = runtime.require_port("cache.default", KeyValuePort)
    cache.set("cursor", b"cursor-1")

    objects = runtime.require_port("objects.docs", ObjectStorePort)
    objects.put_object("docs/readme.txt", b"hello", content_type="text/plain")

    try:
        runtime.require_port("cache.default", VectorSearchPort)
    except DataCapabilityError as exc:
        capability_mismatch = {"error": exc.__class__.__name__, "message": str(exc)}
    else:  # pragma: no cover
        capability_mismatch = {"error": None, "message": "unexpected success"}

    dispatcher = ActionDispatcher(app)
    inspect = dispatcher.execute("data.resource.inspect", {"name": "cache.default"}).value
    doctor = dispatcher.execute("data.doctor", {}).value

    return {
        "approach": development_approach(),
        "vector_hits": vector_hits,
        "search_hits": search_hits,
        "cache_value": cache.get("cursor").decode("utf-8"),
        "object_keys": [item.key for item in objects.list_objects(prefix="docs/")],
        "capability_mismatch": capability_mismatch,
        "inspect": inspect,
        "doctor": doctor,
    }


def run_all() -> dict:
    return {"data_ports": run_data_ports_example()}


def main() -> None:
    print(json.dumps(run_all(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
