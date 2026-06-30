from __future__ import annotations

import json
from http.cookies import SimpleCookie
from pathlib import Path

from muscles import ApplicationMeta, BytesResponse, Configurator, Context, JsonResponse, NoContentResponse
from muscles import JsonRequestBody, JsonResponseBody, Model, Column, String, DateTime, ValueObjectField
from muscles.asgi import asgi_app
from muscles.asgi.asgi import AsgiStrategy
from muscles.asgi.restful import RestApi as AsgiRestApi
from muscles.wsgi import wsgi_app
from muscles.wsgi.wsgi import WsgiStrategy
from muscles.wsgi.restful import RestApi as WsgiRestApi

from .config import ADMIN_SESSION_COOKIE, ADMIN_SESSION_VALUE
from .db import check_admin_password, create_booking, diagnostics, init_db, list_bookings, set_admin_password
from .platform import RouteRegistrar
from .templates import escape, page, render
from .value_objects import EmailAddress


API_DEMO_TOKEN = "demo-framework-token"


class Booking(Model):
    name = Column(String)
    email = Column(ValueObjectField(value_object_class=EmailAddress))
    title = Column(String)
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)
    notes = Column(String)


class ButkoInfoApp:
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
            "MAIN_ROUTE": "page.index",
            "SECRET_KEY": "local-development-only",
        },
        "routes": {"prefix": ""},
        "api": {"prefix": "/api", "default_version": "v1", "controllers": {}},
    })

    def __init__(self, runtime):
        # Runtime-safe DB bootstrap. Fast path is cached inside db.init_db().
        init_db()
        self.runtime = runtime
        self.context = Context(runtime.strategy, params={})
        # API schema and Swagger metadata are declared once and reused by routes.
        self.api = runtime.rest_api(
            prefix="/api/v1",
            version="1.0",
            name="ButkoInfoApi",
            title="butko.info API",
            description="API for booking calendar slots from butko.info",
            contact_email="hello@butko.info",
            servers=[{"url": "http://localhost:8080"}],
        )
        self.route_registrar = RouteRegistrar(
            routes=runtime.routes,
            api=self.api,
            response_class=runtime.response,
            api_key_token=API_DEMO_TOKEN,
        )
        self.route_registrar.attach_api_contract(
            allow_origins=["https://butko.info"],
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "X-Api-Key"],
        )
        register_pages(self.route_registrar)
        register_api(self.route_registrar)

    def __call__(self, environ, start_response):
        self.context.set_param("environ", environ)
        self.context.set_param("start_response", start_response)
        return self.context.execute()

    async def asgi_call(self, scope, receive, send):
        result = self.context.execute(scope=scope, receive=receive, send=send)
        if hasattr(result, "__await__"):
            await result


class ButkoInfoWsgiApp(ButkoInfoApp, metaclass=ApplicationMeta):
    pass


class ButkoInfoAsgiApp(ButkoInfoApp, metaclass=ApplicationMeta):
    pass


class RuntimeBinding:
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


def html_response(response_class, body, status=200, headers=None):
    headers = headers or []
    headers.append(("Content-Type", "text/html; charset=utf-8"))
    return response_class(status=status, body=body, headers=headers)


def redirect(response_class, location):
    return response_class(status=302, body="", headers=[("Location", location)])


def request_form(request):
    return {key: str(value) for key, value in (request.forms or {}).items()}


def is_admin(request):
    cookies = request.cookies or {}
    return cookies.get(ADMIN_SESSION_COOKIE) == ADMIN_SESSION_VALUE


def require_admin(response_class, request):
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


def register_pages(registrar: RouteRegistrar):
    # Static files are served by framework router, not by a separate web server.
    routes = registrar.routes
    response_class = registrar.response_class
    routes.add_static(str(Path(__file__).resolve().parent / "static"), prefix="/static", full_path=True)

    @registrar.page("/", key="page.index", method="GET")
    def index(request):
        body = render("home.html")
        return html_response(response_class, page("butko.info", body, active="home"))

    @registrar.page("/resume", key="page.resume", method="GET")
    def resume(request):
        body = render("resume.html")
        return html_response(response_class, page("Portfolio / Resume", body, active="resume"))

    @registrar.page("/admin", key="admin.index", method="GET")
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

    @registrar.page("/admin/login", key="admin.login", method="GET")
    def login_form(request):
        return html_response(response_class, page("Admin login", render("login.html", error=""), active="admin"))

    @registrar.page("/admin/login", key="admin.login", method="POST")
    def login_submit(request):
        form = request_form(request)
        if check_admin_password(form.get("password", "")):
            return set_login_cookie(redirect(response_class, "/admin"))
        return html_response(
            response_class,
            page("Admin login", render("login.html", error="Wrong password"), active="admin"),
            status=403,
        )

    @registrar.page("/admin/logout", key="admin.logout", method="POST")
    def logout(request):
        return clear_login_cookie(redirect(response_class, "/"))

    @registrar.page("/admin/password", key="admin.password", method="POST")
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

    @registrar.page("/admin/diagnostics", key="admin.diagnostics", method="GET")
    def diagnostics_page(request):
        denied = require_admin(response_class, request)
        if denied:
            return denied
        payload = json.dumps(diagnostics(), indent=2)
        return html_response(
            response_class,
            page("Diagnostics", render("diagnostics.html", diagnostics=escape(payload)), active="admin"),
        )


def register_api(registrar: RouteRegistrar):
    api = registrar.api

    # Controller class is mounted under /api/v1/bookings via RestApi prefix + route.
    @registrar.api_controller("/bookings", description="Calendar slot bookings", summary="Bookings")
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

    protected = registrar.api_group(
        "/protected",
        tags=["Framework primitives"],
        security=registrar.openapi_security,
        response={401: JsonResponseBody(description="Unauthorized")},
    )

    @registrar.api_action(
        protected,
        "/login",
        method="post",
        auth=False,
        summary="Issue demo API token",
    )
    def login(request):
        return JsonResponse({"token": API_DEMO_TOKEN})

    @registrar.api_action(
        protected,
        "/diagnostics",
        method="get",
        summary="Show protected diagnostics",
    )
    def api_diagnostics(request):
        return JsonResponse({"diagnostics": diagnostics()})

    @registrar.api_action(
        protected,
        "/cache",
        method="delete",
        summary="Clear demo cache",
    )
    def clear_cache(request):
        return NoContentResponse()

    @registrar.api_action(
        protected,
        "/asset",
        method="get",
        summary="Download demo bytes",
    )
    def asset(request):
        return BytesResponse(b"muscular-example", content_type="text/plain")


wsgi_project = ButkoInfoWsgiApp(wsgi_runtime())
asgi_project = ButkoInfoAsgiApp(asgi_runtime())

wsgi_application = wsgi_app(wsgi_project, context=wsgi_project.context)
asgi_application = asgi_app(asgi_project, context=asgi_project.context)

app = wsgi_application
