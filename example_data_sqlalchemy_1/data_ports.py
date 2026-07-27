from __future__ import annotations

from dataclasses import asdict
import json

from muscles_data.ports import SqlResourcePort
from muscles_data_sqlalchemy import SqlAlchemySqlResourceFactory

from example_data_common import development_approach
from example_data_common.runtime import build_runtime, local_endpoint


def run_example() -> dict:
    """Open a real SQL session through SqlResourcePort without importing SQLAlchemy."""

    runtime = build_runtime(
        "sql.example",
        {
            "type": "sqlalchemy",
            "url": local_endpoint("SQLALCHEMY_POSTGRES_URL"),
            "name": "example_postgres",
            "pool_pre_ping": True,
            "native_client": False,
        },
        SqlAlchemySqlResourceFactory(),
    )
    try:
        initialized_before = runtime.list_resources()[0]["initialized"]
        sql = runtime.require_port("sql.example", SqlResourcePort)
        session = sql.session()
        session_type = type(session).__name__
        session.close()
        doctor = sql.doctor()

        return {
            "backend": "sqlalchemy",
            "approach": development_approach(),
            "initialized_before": initialized_before,
            "connection_name": sql.connection_name(),
            "session_type": session_type,
            "native_accessed": False,
            "inspect": sql.inspect(),
            "doctor": doctor,
        }
    finally:
        runtime.close()


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
