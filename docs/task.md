# Task — Argus Vision: Object Analytics Platform

> **Status**: Phase 0–7 done. All features implemented.
> **Last updated**: 2026-06-23
> **Scope**: Multi-class observation + rule engine + UI completa.

---

## Resumen ejecutivo

Hoy Argus mide `person` en zonas poligonales. La evolución natural es:

```text
People Counter
↓
Object Analytics
↓
Spatial Analytics
↓
Rule-Based Observation Platform
```

Pieza central: **ROI + [clases permitidas] + [condición temporal/cuantitativa] → evento → métrica → alerta**

Esto abre retail, parking, logística, seguridad, oficinas y transporte con el mismo motor.

---

## Phase 0 — ✅ DONE (este turno)

- ✅ DB migrada: `object_class` en `tracked_entity`, `zone_event`, `metric_snapshot`
- ✅ `roi.observed_classes` JSONB con default `["person"]`
- ✅ `roi_event_rule` con `object_class`, `window_seconds`, `enabled` + CHECK constraint con 14 event_types
- ✅ `roi_occupancy_snapshot.object_class_counts` JSONB
- ✅ `metric_snapshot.median_dwell_seconds`, `unique_objects`
- ✅ UNIQUE `(session_id, roi_id, object_class)` en metric_snapshot
- ✅ `CounterEngine` pasa `object_class` a records
- ✅ `_YOLO_ID_TO_CLASS` mapping con 25 clases COCO más relevantes
- ✅ Repos actualizados (batch INSERTs incluyen object_class)
- ✅ `MetricsService.compute()` agrega por (roi, class)
- ✅ Test end-to-end OK: 6 persons → `object_class_counts: {"person": 6}`
- ✅ `unique_objects=11`, `median_dwell_seconds=0.00` en metric_snapshot
- ⚠️ **PENDIENTE**: `schema.sql` y `scripts/init_db.sql` parcialmente actualizados — necesitan catch-up

Migración aplicada: `scripts/migration_002_object_classes.sql`

---

## Phase 1 — ✅ DONE (catalogo de clases COCO)

**Migración nueva** `scripts/migration_003_object_class_catalog.sql`:

