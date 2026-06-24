import os
from http.server import ThreadingHTTPServer
from pathlib import Path

from src.config.settings import OUTPUT_DIR, REPORTS_DIR
from src.controllers.app_handler import AppHandler


def main() -> None:
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    Path(REPORTS_DIR).mkdir(exist_ok=True)

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Servidor en http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
