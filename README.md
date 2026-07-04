# muscular-example

Layered learning examples for the `muscles` framework.

The repository is organized as a staircase. Start with `example_1`, then move
one level up when the previous level feels clear.

## Development Approach

All examples follow the same small teaching structure:

- contract: schemas, routes, actions or `run_*_example()` outputs are explicit;
- use case: the useful scenario is kept in small functions/classes;
- adapter: WSGI, ASGI, CLI, SQL, AI, Documents, JSON-RPC, SSE, MCP and OTEL stay at the edges;
- test: each level has a compact test contract that proves the example remains executable.

This keeps the examples comparable even when they demonstrate different
libraries.

## Running Examples Correctly

The examples export application callables. Do not treat the repository as a
place to write custom server loops:

- WSGI examples expose `app` or `wsgi_application` and should be run by a WSGI server such as `gunicorn`;
- ASGI examples expose `asgi_application` and should be run by an ASGI server such as `uvicorn`;
- CLI examples are the exception and should be run as Python modules.

Install the runner dependencies from `requirements.txt`, then use the commands
below for each level.

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
PYTHONPATH=../muscles/src:../muscles-wsgi/src:. python3 -m gunicorn example_1.web:app --bind 0.0.0.0:8080
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
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:. python3 -m gunicorn example_2.web:wsgi_application --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:. python3 -m uvicorn example_2.web:asgi_application --host 0.0.0.0 --port 8080
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
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m gunicorn example_4.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m uvicorn example_4.web:asgi_application --host 0.0.0.0 --port 8080
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

### Level 5: data, documents and AI extensions

Package: `example_5`

Shows newer framework extension packages without adding web routing noise:

- `muscles-sql` named connections, repository queries and Unit of Work;
- `muscles-documents` local source loading, parsing, chunking and sync planning;
- `muscles-ai` noop-provider actions through `ActionDispatcher`.

The web foundation intentionally mirrors `example_1`: `ApplicationMeta`,
`Configurator`, `Context(WsgiStrategy)` and one `routes.init(...)` handler.

Run it:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-sql/src:../muscles-documents/src:../muscles-ai/src:. python3 -m gunicorn example_5.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-sql/src:../muscles-documents/src:../muscles-ai/src:. python3 -m example_5.data_ai_documents
```

Open:

- http://localhost:8080/example-5

### Level 6: protocol projections and observability

Package: `example_6`

Shows one action-first Muscles app projected through newer transport and
instrumentation libraries:

- `muscles-jsonrpc` discovers and calls actions as JSON-RPC 2.0 methods;
- `muscles-sse` streams progress/result events from `StreamResult`;
- `muscles-mcp` exposes the same action as MCP tools;
- `muscles-otel` records action lifecycle spans around validation and handler execution.

The web foundation intentionally mirrors `example_1`: `ApplicationMeta`,
`Configurator`, `Context(WsgiStrategy)` and one `routes.init(...)` handler.

Run it:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-asgi/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:. python3 -m gunicorn example_6.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:. python3 -m example_6.protocols_observability
```

Open:

- http://localhost:8080/example-6

## Tests

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:../muscles-sql/src:../muscles-ai/src:../muscles-documents/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:. python3 -m pytest -q
```

The test suite checks every level, verifies that level 4 behaves the same
through WSGI and ASGI test clients, and keeps the new ecosystem extension
examples executable.

## Docker

```bash
docker compose up --build
```

## Project Guides

- English: [docs/PROJECT_GUIDE.en.md](docs/PROJECT_GUIDE.en.md)
- Русский: [docs/PROJECT_GUIDE.ru.md](docs/PROJECT_GUIDE.ru.md)

## Sync Policy

When `muscles`, `muscles-wsgi`, `muscles-asgi`, `muscles-cli`,
`muscles-sql`, `muscles-ai`, `muscles-documents`, `muscles-jsonrpc`,
`muscles-sse`, `muscles-otel`, or `muscles-mcp` behavior changes, this example
should be updated in the same wave and verified by tests.
