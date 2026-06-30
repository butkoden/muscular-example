# muscular-example

Layered learning examples for the `muscles` framework.

The repository is organized as a staircase. Start with `example_1`, then move
one level up when the previous level feels clear.

## Learning Levels

### Level 1: minimal web route

Package: `example_1`

Shows the smallest useful WSGI application:

- `ApplicationMeta`;
- `Configurator`;
- `Context(WsgiStrategy)`;
- one `routes.init(...)` handler.

Run it:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:. python3 -m example_1.server
```

Open:

- http://localhost:8080/example-1

### Level 2: REST API and guards

Package: `example_2`

Adds a small REST API without extra project architecture:

- page route through `routes.init(...)`;
- public endpoint through `api.init(...)`;
- protected API group through `api.group(...)`;
- public login inside a protected group through `auth=False`;
- guard through `api.guard(...)`;
- CORS middleware through `api.use(cors(...))`;
- OpenAPI schema.

Run it:

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:. python3 -m example_2.server
```

Try it:

```bash
curl http://localhost:8080/example-2
curl http://localhost:8080/api/example-2/v1/messages
curl -X POST http://localhost:8080/api/example-2/v1/protected/login
curl http://localhost:8080/api/example-2/v1/protected/status
curl -H 'X-Api-Key: example-2-token' http://localhost:8080/api/example-2/v1/protected/status
```

### Level 3: CLI commands

Package: `example_3`

Shows the CLI runtime separately from web code:

- `Context(CliStrategy)`;
- root command group;
- nested command group;
- slash-style command aliases.

Run it:

```bash
PYTHONPATH=../muscles/src:../muscles-cli/src:. python3 -m example_3.cli example-3/hello Student
PYTHONPATH=../muscles/src:../muscles-cli/src:. python3 -m example_3.cli example-3/tasks list
```

### Level 4: full application

Package: `example_4`

Combines the framework features in one realistic app:

- pages, templates and static files;
- REST API with controller classes and action decorators;
- OpenAPI/Swagger;
- WSGI and ASGI entrypoints with the same contracts;
- API guards and endpoint-level auth override;
- CORS middleware;
- `JsonResponse`, `BytesResponse`, `NoContentResponse`;
- one API path with different route keys per HTTP method;
- SQLite persistence;
- admin login and diagnostics;
- CLI commands for operations.

Run the web app:

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m example_4.cli init-db
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m example_4.server
```

Open:

- http://localhost:8080/
- http://localhost:8080/resume
- http://localhost:8080/swagger
- http://localhost:8080/admin

Default admin password: `admin`

Try protected API features:

```bash
curl -X POST http://localhost:8080/api/v1/protected/login
curl http://localhost:8080/api/v1/protected/diagnostics
curl -H 'X-Api-Key: demo-framework-token' http://localhost:8080/api/v1/protected/diagnostics
curl -X DELETE -H 'X-Api-Key: demo-framework-token' -i http://localhost:8080/api/v1/protected/cache
curl -H 'X-Api-Key: demo-framework-token' http://localhost:8080/api/v1/protected/asset
curl -H 'X-Api-Key: demo-framework-token' http://localhost:8080/api/v1/protected/method-key
curl -X POST -H 'X-Api-Key: demo-framework-token' http://localhost:8080/api/v1/protected/method-key
```

Run level 4 CLI commands:

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m example_4.cli help
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m example_4.cli bookings
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m example_4.cli bookings remove 1
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m example_4.cli bookings/remove 1
```

## Tests

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m pytest -q
```

The test suite checks every level and verifies that level 4 behaves the same
through WSGI and ASGI test clients.

## Docker

```bash
docker compose up --build
```

## Project Guides

- English: [docs/PROJECT_GUIDE.en.md](docs/PROJECT_GUIDE.en.md)
- Русский: [docs/PROJECT_GUIDE.ru.md](docs/PROJECT_GUIDE.ru.md)

## Sync Policy

When `muscles`, `muscles-wsgi`, `muscles-asgi`, or `muscles-cli` behavior
changes, this example should be updated in the same wave and verified by tests.
