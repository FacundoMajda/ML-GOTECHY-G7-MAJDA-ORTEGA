# src/utils/pages.py — Full-page render functions

from src.utils.components import escape


def render_home() -> str:
    return r"""<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Argus Vision | Video Analytics</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script>
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "surface-variant": "#e4e2dd",
        "secondary-fixed": "#ffdbd1",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "surface-container-low": "#f5f3ee",
        "on-secondary": "#ffffff",
        "primary-container": "#13776d",
        "primary-fixed-dim": "#80d6c9",
        "on-primary-fixed-variant": "#005049",
        "surface-container-high": "#eae8e3",
        "tertiary-fixed": "#dae2ff",
        "tertiary-fixed-dim": "#b1c5ff",
        "on-tertiary-fixed-variant": "#00419e",
        "on-primary-container": "#a5fbee",
        "secondary": "#9f4123",
        "primary-fixed": "#9cf2e5",
        "on-error-container": "#93000a",
        "surface-dim": "#dbdad5",
        "outline-variant": "#bdc9c6",
        "primary": "#005d54",
        "on-primary": "#ffffff",
        "secondary-fixed-dim": "#ffb59f",
        "inverse-primary": "#80d6c9",
        "on-secondary-fixed": "#3a0a00",
        "background": "#fbf9f4",
        "outline": "#6e7977",
        "on-background": "#1b1c19",
        "on-surface": "#1b1c19",
        "on-secondary-fixed-variant": "#802a0e",
        "secondary-container": "#fd8865",
        "surface-container-highest": "#e4e2dd",
        "error": "#ba1a1a",
        "surface-tint": "#006a61",
        "tertiary": "#154dad",
        "on-tertiary": "#ffffff",
        "on-tertiary-fixed": "#001946",
        "surface-container-lowest": "#ffffff",
        "on-tertiary-container": "#e7ebff",
        "surface-bright": "#fbf9f4",
        "inverse-surface": "#30312e",
        "surface-container": "#f0eee9",
        "tertiary-container": "#3866c7",
        "on-secondary-container": "#732105",
        "on-surface-variant": "#3e4947",
        "inverse-on-surface": "#f2f1ec",
        "on-primary-fixed": "#00201d",
        "surface": "#fbf9f4"
      },
      borderRadius: { DEFAULT: "0.125rem", lg: "0.25rem", xl: "0.5rem", full: "0.75rem" },
      spacing: { "margin-desktop": "32px", "container-max": "1280px", gutter: "16px", "margin-mobile": "16px", unit: "4px" },
      fontFamily: { "body-sm": ["Inter"], "headline-lg": ["Inter"], "data-mono": ["JetBrains Mono"], "headline-md": ["Inter"], "label-caps": ["Inter"], "body-md": ["Inter"] },
      fontSize: {
        "body-sm": ["12px", { lineHeight: "16px", fontWeight: "400" }],
        "headline-lg": ["24px", { lineHeight: "32px", letterSpacing: "-0.02em", fontWeight: "600" }],
        "data-mono": ["13px", { lineHeight: "18px", fontWeight: "500" }],
        "headline-md": ["18px", { lineHeight: "24px", fontWeight: "600" }],
        "label-caps": ["11px", { lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "700" }],
        "body-md": ["14px", { lineHeight: "20px", fontWeight: "400" }]
      }
    }
  }
}
</script>
<style>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
body { background-color: #fbf9f4; font-family: 'Inter', sans-serif; color: #1b1c19; }
.pulse-dot {
  width: 8px; height: 8px; background-color: #13776d; border-radius: 50%; display: inline-block; margin-right: 8px;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(19, 119, 109, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(19, 119, 109, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(19, 119, 109, 0); }
}
.skeleton { background: linear-gradient(90deg, #e4e2dd 25%, #f0eee9 50%, #e4e2dd 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 8px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.card-hover { transition: all 0.15s ease; }
.card-hover:hover { border-color: #005d54; background: rgba(0,93,84,0.04); }
.spinner { display: inline-block; width: 28px; height: 28px; border: 3px solid #bdc9c6; border-top-color: #005d54; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.progress-bar { width: 100%; height: 6px; background: #bdc9c6; border-radius: 3px; overflow: hidden; margin: 12px 0; }
.progress-bar-fill { height: 100%; background: #005d54; border-radius: 3px; transition: width 0.3s ease; }
.mini-spinner { display: inline-block; width: 10px; height: 10px; border: 2px solid rgba(245,158,11,0.3); border-top-color: #d97706; border-radius: 50%; animation: spin 0.6s linear infinite; }
.bento-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 24px; }
</style>
</head>
<body class="bg-background text-on-background" onload="switchTab('fuentes')">

<!-- TopAppBar -->
<header class="bg-background border-b border-outline-variant fixed top-0 left-0 right-0 h-16 flex justify-between items-center px-margin-desktop z-50">
<div class="flex items-center gap-8">
<h1 class="text-headline-md font-headline-md font-bold text-primary cursor-pointer" onclick="switchTab('dashboard')">Argus Vision</h1>
<nav class="hidden md:flex gap-4">
<a class="text-on-surface-variant hover:text-primary transition-colors duration-200 text-body-md font-body-md cursor-pointer" onclick="switchTab('fuentes')">Fuentes</a>
<a class="text-on-surface-variant hover:text-primary transition-colors duration-200 text-body-md font-body-md cursor-pointer" onclick="switchTab('dashboard')">Dashboard</a>
<a class="text-on-surface-variant hover:text-primary transition-colors duration-200 text-body-md font-body-md cursor-pointer" onclick="switchTab('historial')">Historial</a>
<a class="text-on-surface-variant hover:text-primary transition-colors duration-200 text-body-md font-body-md cursor-pointer" onclick="switchTab('logs')">Logs</a>
</nav>
</div>
</div>
</header>

<!-- SideNavBar -->
<aside class="fixed left-0 top-16 bottom-0 w-64 bg-surface-container-low border-r border-outline-variant flex flex-col z-40">
<div class="p-6 border-b border-outline-variant">
<p class="text-label-caps font-label-caps text-secondary mb-1">SYSTEM OVERVIEW</p>
<p class="text-body-sm font-body-sm text-on-surface-variant">V3.4.2-Stable</p>
</div>
<nav class="flex-1 py-4 overflow-y-auto">
<a class="flex items-center gap-3 px-6 py-3 cursor-pointer nav-link active" data-tab="fuentes" onclick="switchTab('fuentes')">
<span class="material-symbols-outlined" data-icon="monitoring">monitoring</span>
<span class="text-label-caps font-label-caps">FUENTES</span>
</a>
<a class="flex items-center gap-3 px-6 py-3 cursor-pointer nav-link text-on-surface-variant hover:text-primary hover:bg-surface-variant transition-colors" data-tab="dashboard" onclick="switchTab('dashboard')">
<span class="material-symbols-outlined" data-icon="videocam">videocam</span>
<span class="text-label-caps font-label-caps">DASHBOARD</span>
</a>
<a class="flex items-center gap-3 px-6 py-3 cursor-pointer nav-link text-on-surface-variant hover:text-primary hover:bg-surface-variant transition-colors" data-tab="historial" onclick="switchTab('historial')">
<span class="material-symbols-outlined" data-icon="description">description</span>
<span class="text-label-caps font-label-caps">HISTORIAL</span>
</a>
<a class="flex items-center gap-3 px-6 py-3 cursor-pointer nav-link text-on-surface-variant hover:text-primary hover:bg-surface-variant transition-colors" data-tab="logs" onclick="switchTab('logs')">
<span class="material-symbols-outlined" data-icon="terminal">terminal</span>
<span class="text-label-caps font-label-caps">LOGS</span>
</a>
</nav>
<div class="p-4 bg-surface-container-lowest border-t border-outline-variant mt-auto">
<button class="w-full bg-primary text-on-primary font-bold py-3 rounded-lg flex items-center justify-center gap-2 hover:bg-primary-container transition-all" onclick="toggleAddSourceForm()">
<span class="material-symbols-outlined" data-icon="add">add</span>
<span class="text-body-md font-body-md">Add New Source</span>
</button>
<div class="mt-4 flex flex-col gap-2">
<a class="text-on-surface-variant hover:text-primary text-body-sm font-body-sm flex items-center gap-2 cursor-pointer" onclick="switchTab('documentacion')">
<span class="material-symbols-outlined" data-icon="help">help</span> Documentation
</a>
</div>
</div>
</aside>

<!-- Main Content -->
<main class="ml-64 mt-16 p-margin-desktop flex flex-col gap-gutter">

<div id="tab-fuentes" class="tab-content">
<div class="flex justify-between items-end mb-4">
<div>
<nav class="flex text-body-sm font-body-sm text-on-surface-variant gap-2 mb-2"><span>Sources</span></nav>
<h2 class="text-headline-lg font-headline-lg">Video Sources</h2>
</div>
<div class="flex items-center gap-3">
<button class="bg-primary text-on-primary px-4 py-2 font-bold flex items-center gap-2 hover:bg-primary-container transition-all" onclick="toggleAddSourceForm()">
<span class="material-symbols-outlined" data-icon="add">add</span> Add Source
</button>
</div>
</div>

<div id="sources-error" class="hidden bg-error-container border border-error rounded-lg p-4 mb-4 flex items-center gap-3">
<span class="material-symbols-outlined text-error" data-icon="error">error</span>
<span id="sources-error-msg" class="flex-1 text-body-md font-body-md text-on-error-container"></span>
<button class="text-label-caps font-label-caps text-on-error-container font-bold hover:underline" onclick="fetchSources()">Retry</button>
</div>

<div id="sources-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"></div>

<div id="add-source-form" class="hidden bg-surface-container-lowest border border-outline-variant rounded-lg p-6 mt-4">
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<input id="new-name" class="border border-outline-variant rounded-lg p-3 text-body-md font-body-md bg-background text-on-background md:col-span-2" placeholder="Source Name"/>
<select id="new-type" class="border border-outline-variant rounded-lg p-3 text-body-md font-body-md bg-background text-on-background" onchange="updateAddSourceMode()">
<option value="file">FILE</option>
<option value="youtube_vod">YOUTUBE VOD</option>
<option value="youtube_live">YOUTUBE LIVE</option>
<option value="rtsp">RTSP</option>
</select>
<input id="new-uri" class="border border-outline-variant rounded-lg p-3 text-body-md font-body-md bg-background text-on-background" placeholder="URI / path"/>
</div>
<div id="file-upload-wrap" class="mt-4 hidden">
<input type="file" id="new-file-input" accept="video/*" class="hidden"/>
<div id="file-dropzone" class="border-2 border-dashed border-outline rounded-lg p-6 text-center cursor-pointer hover:border-primary transition-all text-body-sm font-body-sm text-on-surface-variant" onclick="document.getElementById('new-file-input').click()">Drop a video here or click to choose one</div>
<div id="file-selected-name" class="text-body-sm font-body-sm text-primary mt-2"></div>
</div>
<div class="flex gap-3 mt-4">
<button class="bg-primary text-on-primary px-6 py-2 font-bold flex items-center gap-2 hover:bg-primary-container transition-all" onclick="saveNewSource()">
<span class="material-symbols-outlined" data-icon="save">save</span> Save
</button>
<button class="border border-outline text-on-surface-variant px-6 py-2 font-bold hover:bg-surface-container transition-all" onclick="toggleAddSourceForm()">Cancel</button>
</div>
<div id="add-source-error" class="text-error text-body-sm font-body-sm mt-2"></div>
</div>
</div>

<div id="tab-dashboard" class="tab-content hidden">
<div class="max-w-container-max mx-auto">
<section class="mb-8 flex justify-between items-end">
<div>
<h1 class="text-headline-lg font-headline-lg text-on-background">Dashboard</h1>
<p class="text-body-md font-body-md text-outline">Resumen completo de metricas de analisis.</p>
</div>
<button class="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded font-bold hover:bg-primary-container transition-all" onclick="fetchDashboard()">
<span class="material-symbols-outlined" style="font-size:18px">refresh</span> Actualizar
</button>
</section>

<div id="dash-cards" class="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
<div class="col-span-2 lg:col-span-5 text-center py-8 text-on-surface-variant"><div class="spinner mx-auto mb-2"></div><p class="text-body-sm">Cargando...</p></div>
</div>

<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
<h4 class="text-label-caps font-label-caps text-secondary uppercase mb-4">Actividad por Fuente</h4>
<div id="dash-source-chart" class="space-y-3">
<p class="text-body-sm text-on-surface-variant text-center py-8">Cargando...</p>
</div>
</div>
<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-6">
<h4 class="text-label-caps font-label-caps text-secondary uppercase mb-4">Top Areas (ROIs)</h4>
<div id="dash-roi-chart" class="space-y-3">
<p class="text-body-sm text-on-surface-variant text-center py-8">Cargando...</p>
</div>
</div>
</div>

<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 mb-8">
<div class="flex items-center justify-between mb-4">
<h4 class="text-label-caps font-label-caps text-secondary uppercase">Ultimos Analisis</h4>
<button class="flex items-center gap-1 text-primary text-label-caps font-bold hover:underline" onclick="switchTab('historial')">
<span class="material-symbols-outlined" style="font-size:16px">arrow_forward</span> Ver todos
</button>
</div>
<div id="dash-recent-sessions"></div>
</div>

<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 mb-8">
<div class="flex justify-between items-start mb-4">
<div>
<h4 class="text-label-caps font-label-caps text-secondary uppercase">Distribucion por Hora (7 dias)</h4>
<p class="text-body-sm font-body-sm text-outline">Entradas y salidas agregadas por hora.</p>
</div>
</div>
<div class="h-40 w-full" id="dash-hourly-chart">
<p class="text-body-sm text-on-surface-variant text-center py-8">Cargando...</p>
</div>
</div>

</div>
</div>


</div>

<div id="tab-historial" class="tab-content hidden">
<div class="max-w-container-max mx-auto">
<section class="mb-8 flex justify-between items-end">
<div>
<h1 class="text-headline-lg font-headline-lg text-on-background">Historial de Analisis</h1>
<p class="text-body-md font-body-md text-outline">Todos los analisis ejecutados en el sistema.</p>
</div>
<button class="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded font-bold hover:bg-primary-container transition-all" onclick="fetchAnalyses()">
<span class="material-symbols-outlined" style="font-size:18px">refresh</span> Actualizar
</button>
</section>
<div id="analyses-error" class="hidden bg-error-container border border-error rounded-lg p-4 mb-4 flex items-center gap-3">
<span class="material-symbols-outlined text-error" data-icon="error">error</span>
<span id="analyses-error-msg" class="flex-1 text-body-md font-body-md text-on-error-container"></span>
<button class="text-label-caps font-label-caps text-on-error-container font-bold hover:underline" onclick="fetchAnalyses()">Reintentar</button>
</div>
<div id="analyses-content">
<div class="col-span-full text-center py-12"><div class="spinner mx-auto mb-2"></div><p class="text-body-sm text-on-surface-variant">Cargando...</p></div>
</div>
</div>
</div>

<div id="tab-analysis-detail" class="tab-content hidden">
<div class="max-w-container-max mx-auto">
<section class="mb-6 flex items-center justify-between">
<div class="flex items-center gap-4">
<button class="flex items-center gap-2 text-primary hover:underline text-body-sm font-body-sm" onclick="switchTab('historial')">
<span class="material-symbols-outlined" style="font-size:18px">arrow_back</span> Volver
</button>
</div>
</section>
<div id="analysis-detail-content"></div>
</div>
</div>


<div id="tab-logs" class="tab-content hidden">
<div class="max-w-container-max mx-auto">
<section class="mb-8 flex justify-between items-end">
<div>
<h1 class="text-headline-lg font-headline-lg text-on-background">Logs del Sistema</h1>
<p class="text-body-md font-body-md text-outline">Recursos del servidor y eventos de problema del sistema.</p>
</div>
<button class="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded font-bold hover:bg-primary-container transition-all" onclick="fetchLogs()">
<span class="material-symbols-outlined" style="font-size:18px">refresh</span> Actualizar
</button>
</section>
<div id="logs-content">
<div class="text-center py-12"><div class="spinner mx-auto mb-2"></div><p class="text-body-sm text-on-surface-variant">Cargando...</p></div>
</div>
</div>
</div>

<div id="tab-documentacion" class="tab-content hidden">
<div class="max-w-container-max mx-auto">
<section class="mb-8">
<h1 class="text-headline-lg font-headline-lg text-on-background">Documentacion</h1>
<p class="text-body-md font-body-md text-outline">Tecnologias y arquitectura del sistema de analisis de video.</p>
</section>

<div class="space-y-4">

<!-- ── StateManager ── -->
<details class="group bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden" open>
<summary class="flex items-center justify-between px-6 py-5 cursor-pointer hover:bg-surface-container/50 transition-colors [&::-webkit-details-marker]:hidden">
<div class="flex items-center gap-4">
<span class="material-symbols-outlined text-primary" style="font-size:28px">account_tree</span>
<div>
<h3 class="text-headline-md font-headline-md font-bold text-on-surface">CounterEngine — State Manager</h3>
<p class="text-body-sm font-body-sm text-on-surface-variant">Motor de estado central: seguimiento de entidades, deteccion de entrada/salida por ROI y snapshots de ocupacion.</p>
</div>
</div>
<span class="material-symbols-outlined text-on-surface-variant group-open:rotate-180 transition-transform">expand_more</span>
</summary>
<div class="px-6 pb-6 border-t border-outline-variant pt-4">
<div class="prose max-w-none text-body-md font-body-md text-on-surface-variant space-y-3">
<p><strong class="text-on-surface">CounterEngine</strong> es el corazon del sistema. Mantiene el estado de cada entidad rastreada a lo largo del video y determina cuando cruzan las Regiones de Interes (ROI).</p>
<ul class="list-disc pl-5 space-y-2">
<li><strong class="text-on-surface">Estado por entidad:</strong> Por cada <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">track_id</code> unico guarda: frame/tiempo de primera y ultima aparicion, ROIs donde esta dentro, y momento de ingreso a cada ROI (para calcular dwell time).</li>
<li><strong class="text-on-surface">Deteccion ENTRY/EXIT:</strong> Usa <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">cv2.pointPolygonTest</code> para verificar si el centro del pie de la persona esta dentro del poligono del ROI. Si el centro esta fuera, usa interseccion geometrica de segmentos (los dos pies vs. las aristas del poligono) para detectar cruces fronterizos.</li>
<li><strong class="text-on-surface">Snapshots de ocupacion:</strong> Cada 30 frames registra cuantas entidades estan dentro/fuera de cada ROI, con sus <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">track_id</code>s.</li>
<li><strong class="text-on-surface">Dwell Time:</strong> Cuando una entidad sale de un ROI, calcula automaticamente el tiempo transcurrido desde que ingreso.</li>
<li><strong class="text-on-surface">Datos exportados:</strong> Al finalizar el analisis exporta entidades rastreadas, snapshots y eventos para persistencia en PostgreSQL.</li>
</ul>
</div>
</div>
</details>

<!-- ── YOLO ── -->
<details class="group bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
<summary class="flex items-center justify-between px-6 py-5 cursor-pointer hover:bg-surface-container/50 transition-colors [&::-webkit-details-marker]:hidden">
<div class="flex items-center gap-4">
<span class="material-symbols-outlined text-primary" style="font-size:28px">radar</span>
<div>
<h3 class="text-headline-md font-headline-md font-bold text-on-surface">YOLO (Ultralytics)</h3>
<p class="text-body-sm font-body-sm text-on-surface-variant">Deteccion de objetos en tiempo real mediante deep learning.</p>
</div>
</div>
<span class="material-symbols-outlined text-on-surface-variant group-open:rotate-180 transition-transform">expand_more</span>
</summary>
<div class="px-6 pb-6 border-t border-outline-variant pt-4">
<div class="prose max-w-none text-body-md font-body-md text-on-surface-variant space-y-3">
<p>Usamos <strong class="text-on-surface">Ultralytics YOLO11n</strong> (YOLO v11 nano) para deteccion de objetos. Es cargado como singleton perezoso — la primera vez que se ejecuta un analisis.</p>
<ul class="list-disc pl-5 space-y-2">
<li><strong class="text-on-surface">Modelo:</strong> <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">yolo11n.pt</code> — variante nano, optimizada para velocidad.</li>
<li><strong class="text-on-surface">Clase por defecto:</strong> <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">0</code> (persona). Configurable desde la UI.</li>
<li><strong class="text-on-surface">Confianza minima:</strong> 0.3 para filtrar detecciones debiles.</li>
<li><strong class="text-on-surface">Integracion con ByteTrack:</strong> Se llama <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">model.track(frame, persist=True, tracker="bytetrack.yaml")</code> que ejecuta deteccion y tracking en un solo paso.</li>
<li><strong class="text-on-surface">Backend:</strong> PyTorch en CPU (configurado con <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">pytorch-cpu</code>).</li>
</ul>
</div>
</div>
</details>

<!-- ── ByteTrack ── -->
<details class="group bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
<summary class="flex items-center justify-between px-6 py-5 cursor-pointer hover:bg-surface-container/50 transition-colors [&::-webkit-details-marker]:hidden">
<div class="flex items-center gap-4">
<span class="material-symbols-outlined text-primary" style="font-size:28px">swap_driving_apps_wheel</span>
<div>
<h3 class="text-headline-md font-headline-md font-bold text-on-surface">ByteTrack</h3>
<p class="text-body-sm font-body-sm text-on-surface-variant">Algoritmo de tracking multi-objeto por asociacion de detecciones.</p>
</div>
</div>
<span class="material-symbols-outlined text-on-surface-variant group-open:rotate-180 transition-transform">expand_more</span>
</summary>
<div class="px-6 pb-6 border-t border-outline-variant pt-4">
<div class="prose max-w-none text-body-md font-body-md text-on-surface-variant space-y-3">
<p><strong class="text-on-surface">ByteTrack</strong> es el tracker multi-objeto que asigna identificadores unicos (<code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">track_id</code>) a cada persona detectada a traves de los frames del video.</p>
<ul class="list-disc pl-5 space-y-2">
<li><strong class="text-on-surface">Asociacion:</strong> Usa matching de IoU (Intersection over Union) entre detecciones consecutivas para mantener la identidad de cada objeto.</li>
<li><strong class="text-on-surface">Manejo de oclusiones:</strong> Utiliza detecciones de alta y baja confianza para mantener el tracking incluso cuando hay oclusiones parciales.</li>
<li><strong class="text-on-surface">Configuracion:</strong> Viene integrado en Ultralytics via <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">bytetrack.yaml</code> — no requiere configuracion adicional.</li>
<li><strong class="text-on-surface">Persistencia:</strong> <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">persist=True</code> permite que el tracker mantenga identidades entre frames sucesivos.</li>
</ul>
</div>
</div>
</details>

<!-- ── OpenCV ── -->
<details class="group bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
<summary class="flex items-center justify-between px-6 py-5 cursor-pointer hover:bg-surface-container/50 transition-colors [&::-webkit-details-marker]:hidden">
<div class="flex items-center gap-4">
<span class="material-symbols-outlined text-primary" style="font-size:28px">view_in_ar</span>
<div>
<h3 class="text-headline-md font-headline-md font-bold text-on-surface">OpenCV</h3>
<p class="text-body-sm font-body-sm text-on-surface-variant">Vision por computadora: captura de video, anotacion de frames y analisis geometrico.</p>
</div>
</div>
<span class="material-symbols-outlined text-on-surface-variant group-open:rotate-180 transition-transform">expand_more</span>
</summary>
<div class="px-6 pb-6 border-t border-outline-variant pt-4">
<div class="prose max-w-none text-body-md font-body-md text-on-surface-variant space-y-3">
<p><strong class="text-on-surface">OpenCV</strong> (<code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">cv2</code>) es la columna vertebral de todas las operaciones de video. Sus usos principales:</p>
<ul class="list-disc pl-5 space-y-2">
<li><strong class="text-on-surface">Captura de video:</strong> <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">VideoCapture</code> con backend FFmpeg para archivos locales, RTSP y streams de YouTube.</li>
<li><strong class="text-on-surface">Escritura de video:</strong> <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">VideoWriter</code> que produce MP4 anotado con bounding boxes y metricas. Post-procesado con FFmpeg a H.264 para compatibilidad web.</li>
<li><strong class="text-on-surface">Geometria de ROI:</strong> <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">pointPolygonTest</code> para determinar si un punto esta dentro de un poligono.</li>
<li><strong class="text-on-surface">Anotacion visual:</strong> <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">rectangle</code>, <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">putText</code>, <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">fillPoly</code>, <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">polylines</code>, <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">addWeighted</code> para overlays semi-transparentes.</li>
<li><strong class="text-on-surface">Previsualizacion:</strong> <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">imencode</code> + <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">resize</code> para servir previews JPEG de las fuentes de video.</li>
</ul>
</div>
</div>
</details>

<!-- ── Psutil ── -->
<details class="group bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
<summary class="flex items-center justify-between px-6 py-5 cursor-pointer hover:bg-surface-container/50 transition-colors [&::-webkit-details-marker]:hidden">
<div class="flex items-center gap-4">
<span class="material-symbols-outlined text-primary" style="font-size:28px">monitoring</span>
<div>
<h3 class="text-headline-md font-headline-md font-bold text-on-surface">Psutil</h3>
<p class="text-body-sm font-body-sm text-on-surface-variant">Monitoreo de recursos del sistema en tiempo real.</p>
</div>
</div>
<span class="material-symbols-outlined text-on-surface-variant group-open:rotate-180 transition-transform">expand_more</span>
</summary>
<div class="px-6 pb-6 border-t border-outline-variant pt-4">
<div class="prose max-w-none text-body-md font-body-md text-on-surface-variant space-y-3">
<p><strong class="text-on-surface">Psutil</strong> (<code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">psutil</code>) se utiliza en la pestana de Logs para mostrar metricas de rendimiento del servidor:</p>
<ul class="list-disc pl-5 space-y-2">
<li><strong class="text-on-surface">CPU:</strong> Porcentaje de uso del proceso via <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">psutil.Process.cpu_percent()</code>.</li>
<li><strong class="text-on-surface">Memoria:</strong> RSS en MB y porcentaje del total del sistema via <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">memory_info().rss</code> y <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">memory_percent()</code>.</li>
<li><strong class="text-on-surface">Disco:</strong> Tamano del directorio del proyecto (excluyendo <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">.venv</code> y <code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">__pycache__</code>).</li>
<li><strong class="text-on-surface">Actividad:</strong> Tiempo de actividad del proceso, numero de hilos (<code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">num_threads()</code>), archivos abiertos (<code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">num_fds()</code>) y conexiones (<code class="text-primary bg-surface-container-high px-1.5 py-0.5 rounded text-data-mono">connections()</code>).</li>
</ul>
</div>
</div>
</details>

</div>
</div>
</div>

</main>

<!-- DRAWER OVERLAY -->
<div id="drawer-overlay" class="fixed inset-0 z-40 bg-black/30 hidden"></div>

<!-- DRAWER -->
<aside id="drawer" class="fixed right-0 top-0 w-[520px] h-full z-50 bg-surface-container-lowest border-l border-outline-variant shadow-lg translate-x-full transition-transform duration-300 flex flex-col">
<div class="flex items-center justify-between px-6 py-4 border-b border-outline-variant flex-shrink-0">
<span id="drawer-title" class="text-headline-md font-headline-md font-bold text-on-surface">Source Name</span>
<button onclick="closeDrawer()" class="material-symbols-outlined text-on-surface-variant hover:text-on-surface cursor-pointer p-1">close</button>
</div>
<div class="flex border-b border-outline-variant flex-shrink-0">
<button class="flex-1 px-4 py-3 text-label-caps font-label-caps text-center cursor-pointer drawer-tab active" data-dtab="preview" onclick="switchDrawerTab('preview')">Preview</button>
<button class="flex-1 px-4 py-3 text-label-caps font-label-caps text-center cursor-pointer drawer-tab text-on-surface-variant hover:text-primary" data-dtab="areas" onclick="switchDrawerTab('areas')">Areas</button>
<button class="flex-1 px-4 py-3 text-label-caps font-label-caps text-center cursor-pointer drawer-tab text-on-surface-variant hover:text-primary" data-dtab="settings" onclick="switchDrawerTab('settings')">Settings</button>
</div>
<div class="flex-1 overflow-y-auto p-6">
<div id="dt-preview" class="dt-content">
<div class="relative w-full mb-4">
<img id="preview-img" class="w-full rounded-lg aspect-video object-cover bg-surface-container" src="" alt="Preview"/>
<canvas id="preview-canvas" class="absolute inset-0 w-full h-full cursor-crosshair rounded-lg"></canvas>
</div>
<button id="draw-area-btn" class="border border-primary text-primary px-4 py-2 font-bold hover:bg-surface-container transition-all text-body-sm font-body-sm" onclick="toggleDrawMode()">Draw Area</button>
<div id="draw-actions" class="hidden flex gap-2 mt-2">
<button class="bg-primary text-on-primary px-4 py-2 font-bold hover:bg-primary-container transition-all text-body-sm font-body-sm" onclick="savePolygon()">Save Area</button>
<button class="border border-outline text-on-surface-variant px-4 py-2 font-bold hover:bg-surface-container transition-all text-body-sm font-body-sm" onclick="cancelDrawing()">Cancel</button>
</div>
</div>
<div id="dt-areas" class="dt-content hidden">
<div id="areas-list"></div>
</div>
<div id="dt-settings" class="dt-content hidden">
<div id="settings-content"></div>
</div>
</div>
<div class="p-4 border-t border-outline-variant flex-shrink-0">
<button class="w-full bg-primary text-on-primary py-3 font-bold flex items-center justify-center gap-2 hover:bg-primary-container transition-all" onclick="openAnalysisModal()">
<span class="material-symbols-outlined" data-icon="play_arrow">play_arrow</span> Run Analysis
</button>
</div>
</aside>

<!-- MODAL -->
<div id="modal" class="fixed inset-0 z-60 flex items-center justify-center bg-black/40 hidden">
<div class="bg-surface-container-lowest rounded-2xl p-6 w-full max-w-lg max-h-[85vh] overflow-y-auto shadow-xl">
<span id="modal-title" class="text-headline-md font-headline-md font-bold text-on-surface block mb-4">Run Analysis</span>
<div id="modal-body"></div>
</div>
</div>

<script>
const state = {
  tab: 'sources',
  sources: [],
  sessions: [],
  selectedSourceId: null,
  drawerOpen: false,
  drawerTab: 'preview',
  drawMode: false,
  currentPolygon: [],
  sourceSettings: {},
  modalOpen: false,
  modalState: 'summary',
  modalSourceId: null,
  modalSessionId: null,
  modalError: null,
  pollingInterval: null,
};
let pendingSourceFile = null;

const _TRACKING_CLASS_TO_YOLO = { person: 0, bicycle: 1, car: 2, backpack: 24 };
const roiColors = [
  { fill: 'rgba(0,93,84,0.15)', stroke: '#005d54' },
  { fill: 'rgba(16,185,129,0.15)', stroke: '#10b981' },
  { fill: 'rgba(245,158,11,0.15)', stroke: '#f59e0b' },
  { fill: 'rgba(239,68,68,0.15)', stroke: '#ef4444' },
  { fill: 'rgba(139,92,246,0.15)', stroke: '#8b5cf6' },
  { fill: 'rgba(236,72,153,0.15)', stroke: '#ec4899' },
];

function esc(s) { if (s == null) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function fetchJSON(url, opts) {
  return fetch(url, opts).then(r => {
    if (r.status === 204) return { status: r.status, data: null };
    return r.json().then(d => ({status: r.status, data: d}));
  });
}

function getSource(id) { return state.sources.find(s => s.id === id); }

function formatDate(iso) { if (!iso) return '-'; const d = new Date(iso); return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}); }

function formatDuration(sec) {
  if (sec == null) return '-';
  if (sec < 60) return Math.round(sec) + 's';
  if (sec < 3600) return Math.floor(sec/60) + 'm ' + Math.round(sec%60) + 's';
  return Math.floor(sec/3600) + 'h ' + Math.floor((sec%3600)/60) + 'm';
}

function sourceTypeLabel(t) { const labels = {file:'FILE', youtube_vod:'YOUTUBE', youtube_live:'LIVE', rtsp:'RTSP'}; return labels[t] || t; }

function getSourceSettings(sourceId) {
  if (!state.sourceSettings[sourceId]) state.sourceSettings[sourceId] = { tracking_classes: ['person'], max_seconds: null };
  return state.sourceSettings[sourceId];
}

function switchTab(tab) {
  state.tab = tab;
  document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
  document.getElementById('tab-' + tab).classList.remove('hidden');
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.dataset.tab === tab);
    if (a.dataset.tab === tab) { a.classList.add('text-primary', 'font-bold', 'border-r-4', 'border-primary', 'bg-surface-container-high'); a.classList.remove('text-on-surface-variant'); }
    else { a.classList.remove('text-primary', 'font-bold', 'border-r-4', 'border-primary', 'bg-surface-container-high'); a.classList.add('text-on-surface-variant'); }
  });
  if (tab === 'fuentes') fetchSources();
  if (tab === 'dashboard') fetchDashboard();
  if (tab === 'historial') fetchAnalyses();
  if (tab === 'logs') { fetchLogs(); }
}

function toggleAddSourceForm() {
  const form = document.getElementById('add-source-form');
  form.classList.toggle('hidden');
  if (!form.classList.contains('hidden')) updateAddSourceMode();
}

function updateAddSourceMode() {
  const type = document.getElementById('new-type').value;
  const uriInput = document.getElementById('new-uri');
  const uploadWrap = document.getElementById('file-upload-wrap');
  if (type === 'file') {
    uriInput.placeholder = 'Uploaded file path (auto)';
    uriInput.readOnly = true;
    uploadWrap.classList.remove('hidden');
  } else {
    uriInput.placeholder = type === 'youtube_vod' ? 'https://www.youtube.com/watch?v=...' : type === 'youtube_live' ? 'YouTube Live URL' : 'rtsp://...';
    uriInput.readOnly = false;
    uploadWrap.classList.add('hidden');
  }
}

async function uploadSelectedFile(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/api/uploads', { method: 'POST', body: form });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Upload failed');
  return data.path;
}

async function saveNewSource() {
  const name = document.getElementById('new-name').value.trim();
  const type = document.getElementById('new-type').value;
  let uri = document.getElementById('new-uri').value.trim();
  const errEl = document.getElementById('add-source-error');
  errEl.textContent = '';

  if (!name) { errEl.textContent = 'Name is required'; return; }
  if (!uri && type !== 'file') { errEl.textContent = 'URI is required'; return; }

  try {
    if (type === 'file') {
      const fileInput = document.getElementById('new-file-input');
      if (!pendingSourceFile && (!fileInput.files || !fileInput.files[0])) { errEl.textContent = 'Please select a file to upload'; return; }
      const file = pendingSourceFile || fileInput.files[0];
      const path = await uploadSelectedFile(file);
      uri = path;
    }
    const res = await fetchJSON('/api/sources', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name, source_type: type, source_uri: uri }) });
    if (res.status >= 400) { errEl.textContent = res.data.error || 'Error creating source'; return; }
    document.getElementById('add-source-form').classList.add('hidden');
    document.getElementById('new-name').value = '';
    document.getElementById('new-uri').value = '';
    document.getElementById('new-type').value = 'file';
    pendingSourceFile = null;
    document.getElementById('file-selected-name').textContent = '';
    fetchSources();
  } catch (e) { errEl.textContent = 'Network error: ' + e.message; }
}

function renderSources() {
  const grid = document.getElementById('sources-grid');
  const err = document.getElementById('sources-error');
  if (state.sources.length === 0) {
    grid.innerHTML = '<div class="col-span-full text-center py-12"><p class="text-body-md font-body-md text-on-surface-variant">No sources yet. Add your first video source.</p></div>';
    return;
  }
  grid.innerHTML = state.sources.map(s => {
    const activeRois = (s.rois || []).length;
    return `<div class="relative group bg-surface-container-lowest border border-outline-variant rounded-lg p-4 card-hover cursor-pointer" onclick="selectSource('${esc(s.id)}')">
      <button onclick="event.stopPropagation(); deleteSource('${esc(s.id)}', '${esc(s.name)}')" class="absolute top-2 right-2 p-1 rounded-full hover:bg-error-container text-on-surface-variant hover:text-error transition-all opacity-0 group-hover:opacity-100" title="Eliminar fuente">
        <span class="material-symbols-outlined" style="font-size:18px">delete</span>
      </button>
      <div class="flex items-center gap-4 mb-3">
        <div class="w-20 h-14 rounded-lg bg-surface-container flex-shrink-0 overflow-hidden">
          <img class="w-full h-full object-cover" src="/api/sources/${esc(s.id)}/preview" alt="${esc(s.name)}" loading="lazy" onerror="this.style.display='none'"/>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-body-md font-body-md font-bold text-on-surface truncate">${esc(s.name)}</p>
          <p class="text-body-sm font-body-sm text-on-surface-variant">${esc(sourceTypeLabel(s.source_type))} ${s.is_live ? '<span class="inline-block w-2 h-2 bg-green-500 rounded-full ml-1"></span>' : ''}</p>
        </div>
      </div>
      <div class="flex items-center gap-4 text-body-sm font-body-sm text-on-surface-variant">
        <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">category</span> ${activeRois} area${activeRois !== 1 ? 's' : ''}</span>
        <span class="flex items-center gap-1"><span class="material-symbols-outlined text-[14px] ${s.frame_width ? 'text-primary' : ''}">${s.frame_width ? 'check_circle' : 'radio_button_unchecked'}</span> ${s.frame_width ? s.frame_width + 'x' + s.frame_height : 'No preview'}</span>
      </div>
    </div>`;
  }).join('');
}

async function fetchSources() {
  const err = document.getElementById('sources-error');
  try {
    const res = await fetchJSON('/api/sources');
    if (res.status >= 400) { err.classList.remove('hidden'); document.getElementById('sources-error-msg').textContent = res.data.error || 'Failed to load sources'; return; }
    err.classList.add('hidden');
    state.sources = res.data;
    renderSources();
    // Re-fetch with ROIs for previews
    await fetch('/api/sources').then(r => r.json()).then(data => { state.sources = data; renderSources(); });
  } catch (e) { err.classList.remove('hidden'); document.getElementById('sources-error-msg').textContent = e.message; }
}

// DRAWER

function selectSource(id) {
  state.selectedSourceId = id;
  state.drawerOpen = true;
  state.drawerTab = 'preview';
  state.drawMode = false;
  state.currentPolygon = [];
  renderSources();
  renderDrawer();
}

function closeDrawer() {
  if (state.drawMode) cancelDrawing();
  state.drawMode = false;
  state.currentPolygon = [];
  state.drawerOpen = false;
  state.selectedSourceId = null;
  state.drawerTab = 'preview';
  document.getElementById('drawer').classList.remove('translate-x-0');
  document.getElementById('drawer-overlay').classList.add('hidden');
  renderSources();
}

function renderDrawer() {
  const src = getSource(state.selectedSourceId);
  const drawer = document.getElementById('drawer');
  const overlay = document.getElementById('drawer-overlay');
  if (!src || !state.drawerOpen) { drawer.classList.remove('translate-x-0'); overlay.classList.add('hidden'); return; }
  document.getElementById('drawer-title').textContent = src.name;
  const img = document.getElementById('preview-img');
  img.src = '/api/sources/' + src.id + '/preview?t=' + Date.now();
  img.onload = function() {
    const canvas = document.getElementById('preview-canvas');
    const rect = img.getBoundingClientRect();
    if (rect.width === 0) return;
    canvas.width = rect.width;
    canvas.height = rect.height;
    if (state.drawMode) drawCanvasDuringDrawMode(); else drawExistingROIs();
  };
  document.querySelectorAll('.drawer-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.dtab === state.drawerTab);
    if (t.dataset.dtab === state.drawerTab) { t.classList.add('bg-surface-container', 'text-primary', 'font-bold'); t.classList.remove('text-on-surface-variant'); }
    else { t.classList.remove('bg-surface-container', 'text-primary', 'font-bold'); t.classList.add('text-on-surface-variant'); }
  });
  showDrawerTab(state.drawerTab);
  drawer.classList.add('translate-x-0');
  overlay.classList.remove('hidden');
}

function switchDrawerTab(tab) {
  state.drawerTab = tab;
  document.querySelectorAll('.drawer-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.dtab === tab);
    if (t.dataset.dtab === tab) { t.classList.add('bg-surface-container', 'text-primary', 'font-bold'); t.classList.remove('text-on-surface-variant'); }
    else { t.classList.remove('bg-surface-container', 'text-primary', 'font-bold'); t.classList.add('text-on-surface-variant'); }
  });
  showDrawerTab(tab);
}

function showDrawerTab(tab) {
  document.querySelectorAll('.dt-content').forEach(c => c.classList.add('hidden'));
  const el = document.getElementById('dt-' + tab);
  if (el) el.classList.remove('hidden');
  if (tab === 'areas') renderAreasTab();
  if (tab === 'settings') renderSettingsTab();
}

function drawExistingROIs() {
  const canvas = document.getElementById('preview-canvas');
  const img = document.getElementById('preview-img');
  if (!canvas || !img) return;
  const ctx = canvas.getContext('2d');
  const src = getSource(state.selectedSourceId);
  if (!src) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!src.rois || !src.rois.length) return;
  const srcW = src.frame_width || img.naturalWidth;
  const srcH = src.frame_height || img.naturalHeight;
  if (!srcW || !srcH) return;
  const scaleX = canvas.width / srcW, scaleY = canvas.height / srcH;
  src.rois.forEach((roi, idx) => {
    const color = roiColors[idx % roiColors.length];
    ctx.beginPath();
    roi.polygon.forEach((pt, i) => { const x = pt[0] * scaleX, y = pt[1] * scaleY; i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y); });
    ctx.closePath();
    ctx.fillStyle = color.fill; ctx.fill();
    ctx.strokeStyle = color.stroke; ctx.lineWidth = 2; ctx.stroke();
  });
}

function drawCanvasDuringDrawMode() {
  const canvas = document.getElementById('preview-canvas');
  if (!canvas) return;
  drawExistingROIs();
  const ctx = canvas.getContext('2d');
  const pts = state.currentPolygon;
  if (pts.length === 0) return;
  ctx.beginPath();
  pts.forEach((pt, i) => { i === 0 ? ctx.moveTo(pt.x, pt.y) : ctx.lineTo(pt.x, pt.y); });
  ctx.strokeStyle = '#10b981'; ctx.lineWidth = 2; ctx.stroke();
  pts.forEach(pt => { ctx.beginPath(); ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2); ctx.fillStyle = '#10b981'; ctx.fill(); });
  if (pts.length >= 3) {
    const first = pts[0];
    ctx.beginPath(); ctx.arc(first.x, first.y, 8, 0, Math.PI * 2);
    ctx.strokeStyle = '#10b981'; ctx.lineWidth = 2; ctx.setLineDash([4,4]); ctx.stroke(); ctx.setLineDash([]);
  }
}

function toggleDrawMode() {
  state.drawMode = !state.drawMode;
  document.getElementById('draw-area-btn').textContent = state.drawMode ? 'Cancel Drawing' : 'Draw Area';
  if (state.drawMode) document.getElementById('draw-actions').classList.remove('hidden');
  else { document.getElementById('draw-actions').classList.add('hidden'); state.currentPolygon = []; drawExistingROIs(); }
}

document.addEventListener('click', function(e) {
  if (!state.drawMode) return;
  const canvas = document.getElementById('preview-canvas');
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left, y = e.clientY - rect.top;
  if (x < 0 || x > canvas.width || y < 0 || y > canvas.height) return;
  if (state.currentPolygon.length >= 3) {
    const first = state.currentPolygon[0];
    const dist = Math.sqrt((x - first.x) ** 2 + (y - first.y) ** 2);
    if (dist <= 10) { document.getElementById('draw-actions').classList.remove('hidden'); drawCanvasDuringDrawMode(); return; }
  }
  state.currentPolygon.push({ x, y });
  drawCanvasDuringDrawMode();
});

async function savePolygon() {
  const src = getSource(state.selectedSourceId);
  if (!src || state.currentPolygon.length < 3) return;
  const canvas = document.getElementById('preview-canvas');
  const img = document.getElementById('preview-img');
  const srcW = src.frame_width || img.naturalWidth;
  const srcH = src.frame_height || img.naturalHeight;
  if (!srcW || !srcH) return;
  const scaleX = srcW / canvas.width, scaleY = srcH / canvas.height;
  const polygon = state.currentPolygon.map(pt => [Math.round(pt.x * scaleX), Math.round(pt.y * scaleY)]);
  const areaName = 'Area ' + ((src.rois || []).length + 1);
  try {
    const res = await fetchJSON('/api/sources/' + src.id + '/rois', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name: areaName, polygon }) });
    if (res.status >= 400) { alert('Error: ' + (res.data.error || 'Unknown')); return; }
    state.drawMode = false; state.currentPolygon = [];
    document.getElementById('draw-actions').classList.add('hidden');
    document.getElementById('draw-area-btn').textContent = 'Draw Area';
    await fetchSources();
    state.drawerTab = 'areas';
    switchDrawerTab('areas');
    renderDrawer();
  } catch (e) { alert('Network error: ' + e.message); }
}

function cancelDrawing() {
  state.drawMode = false; state.currentPolygon = [];
  document.getElementById('draw-actions').classList.add('hidden');
  document.getElementById('draw-area-btn').textContent = 'Draw Area';
  drawExistingROIs();
}

// AREAS TAB

function renderAreasTab() {
  const src = getSource(state.selectedSourceId);
  const container = document.getElementById('areas-list');
  if (!src || !src.rois || src.rois.length === 0) {
    container.innerHTML = '<div class="text-center py-8"><p class="text-body-md font-body-md text-on-surface-variant">No areas defined. Draw one in Preview.</p></div>';
    return;
  }
  container.innerHTML = src.rois.map(roi => {
    const eid = esc(roi.id);
    return `<details class="border border-outline-variant rounded-lg mb-2 overflow-hidden bg-surface-container-low">
      <summary class="flex items-center justify-between px-4 py-3 cursor-pointer font-bold text-body-md font-body-md hover:bg-surface-container transition-colors">
        <span>${esc(roi.name)}</span>
        <button onclick="event.stopPropagation(); deleteROI('${eid}', '${esc(roi.name)}')" class="p-1 rounded-full hover:bg-error-container text-on-surface-variant hover:text-error transition-all" title="Eliminar area">
          <span class="material-symbols-outlined" style="font-size:16px">delete</span>
        </button>
      </summary>
      <div class="px-4 py-3 border-t border-outline-variant">
        <label class="flex items-center gap-2 text-body-sm font-body-sm mb-2 cursor-pointer"><input type="checkbox" class="area-chk" data-field="detect_entry" ${roi.detect_entry ? 'checked' : ''} onchange="saveROIConfig('${eid}')"> Entry Detection</label>
        <label class="flex items-center gap-2 text-body-sm font-body-sm mb-2 cursor-pointer"><input type="checkbox" class="area-chk" data-field="detect_exit" ${roi.detect_exit ? 'checked' : ''} onchange="saveROIConfig('${eid}')"> Exit Detection</label>
        <label class="flex items-center gap-2 text-body-sm font-body-sm mb-2 cursor-pointer"><input type="checkbox" class="area-chk" data-field="detect_occupancy" ${roi.detect_occupancy ? 'checked' : ''} onchange="saveROIConfig('${eid}')"> Occupancy</label>
        <label class="flex items-center gap-2 text-body-sm font-body-sm mb-2 cursor-pointer"><input type="checkbox" class="area-chk" data-field="detect_dwell" ${roi.detect_dwell ? 'checked' : ''} onchange="saveROIConfig('${eid}')"> Dwell Time</label>
        <span id="config-msg-${eid}" class="text-body-sm font-body-sm text-primary"></span>
      </div>
    </details>`;
  }).join('');
}

async function saveROIConfig(roiId) {
  const msgEl = document.getElementById('config-msg-' + roiId);
  if (!msgEl) return;
  const details = msgEl.closest('details');
  if (!details) return;
  const config = {
    detect_entry: details.querySelector('.area-chk[data-field="detect_entry"]').checked,
    detect_exit: details.querySelector('.area-chk[data-field="detect_exit"]').checked,
    detect_occupancy: details.querySelector('.area-chk[data-field="detect_occupancy"]').checked,
    detect_dwell: details.querySelector('.area-chk[data-field="detect_dwell"]').checked,
  };
  msgEl.textContent = 'Saving...';
  try {
    const res = await fetchJSON('/api/rois/' + roiId + '/config', { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(config) });
    msgEl.textContent = res.status === 200 ? 'Saved!' : 'Error';
    msgEl.style.color = res.status === 200 ? '#005d54' : '#ba1a1a';
    setTimeout(() => msgEl.textContent = '', 2000);
  } catch (e) { msgEl.textContent = 'Network error'; msgEl.style.color = '#ba1a1a'; }
}

// DELETE SOURCE / ROI

async function deleteSource(id, name) {
  if (!confirm('Eliminar la fuente "' + name + '"? Esta accion no se puede deshacer.')) return;
  try {
    const res = await fetch('/api/sources/' + id, { method: 'DELETE' });
    if (res.status >= 400) {
      const data = await res.json().catch(() => ({}));
      alert('Error al eliminar: ' + (data.error || 'Error'));
      return;
    }
    if (state.selectedSourceId === id) closeDrawer();
    fetchSources();
  } catch (e) { alert('Error de red: ' + e.message); }
}

async function deleteROI(id, name) {
  if (!confirm('Eliminar el area "' + name + '"? Esta accion no se puede deshacer.')) return;
  try {
    const res = await fetch('/api/rois/' + id, { method: 'DELETE' });
    if (res.status >= 400) {
      const data = await res.json().catch(() => ({}));
      alert('Error al eliminar: ' + (data.error || 'Error'));
      return;
    }
    await fetchSources();
    renderDrawer();
    renderAreasTab();
  } catch (e) { alert('Error de red: ' + e.message); }
}

// SETTINGS TAB

function renderSettingsTab() {
  const src = getSource(state.selectedSourceId);
  if (!src) return;
  const settings = getSourceSettings(src.id);
  document.getElementById('settings-content').innerHTML = `
    <div class="mb-6">
      <h3 class="text-label-caps font-label-caps text-on-surface-variant mb-3">TRACKING CLASSES</h3>
      ${['person','car','bicycle','backpack'].map(cls => `
        <label class="flex items-center gap-2 text-body-sm font-body-sm mb-2 cursor-pointer">
          <input type="checkbox" class="settings-chk" data-class="${cls}" onchange="onTrackingClassChange('${esc(src.id)}')" ${(settings.tracking_classes||[]).includes(cls)?'checked':''}> ${cls.charAt(0).toUpperCase()+cls.slice(1)}
        </label>`).join('')}
    </div>
    <div class="mb-6">
      <h3 class="text-label-caps font-label-caps text-on-surface-variant mb-3">SEGUNDOS A ANALIZAR</h3>
      <div class="flex items-center gap-3">
        <input type="number" id="settings-maxseconds" class="flex-1 border border-outline-variant rounded-lg p-3 text-body-md font-body-md bg-background text-on-background" min="10" step="10" value="${settings.max_seconds||60}" ${settings.max_seconds===null?'disabled':''} onchange="updateSourceSetting('${esc(src.id)}','max_seconds',this.value?parseInt(this.value):null)">
        <label class="flex items-center gap-2 text-body-sm font-body-sm cursor-pointer whitespace-nowrap">
          <input type="checkbox" ${settings.max_seconds===null?'checked':''} onchange="toggleFullVideo('${esc(src.id)}')"> Video Completo
        </label>
      </div>
    </div>`;
}

function onTrackingClassChange(sourceId) {
  const settings = getSourceSettings(sourceId);
  settings.tracking_classes = Array.from(document.querySelectorAll('.settings-chk:checked')).map(cb => cb.dataset.class);
}
function updateSourceSetting(sourceId, key, value) { const settings = getSourceSettings(sourceId); settings[key] = value; }
function toggleFullVideo(sourceId) {
  const input = document.getElementById('settings-maxseconds');
  const checkbox = input.parentElement.querySelector('input[type="checkbox"]');
  if (checkbox.checked) { input.disabled = true; input.value = ''; updateSourceSetting(sourceId, 'max_seconds', null); }
  else { input.disabled = false; input.value = input.value || '60'; updateSourceSetting(sourceId, 'max_seconds', parseInt(input.value)); }
}

// ANALYSIS FLOW

function openAnalysisModal() {
  state.modalState = 'summary';
  state.modalSourceId = state.selectedSourceId;
  state.modalSessionId = null;
  state.modalError = null;
  state.pollingInterval = null;
  renderModal();
}

function closeModal() {
  if (state.pollingInterval) { clearInterval(state.pollingInterval); state.pollingInterval = null; }
  document.getElementById('modal').classList.add('hidden');
  state.modalOpen = false;
}

function renderModal() {
  const modal = document.getElementById('modal');
  const body = document.getElementById('modal-body');
  modal.classList.remove('hidden');
  const src = state.modalSourceId ? getSource(state.modalSourceId) : null;
  const srcName = src ? src.name : '...';
  if (state.modalState === 'summary') {
    const settings = getSourceSettings(state.modalSourceId);
    document.getElementById('modal-title').textContent = 'Run Analysis — ' + srcName;
    body.innerHTML = `
      <div class="space-y-3 mb-6">
        <div class="flex justify-between py-2 border-b border-outline-variant"><span class="text-body-sm font-body-sm text-on-surface-variant">Source</span><span class="text-body-sm font-body-sm font-bold">${esc(srcName)}</span></div>
        <div class="flex justify-between py-2 border-b border-outline-variant"><span class="text-body-sm font-body-sm text-on-surface-variant">Tracking</span><span class="text-body-sm font-body-sm font-bold">${(settings.tracking_classes||['person']).join(', ')}</span></div>
        <div class="flex justify-between py-2 border-b border-outline-variant"><span class="text-body-sm font-body-sm text-on-surface-variant">Segundos a Analizar</span><span class="text-body-sm font-body-sm font-bold">${settings.max_seconds ? settings.max_seconds + 's' : 'Video Completo'}</span></div>
        <div class="flex justify-between py-2"><span class="text-body-sm font-body-sm text-on-surface-variant">Areas</span><span class="text-body-sm font-body-sm font-bold">${src&&src.rois?src.rois.length:0} area${src&&src.rois&&src.rois.length!==1?'s':''}</span></div>
      </div>
      <div class="flex gap-3">
        <button class="flex-1 border border-outline text-on-surface-variant py-3 font-bold hover:bg-surface-container transition-all" onclick="closeModal()">Cancel</button>
        <button class="flex-1 bg-primary text-on-primary py-3 font-bold hover:bg-primary-container transition-all" onclick="startAnalysis()">Generate →</button>
      </div>`;
  } else if (state.modalState === 'progress') {
    document.getElementById('modal-title').textContent = 'Processing';
    body.innerHTML = '<div class="text-center py-6"><div class="spinner mx-auto"></div><p class="text-body-md font-body-md text-on-surface-variant mt-4">Processing video analysis...</p><div class="progress-bar"><div class="progress-bar-fill" id="progress-fill"></div></div><p id="progress-text" class="text-body-sm font-body-sm text-on-surface-variant">Starting...</p></div>';
  } else if (state.modalState === 'result') {
    document.getElementById('modal-title').textContent = 'Analysis Complete';
    var sid = state.modalSessionId;
    body.innerHTML = '<div class="text-center py-6"><div class="text-5xl mb-3 text-green-600">✓</div><h3 class="text-headline-md font-headline-md font-bold mb-2">Complete!</h3><p class="text-body-sm font-body-sm text-on-surface-variant">Session ID: ' + esc(sid) + '</p></div><div class="flex gap-3"><button class="flex-1 border border-outline text-on-surface-variant py-3 font-bold hover:bg-surface-container transition-all" onclick="closeModal()">Close</button><button class="flex-1 bg-primary text-on-primary py-3 font-bold hover:brightness-110 transition-all" onclick="closeModal(); viewAnalysis(\'' + sid + '\')">View Report</button></div>';
  } else if (state.modalState === 'error') {
    document.getElementById('modal-title').textContent = 'Analysis Failed';
    body.innerHTML = '<div class="text-center py-6"><div class="text-5xl mb-3 text-error">✗</div><p class="text-body-md font-body-md text-error">' + esc(state.modalError || 'Unknown error') + '</p></div><div class="flex gap-3"><button class="flex-1 border border-outline text-on-surface-variant py-3 font-bold hover:bg-surface-container transition-all" onclick="closeModal()">Close</button><button class="flex-1 bg-primary text-on-primary py-3 font-bold hover:bg-primary-container transition-all" onclick="retryAnalysis()">Retry</button></div>';
  }
}

function retryAnalysis() { state.modalState = 'summary'; renderModal(); }

function startAnalysis() {
  if (!state.modalSourceId) return;
  const settings = getSourceSettings(state.modalSourceId);
  state.modalState = 'progress'; renderModal();
  fetchJSON('/process', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ video_source_id: state.modalSourceId, tracking_classes: settings.tracking_classes || ['person'], frame_skip: 1, max_seconds: settings.max_seconds, metrics: { entries: true, exits: true, occupancy: true, dwell_time: false, heatmap: false }, output: { report: true, annotated_video: true } }) })
  .then(({status, data}) => {
    if (status >= 400) { state.modalState = 'error'; state.modalError = data.error || 'Failed'; renderModal(); return; }
    state.pollingInterval = setInterval(pollJobStatus, 2000);
  }).catch(err => { state.modalState = 'error'; state.modalError = err.message; renderModal(); });
}

function pollJobStatus() {
  fetch('/api/job/status').then(r => r.json()).then(status => {
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-text');
    if (fill && status.total_frames > 0) fill.style.width = (status.progress * 100) + '%';
    if (text) text.textContent = status.message || (status.frames_done + '/' + (status.total_frames || '?') + ' frames');
    if (!status.running) {
      if (state.pollingInterval) { clearInterval(state.pollingInterval); state.pollingInterval = null; }
      if (status.error) { state.modalState = 'error'; state.modalError = status.error; renderModal(); }
      else { state.modalState = 'result'; state.modalSessionId = status.session_id; renderModal(); if (state.tab === 'jobs') fetchSessions(); }
    }
  }).catch(() => {});
}

// JOBS TAB

async function fetchSessions() {
  const err = document.getElementById('jobs-error');
  try {
    const res = await fetchJSON('/api/sessions');
    if (res.status >= 400) { err.classList.remove('hidden'); document.getElementById('jobs-error-msg').textContent = res.data.error || 'Failed'; return; }
    err.classList.add('hidden');
    state.sessions = res.data;
    renderSessions();
  } catch (e) { err.classList.remove('hidden'); document.getElementById('jobs-error-msg').textContent = e.message; }
}

function renderSessions() {
  const content = document.getElementById('jobs-content');
  if (state.sessions.length === 0) { content.innerHTML = '<div class="text-center py-12"><p class="text-body-md font-body-md text-on-surface-variant">No jobs yet. Run an analysis from a source.</p></div>'; return; }
  content.innerHTML = '<div class="overflow-x-auto"><table class="w-full text-left border-collapse"><thead><tr class="bg-surface-container-low"><th class="px-6 py-4 text-label-caps font-label-caps text-secondary uppercase border-b border-outline-variant">Source</th><th class="px-6 py-4 text-label-caps font-label-caps text-secondary uppercase border-b border-outline-variant">Status</th><th class="px-6 py-4 text-label-caps font-label-caps text-secondary uppercase border-b border-outline-variant">Date</th><th class="px-6 py-4 text-label-caps font-label-caps text-secondary uppercase border-b border-outline-variant">Duration</th><th class="px-6 py-4 text-label-caps font-label-caps text-secondary uppercase border-b border-outline-variant">Entities</th><th class="px-6 py-4 text-label-caps font-label-caps text-secondary uppercase border-b border-outline-variant text-right">Actions</th></tr></thead><tbody class="divide-y divide-outline-variant">' + state.sessions.map(s => {
    const status = (s.status || 'completed').toLowerCase();
    let badge = status === 'completed' ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#e8f5f3] text-[#13776d]"><span class="w-1.5 h-1.5 rounded-full bg-primary mr-2"></span>Completed</span>' : status === 'failed' ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-error-container text-error"><span class="w-1.5 h-1.5 rounded-full bg-error mr-2"></span>Failed</span>' : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800"><span class="mini-spinner mr-2"></span>Running</span>';
    let action = status === 'completed' ? '<a href="/api/sessions/' + esc(s.id) + '/report" target="_blank" class="bg-primary text-on-primary text-label-caps font-bold px-4 py-1.5 rounded-lg uppercase shadow-sm hover:brightness-110 active:scale-95 transition-all" style="text-decoration:none">Report</a>' : '<button class="border border-outline text-outline text-label-caps font-bold px-4 py-1.5 rounded-lg uppercase hover:bg-surface-container transition-all">Details</button>';
    return '<tr class="hover:bg-surface-container transition-colors"><td class="px-6 py-4 text-body-md font-body-md text-on-surface">' + esc(s.source_name || '-') + '</td><td class="px-6 py-4">' + badge + '</td><td class="px-6 py-4 text-data-mono font-data-mono text-outline">' + formatDate(s.started_at) + '</td><td class="px-6 py-4 text-data-mono font-data-mono text-outline">' + formatDuration(s.duration_seconds) + '</td><td class="px-6 py-4 text-data-mono font-data-mono text-outline">' + (s.total_entities != null ? s.total_entities : '-') + '</td><td class="px-6 py-4 text-right">' + action + '</td></tr>';
  }).join('') + '</tbody></table></div>';
}

// ANALYTICS CHARTS

function formatDwell(sec) {
  if (sec == null || sec === 0) return '-';
  if (sec < 60) return Math.round(sec) + 's';
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return m + 'm ' + s + 's';
}

async function fetchOccupancyTrends() {
  const container = document.getElementById('occupancy-bars');
  if (!container) return;
  try {
    const res = await fetch('/api/analytics/occupancy-trends');
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) {
      container.innerHTML = '<div class="w-full text-center py-8 text-body-sm font-body-sm text-on-surface-variant">No occupancy data for the last 24h</div>';
      return;
    }
    const maxVal = Math.max(...data.map(d => d.avg_occupancy), 1);
    container.innerHTML = data.map(d => {
      const h = Math.max((d.avg_occupancy / maxVal) * 100, 2);
      const time = new Date(d.hour);
      const label = time.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
      const isPeak = d.avg_occupancy === maxVal;
      return '<div class="flex-1 flex flex-col items-center gap-1 h-full justify-end">' +
        '<span class="text-data-mono font-data-mono text-primary text-[10px]">' + d.avg_occupancy + '</span>' +
        '<div class="w-full rounded-t-sm transition-all ' + (isPeak ? 'bg-primary' : 'bg-primary/30 hover:bg-primary/50') + '" style="height:' + h + '%" title="' + label + ' - ' + d.avg_occupancy + ' people"></div>' +
        '<span class="text-[9px] text-outline truncate w-full text-center">' + label + '</span></div>';
    }).join('');
  } catch (e) {
    container.innerHTML = '<div class="w-full text-center py-8 text-body-sm font-body-sm text-error">Failed to load trends</div>';
  }
}

async function fetchDwellTimes() {
  const container = document.getElementById('dwell-times-content');
  if (!container) return;
  try {
    const res = await fetch('/api/analytics/dwell-times');
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) {
      container.innerHTML = '<div class="text-center py-8"><p class="text-body-sm font-body-sm text-on-surface-variant">No dwell time data yet. Run an analysis with Dwell Time enabled.</p></div>';
      return;
    }
    const maxVal = Math.max(...data.map(d => d.avg_dwell_seconds), 1);
    container.innerHTML = data.map(d => {
      const pct = Math.min((d.avg_dwell_seconds / maxVal) * 100, 100);
      return '<div class="space-y-2">' +
        '<div class="flex justify-between text-body-sm font-body-sm">' +
        '<span class="text-on-surface">' + esc(d.roi_name) + '</span>' +
        '<span class="font-data-mono text-primary font-bold">' + formatDwell(d.avg_dwell_seconds) + '</span>' +
        '</div>' +
        '<div class="w-full bg-surface-container h-2 rounded-full overflow-hidden"><div class="bg-primary h-full rounded-full" style="width:' + pct + '%;"></div></div>' +
        '</div>';
    }).join('');
  } catch (e) {
    container.innerHTML = '<div class="text-center py-8"><p class="text-body-sm font-body-sm text-error">Failed to load dwell times</p></div>';
  }
}

function exportReport() { alert('Export feature coming soon'); }

// LOGS SIMULATION
async function fetchLogs() {
  const container = document.getElementById('logs-content');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-12"><div class="spinner mx-auto mb-2"></div><p class="text-body-sm text-on-surface-variant">Cargando...</p></div>';
  try {
    const res = await fetch('/api/logs/data');
    const data = await res.json();
    if (!data || data.error) {
      container.innerHTML = '<div class="text-center py-12"><p class="text-body-md font-body-md text-on-surface-variant">Error al cargar logs: ' + (data ? data.error : 'sin datos') + '</p></div>';
      return;
    }
    var r = data.resources || {};
    var problems = data.problems || [];

    // ── Resource cards ──
    var uptimeStr = formatUptime(r.uptime_seconds);
    var cards = [
      { label: 'CPU', value: (r.cpu_percent != null ? r.cpu_percent : '-') + '%', sub: (r.cpu_count || '-') + ' cores', icon: 'memory', color: 'text-primary' },
      { label: 'Memoria', value: (r.memory_mb != null ? r.memory_mb : '-') + ' MB', sub: (r.memory_percent != null ? r.memory_percent + '% del total' : ''), icon: 'ram', color: 'text-secondary' },
      { label: 'Disco', value: (r.disk_mb != null ? r.disk_mb : '-') + ' MB', sub: 'proyecto (sin .venv)', icon: 'storage', color: 'text-tertiary' },
      { label: 'Actividad', value: uptimeStr, sub: (r.threads || '-') + ' hilos · ' + (r.open_files || '-') + ' archivos', icon: 'speed', color: 'text-primary' },
    ];
    var cardsHtml = '<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">' + cards.map(function(c) {
      return '<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4"><div class="flex items-center justify-between mb-2"><p class="text-label-caps font-label-caps text-secondary uppercase">' + c.label + '</p><span class="material-symbols-outlined ' + c.color + ' opacity-50" style="font-size:20px">' + c.icon + '</span></div><p class="text-headline-md font-headline-md font-bold ' + c.color + '">' + c.value + '</p><p class="text-body-xs font-body-xs text-on-surface-variant mt-1">' + c.sub + '</p></div>';
    }).join('') + '</div>';

    // ── Python version row ──
    var pyRow = r.python_version
      ? '<div class="bg-surface-container-lowest border border-outline-variant rounded-xl px-5 py-3 mb-6 flex items-center gap-3"><span class="material-symbols-outlined text-on-surface-variant" style="font-size:18px">code</span><span class="text-body-sm text-on-surface-variant">Python <span class="font-data-mono font-bold text-on-surface">' + esc(r.python_version) + '</span></span></div>'
      : '';

    // ── Problems section ──
    var problemsHtml = '';
    if (problems.length === 0) {
      problemsHtml = '<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-8 text-center"><span class="material-symbols-outlined text-outline mb-2" style="font-size:40px">check_circle</span><p class="text-body-md font-body-md text-on-surface-variant">No hay problemas registrados.</p></div>';
    } else {
      var problemRows = '';
      for (var p = 0; p < problems.length; p++) {
        var pr = problems[p];
        var icon = pr.type === 'session_failed' ? 'error' : (pr.type === 'overcapacity' ? 'warning' : 'timer_off');
        var badgeClass = pr.type === 'session_failed' ? 'bg-error/10 text-error' : (pr.type === 'overcapacity' ? 'bg-secondary/10 text-secondary' : 'bg-tertiary/10 text-tertiary');
        var badgeLabel = pr.type === 'session_failed' ? 'Fallo' : (pr.type === 'overcapacity' ? 'Sobrecarga' : 'Dwell Excedido');
        var time = pr.occurred_at ? new Date(pr.occurred_at).toLocaleString() : '-';
        problemRows += '<tr class="border-b border-outline-variant hover:bg-surface-container/50 transition-colors">' +
          '<td class="p-3"><span class="material-symbols-outlined ' + badgeClass.replace('bg-', 'text-').split(' ')[0] + '" style="font-size:20px">' + icon + '</span></td>' +
          '<td class="p-3"><span class="px-2 py-0.5 rounded text-xs font-bold ' + badgeClass + '">' + badgeLabel + '</span></td>' +
          '<td class="p-3 text-body-sm text-on-surface">' + esc(pr.detail) + '</td>' +
          '<td class="p-3 text-body-sm text-on-surface-variant font-data-mono">' + time + '</td>' +
          '</tr>';
      }
      problemsHtml = '<div class="bg-surface-container-lowest border border-outline-variant rounded-xl"><div class="flex items-center justify-between px-5 py-4 border-b border-outline-variant"><h3 class="text-label-caps font-label-caps text-secondary uppercase">Problemas y Alertas</h3><span class="text-body-sm text-on-surface-variant font-data-mono">' + problems.length + ' eventos</span></div><div class="overflow-x-auto max-h-[500px] overflow-y-auto"><table class="w-full text-left"><thead class="sticky top-0 bg-surface-container-lowest"><tr class="border-b border-outline-variant text-label-caps text-secondary uppercase"><th class="p-3 font-medium"></th><th class="p-3 font-medium">Tipo</th><th class="p-3 font-medium">Detalle</th><th class="p-3 font-medium">Fecha</th></tr></thead><tbody>' + problemRows + '</tbody></table></div></div>';
    }

    container.innerHTML = cardsHtml + pyRow + problemsHtml;
  } catch (e) {
    container.innerHTML = '<div class="text-center py-12"><p class="text-body-md font-body-md text-on-surface-variant">Error al cargar logs: ' + e.message + '</p></div>';
  }
}

function formatUptime(sec) {
  if (sec == null) return '-';
  var d = Math.floor(sec / 86400);
  var h = Math.floor((sec % 86400) / 3600);
  var m = Math.floor((sec % 3600) / 60);
  var s = Math.round(sec % 60);
  var parts = [];
  if (d > 0) parts.push(d + 'd');
  if (h > 0) parts.push(h + 'h');
  if (m > 0) parts.push(m + 'm');
  parts.push(s + 's');
  return parts.join(' ');
}

// FILE UPLOAD

document.addEventListener('DOMContentLoaded', function() {
  const fileInput = document.getElementById('new-file-input');
  if (fileInput) {
    fileInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) { pendingSourceFile = file; document.getElementById('file-selected-name').textContent = file.name; }
    });
  }
  const dropzone = document.getElementById('file-dropzone');
  if (dropzone) {
    dropzone.addEventListener('dragover', function(e) { e.preventDefault(); this.classList.add('border-primary'); });
    dropzone.addEventListener('dragleave', function() { this.classList.remove('border-primary'); });
    dropzone.addEventListener('drop', function(e) { e.preventDefault(); this.classList.remove('border-primary'); const file = e.dataTransfer.files[0]; if (file) { pendingSourceFile = file; document.getElementById('file-selected-name').textContent = file.name; document.getElementById('new-file-input').files = e.dataTransfer.files; } });
  }
  // Set current date
  const dateEl = document.getElementById('current-date-label');
  if (dateEl) {
    const d = new Date();
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    dateEl.textContent = months[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
  }
  // Initial load
  fetchSources();
});

async function fetchDashboard() {
  var dashEl = document.getElementById('dash-cards');
  if (dashEl) dashEl.innerHTML = '<div class="col-span-full text-center py-12"><div class="spinner mx-auto mb-2"></div><p class="text-body-sm text-on-surface-variant">Cargando...</p></div>';
  try {
    const res = await fetch('/api/dashboard');
    const d = await res.json();
    renderDashCards(d);
    renderSourceChart(d.events_by_source);
    renderROIChart(d.top_rois);
    renderRecentSessions(d.recent_sessions);
    renderHourlyChart(d.hourly_distribution);
  } catch (e) {
    const el = document.getElementById('dash-cards');
    if (el) el.innerHTML = '<div class="col-span-full text-center py-8 text-error">Error cargando dashboard</div>';
  }
}

function renderDashCards(d) {
  const container = document.getElementById('dash-cards');
  if (!container) return;
  const cards = [
    { label: 'Entradas', value: d.total_entries || 0, icon: 'login', color: 'text-primary' },
    { label: 'Salidas', value: d.total_exits || 0, icon: 'logout', color: 'text-secondary' },
    { label: 'Entidades Unicas', value: d.total_entities || 0, icon: 'groups', color: 'text-tertiary' },
    { label: 'Horas Analizadas', value: (d.total_hours_analyzed || 0) + 'h', icon: 'schedule', color: 'text-primary' },
    { label: 'Fuentes Activas', value: (d.sources_with_rois || 0) + '/' + (d.total_sources || 0), icon: 'videocam', color: 'text-tertiary' },
  ];
  container.innerHTML = cards.map(c => `
    <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
      <div class="flex items-center justify-between mb-3">
        <p class="text-label-caps font-label-caps text-secondary uppercase">${c.label}</p>
        <span class="material-symbols-outlined ${c.color} opacity-60" style="font-size:20px">${c.icon}</span>
      </div>
      <p class="text-headline-lg font-headline-lg font-bold ${c.color}">${c.value}</p>
    </div>
  `).join('');
}

function renderSourceChart(sources) {
  const el = document.getElementById('dash-source-chart');
  if (!el) return;
  if (!sources || sources.length === 0) {
    el.innerHTML = '<p class="text-body-sm text-on-surface-variant text-center py-8">Sin datos de actividad por fuente.</p>';
    return;
  }
  const maxVal = Math.max(...sources.map(s => (s.entries || 0) + (s.exits || 0)), 1);
  el.innerHTML = sources.map(s => {
    const total = (s.entries || 0) + (s.exits || 0);
    const pct = Math.max((total / maxVal) * 100, 4);
    const entryPct = total > 0 ? ((s.entries || 0) / total) * 100 : 0;
    return `
      <div>
        <div class="flex justify-between text-body-sm font-body-sm mb-1">
          <span class="text-on-surface font-medium">${esc(s.source_name)}</span>
          <span class="text-on-surface-variant">${s.entries || 0} ent / ${s.exits || 0} sal</span>
        </div>
        <div class="w-full bg-surface-container-higher h-5 rounded-full overflow-hidden flex">
          <div class="bg-primary h-full transition-all" style="width:${Math.round(entryPct * pct / 100)}%" title="Entradas: ${s.entries || 0}"></div>
          <div class="bg-secondary h-full transition-all" style="width:${Math.round((100 - entryPct) * pct / 100)}%" title="Salidas: ${s.exits || 0}"></div>
        </div>
      </div>`;
  }).join('');
}

function renderROIChart(rois) {
  const el = document.getElementById('dash-roi-chart');
  if (!el) return;
  if (!rois || rois.length === 0) {
    el.innerHTML = '<p class="text-body-sm text-on-surface-variant text-center py-8">Sin datos de areas.</p>';
    return;
  }
  const maxVal = Math.max(...rois.map(r => (r.entries || 0) + (r.exits || 0)), 1);
  el.innerHTML = rois.map(r => {
    const total = (r.entries || 0) + (r.exits || 0);
    const pct = Math.max((total / maxVal) * 100, 4);
    return `
      <div>
        <div class="flex justify-between text-body-sm font-body-sm mb-1">
          <span class="text-on-surface font-medium">${esc(r.name)}</span>
          <span class="text-on-surface-variant">${r.entries || 0} entradas</span>
        </div>
        <div class="w-full bg-surface-container-higher h-2 rounded-full overflow-hidden">
          <div class="bg-tertiary h-full rounded-full transition-all" style="width:${pct}%"></div>
        </div>
      </div>`;
  }).join('');
}

function renderRecentSessions(sessions) {
  const el = document.getElementById('dash-recent-sessions');
  if (!el) return;
  if (!sessions || sessions.length === 0) {
    el.innerHTML = '<p class="text-body-sm text-on-surface-variant text-center py-4">No hay analisis recientes.</p>';
    return;
  }
  const rows = sessions.map(s => {
    const dur = formatDuration(s.duration_seconds);
    const statusBadge = s.status === 'completed'
      ? '<span class="inline-flex items-center gap-1 text-xs font-medium text-primary"><span class="w-1.5 h-1.5 bg-primary rounded-full"></span>Completado</span>'
      : '<span class="inline-flex items-center gap-1 text-xs font-medium text-error"><span class="w-1.5 h-1.5 bg-error rounded-full"></span>Fallido</span>';
    const date = s.started_at ? new Date(s.started_at).toLocaleString() : '-';
    return `<tr class="border-b border-outline-variant hover:bg-surface-container transition-colors">
      <td class="p-3 text-body-sm font-body-sm">${esc(s.source_name || '-')}</td>
      <td class="p-3 text-body-sm text-on-surface-variant">${date}</td>
      <td class="p-3 text-body-sm text-on-surface-variant font-data-mono">${dur}</td>
      <td class="p-3">${statusBadge}</td>
    </tr>`;
  }).join('');
  el.innerHTML = `<div class="overflow-x-auto"><table class="w-full text-left"><thead>
    <tr class="text-label-caps text-secondary uppercase border-b border-outline-variant">
      <th class="p-3 font-medium">Fuente</th>
      <th class="p-3 font-medium">Fecha</th>
      <th class="p-3 font-medium">Duracion</th>
      <th class="p-3 font-medium">Estado</th>
    </tr>
  </thead><tbody>${rows}</tbody></table></div>`;
}

function renderHourlyChart(hourly) {
  const el = document.getElementById('dash-hourly-chart');
  if (!el) return;
  if (!hourly || hourly.length === 0) {
    el.innerHTML = '<p class="text-body-sm text-on-surface-variant text-center py-8">Sin datos de distribucion horaria.</p>';
    return;
  }
  const maxVal = Math.max(...hourly.map(h => Math.max(h.entries || 0, h.exits || 0)), 1);
  const full = Array.from({length: 24}, (_, i) => {
    const found = hourly.find(h => h.hour === i);
    return found || { hour: i, entries: 0, exits: 0 };
  });
  el.innerHTML = `<div class="h-full flex items-end gap-px relative">
    <div class="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
      <div class="border-t border-outline h-px w-full"></div>
      <div class="border-t border-outline h-px w-full"></div>
      <div class="border-t border-outline h-px w-full"></div>
    </div>
    ${full.map(h => {
      const entryPct = Math.max((h.entries / maxVal) * 100, 2);
      const exitPct = Math.max((h.exits / maxVal) * 100, 2);
      return `<div class="flex-1 flex flex-col items-center justify-end self-stretch relative z-10" style="padding-bottom:14px">
        <div class="flex gap-px items-end justify-center flex-1 w-full">
          <div class="w-[7px] bg-primary rounded-t-sm transition-all min-h-[2px]" style="height:${entryPct}%" title="${String(h.hour).padStart(2,'0')}:00 Entradas: ${h.entries}"></div>
          <div class="w-[7px] bg-secondary rounded-t-sm transition-all min-h-[2px]" style="height:${exitPct}%" title="${String(h.hour).padStart(2,'0')}:00 Salidas: ${h.exits}"></div>
        </div>
        ${h.hour % 4 === 0 ? `<span class="text-[8px] text-outline absolute bottom-0">${String(h.hour).padStart(2,'0')}</span>` : ''}
      </div>`;
    }).join('')}
  </div>`;
}

async function fetchAnalyses() {
  const container = document.getElementById('analyses-content');
  if (!container) return;
  var errDiv = document.getElementById('analyses-error');
  if (errDiv) errDiv.classList.add('hidden');
  container.innerHTML = '<div class="col-span-full text-center py-12"><div class="spinner mx-auto mb-2"></div><p class="text-body-sm text-on-surface-variant">Cargando...</p></div>';
  try {
    const res = await fetch('/api/analyses');
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) {
      container.innerHTML = '<div class="col-span-full text-center py-12"><p class="text-body-md font-body-md text-on-surface-variant">No hay analisis aun.</p></div>';
      return;
    }
    var rows = '';
    for (var i = 0; i < data.length; i++) {
      var s = data[i];
      var started = s.started_at ? new Date(s.started_at).toLocaleString() : '-';
      var dur = formatDuration(s.duration_seconds);
      var typeLabel = sourceTypeLabel(s.source_type);
      var statusBadge = s.status === 'completed'
        ? '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary"><span class="w-1.5 h-1.5 bg-primary rounded-full"></span>Completado</span>'
        : '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-error/10 text-error"><span class="w-1.5 h-1.5 bg-error rounded-full"></span>Fallido</span>';
      rows += '<tr class="border-b border-outline-variant hover:bg-surface-container transition-colors">' +
        '<td class="p-4 text-body-sm font-body-sm text-on-surface">' + esc(s.source_name || '-') + '</td>' +
        '<td class="p-4"><span class="text-label-caps text-xs font-bold text-on-surface-variant bg-surface-container-higher px-2 py-1 rounded">' + typeLabel + '</span></td>' +
        '<td class="p-4 text-body-sm text-on-surface-variant">' + started + '</td>' +
        '<td class="p-4 text-body-sm font-data-mono text-on-surface-variant">' + dur + '</td>' +
        '<td class="p-4">' + statusBadge + '</td>' +
        '<td class="p-4 text-right"><button class="bg-primary text-on-primary text-label-caps font-bold px-4 py-1.5 rounded-lg uppercase hover:brightness-110 transition-all" onclick="viewAnalysis(\'' + s.id + '\')">Ver detalle</button></td>' +
        '</tr>';
    }
    container.innerHTML = '<div class="overflow-x-auto bg-surface-container-lowest border border-outline-variant rounded-xl"><table class="w-full text-left"><thead><tr class="border-b border-outline-variant text-label-caps text-secondary uppercase bg-surface-container-low"><th class="p-4 font-medium">Fuente</th><th class="p-4 font-medium">Tipo</th><th class="p-4 font-medium">Fecha</th><th class="p-4 font-medium">Duracion</th><th class="p-4 font-medium">Estado</th><th class="p-4 font-medium text-right">Accion</th></tr></thead><tbody>' + rows + '</tbody></table></div>';
  } catch (e) {
    var errMsg = document.getElementById('analyses-error-msg');
    if (errMsg) errMsg.textContent = e.message;
    var errDiv = document.getElementById('analyses-error');
    if (errDiv) errDiv.classList.remove('hidden');
    container.innerHTML = '';
  }
}

async function viewAnalysis(id) {
  try {
    var res = await fetch('/api/analyses/' + id);
    if (!res.ok) return;
    var data = await res.json();

    var sourceName = esc(data.source_name || '-');
    var dateStr = data.started_at ? new Date(data.started_at).toLocaleString() : '-';
    var durStr = formatDuration(data.duration_seconds);
    var statusBadge = data.status === 'completed'
      ? '<span class="inline-flex items-center gap-1 text-xs font-medium text-primary"><span class="w-1.5 h-1.5 bg-primary rounded-full"></span>Completado</span>'
      : '<span class="inline-flex items-center gap-1 text-xs font-medium text-error"><span class="w-1.5 h-1.5 bg-error rounded-full"></span>Fallido</span>';

    var totalEntities = data.total_entities || 0;
    var totalEntries = data.total_entries || 0;
    var totalExits = data.total_exits || 0;
    var totalEvents = data.total_events || 0;

    // ── Header summary cards ──
    var headerCards = [
      { label: 'Entradas', value: totalEntries, icon: 'login', color: 'text-primary' },
      { label: 'Salidas', value: totalExits, icon: 'logout', color: 'text-secondary' },
      { label: 'Entidades Detectadas', value: totalEntities, icon: 'groups', color: 'text-tertiary' },
      { label: 'Eventos Totales', value: totalEvents, icon: 'timeline', color: 'text-primary' },
    ];
    var headerHtml = '<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">' + headerCards.map(function(c) {
      return '<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5"><div class="flex items-center justify-between mb-2"><p class="text-label-caps font-label-caps text-secondary uppercase">' + c.label + '</p><span class="material-symbols-outlined ' + c.color + ' opacity-60" style="font-size:20px">' + c.icon + '</span></div><p class="text-headline-md font-headline-md font-bold ' + c.color + '">' + c.value + '</p></div>';
    }).join('') + '</div>';

    // ── Video + Info row (side by side) ──
    var videoUrl = data.output_video_path ? data.output_video_path : null;
    var videoHtml = videoUrl
      ? '<div class="lg:w-1/2"><div class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden"><video class="w-full aspect-video object-contain bg-black" controls preload="metadata"><source src="' + videoUrl + '" type="video/mp4"></video><div class="px-4 py-2 border-t border-outline-variant flex items-center gap-2"><span class="material-symbols-outlined text-on-surface-variant" style="font-size:16px">download</span><a href="' + videoUrl + '" download class="text-body-sm text-primary hover:underline">Descargar video</a></div></div></div>'
      : '';
    var infoHtml = '<div class="flex flex-col lg:flex-row gap-6 mb-6">' + videoHtml +
      '<div class="' + (videoUrl ? 'lg:w-1/2' : 'w-full') + '"><div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 h-full"><div class="grid grid-cols-2 gap-4"><div><p class="text-label-caps text-secondary uppercase text-xs mb-1">Fuente</p><p class="text-body-md font-body-md font-bold text-on-surface">' + sourceName + '</p></div><div><p class="text-label-caps text-secondary uppercase text-xs mb-1">Fecha</p><p class="text-body-md font-body-md text-on-surface-variant">' + dateStr + '</p></div><div><p class="text-label-caps text-secondary uppercase text-xs mb-1">Duracion</p><p class="text-body-md font-body-md text-on-surface-variant font-data-mono">' + durStr + '</p></div><div><p class="text-label-caps text-secondary uppercase text-xs mb-1">Estado</p><p class="text-body-md font-body-md">' + statusBadge + '</p></div></div></div></div></div>';

    // ── Metrics per ROI table ──
    var metricsRows = '';
    if (Array.isArray(data.metrics) && data.metrics.length > 0) {
      for (var m = 0; m < data.metrics.length; m++) {
        var met = data.metrics[m];
        var roiName = met.roi_id ? met.roi_id.substring(0, 8) + '...' : '-';
        var dwellStr = met.avg_dwell_seconds ? met.avg_dwell_seconds.toFixed(1) + 's' : '-';
        metricsRows += '<tr class="border-b border-outline-variant">' +
          '<td class="p-3 text-body-sm font-body-sm text-on-surface">' + esc(roiName) + '</td>' +
          '<td class="p-3 text-body-sm text-center font-data-mono text-primary font-bold">' + (met.entries || 0) + '</td>' +
          '<td class="p-3 text-body-sm text-center font-data-mono text-secondary font-bold">' + (met.exits || 0) + '</td>' +
          '<td class="p-3 text-body-sm text-center font-data-mono text-on-surface-variant">' + (met.max_occupancy || 0) + '</td>' +
          '<td class="p-3 text-body-sm text-center font-data-mono text-on-surface-variant">' + dwellStr + '</td></tr>';
      }
    }
    var metricsTable = metricsRows
      ? '<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 mb-6"><h4 class="text-label-caps font-label-caps text-secondary uppercase mb-4">Metricas por Area (ROI)</h4><div class="overflow-x-auto"><table class="w-full text-left"><thead><tr class="border-b border-outline-variant text-label-caps text-secondary uppercase"><th class="p-3 font-medium">ROI</th><th class="p-3 font-medium text-center">Entradas</th><th class="p-3 font-medium text-center">Salidas</th><th class="p-3 font-medium text-center">Pico</th><th class="p-3 font-medium text-center">Dwell Avg</th></tr></thead><tbody>' + metricsRows + '</tbody></table></div></div>'
      : '';

    // ── Individual event log ──
    var eventRows = '';
    if (Array.isArray(data.zone_events) && data.zone_events.length > 0) {
      for (var e = 0; e < data.zone_events.length; e++) {
        var ev = data.zone_events[e];
        var evTime = ev.occurred_at ? new Date(ev.occurred_at).toLocaleTimeString() : '-';
        var evTypeIcon = ev.event_type === 'entry'
          ? '<span class="inline-flex items-center gap-1 text-xs font-medium text-primary"><span class="w-2 h-2 bg-primary rounded-full"></span>ENTRADA</span>'
          : '<span class="inline-flex items-center gap-1 text-xs font-medium text-secondary"><span class="w-2 h-2 bg-secondary rounded-full"></span>SALIDA</span>';
        var dwellStr2 = ev.dwell_seconds ? formatDwell(ev.dwell_seconds) : '-';
        eventRows += '<tr class="border-b border-outline-variant hover:bg-surface-container/50 transition-colors">' +
          '<td class="p-3 text-body-sm font-data-mono text-on-surface-variant">' + evTime + '</td>' +
          '<td class="p-3">' + evTypeIcon + '</td>' +
          '<td class="p-3 text-body-sm text-on-surface">' + esc(ev.roi_name || '-') + '</td>' +
          '<td class="p-3 text-body-sm font-data-mono text-on-surface-variant">' + (ev.track_id != null ? 'ID ' + ev.track_id : '-') + '</td>' +
          '<td class="p-3 text-body-sm font-data-mono text-on-surface-variant">' + (ev.frame_number != null ? '#' + ev.frame_number : '-') + '</td>' +
          '<td class="p-3 text-body-sm font-data-mono text-on-surface-variant text-right">' + dwellStr2 + '</td></tr>';
      }
    }

    var eventSection = eventRows
      ? '<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5"><div class="flex items-center justify-between mb-4"><h4 class="text-label-caps font-label-caps text-secondary uppercase">Registro de Eventos</h4><span class="text-body-sm text-on-surface-variant">' + data.zone_events.length + ' eventos</span></div><div class="overflow-x-auto max-h-[500px] overflow-y-auto"><table class="w-full text-left"><thead class="sticky top-0 bg-surface-container-lowest"><tr class="border-b border-outline-variant text-label-caps text-secondary uppercase"><th class="p-3 font-medium">Hora</th><th class="p-3 font-medium">Tipo</th><th class="p-3 font-medium">Area</th><th class="p-3 font-medium">Track ID</th><th class="p-3 font-medium">Frame</th><th class="p-3 font-medium text-right">Dwell</th></tr></thead><tbody>' + eventRows + '</tbody></table></div></div>'
      : '<div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-5"><p class="text-body-sm text-on-surface-variant text-center py-4">Sin eventos registrados para este analisis.</p></div>';

    var detailHtml = headerHtml + infoHtml + metricsTable + eventSection;
    document.getElementById('analysis-detail-content').innerHTML = detailHtml;
    document.querySelectorAll('.tab-content').forEach(function(t) { t.classList.add('hidden'); });
    var detailTab = document.getElementById('tab-analysis-detail');
    if (detailTab) detailTab.classList.remove('hidden');
    state.tab = 'historial';
    document.querySelectorAll('.nav-link').forEach(function(a) {
      var isHistorial = a.dataset.tab === 'historial';
      a.classList.toggle('text-primary', isHistorial);
      a.classList.toggle('font-bold', isHistorial);
      a.classList.toggle('border-r-4', isHistorial);
      a.classList.toggle('border-primary', isHistorial);
      a.classList.toggle('bg-surface-container-high', isHistorial);
      a.classList.toggle('text-on-surface-variant', !isHistorial);
    });
  } catch (e) {
    console.error('viewAnalysis error', e);
  }
}

</script>
</body>
</html>"""
