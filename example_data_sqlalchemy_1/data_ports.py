from __future__ import annotations

import importlib
import json
from typing import Any, Mapping, cast

from muscles_data import DataCapability
from muscles_data.catalog import DataAdapterCatalog
from muscles_data.config import DataConfig
from muscles_data.ports import SqlResourcePort
from muscles_data.runtime import DataRuntime
from muscles_data_sqlalchemy import SqlAlchemySqlResourceFactory

from example_data_common import development_approach


def run_example() -> dict:
    sqlalchemy = importlib.import_module("sqlalchemy")
    catalog = DataAdapterCatalog.with_defaults()
    catalog.register(SqlAlchemySqlResourceFactory())
    runtime = DataRuntime(
        config=DataConfig.from_raw(
            {"data": {"resources": {"sql.local": {"type": "sqlalchemy", "url": "sqlite:///:memory:", "name": "local_sqlite", "native_client": True}}}}
        ),
        catalog=catalog,
    )

    initialized_before = runtime.list_resources()[0]["initialized"]
    sql = cast(SqlResourcePort, runtime.require_port("sql.local", SqlResourcePort))
    with cast(Any, sql.session()) as session:
        session.execute(sqlalchemy.text("create table notes (id integer primary key, title varchar)"))
        session.execute(sqlalchemy.text("insert into notes (title) values (:title)"), {"title": "SQLAlchemy port"})
        rows = session.execute(sqlalchemy.text("select title from notes order by id")).fetchall()

    native = cast(Mapping[str, object], runtime.require_resource("sql.local", DataCapability.NATIVE_CLIENT).native_client())
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


def main() -> None:
    print(json.dumps(run_example(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
