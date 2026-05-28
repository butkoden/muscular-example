# muscular-example

Public example project based on `butko-info-site` that demonstrates how to build
real Muscular applications with:

- website pages;
- REST API with Swagger/OpenAPI;
- CLI commands with nested routing;
- SQLite persistence;
- simple admin/auth flow.

This repository is meant to stay in sync with the framework evolution.

## Quick Start

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli init-db
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.server
```

Open:

- http://localhost:8080/
- http://localhost:8080/resume
- http://localhost:8080/swagger
- http://localhost:8080/admin

Default admin password: `admin`

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
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli help
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli bookings
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli bookings remove 1
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-cli/src python3 -m butko_info.cli bookings/remove 1
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
