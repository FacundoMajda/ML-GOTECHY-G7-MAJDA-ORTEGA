# src/app.py — Entry point refactorizado
import os
from http.server import ThreadingHTTPServer

from src.controllers.app_handler import AppHandler


def main() -> None:
    # HOST=0.0.0.0 para aceptar conexiones desde el port-forward de Docker
    # Default 0.0.0.0 para que funcione out-of-the-box; se puede override
    # con la env var HOST para desarrollo local en 127.0.0.1 si hace falta.
    host = os.environ.get("HOST", "0.0.0.0")
    server = ThreadingHTTPServer((host, 8000), AppHandler)
    print(f"Servidor en http://{host}:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
