from __future__ import annotations

import inspect
import json
from http.cookies import SimpleCookie
from pathlib import Path

from muscles import ApiKeyAuthSecurity, BytesResponse, Configurator, Context, JsonResponse
from muscles import NoContentResponse
from muscles import JsonRequestBody, JsonResponseBody, Model, Column, String, DateTime, ValueObjectField
from muscles.core.cors import cors
from muscles.asgi import MuscularAsgiApp, asgi_app
from muscles.asgi.asgi import AsgiStrategy
from muscles.asgi.restful import RestApi as AsgiRestApi
from muscles.wsgi import MuscularWsgiApp, wsgi_app
from muscles.wsgi.wsgi import WsgiStrategy
from muscles.wsgi.restful import RestApi as WsgiRestApi

from .config import ADMIN_SESSION_COOKIE, ADMIN_SESSION_VALUE
from .db import check_admin_password, create_booking, diagnostics, init_db, list_bookings, set_admin_password
from .templates import escape, page, render
from .value_objects import EmailAddress


API_DEMO_TOKEN = "demo-framework-token"
API_KEY_HEADER = "X-Api-Key"
API_PREFIX = "/api/v1"
API_ALLOWED_ORIGIN = "https://example.local"
API_SECURITY = [ApiKeyAuthSecurity(name=API_KEY_HEADER, key="ApiKey")]


class Booking(Model):
    """Schema model used by OpenAPI and runtime validation.

    RU: Это не ORM-модель. Здесь описан контракт входящего payload для API.
    EN: This is not an ORM model. It describes the incoming API payload contract.
    """

    name = Column(String)
    email = Column(ValueObjectField(value_object_class=EmailAddress))
    title = Column(String)
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)
    notes = Column(String)


class Example4App:
    """Full web/API application shared by WSGI and ASGI.

    RU: В этом уровне показан максимум возможностей примера: страницы, API,
    OpenAPI, guards, CORS, разные response helpers, SQLite и админка.

    EN: This level shows the largest feature set in the example: pages, API,
    OpenAPI, guards, CORS, response helpers, SQLite, and an admin area.
    """

    package_paths = []
    shutup = False

    # RU: Конфигурация остается рядом с приложением, чтобы пример был цельным.
    # EN: Configuration stays next to the app so the example remains self-contained.
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
            "MAIN_ROUTE": "example_4.page.index",
            "SECRET_KEY": "local-development-only",
        },
        "routes": {"prefix": ""},
        "api": {"prefix": "/api", "default_version": "v1", "controllers": {}},
    })

    def __init__(self, runtime):
        # RU: init_db() безопасен для повторного вызова и поднимает SQLite-схему.
        # EN: init_db() is safe to call repeatedly and prepares the SQLite schema.
        init_db()

        self.runtime = runtime
        self.context = Context(runtime.strategy, params={})

        # RU: RestApi описывает публичный API-контракт и генерирует OpenAPI.
        # EN: RestApi describes the public API contract and generates OpenAPI.
        self.api = runtime.rest_api(
            prefix=API_PREFIX,
            version="1.0",
            name="Example4Api",
            title="Muscular Example API",
            description="Full example API for learning Muscles framework features",
            contact_email="hello@example.local",
            servers=[{"url": "http://localhost:8080"}],
        )

        configure_api_contract(self.api)
        register_pages(runtime.routes, runtime.response)
        register_api(self.api)

    def __call__(self, environ, start_response):
        # RU: WSGI entrypoint: кладем request primitives в Context и запускаем routing.
        # EN: WSGI entrypoint: store request primitives in Context and run routing.
        self.context.set_param("environ", environ)
        self.context.set_param("start_response", start_response)
        return self.context.execute()

    async def asgi_call(self, scope, receive, send):
        # RU: ASGI entrypoint аналогичен WSGI, но результат может быть awaitable.
        # EN: ASGI entrypoint mirrors WSGI, but the result may be awaitable.
        result = self.context.execute(scope=scope, receive=receive, send=send)
        if inspect.isawaitable(result):
            await result


class Example4WsgiApp(Example4App, MuscularWsgiApp):
    pass


class Example4AsgiApp(Example4App, MuscularAsgiApp):
    pass


class RuntimeBinding:
    """Runtime-specific objects used by the shared application class.

    RU: Этот маленький объект заменяет условные if runtime == "wsgi" по всему
    коду. Отличия WSGI/ASGI собраны в одном месте.

    EN: This tiny object replaces scattering if runtime == "wsgi" throughout
    the code. WSGI/ASGI differences are collected in one place.
    """

    def __init__(self, *, name, strategy, rest_api, routes, response):
        self.name = name
        self.strategy = strategy
        self.rest_api = rest_api
        self.routes = routes
        self.response = response


