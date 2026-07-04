from wsgiref.simple_server import make_server

from .web import app


def main():
    # RU: Уровень 5 запускается через тот же минимальный WSGI-server, что и example_1.
    # EN: Level 5 uses the same minimal WSGI server shape as example_1.
    host = "0.0.0.0"
    port = 8080
    print(f"Example 5 is running at http://localhost:{port}/example-5")
    with make_server(host, port, app) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
