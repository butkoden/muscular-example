import io
import json
from typing import Any

from example_4.web import app


BASE_ENV: dict[str, Any] = {
    "SERVER_PROTOCOL": "HTTP/1.1",
    "UWSGI_ROUTER": "http",
    "HTTP_HOST": "localhost:8080",
    "SERVER_NAME": "localhost",
    "SERVER_PORT": "8080",
    "REMOTE_ADDR": "127.0.0.1",
    "REMOTE_PORT": "50000",
}


def call(path: str, method: str = "GET", body: bytes = b"", content_type: str = "text/html"):
    status_headers: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]):
        status_headers["status"] = status
        status_headers["headers"] = headers

    env: dict[str, Any] = dict(BASE_ENV)
    env.update({
        "REQUEST_METHOD": method,
        "REQUEST_URI": path,
        "PATH_INFO": path,
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    })
    chunks = app(env, start_response)
    return status_headers, b"".join(chunks)


def cookie_from(headers: list[tuple[str, str]], name: str) -> str:
    for key, value in headers:
        if key.lower() == "set-cookie" and value.startswith(name):
            return value.split(";", 1)[0]
    return ""


def test_home_page_renders():
    meta, body = call("/")
    assert meta["status"].startswith("200")
    assert b"Muscular Example" in body


def test_pages_assets_and_swagger_render():
    for path, marker in [
        ("/resume", b"Portfolio"),
        ("/static/site.css", b".site-header"),
        ("/swagger", b"Swagger"),
        ("/api/v1/schema", b"Muscular Example API"),
    ]:
        meta, body = call(path)
        assert meta["status"].startswith("200")
        assert marker in body

    schema = json.loads(call("/api/v1/schema")[1].decode())
    assert schema["servers"] == [{"url": "http://localhost:8080"}]
    assert "/api/v1/bookings" in schema["paths"]


def test_booking_api_creates_record():
    payload = json.dumps({
        "name": "Denis",
        "email": "denis@example.test",
        "title": "Test slot",
        "starts_at": "2026-06-01T10:00:00+03:00",
        "ends_at": "2026-06-01T10:30:00+03:00",
        "notes": "Smoke test",
    }).encode()

    meta, body = call("/api/v1/bookings", method="POST", body=payload, content_type="application/json")

    assert meta["status"].startswith("200")
    assert b"Test slot" in body


def test_booking_api_rejects_invalid_email():
    payload = json.dumps({
        "name": "Denis",
        "email": "not-an-email",
        "title": "Invalid",
        "starts_at": "2026-06-01T10:00:00+03:00",
        "ends_at": "2026-06-01T10:30:00+03:00",
        "notes": "Should fail",
    }).encode()

    meta, body = call("/api/v1/bookings", method="POST", body=payload, content_type="application/json")
    assert meta["status"].startswith("400")
    assert b"Validation failed" in body


def test_admin_login_and_diagnostics():
    body = b"password=admin"
    meta, _ = call(
        "/admin/login",
        method="POST",
        body=body,
        content_type="application/x-www-form-urlencoded",
    )
    cookie = cookie_from(meta["headers"], "example_4_admin")

    status_headers: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]):
        status_headers["status"] = status
        status_headers["headers"] = headers

    env: dict[str, Any] = dict(BASE_ENV)
    env.update({
        "REQUEST_METHOD": "GET",
        "REQUEST_URI": "/admin/diagnostics",
        "PATH_INFO": "/admin/diagnostics",
        "CONTENT_TYPE": "text/html",
        "CONTENT_LENGTH": "0",
        "HTTP_COOKIE": cookie,
        "wsgi.input": io.BytesIO(),
    })
    chunks = app(env, start_response)
    body = b"".join(chunks)

    assert status_headers["status"].startswith("200")
    assert b"database_exists" in body