def wsgi_runtime():
    from muscles.wsgi.wsgi import BaseResponse, routes

    return RuntimeBinding(
        name="wsgi",
        strategy=WsgiStrategy,
        rest_api=WsgiRestApi,
        routes=routes,
        response=BaseResponse,
    )


def asgi_runtime():
    from muscles.asgi.asgi import BaseResponse, routes

    return RuntimeBinding(
        name="asgi",
        strategy=AsgiStrategy,
        rest_api=AsgiRestApi,
        routes=routes,
        response=BaseResponse,
    )


def configure_api_contract(api):
    # RU: CORS подключен как middleware API. Одинаково работает в WSGI и ASGI.
    # EN: CORS is attached as API middleware. It works the same in WSGI and ASGI.
    api.use(cors(
        allow_origins=[API_ALLOWED_ORIGIN],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", API_KEY_HEADER],
    ))

    # RU: Guard с pattern защищает сразу все /protected endpoints.
    # EN: A pattern guard protects all /protected endpoints at once.
    api.guard(f"{API_PREFIX}/protected/**", require_api_key)


def header_value(request, name):
    # RU: HTTP-заголовки регистронезависимы, поэтому сравниваем через lower().
    # EN: HTTP headers are case-insensitive, so compare via lower().
    expected = name.lower()
    for key, value in (request.headers or {}).items():
        if str(key).lower() == expected:
            return value
    return None


def require_api_key(request):
    # RU: Guard возвращает None, когда доступ разрешен.
    # EN: A guard returns None when access is allowed.
    if header_value(request, API_KEY_HEADER) == API_DEMO_TOKEN:
        return None

    # RU: Любой response object можно вернуть прямо из guard.
    # EN: Any response object can be returned directly from a guard.
    return JsonResponse(
        {"error_code": "unauthorized", "error": "unauthorized"},
        status=401,
    )


def html_response(response_class, body, status=200, headers=None):
    # RU: Создаем новый список headers, чтобы случайно не мутировать внешний список.
    # EN: Build a new headers list to avoid mutating an external list by accident.
    response_headers = list(headers or [])
    response_headers.append(("Content-Type", "text/html; charset=utf-8"))
    return response_class(status=status, body=body, headers=response_headers)


def redirect(response_class, location):
    return response_class(status=302, body="", headers=[("Location", location)])


def request_form(request):
    # RU: request.forms уже разобран framework-ом из form-urlencoded body.
    # EN: request.forms is already parsed by the framework from form-urlencoded body.
    return {key: str(value) for key, value in (request.forms or {}).items()}


def is_admin(request):
    cookies = request.cookies or {}
    return cookies.get(ADMIN_SESSION_COOKIE) == ADMIN_SESSION_VALUE


def require_admin(response_class, request):
    # RU: Page-level auth можно держать обычной функцией, без API guard.
    # EN: Page-level auth can stay a regular function, without an API guard.
    if not is_admin(request):
        return redirect(response_class, "/admin/login")
    return None


def set_login_cookie(response):
    cookie = SimpleCookie()
    cookie[ADMIN_SESSION_COOKIE] = ADMIN_SESSION_VALUE
    cookie[ADMIN_SESSION_COOKIE]["path"] = "/"
    cookie[ADMIN_SESSION_COOKIE]["httponly"] = True
    response._headers.append(("Set-Cookie", cookie.output(header="").strip()))
    return response


def clear_login_cookie(response):
    response._headers.append((
        "Set-Cookie",
        f"{ADMIN_SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly",
    ))
    return response


