from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from muscles_data.catalog import DataAdapterCatalog
from muscles_data.config import DataConfig
from muscles_data.runtime import DataRuntime


LOCAL_ENDPOINTS = {
    "ELASTICSEARCH_URL": "http://127.0.0.1:29200",
    "OPENSEARCH_URL": "http://127.0.0.1:29201",
    "QDRANT_URL": "http://127.0.0.1:26333",
    "REDIS_URL": "redis://127.0.0.1:26389/15",
    "MONGODB_URL": "mongodb://127.0.0.1:27017",
    "SQLALCHEMY_POSTGRES_URL": "postgresql+psycopg://muscles:muscles@127.0.0.1:25433/muscles_data",
    "S3_ENDPOINT_URL": "http://127.0.0.1:29010",
}


def local_endpoint(name: str) -> str:
    """Return an explicit env-configured endpoint for the local example stack."""

    default = LOCAL_ENDPOINTS.get(name)
    if default is None:
        raise KeyError(f"Unknown data example endpoint: {name}")
    return os.getenv(name, default)


def build_runtime(
    resource_name: str,
    options: Mapping[str, Any],
    factory: Any,
) -> DataRuntime:
    """Compose one real adapter without importing or using its vendor client."""

    catalog = DataAdapterCatalog.with_defaults()
    catalog.register(factory)
    return DataRuntime(
        config=DataConfig.from_raw({"data": {"resources": {resource_name: dict(options)}}}),
        catalog=catalog,
    )