```sql
CREATE TABLE IF NOT EXISTS object_class_catalog (
    id          INTEGER PRIMARY KEY,  -- COCO class_id (0-79)
    name        TEXT NOT NULL UNIQUE, -- "person", "car", etc.
    category    TEXT NOT NULL,        -- "person" | "vehicle" | "animal" | "electronics" | "furniture" | "food" | "accessory" | "kitchen" | "outdoor" | "misc"
    is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

-- Seed 80 clases COCO agrupadas por categoría
INSERT INTO object_class_catalog (id, name, category) VALUES
  (0, 'person', 'person'),
  (1, 'bicycle', 'vehicle'),
  (2, 'car', 'vehicle'),
  (3, 'motorcycle', 'vehicle'),
  (4, 'airplane', 'vehicle'),
  (5, 'bus', 'vehicle'),
  (6, 'train', 'vehicle'),
  (7, 'truck', 'vehicle'),
  (8, 'boat', 'vehicle'),
  (9, 'traffic light', 'urban'),
  (10, 'fire hydrant', 'urban'),
  (11, 'stop sign', 'urban'),
  (12, 'parking meter', 'urban'),
  (13, 'bench', 'urban'),
  (14, 'bird', 'animal'),
  (15, 'cat', 'animal'),
  (16, 'dog', 'animal'),
  (17, 'horse', 'animal'),
  (18, 'sheep', 'animal'),
  (19, 'cow', 'animal'),
  (20, 'elephant', 'animal'),
  (21, 'bear', 'animal'),
  (22, 'zebra', 'animal'),
  (23, 'giraffe', 'animal'),
  (24, 'backpack', 'accessory'),
  (25, 'umbrella', 'accessory'),
  (26, 'handbag', 'accessory'),
  (27, 'tie', 'accessory'),
  (28, 'suitcase', 'accessory'),
  (29, 'frisbee', 'outdoor'),
  (30, 'skis', 'outdoor'),
  (31, 'snowboard', 'outdoor'),
  (32, 'sports ball', 'outdoor'),
  (33, 'kite', 'outdoor'),
  (34, 'baseball bat', 'outdoor'),
  (35, 'baseball glove', 'outdoor'),
  (36, 'skateboard', 'outdoor'),
  (37, 'surfboard', 'outdoor'),
  (38, 'tennis racket', 'outdoor'),
  (39, 'bottle', 'kitchen'),
  (40, 'wine glass', 'kitchen'),
  (41, 'cup', 'kitchen'),
  (42, 'fork', 'kitchen'),
  (43, 'knife', 'kitchen'),
  (44, 'spoon', 'kitchen'),
  (45, 'bowl', 'kitchen'),
  (46, 'banana', 'food'),
  (47, 'apple', 'food'),
  (48, 'sandwich', 'food'),
  (49, 'orange', 'food'),
  (50, 'broccoli', 'food'),
  (51, 'carrot', 'food'),
  (52, 'hot dog', 'food'),
  (53, 'pizza', 'food'),
  (54, 'donut', 'food'),
  (55, 'cake', 'food'),
  (56, 'chair', 'furniture'),
  (57, 'couch', 'furniture'),
  (58, 'potted plant', 'furniture'),
  (59, 'bed', 'furniture'),
  (60, 'dining table', 'furniture'),
  (61, 'toilet', 'furniture'),
  (62, 'tv', 'electronics'),
  (63, 'laptop', 'electronics'),
  (64, 'mouse', 'electronics'),
  (65, 'remote', 'electronics'),
  (66, 'keyboard', 'electronics'),
  (67, 'cell phone', 'electronics'),
  (68, 'microwave', 'appliance'),
  (69, 'oven', 'appliance'),
  (70, 'toaster', 'appliance'),
  (71, 'sink', 'appliance'),
  (72, 'refrigerator', 'appliance'),
  (73, 'book', 'misc'),
  (74, 'clock', 'misc'),
  (75, 'vase', 'misc'),
  (76, 'scissors', 'misc'),
  (77, 'teddy bear', 'misc'),
  (78, 'hair drier', 'misc'),
  (79, 'toothbrush', 'misc')
ON CONFLICT (id) DO NOTHING;
```

**Nuevo repo** `src/repositories/class_catalog_repo.py`:

```python
class ObjectClassCatalogRepository:
    def list_all(self, only_active: bool = True) -> list[dict]
    def list_by_category(self, category: str) -> list[dict]
    def get(self, class_id: int) -> dict | None
    def list_grouped_by_category(self) -> dict[str, list[dict]]  # para la UI
    def get_id_for_name(self, name: str) -> int | None
```

**Endpoints nuevos**:
- `GET /api/classes` → lista completa de 80 clases con `category`
- `GET /api/classes/grouped` → `{ "person": [{id:0, name:"person"}], "vehicle": [...] }`

---

## Phase 2 — ✅ DONE (UI de catálogo de clases observado por ROI)

### Drawer → nueva tab "Clases" + integrar al savePolygon

**Cambio en `savePolygon()`**: al crear una ROI nueva, el form pide nombre + clases observadas.

**Cambio en `renderAreasTab()`**: cada ROI existente muestra sus clases observadas como chips editables (toggle on/off).

**Form de creación** (debajo del nombre de la ROI):

```html
<label>Clases a observar:</label>
<div class="grid grid-cols-2 gap-2">
  <label><input type="checkbox" data-class="person" checked> Person</label>
  <label><input type="checkbox" data-class="car"> Car</label>
  <label><input type="checkbox" data-class="truck"> Truck</label>
  <!-- resto agrupadas por categoría -->
</div>
```

**Endpoint nuevo**:
- `PUT /api/rois/<id>/observed-classes` body: `{"classes": ["person", "car", ...]}`
  - Persiste en `roi.observed_classes` (JSONB)

**Lógica al correr análisis** (en `AnalyticsService.process()`): filtra `track_classes` por la intersección entre lo que la UI pidió y lo que cada ROI observa. Si una ROI no observa `car`, los autos que pasen por ella se trackean pero no se cuentan como `entry` (o no se procesan).

