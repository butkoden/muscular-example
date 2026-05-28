from wsgiref.simple_server import make_server

from .db import init_db
from .web import app


def main():
    init_db()
    host = "0.0.0.0"
    port = 8080
    print(f"butko.info demo is running at http://localhost:{port}")
    with make_server(host, port, app) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
