from __future__ import annotations

import json

from muscles import inspect_application
from muscles.asgi.testing import TestClient
from muscles.cli.tooling import main as cli_main
from muscles_mcp import McpAdapter

from example_8.booking_app import app, booking_use_case, http_application


def test_booking_example_contract_exposes_one_action_to_three_projections():
    contract = inspect_application(app)

    actions = [action for action in contract["actions"] if action["name"] == "bookings.create"]

    assert len(actions) == 1
    assert actions[0]["input_schema"]["required"] == ["title"]
    assert actions[0]["transports"] == ["http", "cli", "mcp"]
    assert actions[0]["metadata"]["mcp"]["name"] == "bookings.create"


def test_http_cli_and_mcp_call_the_same_booking_use_case(monkeypatch, capsys):
    calls: list[tuple[str, int]] = []

    def record_booking(*, title: str, guest_count: int):
        calls.append((title, guest_count))
        return {"id": len(calls), "title": title, "guest_count": guest_count, "status": "created"}

    monkeypatch.setattr(booking_use_case, "create", record_booking)

    http_response = TestClient(http_application).post(
        "/actions/bookings.create",
        json={"title": "HTTP", "guest_count": 2},
    )
    assert http_response.status_code == 200
    assert http_response.json()["result"]["title"] == "HTTP"

    cli_exit_code = cli_main(
        [
            "action",
            "run",
            "bookings.create",
            "--app",
            "example_8.booking_app:app",
            "--payload-json",
            json.dumps({"title": "CLI", "guest_count": 3}),
            "--json",
        ]
    )
    assert cli_exit_code == 0
    assert json.loads(capsys.readouterr().out)["result"]["title"] == "CLI"

    mcp_response = McpAdapter.from_application(app, context="mcp_public").call_tool(
        "bookings.create",
        {"title": "MCP", "guest_count": 4},
    )
    assert mcp_response.get("isError", False) is False
    assert mcp_response["content"][0]["json"]["title"] == "MCP"

    assert calls == [("HTTP", 2), ("CLI", 3), ("MCP", 4)]


def test_booking_example_rejects_invalid_payload_through_http():
    response = TestClient(http_application).post("/actions/bookings.create", json={})

    assert response.status_code == 400
    assert response.json()["code"] == "action_validation_error"
    assert response.json()["action"] == "bookings.create"
