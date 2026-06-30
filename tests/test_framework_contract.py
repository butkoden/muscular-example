from __future__ import annotations

import pytest

from muscles.asgi.testing import TestClient as AsgiTestClient
from muscles.wsgi.testing import TestClient as WsgiTestClient

from example_4.web import asgi_application, wsgi_application


@pytest.fixture(params=[
    pytest.param("wsgi", id="wsgi"),
    pytest.param("asgi", id="asgi"),
])
def client(request):
    if request.param == "wsgi":
        return WsgiTestClient(wsgi_application)
    return AsgiTestClient(asgi_application)


def test_protected_endpoints_use_shared_openapi_security_scheme(client):
    schema = client.get("/api/v1/schema").json()
    security = schema["components"]["securitySchemes"]["ApiKey"]

    assert security["type"] == "apiKey"
    assert security["in"] == "header"
    assert security["name"] == "X-Api-Key"


def test_direct_framework_registration_keeps_login_public_but_secures_group_routes(client):
    schema = client.get("/api/v1/schema").json()

    assert "security" not in schema["paths"]["/api/v1/protected/login"]["post"]
    assert schema["paths"]["/api/v1/protected/diagnostics"]["get"]["security"] == [{"ApiKey": []}]
    assert schema["paths"]["/api/v1/protected/cache"]["delete"]["security"] == [{"ApiKey": []}]
    assert schema["paths"]["/api/v1/protected/asset"]["get"]["security"] == [{"ApiKey": []}]
    assert schema["paths"]["/api/v1/protected/method-key"]["get"]["security"] == [{"ApiKey": []}]
    assert schema["paths"]["/api/v1/protected/method-key"]["post"]["security"] == [{"ApiKey": []}]


def test_all_protected_routes_are_guarded_by_direct_framework_contract(client):
    for method, path in (
        ("GET", "/api/v1/protected/diagnostics"),
        ("DELETE", "/api/v1/protected/cache"),
        ("GET", "/api/v1/protected/asset"),
        ("GET", "/api/v1/protected/method-key"),
        ("POST", "/api/v1/protected/method-key"),
    ):
        response = client.request(method, path)
        assert response.status_code == 401
        payload = response.json()
        assert payload["error"] == "unauthorized"
