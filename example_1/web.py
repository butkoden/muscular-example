from __future__ import annotations

from typing import Any, cast

from muscles import ApplicationMeta, Configurator, Context
from muscles.wsgi import wsgi_app
from muscles.wsgi.wsgi import BaseResponse, WsgiStrategy, routes


class Example1App(metaclass=ApplicationMeta):
    """Minimal WSGI application.

    RU: Здесь нет API, базы данных и middleware. Только приложение,
    контекст выполнения и один route.

    EN: There is no API, database, or middleware here. Just the application,
    execution context, and one route.
    """

    package_paths = []
    shutup = False

    # RU: Configurator нужен Muscles-приложению даже в простом примере.
    # EN: Muscles applications still need Configurator in a tiny example.
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
            "MAIN_ROUTE": "example_1.home",
            "SECRET_KEY": "local-development-only",
        },
        "routes": {"prefix": ""},
    })

    def __init__(self):
        # RU: Context связывает приложение со стратегией WSGI.
        # EN: Context connects the application to the WSGI strategy.
        self.context = Context(cast(Any, WsgiStrategy), params={})

    def __call__(self, environ, start_response):
        # RU: WSGI передает environ/start_response, Muscles кладет их в Context.
        # EN: WSGI passes environ/start_response; Muscles stores them in Context.
        self.context.set_param("environ", environ)
        self.context.set_param("start_response", start_response)
        return self.context.execute()


@routes.init("/example-1", key="example_1.home", method="GET")
def home(request):
    # RU: Handler может вернуть готовый response object.
    # EN: A handler can return a ready response object.
    return BaseResponse(
        status=200,
        body="Hello from example_1",
        headers=[("Content-Type", "text/plain; charset=utf-8")],
    )


project = Example1App()
app = wsgi_app(project, context=project.context)
