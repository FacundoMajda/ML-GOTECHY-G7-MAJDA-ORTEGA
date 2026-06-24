# Argus Vision — UI/UX Overhaul Plan

> **Status**: Plan aprobado — listo para ejecución
> **Created**: 2026-06-23
> **Scope**: 100% capa de presentación — aprovecha toda la arquitectura existente (DB, Repos, Services, Controllers)

---

## Resumen de Problemas

| Categoría | Problemas |
|-----------|-----------|
| **🔴 Bugs Críticos** | JSON inválido frontend, Toggle body mal serializado, HTTP 500→400, Race condition regla eliminada |
| **🟠 Performance** | Polling excesivo `/api/sources`, YouTube re-resolución sin cache, 1270x720 anómalo |
| **🟡 UX/Producto** | Clases hardcodeadas (4), tabs fragmentados (Areas/Settings/Reglas), "Run Analysis" subdimensionado, errores genéricos, sin perfiles de análisis |
| **🔵 Arquitectura** | Abstracción incorrecta: Entradas/Salidas vs Tracks→Clases→Eventos→Métricas→Reportes, reportes no multiclase, sin timeline, sin agregación por ROI/track |

---

## Plan de Acción — 4 Fases

---

### FASE 1 — Bugs Críticos + HTTP Correctos (1-2 días)

**Objetivo**: Estabilizar la comunicación frontend↔backend.

| Task | Archivo | Detalle |
|------|---------|---------|
| 1.1 `_read_json_body()` helper | `app_handler.py` | Centraliza `json.loads`, devuelve 400 en `JSONDecodeError` |
| 1.2 Toggle sin body | `app_handler.py` | `POST /toggle` opcional; si no hay body → toggle real (leer estado actual e invertir) |
| 1.3 Race condition UI | `pages.py` | Invalidar `rulesCache` tras DELETE; deshabilitar botones edit/toggle en card eliminada |
| 1.4 Debounce `fetchSources` | `pages.py` | Cache 5s + `force=true` solo tras mutaciones (create/delete) |
| 1.5 YouTube URL cache | `youtube_utils.py` | `_youtube_url_cache: Dict[str, (url, expiry)]` TTL 30min |
| 1.6 Validar resolución | `providers/*.py` | Log warning si `w % 16 != 0` or `h % 16 != 0` |

**Verificación**: `curl -X POST /api/rois/x/alert-rules -d 'bad json'` → 400; toggle sin body funciona; no más 500 por JSON.

---

### FASE 2 — Unificación de Tabs + Clases Multiclase (2-3 días)

**Objetivo**: 3 tabs cohesivos en el Drawer, usando todo lo que ya existe en DB/Repos.

#### 2.1 Drawer Tabs → `Preview | Zonas | Settings`

```html
<!-- Actual: 4 tabs -->
Preview | Areas | Settings | Reglas

<!-- Nuevo: 3 tabs -->
Preview | Zonas | Settings
```

| Tab | Contenido |
|-----|-----------|
| **Preview** | Video + canvas + Draw Area (sin cambios) |
| **Zonas** | **Unificado**: 1 card por ROI → Detección + Clases Observadas + Reglas |
| **Settings** | Source-level: Tracking Classes (catálogo completo 80) + Max Segundos + Perfiles |

#### 2.2 Card Unificada por ROI (en "Zonas")

```
┌────────────────────────────────────────────────────────────┐
│ 🟢 Parking                                          [🗑]   │
├────────────────────────────────────────────────────────────┤
│ 🔍 DETECCIÓN                                               │
│ [☑] Entrada  [☑] Salida  [☑] Ocupación  [☐] Permanencia  │
├────────────────────────────────────────────────────────────┤
│ 🏷️ CLASES OBSERVADAS (default = Source tracking classes)  │
│ [🔍 Filtrar...]                                            │
│ ┌─ PERSONA ────────────────────────────────────────────┐  │
│ │ ● person  ○ backpack  ○ handbag  ○ suitcase ...      │  │
│ ├─ VEHÍCULOS ──────────────────────────────────────────┤  │
│ │ ● car  ● truck  ○ bus  ○ motorcycle  ○ bicycle ...   │  │
│ └──────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────┤
│ ⚡ REGLAS (2)                                            │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ ⚠ warning  Car count > 50  → OccupancyHigh          │ │
│ │    🏷️ car  >  50                                    │ │
│ │    [✏️] [🗑] [☐]                                    │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │ ℹ info  Person dwell > 120s → DwellExceeded         │ │
│ │    🏷️ person  >  120                                │ │
│ │    [✏️] [🗑] [☑]                                    │ │
│ └──────────────────────────────────────────────────────┘ │
│ [+ Agregar regla]                                        │
└────────────────────────────────────────────────────────────┘
```

