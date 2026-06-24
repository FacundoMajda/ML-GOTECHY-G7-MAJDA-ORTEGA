# src/app.py — Entry point refactorizado
import os
from http.server import ThreadingHTTPServer
from pathlib import Path

from src.config.settings import OUTPUT_DIR, REPORTS_DIR
from src.controllers.app_handler import AppHandler


def main() -> None:
    # Ensure output directories exist at startup
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    Path(REPORTS_DIR).mkdir(exist_ok=True)

    # HOST=0.0.0.0 para aceptar conexiones desde el port-forward de Docker
    # Default 0.0.0.0 para que funcione out-of-the-box; se puede override
    # con la env var HOST para desarrollo local en 127.0.0.1 si hace falta.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Servidor en http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
