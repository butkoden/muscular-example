from __future__ import annotations

import os

import pytest

from example_data_elasticsearch_1.data_ports import run_example as run_elasticsearch_example
from example_data_mongodb_1.data_ports import run_example as run_mongodb_example
from example_data_opensearch_1.data_ports import run_example as run_opensearch_example
from example_data_qdrant_1.data_ports import run_example as run_qdrant_example
from example_data_redis_1.data_ports import run_example as run_redis_example
from example_data_s3_1.data_ports import run_example as run_s3_example
from example_data_sqlalchemy_1.data_ports import run_example as run_sqlalchemy_example


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("MUSCULAR_EXAMPLE_DATA_INTEGRATION"),
        reason="real data adapter examples require the Docker data stack",
    ),
]


@pytest.mark.parametrize(
    ("runner", "backend"),
    [
        (run_elasticsearch_example, "elasticsearch"),
        (run_opensearch_example, "opensearch"),
        (run_qdrant_example, "qdrant"),
        (run_redis_example, "redis"),
        (run_mongodb_example, "mongodb"),
        (run_s3_example, "s3"),
        (run_sqlalchemy_example, "sqlalchemy"),
    ],
)
def test_real_adapter_example_uses_live_backend(runner, backend):
    result = runner()

    assert result["backend"] == backend
    assert result["doctor"]["status"] == "ok"
    assert result["initialized_before"] is False


def test_real_search_examples_use_search_port_operations():
    for runner in (run_elasticsearch_example, run_opensearch_example):
        result = runner()

        assert result["hits"] == [result["document_id"]]
        assert result["highlights"]
        assert result["upsert"]["written"] == 1
        assert result["deleted"]["deleted"] == 1


def test_real_qdrant_example_uses_vector_port_operations():
    result = run_qdrant_example()

    assert result["hits"] == [result["document_id"]]
    assert result["upsert"]["written"] == 2
    assert result["deleted"]["deleted"] == 2


def test_real_redis_example_uses_all_three_ports():
    result = run_redis_example()

    assert result["cache_value"] == "page-2"
    assert result["cache_exists"] is True
    assert result["lock_acquired"] is True
    assert result["lock_release"]["deleted"] == 1
    assert result["stream_publish"]["written"] == 1
    assert result["stream_messages"]
    assert result["stream_ack"]["matched"] == 1


def test_real_mongodb_example_uses_document_store_port():
    result = run_mongodb_example()

    assert result["found"]["name"] == "Denis"
    assert result["listed_names"] == ["Denis", "Reader"]
    assert result["deleted"]["deleted"] == 1


def test_real_s3_example_uses_object_store_port():
    result = run_s3_example()

    assert result["blob"] == {
        "key": result["blob"]["key"],
        "content": "hello",
        "content_type": "text/plain",
    }
    assert result["listed_keys"] == sorted([result["blob"]["key"], result["second_key"]])
    assert result["deleted"]["deleted"] == 1
    assert "minioadmin" not in repr(result)


def test_real_sqlalchemy_example_uses_sql_resource_port_only():
    result = run_sqlalchemy_example()

    assert result["connection_name"] == "example_postgres"
    assert result["session_type"]
    assert result["native_accessed"] is False
