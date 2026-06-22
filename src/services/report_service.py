import html
from pathlib import Path

from src.models.contracts import SessionResult


def generate_report_html(summary: SessionResult) -> str:
    print(f"[DEBUG] report_service.generate_report_html: ENTRY session_id={summary.id} video_source_id={summary.video_source_id} n_events={len(summary.zone_events)} n_entities={len(summary.tracked_entities)}", flush=True)
    if summary.zone_events:
        rows = []
        for ev in summary.zone_events[-50:]:
            rows.append(
                f"<tr>"
                f"<td>{ev.frame_number or '-'} </td>"
                f"<td>{ev.track_id or '-'} </td>"
                f"<td>{ev.event_type.value}</td>"
                f"<td>{ev.roi_id} </td>"
                f"<td>{ev.dwell_seconds or '-'} </td>"
                f"</tr>"
            )
        events_rows = "\n".join(rows)
    else:
        events_rows = "<tr><td colspan='5'>Sin eventos registrados.</td></tr>"

    entry_count = sum(1 for e in summary.zone_events if e.event_type.value == "entry")
    exit_count = sum(1 for e in summary.zone_events if e.event_type.value == "exit")
    roi_ids = sorted({e.roi_id for e in summary.zone_events} | {s.roi_id for s in summary.occupancy_snapshots})

    roi_rows = []
    for roi_id in roi_ids:
        roi_entry = sum(
            1 for e in summary.zone_events if e.roi_id == roi_id and e.event_type.value == "entry"
        )
        roi_exit = sum(
            1 for e in summary.zone_events if e.roi_id == roi_id and e.event_type.value == "exit"
        )
        roi_snapshots = [s for s in summary.occupancy_snapshots if s.roi_id == roi_id]
        max_inside = max((s.count_inside for s in roi_snapshots), default=0)
        last_inside = roi_snapshots[-1].count_inside if roi_snapshots else 0
        roi_rows.append(
            f"<tr><td>{html.escape(roi_id)}</td><td>{roi_entry}</td><td>{roi_exit}</td>"
            f"<td>{max_inside}</td><td>{last_inside}</td></tr>"
        )
    roi_rows_html = "\n".join(roi_rows) if roi_rows else "<tr><td colspan='5'>Sin ROIs procesadas.</td></tr>"

    output_video_html = ""
    if summary.output_video_path:
        output_path = Path(summary.output_video_path)
        if output_path.exists():
            try:
                rel = output_path.resolve().relative_to(Path.cwd().resolve())
                url = "/files/" + str(rel).replace("\\", "/")
                output_video_html = f"""
                <div class="panel">
                  <h2>Video Anotado</h2>
                  <video controls preload="metadata" style="width:100%;border-radius:16px;background:#111">
                    <source src="{html.escape(url)}" type="video/mp4">
                  </video>
                  <p><strong>Ruta:</strong> <code>{html.escape(summary.output_video_path)}</code></p>
                </div>
                """
            except Exception:
                output_video_html = f"""
                <div class="panel">
                  <h2>Video Anotado</h2>
                  <p><strong>Ruta:</strong> <code>{html.escape(summary.output_video_path)}</code></p>
                </div>
                """

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Reporte {summary.video_source_id}</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --panel: #fffaf3;
      --accent: #0f766e;
      --accent-2: #b45309;
      --line: #eadfce;
      --ink: #1f2937;
      --muted: #6b7280;
    }}
     * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Georgia, serif; color: var(--ink); background: var(--bg); }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 60px; }}
    .hero {{ background: rgba(255,250,243,0.94); border: 1px solid var(--line); border-radius: 22px; padding: 22px; margin-bottom: 24px; }}
    h1 {{ margin: 0 0 12px; font-size: 2rem; }}
    p {{ margin: 0 0 10px; }}
    .muted {{ color: var(--muted); }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin: 24px 0; }}
    .stat {{ padding: 18px; border-radius: 18px; background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(245,239,230,0.98)); border: 1px solid var(--line); }}
    .stat .label {{ color: var(--muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    .stat .value {{ font-size: 2rem; font-weight: 700; margin-top: 8px; }}
    .panel {{ background: rgba(255,250,243,0.94); border: 1px solid var(--line); border-radius: 22px; padding: 22px; margin-bottom: 18px; }}
    h2 {{ margin: 0 0 14px; font-size: 1.2rem; color: var(--accent); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; }}
    th, td {{ text-align: left; padding: 12px 10px; border-bottom: 1px solid var(--line); }}
    th {{ color: var(--accent); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    code {{ font-family: Consolas, monospace; background: rgba(15,118,110,0.08); padding: 2px 6px; border-radius: 6px; font-size: 0.88rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <p class="muted">Reporte generado {summary.started_at.strftime('%Y-%m-%d %H:%M:%S') if summary.started_at else 'N/A'}</p>
      <h1>{summary.video_source_id}</h1>
      <p><strong>Frames:</strong> {summary.total_frames or 0} &nbsp; <strong>FPS:</strong> {summary.fps or 'N/A'} &nbsp; <strong>Timestamp mode:</strong> <code>{summary.timestamp_mode.value}</code></p>
      <p><strong>Inicio:</strong> {summary.started_at.isoformat() if summary.started_at else 'N/A'} &nbsp; <strong>Fin:</strong> {summary.ended_at.isoformat() if summary.ended_at else 'N/A'}</p>
    </div>

    <div class="stats">
      <div class="stat">
        <div class="label">Entradas</div>
        <div class="value">{entry_count}</div>
      </div>
      <div class="stat">
        <div class="label">Salidas</div>
        <div class="value">{exit_count}</div>
      </div>
      <div class="stat">
        <div class="label">Entidades trackeadas</div>
        <div class="value">{len(summary.tracked_entities)}</div>
      </div>
      <div class="stat">
        <div class="label">Eventos totales</div>
        <div class="value">{len(summary.zone_events)}</div>
      </div>
    </div>

    {output_video_html}

    <div class="panel">
      <h2>Resumen por ROI</h2>
      <table>
        <thead>
          <tr><th>ROI</th><th>Entradas</th><th>Salidas</th><th>Max dentro</th><th>Ultimo snapshot</th></tr>
        </thead>
        <tbody>
          {roi_rows_html}
        </tbody>
      </table>
    </div>

    <div class="panel">
      <h2>Eventos (ultimos 50)</h2>
      <table>
        <thead>
          <tr><th>Frame</th><th>Track ID</th><th>Tipo</th><th>ROI</th><th>Dwell (s)</th></tr>
        </thead>
        <tbody>
          {events_rows}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>"""
