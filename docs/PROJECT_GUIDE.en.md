# muscular-example Guide (EN)

## Purpose

`muscular-example` is now organized as a seven-level learning staircase. Each
level adds a small set of Muscles features, so new readers do not have to start
from the full application.

## Shared Development Approach

All levels use the same teaching format:

- contract: schemas, routes, actions, or `run_*_example()` outputs are explicit;
- use case: the useful scenario lives in a small function or class;
- adapter: WSGI, ASGI, CLI, SQL, AI, Documents, JSON-RPC, SSE, MCP, and OTEL stay at the edges;
- test: each level has a compact test contract proving the example is executable.

This makes the examples feel like one development style applied to different
libraries, not a set of unrelated scripts.

## Running Examples Correctly

The examples export application callables instead of implementing their own
server loops:

- WSGI examples run through a WSGI server such as `gunicorn`;
- ASGI examples run through an ASGI server such as `uvicorn`;
- CLI examples run as Python modules.

`wsgiref.simple_server` loops are intentionally avoided because they hide the
example contract and look like a homemade production server.

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

Run:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:. python3 -m gunicorn example_1.web:app --bind 0.0.0.0:8080
```

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

Run:

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:. python3 -m gunicorn example_2.web:wsgi_application --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:. python3 -m uvicorn example_2.web:asgi_application --host 0.0.0.0 --port 8080
```

## Level 3: CLI

Package: `example_3`

Learn:

- `Context(CliStrategy)`;
- `@cli.group(...)`;
- `@group.command(...)`;
- nested groups;
- both `example-3/tasks list` and `example-3 tasks list`.

CLI is separated from web code so command routing can be studied on its own.

Run:

```bash
PYTHONPATH=../muscles/src:../muscles-cli/src:. python3 -m example_3.cli example-3/hello Student
```

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

Run:

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m example_4.cli init-db
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m gunicorn example_4.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m uvicorn example_4.web:asgi_application --host 0.0.0.0 --port 8080
```

## Level 5: data, documents and AI extensions

Package: `example_5`

Learn:

- `SqlConnectionRegistry` for named SQL connections;
- `SqlRepository` and `UnitOfWork` for CRUD/query flow;
- `muscles-documents` as `documents.*` actions;
- `muscles-ai` as `ai.*` actions with the noop provider;
- extension action calls through the shared `ActionDispatcher`.

Key idea: newer packages extend the application model without forcing a separate
transport architecture.

The web foundation mirrors `example_1`: `ApplicationMeta`, `Configurator`,
`Context(WsgiStrategy)`, and one `routes.init(...)` handler at `/example-5`.

Run:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-sql/src:../muscles-documents/src:../muscles-ai/src:. python3 -m gunicorn example_5.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-sql/src:../muscles-documents/src:../muscles-ai/src:. python3 -m example_5.data_ai_documents
```

## Level 6: protocol projections and observability

Package: `example_6`

Learn:

- one `@app.action(...)` as the source of truth;
- `JsonRpcAdapter` for JSON-RPC 2.0;
- `SseAdapter` for `StreamResult` and typed events;
- `McpStrategy` for MCP tools/resources;
- `MusclesTracer` and `instrument_action_dispatch` for lifecycle spans.

Key idea: JSON-RPC, SSE, MCP, and observability do not copy business logic. They
project the same action contract.

The web foundation mirrors `example_1`: `ApplicationMeta`, `Configurator`,
`Context(WsgiStrategy)`, and one `routes.init(...)` handler at `/example-6`.

Run:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-asgi/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:. python3 -m gunicorn example_6.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:. python3 -m example_6.protocols_observability
```

## Level 7: typed data ports

Package: `example_7`

Learn:

- `muscles-data` as a named-resource runtime;
- `DataRuntime.require_port(...)`;
- `VectorSearchPort`, `SearchIndexPort`, `KeyValuePort`, `ObjectStorePort`;
- Elasticsearch-backed `SearchIndexPort` through a fake client, without
  importing the Elasticsearch SDK in the web/use-case contract;
- OpenSearch-backed `SearchIndexPort` through a fake client, without importing
  the OpenSearch SDK in the web/use-case contract;
- Redis-backed `KeyValuePort`, `LockPort`, and `StreamPort` through a fake
  client, without importing the Redis SDK in the web/use-case contract;
- `SqlResourcePort` as a bridge to a named SQL registry;
- SQLAlchemy-backed `SqlResourcePort` as a direct SQLite data adapter, while
  SQLAlchemy stays out of the web/use-case contract;
- Qdrant-backed `VectorSearchPort` through a fake client, without importing
  `qdrant-client` in the web/use-case contract;
- explicit capability mismatch errors;
- safe diagnostics through `data.resource.inspect` and `data.doctor`;
- in-memory/fake resources without external services.

Key idea: a project may declare different backend resources, while framework
code uses small typed ports instead of vendor SDKs.
Keyword/BM25 search against Elasticsearch goes through `SearchIndexPort`; the
direct Elasticsearch client remains an adapter detail or advanced native access
in a project.
Keyword/BM25 search against OpenSearch also goes through `SearchIndexPort`, but
uses a separate `type: opensearch` adapter and dependency.
Cache, lock, and simple stream scenarios against Redis go through
`KeyValuePort`, `LockPort`, and `StreamPort`; the direct Redis client remains an
adapter detail or advanced native access in a project.
SQL connection lifecycle
still belongs to `muscles-sql` or a compatible project registry, but a project
may also choose a direct `type: sqlalchemy` resource when it wants a SQLAlchemy
session through the same `SqlResourcePort`.
Vector search against Qdrant goes through `VectorSearchPort`; the direct Qdrant
client remains an adapter detail or advanced native access in a project.

The web foundation mirrors `example_1`: `ApplicationMeta`, `Configurator`,
`Context(WsgiStrategy)`, and one `routes.init(...)` handler at `/example-7`.

Run:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-data/src:. python3 -m gunicorn example_7.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-data/src:. python3 -m example_7.data_ports
```

## Reading Order

1. Start with `example_1/web.py`.
2. Open `example_2/web.py` and compare a page route with API routes.
3. Read `example_3/cli.py`.
4. Move to `example_4/web.py` and `example_4/cli.py`.
5. Read `example_5/web.py` and `example_5/data_ai_documents.py`.
6. Continue with `example_6/web.py` and `example_6/protocols_observability.py`.
7. Finish with `example_7/web.py` and `example_7/data_ports.py`.

The code intentionally uses Russian and English comments together: Russian
explains the local learning context, English keeps framework terminology close
to documentation and OpenAPI wording.

## Checks

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:../muscles-sql/src:../muscles-ai/src:../muscles-documents/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:../muscles-data/src:. python3 -m pytest -q
```

Tests cover all levels, verify WSGI/ASGI parity for the full application, and
keep the new extension examples executable.