**Componentes reutilizables**:
- `renderClassSelector(categories, selectedIds, onChange)` — collapsible por categoría, chips coloreados
- `renderRuleCard(rule, onEdit, onDelete, onToggle)` — inline, usa colores de severidad
- `roiColors[roiIndex]` para borde/acento de cada card

#### 2.3 Settings Tab — Tracking Classes desde Catálogo

```javascript
// Actual: hardcoded ['person','car','bicycle','backpack']
// Nuevo: fetch('/api/classes/grouped') → grouped by category
```

UI:
- Search input global
- Categorías colapsables con "Seleccionar todo / Ninguno"
- Chips coloreados por categoría (reusar `roiColors` palette)
- Guardar en `sourceSettings[sourceId].tracking_classes`

#### 2.4 Perfiles de Análisis (opcional v1)

```javascript
const ANALYSIS_PROFILES = {
  retail:    { classes: ['person','backpack','handbag','suitcase'], metrics: ['entry','exit','dwell','occupancy'] },
  traffic:   { classes: ['car','truck','bus','motorcycle','bicycle'], metrics: ['occupancy','entry','exit','count'] },
  security:  { classes: ['person','backpack','suitcase'], metrics: ['entry','exit','dwell','alert'] },
};
```

Selector en modal "Run Analysis" → pre-puebla clases + métricas.

---

### FASE 3 — Reportes Multiclase + Analytics (2-3 días)

**Objetivo**: Reportes que reflejen la realidad multiclase que ya persiste la DB.

#### 3.1 Dashboard — Métricas Reales

| Actual | Nuevo |
|--------|-------|
| Entradas / Salidas / Entidades / Eventos | **KPIs multiclase** |
| | • Unique Tracks (total) |
| | • Class Distribution (top 5 + "Otros") |
| | • Peak Occupancy / Avg Occupancy |
| | • Avg Dwell / Median Dwell |
| | • Entry Rate / Exit Rate (tracks/min) |
| | • Alerts 24h (por severidad) |

#### 3.2 Reportes por Sesión — Estructura Multiclase

```
VIDEO ANALYSIS REPORT
Source: Store | Duration: 27s | Unique Tracks: 62

DETECCIONES
┌─────────────┬───────┬────────┐
│ Clase       │ Count │ %      │
├─────────────┼───────┼────────┤
│ Person      │ 40    │ 64.5%  │
│ Car         │ 12    │ 19.4%  │
│ Backpack    │  6    │  9.7%  │
│ Bicycle     │  4    │  6.5%  │
└─────────────┴───────┴────────┘

ROI METRICS — Area 1
┌─────────────┬───────┬───────┬────────────┬─────────┬─────────┐
│ Clase       │ Ent.  │ Sal.  │ Peak Occ.  │ Avg Dw. │ Unique  │
├─────────────┼───────┼───────┼────────────┼─────────┼─────────┤
│ Person      │ 34    │ 32    │ 18         │ 12s     │ 28      │
│ Car         │ 10    │ 10    │ 5          │ 8s      │ 8       │
│ Backpack    │  5    │  5    │ 3          │ 5s      │ 4       │
└─────────────┴───────┴───────┴────────────┴─────────┴─────────┘

ALERTS
• Crowding (Person > 20) — 2 ocurrencias
• Vehicle in Pedestrian Zone — 1 ocurrencia
```

