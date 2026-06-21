# src/app.py — Entry point refactorizado
from http.server import ThreadingHTTPServer

from src.controllers.app_handler import AppHandler


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), AppHandler)
    print("Servidor en http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