**Decisión KISS**: para no romper nada, dejo `track_classes` como un global del analysis (lo que YOLO detecta) y `roi.observed_classes` como un filtro a nivel de conteo: el track se persiste siempre (con su `object_class`), pero los `entry`/`exit` events solo se emiten para `roi.observed_classes`. Esto NO agrega queries, solo un `if` extra en CounterEngine.

---

## Phase 3 — ✅ DONE (Rule engine configurable)

### Nueva tabla `alert_rule` (separada de `roi_event_rule`)

`roi_event_rule` queda para reglas de generación de eventos. `alert_rule` queda para reglas que disparan alertas.

```sql
CREATE TABLE alert_rule (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roi_id          UUID NOT NULL REFERENCES roi(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    -- CONDICIÓN
    class_id        INTEGER,  -- NULL = cualquier clase observada en la ROI
    metric          TEXT NOT NULL,  -- 'count' | 'dwell_seconds' | 'occupancy'
    operator        TEXT NOT NULL,  -- '>' | '<' | '>=' | '<=' | '==' | 'between'
    threshold       NUMERIC,
    threshold2      NUMERIC,  -- solo para 'between'
    -- VENTANA TEMPORAL
    time_from       TIME,  -- NULL = siempre
    time_to         TIME,
    -- ACCIÓN
    event_type      TEXT NOT NULL,  -- 'OccupancyHigh' | 'DwellExceeded' | ...
    severity        TEXT NOT NULL DEFAULT 'warning',  -- 'info'|'warning'|'critical'
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT alert_rule_metric_check CHECK (metric IN ('count','dwell_seconds','occupancy')),
    CONSTRAINT alert_rule_operator_check CHECK (operator IN ('>','<','>=','<=','==','between')),
    CONSTRAINT alert_rule_severity_check CHECK (severity IN ('info','warning','critical'))
);
```

**Nuevo repo** `src/repositories/alert_rule_repo.py`:

```python
class AlertRuleRepository:
    def list_by_roi(self, roi_id) -> list[dict]
    def list_active(self, roi_id=None) -> list[dict]  # para el evaluator
    def create(self, ...) -> UUID
    def update(self, rule_id, ...)
    def delete(self, rule_id)
    def toggle_active(self, rule_id, active: bool)
```

**Endpoints nuevos**:
- `GET /api/rois/<id>/alert-rules` → lista de reglas de la ROI
- `POST /api/rois/<id>/alert-rules` → crear regla
- `PUT /api/alert-rules/<id>` → editar
- `DELETE /api/alert-rules/<id>`
- `POST /api/alert-rules/<id>/toggle` → activar/desactivar

**Schema del body de creación**:
```json
{
  "name": "Parking lleno",
  "class_id": 2,
  "metric": "count",
  "operator": ">",
  "threshold": 50,
  "threshold2": null,
  "time_from": null,
  "time_to": null,
  "event_type": "OccupancyHigh",
  "severity": "warning"
}
```

---

## Phase 4 — ✅ DONE (UI de Reglas por ROI)

### Drawer → nueva tab "Reglas"

**Vista de lista** (`renderRulesTab()`):

```html
<div id="rules-list">
  <div class="roi-rules-block">
    <h4>Parking</h4>
    <div class="rule-card">
      <span class="severity-badge">⚠ warning</span>
      <span class="rule-name">Car count > 50</span>
      <span class="rule-detail">SI count(car) > 50 ENTONCES OccupancyHigh</span>
      <button>edit</button> <button>delete</button> <toggle active>
    </div>
    <button>+ Agregar regla</button>
  </div>
</div>
```

**Form de crear/editar** (modal in-place o expand):

```html
<form>
  <input placeholder="Nombre de la regla" />
  <select>ROI (auto-llenado)</select>
  <label>Clase a observar</label>
  <select data-catalog="class">
    <option value="">Todas las observadas</option>
    <option value="0">Person</option>
    <option value="2">Car</option>
    ...
  </select>
  <label>Métrica</label>
  <select><option>count</option><option>occupancy</option><option>dwell_seconds</option></select>
  <label>Operador</label>
  <select><option>></option><option><</option>...</select>
  <label>Threshold</label>
  <input type="number" />
  <label>Severidad</label>
  <select><option>info</option><option>warning</option><option>critical</option></select>
  <label>Evento a generar</label>
  <select><option>OccupancyHigh</option><option>DwellExceeded</option>...</select>
  <button>Cancelar</button> <button>Guardar</button>
</form>
```

