# Muscular Project Guide (EN)

## Purpose

`muscular-example` is a practical reference for building full-stack projects on
top of the Muscular ecosystem.

It shows how to combine:

- `muscles` core (`ApplicationMeta`, `Configurator`, `Context`);
- `muscles-wsgi` runtime for web/API;
- `muscles-asgi` runtime with the same web/API contracts;
- `muscles-cli` runtime for console automation.

## 1) Recommended project layout

```text
project/
  your_app/
    web.py
    server.py
    cli.py
    db.py
    templates.py
    templates/
    static/
  tests/
  pyproject.toml
  docker-compose.yml
  Dockerfile
```

## 2) Application bootstrap

Create an application class with:

1. `ApplicationMeta`
2. static config (`Configurator`)
3. runtime strategy (`Context(WsgiStrategy, params={})` or `Context(AsgiStrategy, params={})`)

This example keeps a shared base application and creates thin runtime-specific
classes:

```python
from muscles import ApplicationMeta, Context
from muscles.asgi import asgi_app
from muscles.asgi.asgi import AsgiStrategy
from muscles.wsgi import wsgi_app
from muscles.wsgi.wsgi import WsgiStrategy


class App:
    def __init__(self, strategy):
        self.context = Context(strategy, params={})


class WsgiApp(App, metaclass=ApplicationMeta):
    pass


class AsgiApp(App, metaclass=ApplicationMeta):
    pass


wsgi_application = wsgi_app(WsgiApp(WsgiStrategy), context="context")
asgi_application = asgi_app(AsgiApp(AsgiStrategy), context="context")
```

Then register:

- page routes (`routes.init(...)`);
- API controllers (`RestApi`, `@api.controller`, `@api.action`);
- startup actions (e.g., `init_db()`).

## 3) Routing strategy

Use route trees consistently:

- Web: `/`, `/resume`, `/admin/...`
- API: `/api/v1/...`
- CLI: `bookings remove 1` and alias `bookings/remove 1`

The same conceptual route hierarchy makes behavior predictable between web, api
and console.

## 4) Data layer

For small projects, SQLite is enough:

- initialize schema once per process/path;
- keep WAL mode for better concurrency;
- isolate DB operations in `db.py`.

## 5) API and OpenAPI

Define request/response models with Muscular schema classes and attach them to
actions. Swagger/OpenAPI is generated automatically from these definitions.

Value objects can be introduced gradually via `ValueObjectField`:

- keep OpenAPI and routing contracts stable;
- enforce domain invariants in dedicated value classes;
- avoid spreading format checks across handlers.

Protected groups can still expose public endpoints by overriding auth on a
single handler:

```python
api.guard("/api/v1/protected/**", require_api_key)
protected = api.group("/protected", tags=["Framework primitives"], security=["ApiKey"])


@protected.init("/login", method="post", auth=False)
def login(request):
    return JsonResponse({"token": API_DEMO_TOKEN})
```

Use core response helpers for protocol-neutral handlers:

- `JsonResponse` for explicit JSON payloads;
- `BytesResponse` for binary/text bytes;
- `NoContentResponse` for `204 No Content`.

The example also registers `cors(...)` on the API itinerary, so preflight and
regular responses behave the same under WSGI and ASGI.

Muscles core now owns the shared backend pipeline for typed handler arguments,
dependency resolution, guards, route-level security and middleware. WSGI and
ASGI adapters use that pipeline, while this example verifies parity through the
same API tests for both transports.

Route contract v2 also allows one API path to use distinct route keys per HTTP
method:

```python
@protected.init("/method-key", key="framework.method_key.read", method="get")
def method_key_read(request):
    return JsonResponse({"operation": "read"})


@protected.init("/method-key", key="framework.method_key.write", method="post")
def method_key_write(request):
    return JsonResponse({"operation": "write"})
```

## 6) CLI layer

Use grouped commands for operational workflows:

- `init-db`
- `bookings list`
- `bookings remove <id>`
- `diagnostics`
- `set-password`

## 7) Testing baseline

At minimum:

- smoke test for pages/static/swagger/schema;
- API booking flow test;
- admin login + diagnostics test;
- CLI command behavior test.
- WSGI/ASGI parity test for guarded routes, auth override, CORS, response helpers
  and distinct route keys on the same path.

## 8) How to create your own project from this template

1. Copy this repo.
2. Rename package and domain-specific templates/content.
3. Keep architecture and tests.
4. Update DB schema and API models for your domain.
5. Add CI checks and deployment targets.

## 9) Keeping this example up to date

Whenever framework internals change:

1. pull latest `muscles*` repos;
2. run example tests;
3. patch example usage where contracts changed;
4. document migration notes in README/changelog.
