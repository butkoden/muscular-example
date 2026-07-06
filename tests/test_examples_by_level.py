from pathlib import Path

import pytest

from muscles.asgi.testing import TestClient as AsgiTestClient
from muscles.wsgi.testing import TestClient as WsgiTestClient

from example_1.web import app as example_1_app
from example_2.web import API_TOKEN as EXAMPLE_2_TOKEN
from example_2.web import asgi_application as example_2_asgi_application
from example_2.web import wsgi_application as example_2_wsgi_application
from example_3.cli import CliApp as Example3CliApp
from example_3.cli import expand_slash_args as expand_example_3_slash_args


def test_readme_describes_the_learning_levels():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Level 1: minimal web route" in readme
    assert "Level 2: REST API and guards" in readme
    assert "Level 3: CLI commands" in readme
    assert "Level 4: full application" in readme
    assert "Level 5: data, documents and AI extensions" in readme
    assert "Level 6: protocol projections and observability" in readme
    assert "Level 7: typed data ports" in readme


def test_example_1_is_a_minimal_wsgi_page():
    response = WsgiTestClient(example_1_app).get("/example-1")

    assert response.status_code == 200
    assert b"Hello from example_1" in response.content


@pytest.fixture(params=[
    pytest.param("wsgi", id="wsgi"),
    pytest.param("asgi", id="asgi"),
])
def example_2_client(request):
    if request.param == "wsgi":
        return WsgiTestClient(example_2_wsgi_application)
    return AsgiTestClient(example_2_asgi_application)


def test_example_2_shows_api_group_guards_and_openapi(example_2_client):
    public_response = example_2_client.post("/api/example-2/v1/protected/login")
    denied_response = example_2_client.get("/api/example-2/v1/protected/status")
    allowed_response = example_2_client.get(
        "/api/example-2/v1/protected/status",
        headers={"X-Api-Key": EXAMPLE_2_TOKEN},
    )
    schema = example_2_client.get("/api/example-2/v1/schema").json()

    assert public_response.status_code == 200
    assert public_response.json() == {"token": EXAMPLE_2_TOKEN}
    assert denied_response.status_code == 401
    assert allowed_response.status_code == 200
    assert "/api/example-2/v1/messages" in schema["paths"]
    assert "security" not in schema["paths"]["/api/example-2/v1/protected/login"]["post"]


def test_example_3_shows_grouped_cli_commands():
    assert expand_example_3_slash_args(("example-3/tasks", "list")) == ("example-3", "tasks", "list")

    app = Example3CliApp()

    assert app.run("example-3", "hello", "Student") is True
    assert app.run("example-3", "tasks", "list") is True
