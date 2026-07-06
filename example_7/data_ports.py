from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
import importlib
import json
from types import SimpleNamespace
from typing import Any, cast

from muscles import ActionDispatcher
from muscles_data import DataCapability
from muscles_data.catalog import DataAdapterCatalog
from muscles_data.config import DataConfig
from muscles_data.errors import DataCapabilityError
from muscles_data.package import init_package
from muscles_data.ports import KeyValuePort, ObjectStorePort, SearchIndexPort, SqlResourcePort, VectorSearchPort
from muscles_data.runtime import DataRuntime


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
    vector = cast(VectorSearchPort, runtime.require_port("vector.docs", VectorSearchPort))
    vector.upsert_vectors([
        {"id": "doc-1", "vector": [1.0, 0.0], "payload": {"title": "Data ports"}},
        {"id": "doc-2", "vector": [0.0, 1.0], "payload": {"title": "Other"}},
    ])
    vector_hits = [hit.id for hit in vector.search_vectors([0.9, 0.1], limit=1)]

    search = cast(SearchIndexPort, runtime.require_port("search.docs", SearchIndexPort))
    search.upsert_documents([
        {"id": "doc-1", "text": "Muscles data ports keep framework code backend-neutral."},
        {"id": "doc-2", "text": "Other note."},
    ])
    search_hits = [hit.id for hit in search.search_text("backend-neutral")]

    cache = cast(KeyValuePort, runtime.require_port("cache.default", KeyValuePort))
    cache.set("cursor", b"cursor-1")

    objects = cast(ObjectStorePort, runtime.require_port("objects.docs", ObjectStorePort))
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
    cache_value = cache.get("cursor")
    if cache_value is None:  # pragma: no cover
        raise RuntimeError("cache cursor was not written")

    return {
        "approach": development_approach(),
        "vector_hits": vector_hits,
        "search_hits": search_hits,
        "cache_value": cache_value.decode("utf-8"),
        "object_keys": [item.key for item in objects.list_objects(prefix="docs/")],
        "capability_mismatch": capability_mismatch,
        "inspect": inspect,
        "doctor": doctor,
    }


class FakeSqlRegistry:
    def session(self, name: str = "default"):
        return f"session:{name}"

    def session_factory(self, name: str = "default"):
        return f"factory:{name}"

    def inspect(self, name: str = "default"):
        return {
            "status": "ok",
            "connection": {
                "name": name,
                "url": "sqlite://secret@/:memory:",
                "safe_url": "sqlite:///:memory:",
                "role": "read_write",
            },
        }


class FakeQdrantPoint:
    def __init__(self, point_id: str, score: float, payload: dict) -> None:
        self.id = point_id
        self.score = score
        self.payload = payload


class FakeQdrantQueryResult:
    def __init__(self, points: list[FakeQdrantPoint]) -> None:
        self.points = points


class FakeQdrantClient:
    def __init__(self) -> None:
        self.collection = "docs"

    def query_points(self, **_kwargs):
        return FakeQdrantQueryResult([
            FakeQdrantPoint("doc-1", 0.92, {"section": "docs"}),
        ])

    def upsert(self, **_kwargs):
        return {"status": "completed"}

    def delete(self, **_kwargs):
        return {"status": "completed"}

    def collection_exists(self, collection_name: str) -> bool:
        return collection_name == self.collection


class FakeQdrantModels:
    class MatchValue:
        def __init__(self, value) -> None:
            self.value = value

    class MatchAny:
        def __init__(self, any) -> None:
            self.any = any

    class Range:
        def __init__(self, **kwargs) -> None:
            self.values = kwargs

    class FieldCondition:
        def __init__(self, *, key: str, match=None, range=None) -> None:
            self.key = key
            self.match = match
            self.range = range

    class Filter:
        def __init__(self, *, must=None, should=None, must_not=None) -> None:
            self.must = must or []
            self.should = should or []
            self.must_not = must_not or []

    class PointStruct:
        def __init__(self, *, id, vector, payload=None) -> None:
            self.id = id
            self.vector = vector
            self.payload = payload or {}

    class PointIdsList:
        def __init__(self, *, points) -> None:
            self.points = points

    class FilterSelector:
        def __init__(self, *, filter) -> None:
            self.filter = filter


