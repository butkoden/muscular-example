from __future__ import annotations

import pytest

from muscles.asgi.testing import TestClient as AsgiTestClient
from muscles.wsgi.testing import TestClient as WsgiTestClient

from butko_info.web import API_DEMO_TOKEN, asgi_application, wsgi_application


@pytest.fixture(params=[
    pytest.param("wsgi", id="wsgi"),
    pytest.param("asgi", id="asgi"),
])
def client(request):
    if request.param == "wsgi":
        return WsgiTestClient(wsgi_application)
    return AsgiTestClient(asgi_application)


def test_public_login_overrides_protected_group_guard(client):
    response = client.post("/api/v1/protected/login")

    assert response.status_code == 200
    assert response.json() == {"token": API_DEMO_TOKEN}


def test_protected_endpoint_requires_guard_header(client):
    denied = client.get("/api/v1/protected/diagnostics")
    allowed = client.get(
        "/api/v1/protected/diagnostics",
        headers={"X-Api-Key": API_DEMO_TOKEN},
    )

    assert denied.status_code == 401
    denied_payload = denied.json()
    assert denied_payload["error"] == "unauthorized"
    assert denied_payload["error_code"] == "unauthorized"
    assert allowed.status_code == 200
    assert allowed.json()["diagnostics"]["database"].endswith(".sqlite3")
    assert allowed.json()["diagnostics"]["database_exists"] is True


def test_core_response_helpers_work_in_wsgi_and_asgi(client):
    empty = client.delete(
        "/api/v1/protected/cache",
        headers={"X-Api-Key": API_DEMO_TOKEN},
    )
    asset = client.get(
        "/api/v1/protected/asset",
        headers={"X-Api-Key": API_DEMO_TOKEN},
    )

    assert empty.status_code == 204
    assert empty.content == b""
    assert asset.status_code == 200
    assert asset.content == b"muscular-example"
    assert asset.headers["Content-Type"] == "text/plain"


def test_cors_preflight_is_available_for_api(client):
    response = client.request(
        "OPTIONS",
        "/api/v1/protected/diagnostics",
        headers={
            "Origin": "https://butko.info",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == "https://butko.info"
    assert "GET" in response.headers["Access-Control-Allow-Methods"]


def test_openapi_documents_group_metadata_and_auth_override(client):
    schema = client.get("/api/v1/schema").json()

    login = schema["paths"]["/api/v1/protected/login"]["post"]
    diagnostics = schema["paths"]["/api/v1/protected/diagnostics"]["get"]

    assert login["tags"] == ["Framework primitives"]
    assert "security" not in login
    assert diagnostics["tags"] == ["Framework primitives"]
    assert "401" in diagnostics["responses"]
