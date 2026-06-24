<div align="center">

# 🎯 Argus Vision — Video Analytics Platform

### Detección, tracking y conteo de personas en zonas definidas (ROIs) sobre video

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![YOLOv11](https://img.shields.io/badge/YOLO-v11-00FFFF?style=for-the-badge&logo=ultralytics&logoColor=black)](https://ultralytics.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**Grupo 7 · Majda · Ortega | Proyecto ML – GOTECHY**

</div>

---

## 📋 Tabla de contenidos

- [¿Qué es Argus Vision?](#-qué-es-argus-vision)
- [Features](#-features)
- [Stack tecnológico](#-stack-tecnológico)
- [Quick start con Docker](#-quick-start-con-docker)
- [Quick start local con uv](#-quick-start-local-con-uv)
- [Configuración](#-configuración)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [API Reference](#-api-reference)
- [Pipeline de análisis](#-pipeline-de-análisis)
- [Schema de la base de datos](#-schema-de-la-base-de-datos)
- [Autores](#-autores)

---

## 🎯 ¿Qué es Argus Vision?

Argus Vision es una **plataforma web de análisis de video** que corre YOLOv11 + ByteTrack sobre distintas fuentes de video, permite dibujar zonas de interés (ROIs) poligonales, ejecuta análisis en background con feedback en tiempo real, persiste todo en PostgreSQL y expone un dashboard con métricas de entrada, salida, ocupación y permanencia por ROI.

Sustituye la versión anterior del proyecto basada en notebook (`notebooks/ml_gotechy.ipynb`).

**App corriendo en `localhost:8000` · UI de logs (Dozzle) en `localhost:8080`.**

---

## ✨ Features

### Captura de video
- 📁 **Archivos locales** — upload desde la UI o path directo
- ▶️ **YouTube VOD** — extracción de stream URL via `yt-dlp` (con filtro anti-AV1)
- 🔴 **YouTube Live** — reconexión automática hasta 5 reintentos
- 📡 **RTSP** — cámaras IP / streams en red local, reconexión automática

### Detección y tracking
- 🤖 **YOLOv11n** (Ultralytics) — single model, CPU-only
- 🎯 **ByteTrack** integrado via `bytetrack.yaml` con `persist=True`
- 🏷️ **80 clases COCO** filtrables por ROI (`observed_classes`) — default: `person`. Cualquier subset de las 80 clases puede trackearse y asociarse a un ROI.

### Regiones de Interés (ROIs)
- 📐 **Polígonos interactivos** dibujados en la UI con click-to-add
- 🚪 **Detección de entry/exit** — `pointPolygonTest` + intersección de segmentos para cruces fronterizos
- 📊 **Snapshots de ocupación** cada 30 frames
- ⏱️ **Dwell time** automático al salir de la zona
- 🏷️ **Multi-class filtering** — cada ROI declara `observed_classes` (subset de COCO 80) para reducir falsos positivos

### Alert Rules por ROI
- 🎯 **5 tipos de regla** — `OccupancyHigh`, `OccupancyLow`, `DwellExceeded`, `ObjectCountExceeded`, `ForbiddenClassDetected`
- 📐 **Métricas comparables** — `count`, `occupancy`, `dwell_seconds` con operadores `>`, `<`, `>=`, `<=`, `==`, `between`
- 🚨 **3 niveles de severidad** — `info` (azul), `warning` (ámbar), `critical` (rojo)
- ⏰ **Ventana horaria opcional** — `time_from` / `time_to` para reglas activas solo en cierto rango del día
- 🎚️ **Per-class thresholds** — `class_id` opcional para reglas que aplican solo a una clase específica
- 📊 **Visualización en análisis** — bloque "Reglas evaluadas" arriba del log de eventos, badge `DISPARADA`/`cumplida` por regla

### Persistencia y métricas
- 💾 **9 tablas PostgreSQL** — sources, ROIs, alert_rules, sessions, tracked entities, snapshots, events, metric snapshots, class catalog
- ⚡ **Batch INSERTs paralelos** (3 hilos) en `ThreadPoolExecutor` para persistencia rápida
- 🔒 **Unique constraints** que previenen duplicados: `(session_id, track_id)` y `(session_id, roi_id, frame_number)`
- 📈 **MetricSnapshot** derivado: entries, exits, max_occupancy, avg_dwell por ROI por sesión

### UI / SPA (5 tabs)
- **Fuentes** — grid de video sources con preview + creación interactiva de ROIs + alert rules
- **Panel / Dashboard** — 11 métricas agregadas + breakdown de alerts por severidad + timeline cronológica
- **Trabajos / Historial** — lista de análisis con duración, total entities, total events, status, Ver Detalle / Re-ejecutar
- **Logs** — recursos del sistema (CPU, RAM, disco, threads) + eventos problemáticos (sessions failed, overcapacity, dwell_exceeded)
- **Chatbot** — asistente conversacional (Cohere API) que responde preguntas sobre cualquier reporte
- **Documentación in-app** — vista con `<details>` sobre cada componente del stack

### Output
- 🎬 **Video anotado** en H.264 (`avc1`) con bounding boxes, IDs, ROI overlays y panel de stats
- 📄 **Reporte HTML** por análisis — métricas por zona, totales, dwell
- 📥 **Servidor de video** via `/api/video/<filename>` con soporte de `Range` para streaming

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|---|---|
| ML | `ultralytics` (YOLOv11n) + ByteTrack + `lap` |
| Video | `opencv-python-headless` + `yt-dlp` + `imageio-ffmpeg` (bundled) |
| Backend | Python 3.12, `http.server.ThreadingHTTPServer` + `BaseHTTPRequestHandler` |
| Base de datos | PostgreSQL 14+ (probado con Neon serverless) — `psycopg2-binary` |
| Frontend | Vanilla JS SPA (en `src/utils/pages.py`) con Tailwind CDN, sin framework |
| Build | `uv` + multi-stage Docker |
| Observabilidad | Dozzle (logs UI en `localhost:8080`) |
| Procesos | `ThreadedHTTPServer` para requests concurrentes + `ThreadedConnectionPool` (psycopg2) para DB |

---

## 🐳 Quick start con Docker

### Prerrequisitos
- Docker + Docker Compose
- Una base de datos PostgreSQL (recomendado: [Neon](https://neon.tech), free tier)

### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/FacundoMajda/ML-GOTECHY-G7-MAJDA-ORTEGA.git
   cd ML-GOTECHY-G7-MAJDA-ORTEGA
   ```

2. **Crear `.env`** con la URL de tu base de datos
   ```bash
   cp .env.example .env
   # Editar .env y poner tu NEON_DB_URL
   ```
   ```env
   NEON_DB_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require
   ```

3. **Inicializar el schema** (idempotente)
   ```bash
   docker compose run --rm app python -c "import psycopg2, os; conn = psycopg2.connect(os.environ['NEON_DB_URL']); cur = conn.cursor(); cur.execute(open('schema.sql').read()); conn.commit(); print('Schema OK')"
   ```

4. **Levantar el stack**
   ```bash
   docker compose up -d --build
   ```

5. **Bind mount de uploads**: el stack monta `./uploads:/app/uploads`. Videos preexistentes pueden copiarse a `./uploads/` y referenciarse con `source_uri: 'uploads/<file>'`.

6. **Abrir en el navegador**
   - App: <http://localhost:8000>
   - Dozzle (logs UI): <http://localhost:8080>

---

## 💻 Quick start local con uv

```bash
git clone https://github.com/FacundoMajda/ML-GOTECHY-G7-MAJDA-ORTEGA.git
cd ML-GOTECHY-G7-MAJDA-ORTEGA
uv sync
export NEON_DB_URL=postgresql://user:password@host/db?sslmode=require
psql "$NEON_DB_URL" < schema.sql
uv run python -m src.app
```

App en <http://localhost:8000>.

---

## ⚙️ Configuración

Variables de entorno (todas se leen de `.env` o del entorno del shell):

| Variable | Default | Descripción |
|---|---|---|
| `NEON_DB_URL` | (required) | Connection string a PostgreSQL. La app falla rápido si no está definida. |
| `HOST` | `0.0.0.0` | Bind address del HTTP server |
| `YOLO_MODEL_PATH` | `src/inference/yolo11n.pt` | Ruta al modelo YOLO (debe existir o falla al instanciar) |
| `OUTPUT_DIR` | `outputs` | Carpeta para videos anotados |
| `REPORTS_DIR` | `reports` | Carpeta para reportes HTML |
| `UPLOADS_DIR` | `uploads` | Carpeta para archivos subidos vía `/api/uploads` |

**Cambiar el modelo YOLO**: el default es `yolo11n.pt` (nano, ~5MB, más rápido). Para mejor precisión usar `yolo11s/m/l/x.pt` (más pesados, más lentos). Se cambia con la env var `YOLO_MODEL_PATH` o reemplazando el archivo en `src/inference/`.

---

## 📁 Estructura del proyecto

```
ML-GOTECHY-G7-MAJDA-ORTEGA/
├── src/
│   ├── app.py                          # Entry point (python -m src.app)
│   ├── config/
│   │   └── settings.py                 # Env loader (NEON_DB_URL, paths)
│   ├── controllers/
│   │   └── app_handler.py              # HTTP router + 16 endpoints (1087 líneas)
│   ├── services/
│   │   ├── analytics_service.py        # AnalyticsService + CounterEngine (YOLO + ROI)
│   │   ├── metrics_service.py          # MetricsService (11 queries para dashboard)
│   │   ├── rule_evaluator.py           # Evalúa alert_rules por snapshot, dispara zone_events
│   │   ├── report_service.py           # Genera reporte HTML estático por análisis
│   │   └── cohere_service.py           # Chatbot: Cohere API client
│   ├── providers/                      # FrameProvider ABC + 4 implementaciones
│   │   ├── base.py
│   │   ├── factory.py                  # VideoSourceFactory.create() por source_type
│   │   ├── local_file.py
│   │   ├── youtube_video.py            # VOD via yt-dlp
│   │   ├── youtube_live.py             # Live con auto-reconnect
│   │   ├── rtsp.py                     # RTSP con auto-reconnect
│   │   └── youtube_utils.py            # yt-dlp wrapper + format candidates
│   ├── repositories/                   # 9 repos (psycopg2 directos, sin ORM)
│   │   ├── db.py                       # ThreadedConnectionPool (min=2, max=20)
│   │   ├── video_source_repo.py
│   │   ├── roi_repo.py
│   │   ├── session_repo.py
│   │   ├── tracked_entity_repo.py      # batch INSERT con ON CONFLICT
│   │   ├── occupancy_snapshot_repo.py  # batch INSERT con ON CONFLICT DO NOTHING
│   │   ├── zone_event_repo.py          # batch INSERT (metadata es JSONB)
│   │   ├── metric_snapshot_repo.py
│   │   ├── alert_rule_repo.py          # alert_rule CRUD
│   │   └── class_catalog_repo.py       # COCO class catalog
│   ├── models/
│   │   ├── contracts.py                # Dataclasses (ROIConfig, VideoSourceConfig, etc.)
│   │   └── enums.py                    # SourceType, EventType, TrackingClass, TimestampMode
│   ├── utils/
│   │   ├── pages.py                    # SPA completa (HTML + JS, ~2500 líneas)
│   │   ├── components.py
│   │   └── html_utils.py
│   └── inference/
│       └── yolo11n.pt                  # Pesos YOLO (commiteados)
├── notebooks/
│   └── ml_gotechy.ipynb                # Versión histórica del proyecto (notebook)
├── scripts/
│   └── init_db.sql                     # Schema idempotente (alternativa a schema.sql)
├── schema.sql                          # Dump completo del schema
├── docker-compose.yml                  # app + dozzle
├── Dockerfile                          # Multi-stage build con uv + CPU torch
├── pyproject.toml                      # Dependencias (uv-managed)
├── uv.lock
├── .env.example
└── README.md
```

---

## 📡 API Reference

### Sources

| Method | Path | Descripción |
|---|---|---|
| `GET` | `/api/sources` | Lista todas las video sources con sus ROIs |
| `POST` | `/api/sources` | Crea una source (`name`, `source_type`, `source_uri`) |
| `DELETE` | `/api/sources/<id>` | Elimina una source (cascade a ROIs y sessions) |
| `GET` | `/api/sources/<id>/preview` | JPEG del primer frame con ROIs dibujadas (resized a 640px) |
| `POST` | `/api/uploads` | Upload de archivo local (multipart/form-data, field `file`) |

### ROIs

| Method | Path | Descripción |
|---|---|---|
| `POST` | `/api/sources/<id>/rois` | Crea un ROI poligonal (`name`, `polygon: [[x,y], ...]`) |
| `PUT` | `/api/rois/<id>/config` | Actualiza flags: `detect_entry`, `detect_exit`, `detect_occupancy`, `detect_dwell`, `alerts` |
| `DELETE` | `/api/rois/<id>` | Elimina un ROI |

### Alert Rules

| Method | Path | Descripción |
|---|---|---|
| `GET` | `/api/rois/<id>/alert-rules` | Lista alert rules activas (e inactivas) para un ROI |
| `POST` | `/api/rois/<id>/alert-rules` | Crea rule: `name`, `metric`, `operator`, `threshold`, `event_type`, `severity`, `class_id?`, `time_from?`, `time_to?` |
| `PUT` | `/api/alert-rules/<id>` | Update parcial de cualquier campo |
| `POST` | `/api/alert-rules/<id>/toggle` | Toggle `active` (enable/disable) |
| `DELETE` | `/api/alert-rules/<id>` | Elimina rule |
| `GET` | `/api/rois/<id>/metrics/summary` | Mini-stats del último session (entries, exits, max_occupancy, top_rules) |

### Analysis

| Method | Path | Descripción |
|---|---|---|
| `POST` | `/process` | Inicia análisis en background thread. Body JSON: `video_source_id`, `tracking_classes`, `frame_skip`, `max_seconds`, `output_video` |
| `GET` | `/api/job/status` | Status del job en curso: `running`, `progress`, `frames_done`, `total_frames`, `seconds_done`, `message`, `error` |
| `GET` | `/api/sessions` | Lista de sesiones de análisis con métricas agregadas |
| `GET` | `/api/sessions/<id>/report` | Reporte HTML estático del análisis |
| `GET` | `/api/sessions/<id>/tracks` | Tracks de la sesión (entidades detectadas con clase, frame first/last seen) |
| `GET` | `/api/analyses` | Lista limpia de análisis (para la tab Trabajos) |
| `GET` | `/api/analyses/<id>` | Detalle: `metrics`, `zone_events` (con `severity`/`rule_name`/`value`/`rule_id`), `class_summary`, `alert_rules_by_roi` (con flag `triggered`) |

### System

| Method | Path | Descripción |
|---|---|---|
| `GET` | `/api/dashboard` | Métricas agregadas (11 fields: totales, top ROIs, distribuciones) |
| `GET` | `/api/analytics/occupancy-trends` | Tendencias de ocupación por hora (últimas 24h) |
| `GET` | `/api/analytics/dwell-times` | Dwell time promedio y máximo por ROI |
| `GET` | `/api/logs/data` | Recursos del sistema (CPU, RAM, disco, threads) + eventos problemáticos |
| `GET` | `/api/video/<filename>` | Sirve video anotado con soporte de `Range` (streaming) |

---

## 🔄 Pipeline de análisis

Cuando se hace `POST /process`, la app ejecuta el siguiente flujo en un thread daemon:

```
1. _repo.get_by_id() + _roi_repo.list_by_source()  ─→ 2 queries sync
2. VideoSourceFactory.create(config)                ─→ 1 provider instance
3. AnalyticsService.process() [loop]
   ├─ provider.next_frame()                          ─→ block en cv2.VideoCapture.read()
   ├─ model.track(frame, persist=True,
   │              classes=track_classes, conf=0.3,
   │              tracker="bytetrack.yaml")
   ├─ CounterEngine.update() por cada detección
   │    ├─ cv2.pointPolygonTest() para entry/exit
   │    ├─ segments_intersect() para cruces border
   │    └─ si frame % 30 == 0 → OccupancySnapshot
   ├─ writer.write(_annotate_frame())                ─→ avc1 (H.264) con fallback mp4v
   └─ progress_callback(frames_done, total, ...)     ─→ actualiza _job_progress in-memory
4. Re-encode FMP4 → H.264 via imageio_ffmpeg (opcional)
5. _persist_session() [en ThreadPoolExecutor(3)]
   ├─ entity_repo.save_all()     ─→ batch INSERT con ON CONFLICT (session_id, track_id)
   ├─ snapshot_repo.create_batch() ─→ batch INSERT con ON CONFLICT (session_id, roi_id, frame_number)
   ├─ zone_repo.create_batch()   ─→ batch INSERT (entry/exit + alert-triggered con metadata JSONB)
   └─ RuleEvaluator.evaluate() en cada snapshot ─→ evalúa alert_rules activas; dispara zone_events con event_type=dwell_exceeded/overcapacity + metadata={severity, rule_name, value}
6. MetricsService.compute(session_id)               ─→ deriva metric_snapshot por ROI
7. generate_report_html(session_id)                 ─→ escribe reports/<id>.html
8. _job_progress["running"] = False                 ─→ UI cierra el modal de progreso
```

---

## 🗄️ Schema de la base de datos

8 tablas PostgreSQL:

| Tabla | Propósito |
|---|---|
| `video_source` | Fuentes de video configuradas (file, youtube_vod, youtube_live, rtsp) |
| `roi` | Regiones de Interés poligonales con flags de detección (entry, exit, occupancy, dwell) |
| `alert_rule` | Reglas de alertas por ROI. Columnas: `metric`, `operator`, `threshold`, `threshold2`, `event_type` (OccupancyHigh/DwellExceeded/...), `severity` (info/warning/critical), `class_id?`, `time_from?`, `time_to?`, `active` |
| `detection_session` | Una ejecución del pipeline — `started_at`, `ended_at`, `status`, `output_video_path` |
| `tracked_entity` | UNIQUE `(session_id, track_id)` — IDs persistentes de ByteTrack |
| `roi_occupancy_snapshot` | UNIQUE `(session_id, roi_id, frame_number)` — estado por ROI cada 30 frames |
| `zone_event` | Eventos puntuales: `entry`, `exit`, `overcapacity`, `dwell_exceeded`. Columna `metadata` JSONB con `severity`, `rule_name`, `value`, `event_type`, `threshold`, `operator` para eventos disparados por alert rules |
| `metric_snapshot` | Derivado: entries, exits, max_occupancy, avg_dwell por ROI por sesión |

**Inicializar**: `psql $NEON_DB_URL < schema.sql` (o `scripts/init_db.sql` que es idempotente).

---

## 👥 Autores

| Nombre | GitHub |
|---|---|
| Facundo Majda | [@FacundoMajda](https://github.com/FacundoMajda) |
| Marcelo Ortega | [@ortegamarcelodev](https://github.com/ortegamarcelodev) |

---

<div align="center">

**GOTECHY · Grupo 7 · 2026**

*Proyecto de Machine Learning y Visión por Computadora*

</div>
