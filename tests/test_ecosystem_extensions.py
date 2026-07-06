from muscles.wsgi.testing import TestClient as WsgiTestClient

from example_5.data_ai_documents import run_ai_example, run_documents_example, run_sql_example
from example_5.web import app as example_5_app
from example_6.protocols_observability import (
    run_jsonrpc_example,
    run_mcp_example,
    run_otel_example,
    run_sse_example,
)
from example_6.web import app as example_6_app
from example_7.data_ports import run_data_ports_example, run_qdrant_vector_port_example, run_sql_resource_port_example
from example_7.web import app as example_7_app


def test_example_5_shows_sql_documents_and_ai_packages():
    sql = run_sql_example()
    documents = run_documents_example()
    ai = run_ai_example()

    for payload in (sql, documents, ai):
        assert payload["approach"]["contract"]
        assert payload["approach"]["use_case"]
        assert payload["approach"]["adapter"]

    assert sql["connection_names"] == ["analytics", "default"]
    assert sql["ready_topics"] == ["muscles-sql", "muscles-documents"]
    assert sql["total"] == 3

    assert documents["loaded_count"] == 2
    assert documents["chunks_count"] >= 1
    assert documents["sync_operations"]
    assert all("name" in operation for operation in documents["sync_operations"])

    assert ai["answer"]
    assert "default" in ai["sources"]
    assert ai["doctor"]["status"] == "ok"


def test_example_6_projects_actions_to_jsonrpc_sse_mcp_and_otel():
    jsonrpc = run_jsonrpc_example()
    sse = run_sse_example()
    mcp = run_mcp_example()
    otel = run_otel_example()

    for payload in (jsonrpc, sse, mcp, otel):
        assert payload["approach"]["contract"]
        assert payload["approach"]["use_case"]
        assert payload["approach"]["adapter"]

    assert "learning.echo" in jsonrpc["methods"]
    assert jsonrpc["echo"]["result"] == {"text": "Hello JSON-RPC", "transport": "jsonrpc"}

    assert sse["status"] == 200
    assert sse["content_type"].startswith("text/event-stream")
    assert any("event: progress" in chunk for chunk in sse["chunks"])
    assert any("event: result" in chunk for chunk in sse["chunks"])

    assert "learning.echo" in mcp["tools"]
    assert mcp["call"]["content"][0]["json"]["transport"] == "mcp"

    assert otel["result"] == {"text": "Hello trace", "transport": "jsonrpc"}
    assert "muscles.action.execute" in otel["spans"]
    assert "muscles.action.validate" in otel["spans"]
    assert "muscles.action.handler" in otel["spans"]


def test_examples_5_and_6_keep_example_1_wsgi_foundation():
    example_5 = WsgiTestClient(example_5_app).get("/example-5")
    example_6 = WsgiTestClient(example_6_app).get("/example-6")

    assert example_5.status_code == 200
    assert example_5.json()["level"] == 5
    assert "sql" in example_5.json()["result"]

    assert example_6.status_code == 200
    assert example_6.json()["level"] == 6
    assert "jsonrpc" in example_6.json()["result"]


def test_example_7_shows_typed_data_ports_and_diagnostics():
    result = run_data_ports_example()

    assert result["approach"]["contract"]
    assert result["approach"]["use_case"]
    assert result["approach"]["adapter"]
    assert result["vector_hits"] == ["doc-1"]
    assert result["search_hits"] == ["doc-1"]
    assert result["object_keys"] == ["docs/readme.txt"]
    assert result["cache_value"] == "cursor-1"
    assert result["capability_mismatch"]["error"] == "DataCapabilityError"
    assert result["doctor"]["status"] == "ok"
    assert "native_client" not in repr(result["inspect"])


def test_example_7_shows_sql_resource_port_bridge():
    result = run_sql_resource_port_example()

    assert result["approach"]["contract"]
    assert result["connection_name"] == "main"
    assert result["session"] == "session:main"
    assert result["session_factory"] == "factory:main"
    assert result["inspect"]["connection"]["url"] == "***"
    assert result["inspect"]["connection"]["safe_url"] == "sqlite:///:memory:"
    assert result["doctor"]["status"] == "ok"
    assert "secret" not in repr(result)


def test_example_7_shows_qdrant_vector_port_bridge():
    result = run_qdrant_vector_port_example()

    assert result["approach"]["contract"]
    assert result["hits"] == ["doc-1"]
    assert result["upsert"]["written"] == 2
    assert result["deleted_by_id"]["deleted"] == 1
    assert result["deleted_by_filter"]["status"] == "ok"
    assert result["doctor"]["status"] == "ok"
    assert result["inspect"]["options"]["url"] == "***"
    assert result["inspect"]["options"]["api_key"] == "***"
    assert "qdrant-secret" not in repr(result)


def test_example_7_keeps_example_1_wsgi_foundation():
    response = WsgiTestClient(example_7_app).get("/example-7")

    assert response.status_code == 200
    assert response.json()["level"] == 7
    assert "data_ports" in response.json()["result"]
    assert "sql_resource_port" in response.json()["result"]
    assert "qdrant_vector_port" in response.json()["result"]
