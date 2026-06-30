from wsgiref.simple_server import make_server

from .web import app


def main():
    # RU: Для первого уровня достаточно встроенного WSGI-сервера Python.
    # EN: Python's built-in WSGI server is enough for the first level.
    host = "0.0.0.0"
    port = 8080
    print(f"Example 1 is running at http://localhost:{port}/example-1")
    with make_server(host, port, app) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