---

## Phase 5 — ✅ DONE (Rule Evaluator)

**Nuevo archivo** `src/services/rule_evaluator.py`:

```python
class RuleEvaluator:
    """Evalúa alert_rule contra snapshots/zone_events en cada tick."""
    
    def __init__(self, session_id, roi_id, rules: list[dict]):
        self.session_id = session_id
        self.roi_id = roi_id
        self.rules = rules
        self._state: dict[str, dict] = {}
    
    def evaluate(self, snapshot, class_counts) -> list[ZoneEventRecord]:
        """Devuelve eventos generados por reglas que se cumplen."""
        new_events = []
        for rule in self.rules:
            if not rule['active']:
                continue
            if not self._in_time_window(rule):
                continue
            value = self._get_metric_value(rule, snapshot, class_counts)
            if self._check_condition(value, rule):
                new_events.append(ZoneEventRecord(
                    roi_id=self.roi_id,
                    event_type=EventType(rule['event_type']),
                    object_class=_resolve_class_name(rule.get('class_id')),
                    metadata={
                        'rule_id': str(rule['id']),
                        'rule_name': rule['name'],
                        'value': value,
                        'threshold': rule['threshold'],
                        'severity': rule['severity'],
                    }
                ))
        return new_events
    
    def _check_condition(self, value, rule) -> bool:
        op = rule['operator']
        t1 = rule['threshold']
        t2 = rule.get('threshold2')
        if op == '>': return value > t1
        if op == '<': return value < t1
        if op == '>=': return value >= t1
        if op == '<=': return value <= t1
        if op == '==': return value == t1
        if op == 'between': return t1 <= value <= t2
        return False
```

**Integración en CounterEngine**: después del snapshot periódico (cada 30 frames), llamar `RuleEvaluator.evaluate(snapshot, class_counts)` y mergear sus eventos al array `self.events` antes de `_persist_session`.

**Migración de reglas existentes**: copiar las 4 reglas actuales de `roi_event_rule` (entry/exit/overcapacity/dwell_exceeded) a la nueva tabla `alert_rule` con `metric='count'|'dwell_seconds'`, etc.

---

## Phase 6 — ✅ DONE (Dashboard con alertas + distribución por clase)

**Cambio en `get_dashboard()`** (metrics_service.py):

```python
def get_dashboard(self) -> dict:
    return {
        # ── lo que ya hay ──
        "total_entries": ...,
        "total_exits": ...,
        "session_count": ...,
        "total_entities": ...,
        "total_sources": ...,
        "sources_with_rois": ...,
        "total_hours_analyzed": ...,
        "avg_occupancy": ...,
        "avg_dwell_seconds": ...,
        "completed_analyses": ...,
        "failed_analyses": ...,
        "total_analyses": ...,
        "top_rois": ...,
        "events_by_source": ...,
        "recent_sessions": ...,
        "hourly_distribution": ...,
        # ── NUEVO ──
        "active_alerts": self._get_active_alerts(),
        "alerts_by_severity": self._get_alerts_by_severity(),
        "class_distribution": self._get_class_distribution(),
        "alerts_timeline": self._get_alerts_timeline(),
    }

def _get_active_alerts(self) -> int:
    return execute_query("""
        SELECT COUNT(*) FROM zone_event
        WHERE metadata IS NOT NULL
          AND metadata::jsonb ? 'rule_id'
          AND occurred_at >= NOW() - INTERVAL '24 hours'
    """, fetch='one')[0]
```

**UI Dashboard** (en `renderDashboard()`):
- Card: "Active Alerts" (cantidad 24h, color por severity)
- Card: "Class Distribution" (top 5 clases con %)
- Sección: "Alerts Timeline" (últimas 20 alertas con icono + severidad)

