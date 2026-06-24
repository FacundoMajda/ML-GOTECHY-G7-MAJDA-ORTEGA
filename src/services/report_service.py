# src/services/report_service.py
# Genera reporte HTML desde MetricSnapshot + Session.
# Sin datos internos: no frame_number, no track_id, no roi_id completo.

from src.repositories.session_repo import SessionRepository
from src.repositories.metric_snapshot_repo import MetricSnapshotRepository
from src.repositories.roi_repo import ROIRepository
from src.repositories.db import execute_query


def generate_report_html(session_id: str) -> str:
    """Genera HTML limpio para un analisis. Lee de metric_snapshot."""
    session_repo = SessionRepository()
    snapshot_repo = MetricSnapshotRepository()
    roi_repo = ROIRepository()

    session = session_repo.get_by_id(session_id)
    if not session:
        return "<html><body><h1>Analisis no encontrado</h1></body></html>"

    snapshots = snapshot_repo.get_by_session(session_id)

    # Cache de nombres de ROI
    roi_names: dict[str, str] = {}

    def _roi_name(roi_id: str) -> str:
        if roi_id not in roi_names:
            roi = roi_repo.get_by_id(roi_id)
            roi_names[roi_id] = roi["name"] if roi and roi.get("name") else roi_id[:8]
        return roi_names[roi_id]

    # Metricas totales
    total_entries = sum(s["entries"] for s in snapshots)
    total_exits = sum(s["exits"] for s in snapshots)
    max_occ = max((s["max_occupancy"] for s in snapshots), default=0)

    # ── Por ROI (agg por roi, sumando clases) ──
    roi_agg: dict[str, dict] = {}
    for s in snapshots:
        rid = s["roi_id"]
        if rid not in roi_agg:
            roi_agg[rid] = {"entries": 0, "exits": 0, "max_occ": 0}
        roi_agg[rid]["entries"] += s["entries"]
        roi_agg[rid]["exits"] += s["exits"]
        roi_agg[rid]["max_occ"] = max(roi_agg[rid]["max_occ"], s["max_occupancy"])

    roi_rows = []
    for rid, m in roi_agg.items():
        name = _roi_name(rid)
        roi_rows.append(
            f"<tr>"
            f"<td>{name}</td>"
            f"<td>{m['entries']}</td>"
            f"<td>{m['exits']}</td>"
            f"<td>{m['max_occ']}</td>"
            f"</tr>"
        )
    roi_rows_html = "\n".join(roi_rows) if roi_rows else "<tr><td colspan='4'>Sin ROIs procesadas.</td></tr>"

    # ── Distribucion por Clase (por ROI + clase) ──
    cls_rows = []
    for s in snapshots:
        name = _roi_name(s["roi_id"])
        object_class = s.get("object_class") or "person"
        dwell_str = f'{s["avg_dwell_seconds"]:.1f}s' if s.get("avg_dwell_seconds") else "-"
        cls_rows.append(
            f"<tr>"
            f"<td>{name}</td>"
            f"<td>{object_class}</td>"
            f"<td>{s['entries']}</td>"
            f"<td>{s['exits']}</td>"
            f"<td>{s['max_occupancy']}</td>"
            f"<td>{dwell_str}</td>"
            f"<td>{s['unique_objects']}</td>"
            f"</tr>"
        )
    cls_rows_html = "\n".join(cls_rows) if cls_rows else "<tr><td colspan='7'>Sin datos por clase.</td></tr>"

    started = session.get("started_at", "")
    ended = session.get("ended_at", "")
    duration = session.get("duration_seconds")
    dur_str = f'{duration:.1f}s' if duration else "-"
    source_name = session.get("source_name") or session.get("video_source_id") or "-"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Reporte {source_name}</title>
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
    .wrap {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 60px; }}
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
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <p class="muted">Reporte - {started}</p>
      <h1>{source_name}</h1>
      <p><strong>Inicio:</strong> {started} &nbsp; <strong>Fin:</strong> {ended} &nbsp; <strong>Duracion:</strong> {dur_str}</p>
    </div>

    <div class="stats">
      <div class="stat">
        <div class="label">Total Entradas</div>
        <div class="value">{total_entries}</div>
      </div>
      <div class="stat">
        <div class="label">Total Salidas</div>
        <div class="value">{total_exits}</div>
      </div>
      <div class="stat">
        <div class="label">Pico Ocupacion</div>
        <div class="value">{max_occ}</div>
      </div>
      <div class="stat">
        <div class="label">ROIs Analizadas</div>
        <div class="value">{len(snapshots)}</div>
      </div>
    </div>

    <div class="panel">
      <h2>Resumen por Zona</h2>
      <table>
        <thead>
          <tr><th>Zona</th><th>Entradas</th><th>Salidas</th><th>Pico Ocupacion</th></tr>
        </thead>
        <tbody>
          {roi_rows_html}
        </tbody>
      </table>
    </div>

    <div class="panel">
      <h2>Distribucion por Clase</h2>
      <p class="muted" style="margin-bottom:14px">Desglose de entradas, salidas y ocupacion por zona y clase de objeto.</p>
      <table>
        <thead>
          <tr><th>Zona</th><th>Clase</th><th>Entradas</th><th>Salidas</th><th>Pico</th><th>Dwell Prom</th><th>Objetos Unicos</th></tr>
        </thead>
        <tbody>
          {cls_rows_html}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>"""
