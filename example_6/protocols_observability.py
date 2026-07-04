from __future__ import annotations

import json
from collections.abc import Iterator

from muscles import ApplicationMeta, Context, StreamEvent, StreamResult
from muscles.asgi import AsgiStrategy
from muscles_jsonrpc import JsonRpcAdapter
from muscles_mcp import McpStrategy
from muscles_otel import MusclesTracer, instrument_action_dispatch
from muscles_sse import SseAdapter


class ExtensionProjectionApp(metaclass=ApplicationMeta):
    """One action-first app projected through several ecosystem packages."""

    asgi_public = Context(AsgiStrategy, params={"profile": "public"})
    mcp_public = Context(McpStrategy, transport=asgi_public, params={"mcp_profile": "public"})


app = ExtensionProjectionApp()


def _mcp_metadata(route: str, name: str) -> dict:
    return {
        "mcp": {
            "route": route,
            "full_route": f"/learning/{route.lstrip('/')}",
            "name": name,
            "transport": "mcp",
            "server": "public",
            "servers": ["public"],
        }
    }


@app.action(
    name="learning.echo",
    description="Echo text and report the active transport",
    input_schema={
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "transport": {"type": ["string", "null"]},
        },
    },
    transports=["jsonrpc", "mcp"],
    metadata=_mcp_metadata("/echo", "learning.echo"),
)
def echo(payload, context):
    return {"text": payload["text"], "transport": context.transport}


@app.action(
    name="learning.progress",
    description="Stream progress events for long-running learning tasks",
    input_schema={
        "type": "object",
        "properties": {"steps": {"type": "integer", "minimum": 1}},
        "required": ["steps"],
    },
    transports=["sse"],
    stream_output=True,
    stream_metadata={"event_types": ["progress", "result"]},
)
def progress(payload, context):
    steps = int(payload["steps"])
    return StreamResult(source=_progress_events(steps), metadata={"transport": context.transport})


def _progress_events(steps: int) -> Iterator[StreamEvent]:
    for step in range(1, steps + 1):
        yield StreamEvent(
            type="progress",
            event_id=f"step-{step}",
            data={"step": step, "total": steps},
        )
    yield StreamEvent(type="result", event_id="done", data={"status": "complete", "total": steps})


def run_jsonrpc_example() -> dict:
    adapter = JsonRpcAdapter.from_application(app)
    discovery = adapter.handle({"jsonrpc": "2.0", "id": 1, "method": "rpc.discover"})
    echo_response = adapter.handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "learning.echo",
            "params": {"text": "Hello JSON-RPC"},
        }
    )
    return {
        "methods": [method["name"] for method in discovery["result"]],
        "echo": echo_response,
    }


def run_sse_example() -> dict:
    response = SseAdapter.from_application(app).stream_action("learning.progress", {"steps": 2})
    return {
        "status": response.status,
        "content_type": response.headers["Content-Type"],
        "chunks": list(response.stream),
    }


def run_mcp_example() -> dict:
    tools = app.mcp_public.execute(operation="list_tools", server="public")
    call = app.mcp_public.execute(
        operation="call_tool",
        server="public",
        name="learning.echo",
        arguments={"text": "Hello MCP"},
    )
    return {
        "tools": [tool["name"] for tool in tools],
        "call": call,
    }


def run_otel_example() -> dict:
    tracer = MusclesTracer(enabled=True)
    result = instrument_action_dispatch(
        tracer,
        app,
        action_name="learning.echo",
        payload={"text": "Hello trace"},
        transport="jsonrpc",
    )
    return {
        "result": result.value,
        "spans": [record.name for record in tracer.records],
        "span_count": len(tracer.records),
    }


def run_all() -> dict:
    return {
        "jsonrpc": run_jsonrpc_example(),
        "sse": run_sse_example(),
        "mcp": run_mcp_example(),
        "otel": run_otel_example(),
    }


def main() -> None:
    print(json.dumps(run_all(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