#### 3.3 Timeline Visual

- Barras apiladas por hora (últimas 24h) → `Chart.js` o `uPlot` ligero
- Por clase: Person ██████████ Car ████ Bike ██
- Hover → tooltip con conteo exacto

#### 3.4 Agregación por Track

- Endpoint nuevo: `GET /api/sessions/{id}/tracks` → lista tracks con `class_id, class_name, roi_entries[], dwell_times[]`
- UI: "Top 10 Longest Stays" + "Avg/Median Dwell"

---

### FASE 4 — Flujo Source → Analysis → Report (1-2 días)

**Objetivo**: Separar conceptos, eliminar "Run Analysis" subdimensionado.

#### 4.1 Modal "Run Analysis" → Wizard de 2 pasos

```
Paso 1: Configuración
├─ Source: Store (fijo)
├─ Perfil: [Retail ▼] [Traffic] [Security] [Custom]
├─ Tracking Classes: [🔍] chips seleccionados (desde perfil o custom)
├─ Métricas: [☑] Count [☑] Unique [☑] Dwell [☑] Occupancy [☐] Heatmap
├─ Time Range: [60s ▼] [5m] [15m] [Full Video]
└─ Output: [☑] Metrics [☑] Events [☑] PDF Report [☐] Export CSV

Paso 2: Confirmación + Pipeline Visible
Analysis Pipeline:
1. Source Loaded        ✓
2. Frames Extracted     ⟳
3. Detection (YOLO)     ⏳
4. Tracking (ByteTrack) ⏳
5. ROI Events           ⏳
6. Metrics              ⏳
7. Report Generated     ⏳
```

#### 4.2 Historial → Jobs Table

| Análisis | Source | Estado | Duración | Clases | Tracks | Eventos | Reporte |
|----------|--------|--------|----------|--------|--------|---------|---------|
| #245 | Store | ✅ Completed | 27s | Person, Backpack | 62 | 121 | [PDF] [Re-run] |
| #244 | Tokyo | ❌ Failed | 12s | Car, Truck | 0 | 0 | [Logs] |

#### 4.3 Error Handling UX

- `fetchJSON` wrapper: catch → parse `res.data.error` → toast específico
- Network error → "Backend unavailable. Check Logs tab."
- 400 → "Invalid payload: {detail}"
- 500 → "Server error. Check Logs tab."
- Toast no intrusivo (esquina sup. der., auto-dismiss 5s)

---

## Dependencias Técnicas (Ya Existen)

| Necesidad | Ya Implementado |
|-----------|-----------------|
| `/api/classes` + `/grouped` | ✅ `class_catalog_repo.py` |
| `roi.observed_classes` JSONB | ✅ `roi_repo.py` + endpoint PUT |
| `alert_rule` CRUD | ✅ `alert_rule_repo.py` + 5 endpoints |
| `metric_snapshot.object_class` | ✅ `CounterEngine` + `MetricsService.compute()` |
| `zone_event.object_class` + `metadata` | ✅ `RuleEvaluator` |
| `track.class_id` + `class_name` | ✅ `TrackedEntityRecord` |

---

## Priorización Sugerida

```
Semana 1: FASE 1 (bugs críticos) + FASE 2.1-2.3 (tabs + clases)
Semana 2: FASE 2.4 (perfiles) + FASE 3 (reportes multiclase)
Semana 3: FASE 4 (wizard + historial + error UX)
```

---

## Preguntas de Decisión

1. **Tabs naming**: "Zonas" (ES) vs "Zones" / "ROIs" / "Areas" — ¿preferencia?
2. **Default observed_classes**: ¿heredar de source tracking classes (actual) o solo `["person"]` (seguro)?
3. **Class selector UX**: ¿Categorías colapsables + search, o dropdown multi-select searchable?
4. **Rule form**: ¿Mantener inline expandible (actual) o modal pequeño?
5. **Chart library**: ¿`Chart.js` (ya en deps?) o `uPlot` (más ligero, ~15KB)?
6. **Perfiles de análisis**: ¿Incluir en v1 o dejar para v2?