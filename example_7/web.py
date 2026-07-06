from __future__ import annotations

import json

from muscles import ApplicationMeta, Configurator, Context
from muscles.wsgi import wsgi_app
from muscles.wsgi.wsgi import BaseResponse, WsgiStrategy, routes

from .data_ports import run_all


class Example7App(metaclass=ApplicationMeta):
    """Minimal WSGI shell for typed data ports.

    RU: Основа повторяет example_1. Вся data-логика живет в маленьком use-case,
    а web adapter только отдает результат.

    EN: The foundation mirrors example_1. Data logic lives in a small use case,
    while the web adapter only returns the result.
    """

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
            "MAIN_ROUTE": "example_7.home",
            "SECRET_KEY": "local-development-only",
        },
        "routes": {"prefix": ""},
    })

    def __init__(self):
        self.context = Context(WsgiStrategy, params={})

    def __call__(self, environ, start_response):
        self.context.set_param("environ", environ)
        self.context.set_param("start_response", start_response)
        return self.context.execute()


@routes.init("/example-7", key="example_7.home", method="GET")
def home(request):
    payload = {
        "level": 7,
        "title": "Typed data ports",
        "result": run_all(),
    }
    return BaseResponse(
        status=200,
        body=json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        headers=[("Content-Type", "application/json; charset=utf-8")],
    )


project = Example7App()
app = wsgi_app(project, context=project.context)
