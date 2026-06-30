# muscular-example Guide (EN)

## Purpose

`muscular-example` is now organized as a four-level learning staircase. Each
level adds a small set of Muscles features, so new readers do not have to start
from the full application.

## Level 1: minimal web route

Package: `example_1`

Learn:

- `ApplicationMeta`;
- `Configurator`;
- `Context(WsgiStrategy)`;
- direct `@routes.init(...)`;
- returning a ready `BaseResponse`.

This is the shortest example that shows how a request moves from a WSGI
entrypoint to a handler function.

## Level 2: REST API and guards

Package: `example_2`

Learn:

- `routes.init(...)` for a normal page;
- `api.init(...)` for a simple API endpoint;
- `api.group(...)` for shared prefix/tags/security;
- `group.init(..., auth=False)` for a public endpoint inside a protected group;
- `api.guard(...)` for path-pattern protection;
- `api.use(cors(...))` for middleware;
- generated OpenAPI schema.

Key idea: this level already has WSGI and ASGI variants, but API registration is
written once.

## Level 3: CLI

Package: `example_3`

Learn:

- `Context(CliStrategy)`;
- `@cli.group(...)`;
- `@group.command(...)`;
- nested groups;
- both `example-3/tasks list` and `example-3 tasks list`.

CLI is separated from web code so command routing can be studied on its own.

## Level 4: full application

Package: `example_4`

Learn:

- pages, templates, and static files;
- `RestApi`;
- `@api.controller(...)` and `@api.action(...)`;
- `api.group(...)` and `group.init(...)`;
- OpenAPI/Swagger;
- shared WSGI/ASGI runtime binding;
- CORS and guards;
- `JsonResponse`, `BytesResponse`, `NoContentResponse`;
- one API path with distinct route keys per HTTP method;
- SQLite and a small admin area;
- operational CLI commands.

Important: `example_4` no longer uses a custom registration wrapper. The example
now shows the framework APIs directly, so readers can see what Muscles itself
provides.

## Reading Order

1. Start with `example_1/web.py`.
2. Open `example_2/web.py` and compare a page route with API routes.
3. Read `example_3/cli.py`.
4. Finish with `example_4/web.py` and `example_4/cli.py`.

The code intentionally uses Russian and English comments together: Russian
explains the local learning context, English keeps framework terminology close
to documentation and OpenAPI wording.

## Checks

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m pytest -q
```

Tests cover all four levels and verify WSGI/ASGI parity for the full
application.
