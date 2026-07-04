# Гайд по muscular-example (RU)

## Назначение

`muscular-example` теперь устроен как учебная лестница из шести уровней.
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

## Уровень 3: CLI

Пакет: `example_3`

Что изучать:

- `Context(CliStrategy)`;
- `@cli.group(...)`;
- `@group.command(...)`;
- вложенные группы;
- поддержку `example-3/tasks list` и `example-3 tasks list`.

CLI вынесен отдельно, чтобы не смешивать routing web/API с routing команд.

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

## Как читать код

1. Начните с `example_1/web.py`.
2. Затем откройте `example_2/web.py` и сравните page route с API route.
3. После этого посмотрите `example_3/cli.py`.
4. Затем переходите к `example_4/web.py` и `example_4/cli.py`.
5. После этого смотрите `example_5/data_ai_documents.py`.
6. В конце откройте `example_6/protocols_observability.py`.

Код специально покрыт русско-английскими комментариями: русская строка объясняет
смысл, английская помогает читать терминологию из документации и OpenAPI.

## Проверки

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:../muscles-sql/src:../muscles-ai/src:../muscles-documents/src:../muscles-jsonrpc/src:../muscles-sse/src:../muscles-otel/src:../muscles-mcp/src:. python3 -m pytest -q
```

Тесты проверяют все уровни, отдельно подтверждают parity между WSGI и ASGI для
полного приложения и держат новые extension examples исполняемыми.
