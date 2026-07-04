from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from muscles import ActionDispatcher
from muscles_ai import init_package as init_ai_package
from muscles_documents import init_package as init_documents_package
from muscles_sql import FilterClause, QuerySpec, SqlConnectionConfig, SqlConnectionRegistry
from muscles_sql import SqlRepository, UnitOfWork
from sqlalchemy import Column, Integer, MetaData, String, Table


def run_sql_example(db_url: str = "sqlite:///:memory:") -> dict:
    """Show SQL registry, repository queries, and Unit of Work in one flow."""

    registry = SqlConnectionRegistry(
        [
            SqlConnectionConfig(name="default", url=db_url),
            SqlConnectionConfig(name="analytics", url="sqlite:///:memory:", role="read"),
        ]
    )

    manager = registry.manager("default")
    metadata = MetaData()
    learning_notes = Table(
        "learning_notes",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("topic", String, nullable=False),
        Column("status", String, nullable=False),
    )
    metadata.create_all(manager.engine)

    with UnitOfWork(registry.session_factory("default")) as uow:
        repo = SqlRepository(uow.session, learning_notes)
        repo.bulk_create(
            [
                {"topic": "muscles-sql", "status": "ready"},
                {"topic": "muscles-documents", "status": "ready"},
                {"topic": "muscles-ai", "status": "draft"},
            ]
        )

    with registry.session("default") as session:
        repo = SqlRepository(session, learning_notes)
        ready_rows = repo.query(
            QuerySpec(
                filters=[FilterClause("status", "eq", "ready")],
                order_by=[learning_notes.c.id.asc()],
            )
        )
        total = repo.count()

    inspection = registry.inspect("default")
    return {
        "connection_names": registry.names(),
        "safe_url": registry.config("default").safe_url,
        "status": inspection["status"],
        "total": total,
        "ready_topics": [row["topic"] for row in ready_rows],
    }


def run_documents_example() -> dict:
    """Show local document loading, parsing, chunking, and sync planning."""

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "guide.md").write_text(
            "<h1>Muscles documents</h1>\n\nSimple paragraph for parsing.",
            encoding="utf-8",
        )
        (root / "notes.txt").write_text("Line 1\nLine 2\n", encoding="utf-8")

        app = SimpleNamespace()
        init_documents_package(
            app,
            {
                "key": "documents",
                "chunk_size": 12,
                "chunk_overlap": 3,
                "sources": {
                    "repo": {
                        "type": "local",
                        "path": str(root),
                    }
                },
            },
        )
        dispatcher = ActionDispatcher(app)

        sources = dispatcher.execute("documents.sources.list", {"source": "repo"}).value
        loaded = dispatcher.execute("documents.load", {"source": "repo"}).value
        first = next(
            (item for item in loaded["documents"] if item["reference"].endswith("guide.md")),
            loaded["documents"][0],
        )
        parsed = dispatcher.execute(
            "documents.parse",
            {
                "source": first["source"],
                "reference": first["reference"],
                "text": first["text"],
                "parser": "html",
            },
        ).value
        chunks = dispatcher.execute(
            "documents.chunk",
            {
                "source": first["source"],
                "reference": first["reference"],
                "text": parsed["text"],
            },
        ).value
        sync_plan = dispatcher.execute("documents.sync.plan", {"source": "repo"}).value

    return {
        "sources": sources,
        "loaded_count": loaded["count"],
        "parsed_preview": parsed["text"][:32],
        "chunks_count": len(chunks["chunks"]),
        "sync_operations": sync_plan["operations"],
    }


def run_ai_example() -> dict:
    """Show framework-level AI actions with the built-in noop provider."""

    app = SimpleNamespace()
    init_ai_package(
        app,
        {
            "key": "ai",
            "provider": "noop",
            "model_name": "stub-mini",
            "top_k_default": 2,
            "top_k_max": 5,
            "options": {"temperature": 0.0},
        },
    )
    dispatcher = ActionDispatcher(app)

    ask = dispatcher.execute(
        "ai.ask",
        {
            "question": "What can the new Muscles AI package do?",
            "top_k": 2,
            "source": "manual",
        },
    ).value
    search = dispatcher.execute("ai.search", {"query": "muscles", "top_k": 3}).value
    sources = dispatcher.execute("ai.sources.list", {}).value
    doctor = dispatcher.execute("ai.doctor", {}).value

    return {
        "answer": ask["answer"],
        "search_hits": len(search["hits"]),
        "sources": _source_names(sources),
        "doctor": doctor,
    }


def _source_names(payload: dict) -> list[str]:
    sources = payload.get("sources", [])
    if isinstance(sources, dict):
        return sorted(sources)
    return sorted(str(source) for source in sources)


def run_all() -> dict:
    return {
        "sql": run_sql_example(),
        "documents": run_documents_example(),
        "ai": run_ai_example(),
    }


def main() -> None:
    print(json.dumps(run_all(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