---

## Phase 7 — ✅ DONE (Reporte con breakdown por clase)

**Cambio en `generate_report_html()`** (report_service.py):

```python
def generate_report_html(session_id: str) -> str:
    # ... existing code ...
    
    class_breakdown = execute_query("""
        SELECT r.name AS roi_name, ms.object_class, 
               ms.entries, ms.exits, ms.max_occupancy, 
               ms.avg_dwell_seconds, ms.unique_objects
        FROM metric_snapshot ms
        JOIN roi r ON r.id = ms.roi_id
        WHERE ms.session_id = %s
        ORDER BY r.name, ms.entries DESC
    """, (session_id,), fetch='all')
    
    return f"""...
    <h2>Distribución por Clase</h2>
    <table>
      <tr><th>Zona</th><th>Clase</th><th>Entries</th><th>Exits</th><th>Max</th><th>Dwell Avg</th><th>Unique</th></tr>
      {rows_html}
    </table>..."""
```

---

## Phase 8 — ✅ DONE (Settings Tab mejorada)

**Cambio en `renderSettingsTab()`**: la lista de tracking classes se hidrata del catálogo:

```javascript
async function renderSettingsTab() {
  const src = getSource(state.selectedSourceId);
  if (!src) return;
  const catalog = await fetchJSON('/api/classes/grouped');
  const settings = getSourceSettings(src.id);
  
  let html = '<div class="mb-6"><h3>TRACKING CLASSES</h3>';
  for (const [category, classes] of Object.entries(catalog.data)) {
    html += `<div class="mb-3"><h4>${category.toUpperCase()}</h4>`;
    for (const cls of classes) {
      html += `<label><input type="checkbox" class="settings-chk" 
                data-class="${cls.name}" 
                ${(settings.tracking_classes||[]).includes(cls.name)?'checked':''}> 
                ${cls.name}</label>`;
    }
    html += '</div>';
  }
  // ... rest of settings
}
```

---

## Archivos a tocar (resumen)

| Archivo | Acción | Scope |
|---|---|---|
| `scripts/migration_003_object_class_catalog.sql` | NEW | Seed 80 clases COCO |
| `scripts/migration_004_alert_rule.sql` | NEW | Tabla `alert_rule` |
| `src/repositories/class_catalog_repo.py` | NEW | Repo catálogo |
| `src/repositories/alert_rule_repo.py` | NEW | Repo alert rules |
| `src/services/rule_evaluator.py` | NEW | Motor de evaluación |
| `src/controllers/app_handler.py` | EDIT | 4-5 endpoints + integración rule_evaluator |
| `src/services/analytics_service.py` | EDIT | Instanciar RuleEvaluator + merge events |
| `src/services/metrics_service.py` | EDIT | Dashboard con alertas + class distribution |
| `src/services/report_service.py` | EDIT | Reporte con breakdown por clase |
| `src/repositories/roi_repo.py` | EDIT | Soporte `observed_classes` |
| `src/repositories/zone_event_repo.py` | EDIT | Query de active alerts |
| `src/utils/pages.py` | EDIT | UI completa (drawer, dashboard, report) |
| `schema.sql` | EDIT | Catch-up con migration 003 + 004 |
| `scripts/init_db.sql` | EDIT | Catch-up con migration 003 + 004 |

## NO toco (lógica de análisis intocada)

- `CounterEngine.update()` — la lógica de detección/intersección se mantiene
- `YOLO` — la llamada a `model.track()` se mantiene
- `ByteTrack` — el tracker se mantiene
- `providers/*` — la extracción de frames se mantiene
- `ThreadingHTTPServer` — sigue siendo el HTTP server

## Commits planeados

1. `feat: object_class_catalog + 80 COCO classes seed + API endpoints`
2. `feat: rule_evaluator + alert_rule table + rules engine integrated in CounterEngine`
3. `feat: UI for ROI observed-classes + rule builder + dashboard alerts + class distribution`
4. `feat: report with per-class breakdown`

## Riesgos y tradeoffs

