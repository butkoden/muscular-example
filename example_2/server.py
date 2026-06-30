from wsgiref.simple_server import make_server

from .web import wsgi_application


def main():
    # RU: Уровень 2 запускает WSGI-вариант; ASGI-вариант используется в тестах.
    # EN: Level 2 runs the WSGI variant; the ASGI variant is exercised in tests.
    host = "0.0.0.0"
    port = 8080
    print(f"Example 2 is running at http://localhost:{port}/example-2")
    print(f"OpenAPI schema: http://localhost:{port}/api/example-2/v1/schema")
    with make_server(host, port, wsgi_application) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
