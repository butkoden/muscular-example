from __future__ import annotations

import json
from typing import Any, cast

from muscles import ApplicationMeta, Configurator, Context
from muscles.wsgi import wsgi_app
from muscles.wsgi.wsgi import BaseResponse, WsgiStrategy, routes

from .data_ai_documents import run_all


class Example5App(metaclass=ApplicationMeta):
    """Minimal WSGI shell for ecosystem data, documents, and AI examples.

    RU: Основа намеренно такая же, как в example_1: приложение, Configurator,
    Context(WsgiStrategy) и один route. Новые библиотеки живут внутри use-case.

    EN: The foundation intentionally mirrors example_1: app, Configurator,
    Context(WsgiStrategy), and one route. New libraries stay inside the use case.
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
            "MAIN_ROUTE": "example_5.home",
            "SECRET_KEY": "local-development-only",
        },
        "routes": {"prefix": ""},
    })

    def __init__(self):
        self.context = Context(cast(Any, WsgiStrategy), params={})

    def __call__(self, environ, start_response):
        self.context.set_param("environ", environ)
        self.context.set_param("start_response", start_response)
        return self.context.execute()


@routes.init("/example-5", key="example_5.home", method="GET")
def home(request):
    payload = {
        "level": 5,
        "title": "Data, documents and AI extensions",
        "result": run_all(),
    }
    return BaseResponse(
        status=200,
        body=json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        headers=[("Content-Type", "application/json; charset=utf-8")],
    )


project = Example5App()
app = wsgi_app(project, context=project.context)