def run_sql_resource_port_example() -> dict:
    """Show SQL as a data resource bridge without importing SQLAlchemy."""

    registry = FakeSqlRegistry()
    runtime = DataRuntime(
        config=DataConfig.from_raw(
            {
                "data": {
                    "resources": {
                        "sql.main": {
                            "type": "sql",
                            "connection": "main",
                            "role": "read_write",
                        }
                    }
                }
            }
        ),
        catalog=DataAdapterCatalog.with_defaults(sql_registry_provider=lambda: registry),
    )

    sql = cast(SqlResourcePort, runtime.require_port("sql.main", SqlResourcePort))
    return {
        "approach": development_approach(),
        "connection_name": sql.connection_name(),
        "session": sql.session(),
        "session_factory": sql.session_factory(),
        "inspect": sql.inspect(),
        "doctor": sql.doctor(),
    }


def run_sqlalchemy_resource_port_example() -> dict:
    """Show a direct SQLAlchemy resource through the same SQL port."""

    sqlalchemy = importlib.import_module("sqlalchemy")
    runtime = DataRuntime(
        config=DataConfig.from_raw(
            {
                "data": {
                    "resources": {
                        "sql.local": {
                            "type": "sqlalchemy",
                            "url": "sqlite:///:memory:",
                            "name": "local_sqlite",
                            "native_client": True,
                        }
                    }
                }
            }
        ),
        catalog=DataAdapterCatalog.with_defaults(),
    )

    initialized_before = runtime.list_resources()[0]["initialized"]
    sql = cast(SqlResourcePort, runtime.require_port("sql.local", SqlResourcePort))

    session_context = cast(Any, sql.session())
    with session_context as session:
        session.execute(sqlalchemy.text("create table notes (id integer primary key, title varchar)"))
        session.execute(sqlalchemy.text("insert into notes (title) values (:title)"), {"title": "SQLAlchemy port"})
        rows = session.execute(sqlalchemy.text("select title from notes order by id")).fetchall()

    native = cast(
        Mapping[str, object],
        runtime.require_resource("sql.local", DataCapability.NATIVE_CLIENT).native_client(),
    )
    result = {
        "approach": development_approach(),
        "initialized_before": initialized_before,
        "connection_name": sql.connection_name(),
        "rows": [row[0] for row in rows],
        "native_keys": sorted(native),
        "inspect": runtime.inspect_resource("sql.local"),
        "doctor": runtime.doctor(),
    }
    runtime.close()
    return result


def run_qdrant_vector_port_example() -> dict:
    """Show Qdrant as a vector port without a real Qdrant server."""

    client = FakeQdrantClient()
    runtime = DataRuntime(
        config=DataConfig.from_raw(
            {
                "data": {
                    "resources": {
                        "vector.docs": {
                            "type": "qdrant",
                            "url": "https://qdrant.example",
                            "api_key": "qdrant-secret",
                            "collection": "docs",
                            "timeout": 1,
                        }
                    }
                }
            }
        ),
        catalog=DataAdapterCatalog.with_defaults(
            qdrant_client_factory=lambda _config: client,
            qdrant_models_provider=lambda: FakeQdrantModels,
        ),
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


def run_all() -> dict:
    return {
        "data_ports": run_data_ports_example(),
        "sql_resource_port": run_sql_resource_port_example(),
        "sqlalchemy_resource_port": run_sqlalchemy_resource_port_example(),
        "qdrant_vector_port": run_qdrant_vector_port_example(),
    }


def main() -> None:
    print(json.dumps(run_all(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
