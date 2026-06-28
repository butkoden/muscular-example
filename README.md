# muscular-example

Public example project based on `butko-info-site` that demonstrates how to build
real Muscular applications with:

- website pages;
- REST API with Swagger/OpenAPI;
- interchangeable WSGI and ASGI runtime entrypoints;
- route guards with endpoint-level auth override;
- CORS middleware;
- core response helpers (`JsonResponse`, `BytesResponse`, `NoContentResponse`);
- CLI commands with nested routing;
- SQLite persistence;
- simple admin/auth flow.

This repository is meant to stay in sync with the framework evolution.

## Quick Start

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli init-db
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.server
```

Open:

- http://localhost:8080/
- http://localhost:8080/resume
- http://localhost:8080/swagger
- http://localhost:8080/admin

Default admin password: `admin`

## Framework feature examples

`butko_info.web` builds two equivalent applications:

- `wsgi_application` for `muscles-wsgi`;
- `asgi_application` for `muscles-asgi`.

The REST API demonstrates a protected route group with a public endpoint inside
the group:

```python
api.guard("/api/v1/protected/**", require_api_key)
protected = api.group("/protected", tags=["Framework primitives"], security=["ApiKey"])


@protected.init("/login", method="post", auth=False)
def login(request):
    return JsonResponse({"token": API_DEMO_TOKEN})
```

Try it through the WSGI server:

```bash
curl -X POST http://localhost:8080/api/v1/protected/login
curl http://localhost:8080/api/v1/protected/diagnostics
curl -H 'X-Api-Key: demo-framework-token' http://localhost:8080/api/v1/protected/diagnostics
curl -X DELETE -H 'X-Api-Key: demo-framework-token' -i http://localhost:8080/api/v1/protected/cache
curl -H 'X-Api-Key: demo-framework-token' http://localhost:8080/api/v1/protected/asset
```

The test suite runs the same protected API checks through both WSGI and ASGI
test clients.

## Docker

```bash
docker compose up --build
```

If Docker Hub returns `429 Too Many Requests`, either authenticate:

```bash
docker login
docker compose up --build
```

or override image source:

```bash
PYTHON_IMAGE=registry.example.com/python:3.12-slim docker compose up --build
```

## CLI examples

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli help
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli bookings
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli bookings remove 1
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli bookings/remove 1
```

## Tests

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m pytest -q
```

## Project Guides

- English: [docs/PROJECT_GUIDE.en.md](docs/PROJECT_GUIDE.en.md)
- Русский: [docs/PROJECT_GUIDE.ru.md](docs/PROJECT_GUIDE.ru.md)

## Sync Policy

When `muscles`, `muscles-wsgi`, `muscles-asgi`, or `muscles-cli` behavior changes,
this example should be updated in the same wave and verified by tests.

## ValueObject example

The project includes a pilot domain value object (`EmailAddress`) wired through
`ValueObjectField` in `Booking.email` model field.
