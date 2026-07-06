# Гайд по muscular-example (RU)

## Назначение

`muscular-example` теперь устроен как учебная лестница из семи уровней.
Каждый следующий уровень добавляет новые возможности Muscles, не заставляя
новичка сразу читать большое приложение.

## Единый подход к разработке

Все уровни придерживаются одного учебного формата:

- contract: явно описаны schemas, routes, actions или результат `run_*_example()`;
- use case: полезный сценарий держится в маленькой функции или классе;
- adapter: WSGI, ASGI, CLI, SQL, AI, Documents, JSON-RPC, SSE, MCP и OTEL остаются на краях;
- test: у уровня есть компактный тестовый контракт, который подтверждает, что пример исполняемый.

Так читатель видит не набор разных скриптов, а один и тот же способ разработки,
примененный к разным библиотекам.

## Как запускать правильно

Примеры экспортируют application callables, а не реализуют свой сервер:

- WSGI-примеры запускаются через WSGI server, например `gunicorn`;
- ASGI-примеры запускаются через ASGI server, например `uvicorn`;
- CLI-примеры запускаются как Python modules.

Встроенные циклы на `wsgiref.simple_server` намеренно не используются: они
маскируют главный контракт примера и выглядят как самодельный production server.

## Уровень 1: минимальный web route

Пакет: `example_1`

Что изучать:

- `ApplicationMeta`;
- `Configurator`;
- `Context(WsgiStrategy)`;
- прямой декоратор `@routes.init(...)`;
- возврат готового `BaseResponse`.

Это самый короткий пример, где видно, как запрос проходит от WSGI entrypoint до
handler-функции.

Запуск:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:. python3 -m gunicorn example_1.web:app --bind 0.0.0.0:8080
```

## Уровень 2: REST API и guards

Пакет: `example_2`

Что изучать:

- `routes.init(...)` для обычной страницы;
- `api.init(...)` для простого API endpoint;
- `api.group(...)` для общего prefix/tags/security;
- `group.init(..., auth=False)` для публичного endpoint внутри protected-группы;
- `api.guard(...)` для защиты группы по path pattern;
- `api.use(cors(...))` для middleware;
- автоматическую OpenAPI-схему.

Ключевая идея: здесь уже есть WSGI и ASGI варианты, но код регистрации API один.

Запуск:

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:. python3 -m gunicorn example_2.web:wsgi_application --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:. python3 -m uvicorn example_2.web:asgi_application --host 0.0.0.0 --port 8080
```

## Уровень 3: CLI

Пакет: `example_3`

Что изучать:

- `Context(CliStrategy)`;
- `@cli.group(...)`;
- `@group.command(...)`;
- вложенные группы;
- поддержку `example-3/tasks list` и `example-3 tasks list`.

CLI вынесен отдельно, чтобы не смешивать routing web/API с routing команд.

Запуск:

```bash
PYTHONPATH=../muscles/src:../muscles-cli/src:. python3 -m example_3.cli example-3/hello Student
```

## Уровень 4: полное приложение

Пакет: `example_4`

Что изучать:

- страницы, шаблоны и static files;
- `RestApi`;
- `@api.controller(...)` и `@api.action(...)`;
- `api.group(...)` и `group.init(...)`;
- OpenAPI/Swagger;
- общий WSGI/ASGI runtime binding;
- CORS и guards;
- `JsonResponse`, `BytesResponse`, `NoContentResponse`;
- один API path с разными route keys для разных HTTP methods;
- SQLite и простую админку;
- операционные CLI-команды.

Важно: в `example_4` больше нет кастомной прослойки регистрации. Пример
показывает фреймворк напрямую, чтобы читателю было понятно, какие возможности
дает сам Muscles.

Запуск:

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m example_4.cli init-db
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m gunicorn example_4.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m uvicorn example_4.web:asgi_application --host 0.0.0.0 --port 8080
```

## Уровень 5: data, documents и AI extensions

Пакет: `example_5`

Что изучать:

- `SqlConnectionRegistry` для нескольких SQL-подключений;
- `SqlRepository` и `UnitOfWork` для CRUD/query-потока;
- `muscles-documents` как набор `documents.*` actions;
- `muscles-ai` как набор `ai.*` actions с noop provider;
- вызов extension actions через общий `ActionDispatcher`.

Ключевая идея: новые пакеты расширяют application model, но не требуют
отдельной транспортной архитектуры.

Основа web-запуска повторяет `example_1`: `ApplicationMeta`, `Configurator`,
`Context(WsgiStrategy)` и один `routes.init(...)` handler на `/example-5`.

Запуск:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-sql/src:../muscles-documents/src:../muscles-ai/src:. python3 -m gunicorn example_5.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-sql/src:../muscles-documents/src:../muscles-ai/src:. python3 -m example_5.data_ai_documents
```

## Уровень 6: protocol projections и observability

Пакет: `example_6`

Что изучать:

- один `@app.action(...)` как источник истины;
- `JsonRpcAdapter` для JSON-RPC 2.0;
- `SseAdapter` для `StreamResult` и typed events;
- `McpStrategy` для MCP tools/resources;
- `MusclesTracer` и `instrument_action_dispatch` для lifecycle spans.

