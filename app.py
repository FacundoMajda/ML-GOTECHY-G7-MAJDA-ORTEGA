from __future__ import annotations

import html
import mimetypes
import os
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from video_analytics import generate_report_html, list_video_options, process_named_video


BASE_DIR = Path(__file__).resolve().parent


def render_home(
    message: str = "",
    report_html: str = "",
    selected_video_key: str = "mall",
    extra_analysis: str = "no",
    extra_target: str = "",
) -> str:
    cards = []
    options = []
    for item in list_video_options():
        options.append(
            f'<option value="{html.escape(item["key"])}"'
            f'{" selected" if item["key"] == selected_video_key else ""}>'
            f'{html.escape(item["title"])}</option>'
        )
        roi_text = (
            " | ".join(
                f'{zone["count_label"]}: {zone["polygon"]}'
                for zone in item.get("roi_zones", [])
            )
            if item.get("roi_zones")
            else str(item["roi_polygon"])
        )
        cards.append(
            f"""
            <article class="card">
              <div class="eyebrow">Video disponible</div>
              <h3>{html.escape(item["title"])}</h3>
              <p>{html.escape(item["description"])}</p>
              <p class="meta"><strong>Ruta:</strong> <code>{html.escape(item["path"])}</code></p>
              <p class="meta"><strong>ROI:</strong> <code>{html.escape(roi_text)}</code></p>
              <p class="meta"><strong>Flujo:</strong> {html.escape(item["positive_label"])} / {html.escape(item["negative_label"])}</p>
            </article>
            """
        )

    report_section = (
        '<section class="report-shell"><div class="report-header">Resultado</div>'
        f'<iframe title="Reporte" srcdoc="{html.escape(report_html, quote=True)}"></iframe>'
        "</section>"
        if report_html
        else ""
    )

    extra_yes_selected = " selected" if extra_analysis == "yes" else ""
    extra_no_selected = " selected" if extra_analysis != "yes" else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Video Analytics Local</title>
  <style>
    :root {{
      --bg: #f7f1e7;
      --panel: rgba(255,249,240,0.9);
      --ink: #1f2937;
      --muted: #6b7280;
      --accent: #0f766e;
      --accent-2: #9a3412;
      --line: #e8dbc8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      background:
        linear-gradient(135deg, rgba(15,118,110,0.08), transparent 35%),
        linear-gradient(315deg, rgba(154,52,18,0.10), transparent 30%),
        var(--bg);
    }}
    .wrap {{
      max-width: 1260px;
      margin: 0 auto;
      padding: 28px 18px 40px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 20px;
      margin-bottom: 24px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 22px;
      box-shadow: 0 22px 60px rgba(31,41,55,0.08);
      backdrop-filter: blur(10px);
    }}
    h1 {{
      margin: 0 0 12px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 2.5rem;
      line-height: 1.05;
    }}
    p {{
      margin: 0 0 12px;
      line-height: 1.55;
    }}
    .muted {{ color: var(--muted); }}
    form {{
      display: grid;
      gap: 14px;
    }}
    label {{
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    select, button, input {{
      width: 100%;
      border-radius: 14px;
      border: 1px solid var(--line);
      padding: 14px 16px;
      font-size: 1rem;
      background: #fff;
    }}
    button {{
      cursor: pointer;
      background: linear-gradient(135deg, var(--accent), #115e59);
      color: white;
      font-weight: 700;
      border: none;
    }}
    button:hover {{ filter: brightness(1.05); }}
    .message {{
      margin-bottom: 14px;
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(15,118,110,0.08);
      border: 1px solid rgba(15,118,110,0.18);
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .card {{
      background: rgba(255,255,255,0.7);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 18px;
    }}
    .card h3 {{ margin: 0 0 10px; }}
    .eyebrow {{
      font-size: 0.8rem;
      color: var(--accent-2);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }}
    .meta {{
      color: var(--muted);
      font-size: 0.92rem;
      margin-bottom: 8px;
    }}
    .report-shell {{
      background: rgba(255,249,240,0.75);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 10px;
    }}
    .report-header {{
      padding: 12px 16px;
      color: var(--accent);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    iframe {{
      width: 100%;
      min-height: 980px;
      border: none;
      border-radius: 18px;
      background: white;
    }}
    code {{
      font-family: Consolas, monospace;
      background: rgba(15,118,110,0.08);
      padding: 2px 6px;
      border-radius: 6px;
    }}
    @media (max-width: 880px) {{
      .hero {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 2rem; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="panel">
        <p class="muted">Dashboard local para elegir video y generar estadisticas</p>
        <h1>ROI Counter con selector de video</h1>
        <p>Puedes correr el conteo sobre la escalera o sobre <code>mall.mp4</code> sin reescribir el notebook. En el mall ahora hay dos ROIs separadas: una para <strong>entrada</strong> y otra para <strong>salida</strong>.</p>
        <p>Si luego quieres agregar mas videos, solo hay que sumar otra configuracion en <code>video_analytics.py</code>.</p>
      </div>
      <div class="panel">
        {f'<div class="message">{html.escape(message)}</div>' if message else ''}
        <form method="post" action="/process">
          <div>
            <label for="video_key">Elegir video</label>
            <select id="video_key" name="video_key">
              {"".join(options)}
            </select>
          </div>
          <div>
            <label for="write_video">Generar video anotado</label>
            <select id="write_video" name="write_video">
              <option value="yes">Si</option>
              <option value="no">No, solo estadisticas</option>
            </select>
          </div>
          <div>
            <label for="extra_analysis">Quieres analizar otra cosa</label>
            <select id="extra_analysis" name="extra_analysis">
              <option value="no"{extra_no_selected}>No</option>
              <option value="yes"{extra_yes_selected}>Si</option>
            </select>
          </div>
          <div>
            <label for="extra_target">Que te gustaria medir</label>
            <input id="extra_target" name="extra_target" type="text" placeholder="Ej: cuantos llevan gorro" value="{html.escape(extra_target, quote=True)}" />
          </div>
          <button type="submit">Procesar video</button>
        </form>
      </div>
    </section>

    <section class="cards">
      {"".join(cards)}
    </section>

    {report_section}
  </div>
</body>
</html>
"""


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(render_home())
            return

        if parsed.path.startswith("/files/"):
            rel = parsed.path.removeprefix("/files/")
            file_path = (BASE_DIR / rel).resolve()
            if not str(file_path).startswith(str(BASE_DIR)):
                self.send_error(403)
                return
            if not file_path.exists() or not file_path.is_file():
                self.send_error(404)
                return
            mime, _ = mimetypes.guess_type(str(file_path))
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
            return

        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/process":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length).decode("utf-8")
        form = parse_qs(payload)
        video_key = form.get("video_key", ["mall"])[0]
        write_video = form.get("write_video", ["yes"])[0] == "yes"
        extra_analysis = form.get("extra_analysis", ["no"])[0]
        extra_target = form.get("extra_target", [""])[0].strip()

        try:
            summary = process_named_video(
                video_key,
                write_video=write_video,
                extra_analysis_requested=extra_analysis == "yes",
                extra_analysis_target=extra_target,
            )
            report_html = generate_report_html(summary)
            if summary.output_video and Path(summary.output_video).exists():
                relative_video = os.path.relpath(summary.output_video, BASE_DIR).replace("\\", "/")
                report_html += (
                    '<section style="max-width:1200px;margin:18px auto 0;background:white;'
                    'border-radius:18px;padding:20px;border:1px solid #eadfce;">'
                    '<h2 style="margin-top:0">Video anotado</h2>'
                    f'<video controls style="width:100%;border-radius:14px;" src="/files/{html.escape(relative_video)}"></video>'
                    "</section>"
                )
            self._send_html(
                render_home(
                    message=f"Procesamiento completado para {summary.video_title}.",
                    report_html=report_html,
                    selected_video_key=video_key,
                    extra_analysis=extra_analysis,
                    extra_target=extra_target,
                )
            )
        except Exception as exc:
            trace = traceback.format_exc()
            self._send_html(
                render_home(
                    message=f"Error procesando el video: {exc}",
                    report_html=(
                        "<section class='panel'><pre style='white-space:pre-wrap;'>"
                        f"{html.escape(trace)}"
                        "</pre></section>"
                    ),
                    selected_video_key=video_key,
                    extra_analysis=extra_analysis,
                    extra_target=extra_target,
                ),
                status=500,
            )

    def log_message(self, format: str, *args) -> None:
        return

    def _send_html(self, payload: str, status: int = 200) -> None:
        content = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), AppHandler)
    print("Servidor listo en http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
