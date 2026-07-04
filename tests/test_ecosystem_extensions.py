from example_5.data_ai_documents import run_ai_example, run_documents_example, run_sql_example
from example_6.protocols_observability import (
    run_jsonrpc_example,
    run_mcp_example,
    run_otel_example,
    run_sse_example,
)


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