def register_pages(routes, response_class):
    # RU: Static files тоже регистрируются через router Muscles.
    # EN: Static files are registered through the Muscles router too.
    routes.add_static(str(Path(__file__).resolve().parent / "static"), prefix="/static", full_path=True)

    @routes.init("/", key="example_4.page.index", method="GET")
    def index(request):
        body = render("home.html")
        return html_response(response_class, page("Muscular Example", body, active="home"))

    @routes.init("/resume", key="example_4.page.resume", method="GET")
    def resume(request):
        body = render("resume.html")
        return html_response(response_class, page("Portfolio / Resume", body, active="resume"))

    @routes.init("/admin", key="example_4.admin.index", method="GET")
    def admin_index(request):
        denied = require_admin(response_class, request)
        if denied:
            return denied
        bookings = list_bookings()
        rows = "\n".join(
            "<tr><td>{id}</td><td>{name}</td><td>{email}</td><td>{title}</td>"
            "<td>{starts_at}</td><td>{status}</td></tr>".format(**{key: escape(value) for key, value in item.items()})
            for item in bookings
        ) or "<tr><td colspan='6'>No bookings yet</td></tr>"
        body = render("admin.html", rows=rows)
        return html_response(response_class, page("Admin", body, active="admin"))

    @routes.init("/admin/login", key="example_4.admin.login", method="GET")
    def login_form(request):
        return html_response(response_class, page("Admin login", render("login.html", error=""), active="admin"))

    @routes.init("/admin/login", key="example_4.admin.login.submit", method="POST")
    def login_submit(request):
        form = request_form(request)
        if check_admin_password(form.get("password", "")):
            return set_login_cookie(redirect(response_class, "/admin"))
        return html_response(
            response_class,
            page("Admin login", render("login.html", error="Wrong password"), active="admin"),
            status=403,
        )

    @routes.init("/admin/logout", key="example_4.admin.logout", method="POST")
    def logout(request):
        return clear_login_cookie(redirect(response_class, "/"))

    @routes.init("/admin/password", key="example_4.admin.password", method="POST")
    def password(request):
        denied = require_admin(response_class, request)
        if denied:
            return denied
        form = request_form(request)
        new_password = form.get("password", "").strip()
        if len(new_password) < 6:
            return html_response(
                response_class,
                page("Admin", render("message.html", message="Password must be at least 6 characters."), active="admin"),
                status=400,
            )
        set_admin_password(new_password)
        return html_response(response_class, page("Admin", render("message.html", message="Password changed."), active="admin"))

    @routes.init("/admin/diagnostics", key="example_4.admin.diagnostics", method="GET")
    def diagnostics_page(request):
        denied = require_admin(response_class, request)
        if denied:
            return denied
        payload = json.dumps(diagnostics(), indent=2)
        return html_response(
            response_class,
            page("Diagnostics", render("diagnostics.html", diagnostics=escape(payload)), active="admin"),
        )


def register_api(api):
    # RU: Controller class хорош, когда у ресурса есть несколько методов.
    # EN: A controller class is useful when a resource has multiple methods.
    @api.controller("/bookings", description="Calendar slot bookings", summary="Bookings")
    class BookingsController:
        @api.action(
            method="get",
            response={200: JsonResponseBody(description="Booking list")},
        )
        def get(self, request):
            return {"bookings": list_bookings()}

        @api.action(
            method="post",
            request=[JsonRequestBody(description="Booking payload", model=Booking)],
            response={200: JsonResponseBody(description="Created booking")},
        )
        def post(self, request):
            data = request.json if request.is_json else request_form(request)
            required = ["name", "email", "title", "starts_at", "ends_at"]
            missing = [key for key in required if not data.get(key)]
            if missing:
                return {"error": "Missing fields", "fields": missing}, 400
            try:
                booking_payload = Booking(**data).as_dict()
            except Exception as exc:
                return {"error": "Validation failed", "details": str(exc)}, 400
            return {"booking": create_booking(booking_payload)}

    # RU: api.group добавляет общий prefix, tags, security и responses.
    # EN: api.group adds shared prefix, tags, security, and responses.
    protected = api.group(
        "/protected",
        tags=["Framework primitives"],
        security=API_SECURITY,
        response={401: JsonResponseBody(description="Unauthorized")},
    )

    @protected.init(
        "/login",
        method="post",
        auth=False,
        summary="Issue demo API token",
    )
    def login(request):
        # RU: auth=False показывает, что публичный endpoint может жить в protected-группе.
        # EN: auth=False shows that a public endpoint can live inside a protected group.
        return JsonResponse({"token": API_DEMO_TOKEN})

    @protected.init(
        "/diagnostics",
        method="get",
        summary="Show protected diagnostics",
    )
    def api_diagnostics(request):
        return JsonResponse({"diagnostics": diagnostics()})

    @protected.init(
        "/cache",
        method="delete",
        summary="Clear demo cache",
    )
    def clear_cache(request):
        return NoContentResponse()

    @protected.init(
        "/asset",
        method="get",
        summary="Download demo bytes",
    )
    def asset(request):
        return BytesResponse(b"muscular-example", content_type="text/plain")

    @protected.init(
        "/method-key",
        key="framework.method_key.read",
        method="get",
        summary="Read route identity demo",
    )
    def method_key_read(request):
        return JsonResponse({"operation": "read", "route_key": "framework.method_key.read"})

    @protected.init(
        "/method-key",
        key="framework.method_key.write",
        method="post",
        summary="Write route identity demo",
    )
    def method_key_write(request):
        # RU: Тот же path, другой HTTP method и другой route key.
        # EN: Same path, different HTTP method, different route key.
        return JsonResponse({"operation": "write", "route_key": "framework.method_key.write"})


wsgi_project = Example4WsgiApp(wsgi_runtime())
asgi_project = Example4AsgiApp(asgi_runtime())

wsgi_application = wsgi_app(wsgi_project, context=wsgi_project.context)
asgi_application = asgi_app(asgi_project, context=asgi_project.context)

app = wsgi_application