- **Performance**: rule_evaluator corre cada 30 frames, N reglas por ROI. Si hay 100 reglas, se ejecuta 100 veces. Mitigación: cachear `active_rules` por ROI al inicio del analysis.
- **Backward compat**: análisis viejos con `object_class='person'` siguen funcionando. La UI nueva muestra ambas cosas.
- **YOLO no detecta 80 clases con misma confianza**: yolo11n detecta solo las 80 COCO con conf ≥ 0.3, no se puede elegir threshold por clase. Documentado.
- **Settings tab cambia tracking_classes**: hoy el usuario puede elegir 4. Con el catálogo nuevo son 80. Decisión: mostrar agrupadas por categoría.

## Lo que NO está en el plan (fuera de scope)

- Fine-tuning de YOLO para clases custom (cascos, EPP) — requiere entrenar
- Heatmap visualization — feature futuro
- Auth/multi-user — fuera de scope
- Real-time streaming UI (WebSocket) — fuera de scope, polling sigue siendo el mecanismo

---

## Casos de uso objetivo

| Vertical | Clases | Evento clave | Valor |
|---|---|---|---|
| Retail | person | DwellExceeded, OccupancyHigh | Conversión, layout |
| Parking | car, truck, bus | ObjectCountExceeded, DwellExceeded | Ocupación, compliance |
| Warehouse | person, truck | ObjectAppeared + horario | Seguridad nocturna |
| Oficinas | person, laptop | ObjectDisappeared, ZoneInactive | Aforo, activos |
| Transporte | person, bicycle | DensityHigh | Planificación urbana |
| Veterinaria | dog, cat | ClassRatioExceeded | Gestión de sala |

**Patrón que emerge**: `ROI + [clases] + [condición temporal/cuantitativa] → evento → métrica → alerta`

---

## Fuentes de video para demos

- **YouTube VOD** (ya soportado): queries tipo "parking lot cctv", "shopping mall entrance", "traffic intersection cctv"
- **VIRAT Video Dataset** (viratdata.org): escenas outdoor reales, cámara fija
- **Mall Dataset**: shopping mall top-down, ~2000 frames
- **Pexels/Pixabay**: stock HD CC0 sin marca de agua

---

## Resumen

✅ **Phase 0-7 completadas**
- **Phase 0**: DB migration, object_class en tablas, observed_classes
- **Phase 1**: Object class catalog (80 COCO classes seeded, repo, endpoints)
- **Phase 2**: ROI observed_classes (endpoint, CounterEngine filtering)
- **Phase 3**: Alert rule backend (table, repo, 5 endpoints)
- **Phase 4**: UI for rules (rules tab in drawer, CRUD, form)
- **Phase 5**: Rule evaluator (integrated in CounterEngine, tested)
- **Phase 6**: Dashboard with alerts + class distribution (metrics_service + pages)
- **Phase 7**: Report with per-class breakdown (report_service)

**Todos los archivos críticos actualizados:**
- `src/controllers/app_handler.py` (alert rules, JSON error handling, toggle fix)
- `src/services/rule_evaluator.py` (rule evaluation engine)
- `src/services/analytics_service.py` (RuleEvaluator integration)
- `src/services/metrics_service.py` (dashboard with alerts)
- `src/services/report_service.py` (class breakdown report)
- `src/repositories/class_catalog_repo.py` (new catalog repo)
- `src/repositories/alert_rule_repo.py` (new alert rules repo)
- `src/repositories/roi_repo.py` (observed_classes support)
- `src/utils/pages.py` (rules tab UI, dashboard, report)
- `src/providers/youtube_utils.py` (URL caching)
- `scripts/migration_003_object_class_catalog.sql` (80 COCO classes)
- `scripts/migration_004_alert_rule.sql` (alert_rule table)
- `schema.sql` + `scripts/init_db.sql` (catch-up)

**Features implemented:**
- Multi-class object tracking with 80 COCO classes
- Per-ROI observed classes selection
- Composable alert rules with temporal windows
- Real-time alert evaluation during analysis
- Dashboard with alerts + class distribution
- Detailed per-class breakdown reports
- YouTube URL caching for performance
- Debounced API calls to reduce load

**Ready for production!** 🚀