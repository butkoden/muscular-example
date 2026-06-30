# Гайд по muscular-example (RU)

## Назначение

`muscular-example` теперь устроен как учебная лестница из четырех уровней.
Каждый следующий уровень добавляет новые возможности Muscles, не заставляя
новичка сразу читать большое приложение.

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

## Как читать код

1. Начните с `example_1/web.py`.
2. Затем откройте `example_2/web.py` и сравните page route с API route.
3. После этого посмотрите `example_3/cli.py`.
4. В конце переходите к `example_4/web.py` и `example_4/cli.py`.

Код специально покрыт русско-английскими комментариями: русская строка объясняет
смысл, английская помогает читать терминологию из документации и OpenAPI.

## Проверки

```bash
PYTHONPATH=../muscles/src:../muscles-asgi/src:../muscles-wsgi/src:../muscles-cli/src:. python3 -m pytest -q
```

Тесты проверяют все уровни и отдельно подтверждают parity между WSGI и ASGI для
полного приложения.