Ключевая идея: JSON-RPC, SSE, MCP и observability не копируют бизнес-логику, а
проецируют один и тот же action contract.

Основа web-запуска повторяет `example_1`: `ApplicationMeta`, `Configurator`,
`Context(WsgiStrategy)` и один `routes.init(...)` handler на `/example-6`.

Запуск:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-asgi/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:. python3 -m gunicorn example_6.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:. python3 -m example_6.protocols_observability
```

## Уровень 7: typed data ports

Пакет: `example_7`

Что изучать:

- `muscles-data` как runtime именованных data resources;
- `DataRuntime.require_port(...)`;
- `VectorSearchPort`, `SearchIndexPort`, `KeyValuePort`, `ObjectStorePort`;
- `SqlResourcePort` как bridge к named SQL registry;
- явную ошибку capability mismatch;
- безопасные diagnostics через `data.resource.inspect` и `data.doctor`;
- in-memory resources без внешних сервисов и vendor SDK.

Ключевая идея: `example_7` показывает только core contract. Проект может
подключать разные backend resources через отдельные adapter packages, но web и
use-case код продолжают работать через маленькие typed ports, а не через vendor
SDK.

Основа web-запуска повторяет `example_1`: `ApplicationMeta`, `Configurator`,
`Context(WsgiStrategy)` и один `routes.init(...)` handler на `/example-7`.

Запуск:

```bash
PYTHONPATH=../muscles/src:../muscles-wsgi/src:../muscles-data/src:. python3 -m gunicorn example_7.web:app --bind 0.0.0.0:8080
PYTHONPATH=../muscles/src:../muscles-data/src:. python3 -m example_7.data_ports
```

## Примеры отдельных data adapters

Каждый adapter вынесен в свой маленький пример `example_data_[adapter]_1`,
чтобы зависимость от конкретной базы не попадала в core example:

- `example_data_elasticsearch_1`: `SearchIndexPort` через
  `muscles-data-elasticsearch`;
- `example_data_opensearch_1`: `SearchIndexPort` через
  `muscles-data-opensearch`;
- `example_data_redis_1`: `KeyValuePort`, `LockPort` и `StreamPort` через
  `muscles-data-redis`;
- `example_data_sqlalchemy_1`: direct `SqlResourcePort` через
  `muscles-data-sqlalchemy`;
- `example_data_qdrant_1`: `VectorSearchPort` через `muscles-data-qdrant`;
- `example_data_mongodb_1`: `DocumentStorePort` через
  `muscles-data-mongodb`;
- `example_data_s3_1`: `ObjectStorePort` через `muscles-data-s3`.

Запуск:

```bash
PYTHONPATH=../muscles/src:../muscles-data/src:../muscles-data-elasticsearch/src:. python3 -m example_data_elasticsearch_1.data_ports
PYTHONPATH=../muscles/src:../muscles-data/src:../muscles-data-opensearch/src:. python3 -m example_data_opensearch_1.data_ports
PYTHONPATH=../muscles/src:../muscles-data/src:../muscles-data-redis/src:. python3 -m example_data_redis_1.data_ports
PYTHONPATH=../muscles/src:../muscles-data/src:../muscles-data-sqlalchemy/src:. python3 -m example_data_sqlalchemy_1.data_ports
PYTHONPATH=../muscles/src:../muscles-data/src:../muscles-data-qdrant/src:. python3 -m example_data_qdrant_1.data_ports
PYTHONPATH=../muscles/src:../muscles-data/src:../muscles-data-mongodb/src:. python3 -m example_data_mongodb_1.data_ports
PYTHONPATH=../muscles/src:../muscles-data/src:../muscles-data-s3/src:. python3 -m example_data_s3_1.data_ports
```

## Как читать код

1. Начните с `example_1/web.py`.
2. Затем откройте `example_2/web.py` и сравните page route с API route.
3. После этого посмотрите `example_3/cli.py`.
4. Затем переходите к `example_4/web.py` и `example_4/cli.py`.
5. После этого смотрите `example_5/web.py` и `example_5/data_ai_documents.py`.
6. Затем откройте `example_6/web.py` и `example_6/protocols_observability.py`.
7. В конце посмотрите `example_7/web.py` и `example_7/data_ports.py`.

Код специально покрыт русско-английскими комментариями: русская строка объясняет
смысл, английская помогает читать терминологию из документации и OpenAPI.

## Проверки

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:../muscles-sql/src:../muscles-ai/src:../muscles-documents/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:../muscles-data/src:../muscles-data-elasticsearch/src:../muscles-data-mongodb/src:../muscles-data-opensearch/src:../muscles-data-qdrant/src:../muscles-data-redis/src:../muscles-data-s3/src:../muscles-data-sqlalchemy/src:. python3 -m pytest -q
```

Тесты проверяют все уровни, отдельно подтверждают parity между WSGI и ASGI для
полного приложения и держат новые extension examples исполняемыми.
