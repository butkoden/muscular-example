from __future__ import annotations

import inspect

from muscles import ApiKeyAuthSecurity, Configurator, Context, JsonResponse
from muscles import JsonResponseBody
from muscles.core.cors import cors
from muscles.asgi import MuscularAsgiApp, asgi_app
from muscles.asgi.asgi import AsgiStrategy
from muscles.asgi.restful import RestApi as AsgiRestApi
from muscles.wsgi import MuscularWsgiApp, wsgi_app
from muscles.wsgi.wsgi import WsgiStrategy
from muscles.wsgi.restful import RestApi as WsgiRestApi


API_TOKEN = "example-2-token"
API_KEY_HEADER = "X-Api-Key"
API_PREFIX = "/api/example-2/v1"
API_SECURITY = [ApiKeyAuthSecurity(name=API_KEY_HEADER, key="ApiKey")]


class RuntimeBinding:
    """Small adapter that lets the same code build WSGI and ASGI apps.

    RU: В WSGI и ASGI разные strategy/routes/response classes, но регистрация
    API выглядит одинаково. Этот объект хранит эти различия в одном месте.

    EN: WSGI and ASGI have different strategy/routes/response classes, while
    API registration looks the same. This object keeps those differences in
    one place.
    """

    def __init__(self, *, strategy, rest_api, routes, response):
        self.strategy = strategy
        self.rest_api = rest_api
        self.routes = routes
        self.response = response


def wsgi_runtime():
    from muscles.wsgi.wsgi import BaseResponse, routes

    return RuntimeBinding(
        strategy=WsgiStrategy,
        rest_api=WsgiRestApi,
        routes=routes,
        response=BaseResponse,
    )


def asgi_runtime():
    from muscles.asgi.asgi import BaseResponse, routes

    return RuntimeBinding(
        strategy=AsgiStrategy,
        rest_api=AsgiRestApi,
        routes=routes,
        response=BaseResponse,
    )


def header_value(request, name):
    # RU: Заголовки могут прийти в разном регистре, поэтому сравниваем lower().
    # EN: Headers may arrive with different casing, so compare lower() values.
    expected = name.lower()
    for key, value in (request.headers or {}).items():
        if str(key).lower() == expected:
            return value
    return None


def require_api_key(request):
    # RU: Guard возвращает response, если доступ запрещен.
    # EN: A guard returns a response when access is denied.
    if header_value(request, API_KEY_HEADER) != API_TOKEN:
        return JsonResponse({"error": "unauthorized"}, status=401)
    return None


def configure_api(api):
    # RU: Middleware подключается к API один раз и работает для WSGI/ASGI.
    # EN: Middleware is attached once and works for both WSGI and ASGI.
    api.use(cors(
        allow_origins=["https://example.local"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", API_KEY_HEADER],
    ))

    # RU: Guard защищает все endpoints внутри protected-группы.
    # EN: The guard protects every endpoint inside the protected group.
    api.guard(f"{API_PREFIX}/protected/**", require_api_key)


def register_pages(routes, response_class):
    @routes.init("/example-2", key="example_2.home", method="GET")
    def home(request):
        # RU: Страница нужна только чтобы показать обычный web-route рядом с API.
        # EN: This page only shows a normal web route living next to the API.
        return response_class(
            status=200,
            body="Example 2: page route + REST API",
            headers=[("Content-Type", "text/plain; charset=utf-8")],
        )


def register_api(api):
    @api.init(
        "/messages",
        method="get",
        response={200: JsonResponseBody(description="Public message list")},
    )
    def list_messages(request):
        # RU: Самый простой API endpoint: обычный dict превращается в JSON.
        # EN: The simplest API endpoint: a plain dict becomes JSON.
        return {"items": ["public message"]}

    protected = api.group(
        "/protected",
        tags=["Example 2"],
        security=API_SECURITY,
        response={401: JsonResponseBody(description="Unauthorized")},
    )

    @protected.init("/login", method="post", auth=False, summary="Issue demo token")
    def login(request):
        # RU: auth=False снимает guard/security только с этого endpoint.
        # EN: auth=False disables guard/security only for this endpoint.
        return JsonResponse({"token": API_TOKEN})

    @protected.init("/status", method="get", summary="Protected status")
    def status(request):
        return JsonResponse({"status": "ok", "level": 2})


class Example2App:
    package_paths = []
    shutup = False

    config = Configurator(obj={
        "main": {
            "BASEDIR": ".",
            "BASE_URL": "http://localhost:8080",
            "SERVER_NAME": "localhost:8080",
            "HOST": "0.0.0.0",
            "PORT": "8080",
            "ENV": "development",
            "DEBUG": True,
            "TIMEZONE": "Europe/Moscow",
            "MAIN_ROUTE": "example_2.home",
            "SECRET_KEY": "local-development-only",
        },
        "routes": {"prefix": ""},
        "api": {"prefix": "/api", "default_version": "v1", "controllers": {}},
    })

    def __init__(self, runtime):
        self.context = Context(runtime.strategy, params={})
        self.api = runtime.rest_api(
            prefix=API_PREFIX,
            version="1.0",
            name="Example2Api",
            title="Example 2 API",
            description="Small REST API example with OpenAPI and guards",
            servers=[{"url": "http://localhost:8080"}],
        )
        configure_api(self.api)
        register_pages(runtime.routes, runtime.response)
        register_api(self.api)

    def __call__(self, environ, start_response):
        self.context.set_param("environ", environ)
        self.context.set_param("start_response", start_response)
        return self.context.execute()

    async def asgi_call(self, scope, receive, send):
        result = self.context.execute(scope=scope, receive=receive, send=send)
        if inspect.isawaitable(result):
            await result


class Example2WsgiApp(Example2App, MuscularWsgiApp):
    pass


class Example2AsgiApp(Example2App, MuscularAsgiApp):
    pass


wsgi_project = Example2WsgiApp(wsgi_runtime())
asgi_project = Example2AsgiApp(asgi_runtime())

wsgi_application = wsgi_app(wsgi_project, context=wsgi_project.context)
asgi_application = asgi_app(asgi_project, context=asgi_project.context)
