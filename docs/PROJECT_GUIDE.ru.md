# Гайд по проектам Muscular (RU)

## Назначение

`muscular-example` — это практический эталон того, как собирать реальные
приложения на экосистеме Muscular.

В примере объединены:

- ядро `muscles` (`ApplicationMeta`, `Configurator`, `Context`);
- web/api рантайм `muscles-wsgi`;
- web/api рантайм `muscles-asgi` с теми же контрактами;
- консольный рантайм `muscles-cli`.

## 1) Рекомендуемая структура проекта

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

## 2) Инициализация приложения

Создайте класс приложения, где есть:

1. `ApplicationMeta`
2. статическая конфигурация (`Configurator`)
3. стратегия выполнения (`Context(WsgiStrategy, params={})` или `Context(AsgiStrategy, params={})`)

В этом примере общая логика приложения вынесена в base-класс, а поверх него
создаются тонкие runtime-specific классы:

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

Дальше регистрируйте:

- web-роуты (`routes.init(...)`);
- API-контроллеры (`RestApi`, `@api.controller`, `@api.action`);
- startup-действия (например, `init_db()`).

## 3) Стратегия роутинга

Используйте древовидную структуру единообразно:

- Web: `/`, `/resume`, `/admin/...`
- API: `/api/v1/...`
- CLI: `bookings remove 1` и алиас `bookings/remove 1`

Одинаковая логика роутинга в web/api/cli упрощает поддержку.

## 4) Слой данных

Для небольших проектов SQLite обычно достаточно:

- инициализация схемы один раз на процесс/путь БД;
- WAL-режим для лучшей конкурентности;
- все операции с БД в `db.py`.

## 5) API и OpenAPI

Описывайте модели запросов/ответов через schema-классы Muscular и привязывайте
их к action-методам. Swagger/OpenAPI формируется автоматически.

ValueObject можно внедрять постепенно через `ValueObjectField`:

- контракты OpenAPI и роутинга остаются стабильными;
- инварианты домена живут в отдельных value-классах;
- валидация не размазывается по хендлерам.

Защищенная группа может содержать публичный endpoint через локальное
переопределение авторизации:

```python
api.guard("/api/v1/protected/**", require_api_key)
protected = api.group("/protected", tags=["Framework primitives"], security=["ApiKey"])


@protected.init("/login", method="post", auth=False)
def login(request):
    return JsonResponse({"token": API_DEMO_TOKEN})
```

Для protocol-neutral handlers используйте core helpers ответов:

- `JsonResponse` для явного JSON;
- `BytesResponse` для bytes/text payload;
- `NoContentResponse` для `204 No Content`.

В примере также подключен `cors(...)` на API itinerary, поэтому preflight и
обычные ответы ведут себя одинаково под WSGI и ASGI.

Ядро Muscles теперь владеет общим backend pipeline для типизированных
аргументов handler, разрешения зависимостей, guards, route-level security и
middleware. WSGI и ASGI адаптеры используют этот pipeline, а пример проверяет
паритет через одни и те же API-тесты для обоих транспортов.

Route contract v2 также позволяет одному API path иметь разные route keys для
разных HTTP-методов:

```python
@protected.init("/method-key", key="framework.method_key.read", method="get")
def method_key_read(request):
    return JsonResponse({"operation": "read"})


@protected.init("/method-key", key="framework.method_key.write", method="post")
def method_key_write(request):
    return JsonResponse({"operation": "write"})
```

## 6) CLI слой

Группируйте операционные команды:

- `init-db`
- `bookings list`
- `bookings remove <id>`
- `diagnostics`
- `set-password`

## 7) Базовый набор тестов

Минимум:

- smoke для страниц/static/swagger/schema;
- тест API бронирования;
- тест админ-логина и диагностики;
- тест CLI команд.
- parity-тест WSGI/ASGI для protected routes, auth override, CORS, response helpers
  и разных route keys на одном path.

## 8) Как создать свой проект на основе этого примера

1. Скопируйте этот репозиторий.
2. Переименуйте пакет и доменные шаблоны/контент.
3. Сохраните архитектуру и тесты.
4. Адаптируйте схему БД и API-модели под свой домен.
5. Добавьте CI и deployment.

## 9) Как держать пример актуальным

Когда меняются framework-репозитории:

1. обновляйте локальные `muscles*` репы;
2. прогоняйте тесты примера;
3. правьте места, где изменились контракты;
4. фиксируйте миграционные заметки в README/changelog.
