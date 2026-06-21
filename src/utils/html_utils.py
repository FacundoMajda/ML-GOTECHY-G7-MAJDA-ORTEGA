# src/utils/html_utils.py
import html as html_module


def escape(text: str) -> str:
    """Escape HTML special characters."""
    return html_module.escape(text, quote=True)


def render_home() -> str:
    """Home page — SPA with tab navigation (Sources / Jobs),
    source card grid, detail drawer (Preview / Areas / Settings),
    canvas ROI drawing, per-area config, global settings,
    and 3-state analysis modal (Summary -> Progress -> Result/Error).
    Zero parameters — all state managed client-side via JS.
    """
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Video Analytics</title>
  <style>
    :root {
      --bg: #f7f1e7;
      --accent: #0f766e;
      --accent-2: #9a3412;
      --panel: rgba(255,249,240,0.9);
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #e8dbc8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; padding-top: 56px;
      font-family: "Trebuchet MS", sans-serif;
      background: var(--bg); color: var(--ink);
    }

    /* ── Navbar ── */
    #navbar {
      position: fixed; top: 0; left: 0; right: 0; height: 56px; z-index: 100;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 20px;
      background: var(--panel); border-bottom: 1px solid var(--line);
      backdrop-filter: blur(6px);
    }
    #navbar .logo { font-weight: 700; font-size: 1.1rem; color: var(--accent); }
    .tabs { display: flex; gap: 4px; }
    .tab {
      padding: 8px 18px; border: none; border-radius: 8px;
      background: transparent; color: var(--muted); font-weight: 600;
      font-size: 0.85rem; cursor: pointer; transition: all 0.15s;
      text-transform: uppercase; letter-spacing: 0.06em;
    }
    .tab:hover { background: rgba(15,118,110,0.06); color: var(--accent); }
    .tab.active { background: var(--accent); color: #fff; }

    /* ── Tab Content ── */
    .tab-content { display: none; padding: 24px 20px 40px; max-width: 1280px; margin: 0 auto; }
    .tab-content.active { display: block; animation: fadeIn 0.2s ease; }

    /* ── Section Header ── */
    .section-header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 16px;
    }
    .section-header h2 {
      margin: 0; font-size: 0.78rem; text-transform: uppercase;
      letter-spacing: 0.1em; color: var(--accent-2); font-weight: 700;
    }
    .section-header button {
      padding: 8px 16px; border-radius: 10px; border: 1px dashed var(--accent);
      background: transparent; color: var(--accent); font-weight: 600;
      font-size: 0.85rem; cursor: pointer; transition: background 0.15s;
    }
    .section-header button:hover { background: rgba(15,118,110,0.06); }

    /* ── Cards Grid ── */
    .cards-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 14px;
    }
    .source-card {
      display: flex; align-items: center; gap: 12px;
      padding: 12px 14px; border-radius: 14px; border: 1px solid var(--line);
      background: var(--panel); cursor: pointer; transition: all 0.15s;
    }
    .source-card:hover { border-color: var(--accent); background: rgba(15,118,110,0.04); }
    .source-card.selected { border-color: var(--accent); background: rgba(15,118,110,0.08); }
    .source-thumb {
      width: 72px; height: 54px; object-fit: cover; border-radius: 8px;
      background: #e5e7eb; flex-shrink: 0;
    }
    .source-info { flex: 1; min-width: 0; }
    .source-name { font-weight: 700; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .source-meta { font-size: 0.8rem; color: var(--muted); margin-top: 2px; display: flex; align-items: center; gap: 6px; }
    .source-type-badge {
      display: inline-block; font-size: 0.7rem; padding: 1px 6px; border-radius: 4px;
      text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;
    }
    .source-type-badge.type-file { background: #e5e7eb; color: #4b5563; }
    .source-type-badge.type-youtube { background: rgba(220,38,38,0.12); color: #dc2626; }
    .source-type-badge.type-live { background: rgba(22,163,74,0.12); color: #16a34a; }
    .live-dot {
      display: inline-block; width: 8px; height: 8px; border-radius: 50%;
      background: #16a34a; margin-right: 3px;
      animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }

    /* ── Add Source Form (inline) ── */
    #add-source-form {
      margin-top: 14px; padding: 16px; border-radius: 14px;
      border: 1px solid var(--line); background: var(--panel);
      animation: fadeIn 0.2s ease;
    }
    .add-source-grid {
      display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
    }
    .add-source-grid input,
    .add-source-grid select {
      width: 100%; border-radius: 10px; border: 1px solid var(--line);
      padding: 10px 12px; font-size: 0.9rem; background: #fff; color: var(--ink);
    }
    .add-source-grid .full-row { grid-column: 1 / -1; }
    .add-source-actions { display: flex; gap: 10px; margin-top: 12px; }
    .add-source-actions button {
      flex: 1; border-radius: 10px; border: none; padding: 10px;
      font-weight: 600; font-size: 0.9rem; cursor: pointer;
    }
    #save-source-btn { background: var(--accent); color: white; }
    #cancel-source-btn { background: #e5e7eb; color: var(--ink); }
    #add-source-error { color: #dc2626; margin-top: 8px; font-size: 0.85rem; }

    /* ── Jobs Table ── */
    .jobs-table-wrap { overflow-x: auto; }
    .jobs-table {
      width: 100%; border-collapse: collapse; font-size: 0.9rem;
      background: var(--panel); border-radius: 14px; overflow: hidden;
    }
    .jobs-table th {
      text-align: left; padding: 12px 14px;
      font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em;
      color: var(--accent-2); font-weight: 700;
      border-bottom: 1px solid var(--line);
    }
    .jobs-table td { padding: 10px 14px; border-bottom: 1px solid var(--line); }
    .jobs-table tr:nth-child(even) td { background: rgba(255,255,255,0.4); }
    .jobs-table tr:hover td { background: rgba(15,118,110,0.04); }
    .report-btn {
      padding: 4px 12px; border-radius: 6px; border: none;
      background: var(--accent); color: white; font-size: 0.8rem;
      font-weight: 600; cursor: pointer; text-decoration: none;
    }
    .report-btn:hover { filter: brightness(1.05); }
    .report-btn.missing { background: #d1d5db; cursor: not-allowed; }

    /* ── Status Badges ── */
    .badge {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 2px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600;
    }
    .badge-green { background: rgba(22,163,74,0.12); color: #16a34a; }
    .badge-red { background: rgba(220,38,38,0.12); color: #dc2626; }
    .badge-amber { background: rgba(245,158,11,0.12); color: #d97706; }
    .badge-amber .mini-spinner {
      display: inline-block; width: 10px; height: 10px;
      border: 2px solid rgba(245,158,11,0.3); border-top-color: #d97706;
      border-radius: 50%; animation: spin 0.6s linear infinite;
    }
    .report-link {
      padding: 4px 12px; border-radius: 6px; border: none;
      background: var(--accent); color: white; font-size: 0.8rem;
      font-weight: 600; cursor: pointer; text-decoration: none; display: inline-block;
    }
    .report-link:hover { filter: brightness(1.05); }
    .report-link.disabled { background: #d1d5db; cursor: not-allowed; pointer-events: none; }

    /* ── Overlay ── */
    .overlay {
      position: fixed; inset: 0; z-index: 150;
      background: rgba(0,0,0,0.3); opacity: 0; pointer-events: none;
      transition: opacity 0.25s ease;
    }
    .overlay.open { opacity: 1; pointer-events: auto; }

    /* ── Drawer ── */
    .drawer {
      position: fixed; right: 0; top: 0; width: 480px; height: 100%; z-index: 200;
      background: var(--panel); border-left: 1px solid var(--line);
      transform: translateX(100%); transition: transform 0.25s ease;
      display: flex; flex-direction: column;
    }
    .drawer.open { transform: translateX(0); }
    .drawer-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 18px 20px; border-bottom: 1px solid var(--line); flex-shrink: 0;
    }
    .drawer-header span { font-weight: 700; font-size: 1rem; }
    #drawer-close {
      background: none; border: none; font-size: 1.4rem; cursor: pointer;
      color: var(--muted); padding: 4px 8px; border-radius: 6px;
    }
    #drawer-close:hover { background: rgba(0,0,0,0.06); }
    .drawer-body { flex: 1; overflow-y: auto; padding: 20px; }

    /* ── Drawer 3-tab navigation ── */
    .drawer-tabs {
      display: flex; border-bottom: 1px solid var(--line); flex-shrink: 0;
    }
    .drawer-tab {
      flex: 1; padding: 10px; cursor: pointer; text-align: center;
      background: #f8fafc; border: none; font-size: 13px; font-weight: 600;
      color: var(--muted); border-bottom: 2px solid transparent; transition: all 0.15s;
    }
    .drawer-tab:hover { color: var(--accent); background: rgba(15,118,110,0.04); }
    .drawer-tab.active { background: #fff; border-bottom-color: var(--accent); color: var(--accent); }

    /* ── Drawer tab content ── */
    .dt-content { display: none; }
    .dt-content.active { display: block; animation: fadeIn 0.15s ease; }

    /* ── Preview tab ── */
    .preview-wrap { position: relative; width: 100%; margin-bottom: 10px; }
    #preview-img {
      width: 100%; border-radius: 12px; aspect-ratio: 16/9;
      object-fit: cover; background: #e5e7eb; display: block;
    }
    #preview-canvas {
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      cursor: crosshair; border-radius: 12px;
    }
    .draw-actions { display: flex; gap: 8px; margin-top: 8px; }
    .draw-actions button { flex: 1; }
    #draw-area-btn { width: 100%; }

    /* ── Areas tab ── */
    .area-details {
      margin-bottom: 8px; border: 1px solid var(--line); border-radius: 10px;
      background: #fff; overflow: hidden;
    }
    .area-details summary {
      padding: 10px 14px; cursor: pointer; font-weight: 600; font-size: 0.9rem;
    }
    .area-config { padding: 10px 14px 14px; border-top: 1px solid var(--line); }
    .area-config label {
      display: flex; align-items: center; gap: 6px;
      font-size: 0.85rem; cursor: pointer; margin-bottom: 6px;
    }
    .area-config input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--accent); }
    .alert-config {
      margin: 10px 0; padding: 10px; background: #f8fafc; border-radius: 8px;
      border: 1px solid var(--line);
    }
    .alert-config h4 {
      font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em;
      color: var(--accent-2); font-weight: 700; margin: 0 0 8px;
    }
    .alert-row { display: flex; gap: 6px; margin-bottom: 6px; align-items: center; }
    .alert-row select, .alert-row input[type="number"] {
      padding: 4px 8px; border: 1px solid var(--line); border-radius: 6px; font-size: 0.8rem;
    }
    .btn-sm {
      padding: 6px 14px; border-radius: 8px; border: 1px solid var(--line);
      background: #fff; font-size: 0.8rem; font-weight: 600; cursor: pointer;
      transition: all 0.15s;
    }
    .btn-sm:hover { border-color: var(--accent); color: var(--accent); }
    .btn-primary.btn-sm { background: var(--accent); color: #fff; border-color: var(--accent); }
    .btn-primary.btn-sm:hover { filter: brightness(1.05); }
    .btn-danger.btn-sm { background: #dc2626; color: #fff; border-color: #dc2626; }

    /* ── Settings tab ── */
    .settings-group { margin-bottom: 18px; }
    .settings-group h3 {
      font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;
      color: var(--accent-2); font-weight: 700; margin: 0 0 10px;
    }
    .settings-group label {
      display: flex; align-items: center; gap: 6px;
      font-size: 0.9rem; cursor: pointer; margin-bottom: 6px;
    }
    .settings-group select, .settings-group input[type="number"] {
      width: 100%; padding: 8px 10px; border: 1px solid var(--line);
      border-radius: 8px; font-size: 0.9rem; background: #fff; color: var(--ink);
    }
    .settings-inline { display: flex; gap: 8px; align-items: center; }
    .settings-inline input[type="number"] { flex: 1; }
    .settings-inline label { white-space: nowrap; font-size: 0.9rem; }

    /* ── Drawer footer ── */
    .drawer-footer {
      position: sticky; bottom: 0; padding: 14px 20px;
      border-top: 1px solid var(--line); background: var(--panel); flex-shrink: 0;
    }
    .drawer-footer button { width: 100%; }

    /* ── Modal ── */
    .modal {
      position: fixed; inset: 0; z-index: 300;
      background: rgba(0,0,0,0.4); display: none;
      align-items: center; justify-content: center;
      animation: fadeIn 0.2s ease;
    }
    .modal.open { display: flex; }
    .modal-content {
      background: var(--panel); border-radius: 20px; padding: 24px;
      width: 90%; max-width: 500px; max-height: 85vh; overflow-y: auto;
      box-shadow: 0 12px 40px rgba(0,0,0,0.15);
      animation: slideUp 0.25s ease;
    }
    #modal-title {
      font-weight: 700; font-size: 1.1rem; display: block; margin-bottom: 18px;
    }
    .modal-actions { display: flex; gap: 10px; margin-top: 16px; }
    .modal-actions button {
      flex: 1; border-radius: 10px; border: none; padding: 10px;
      font-weight: 600; font-size: 0.9rem; cursor: pointer;
    }
    .btn-primary { background: var(--accent); color: white; }
    .btn-primary:hover { filter: brightness(1.05); }
    .btn-secondary { background: #e5e7eb; color: var(--ink); }
    .btn-secondary:hover { background: #d1d5db; }
    .btn-danger { background: #dc2626; color: white; }
    .btn-danger:hover { filter: brightness(1.05); }

    /* ── Modal Summary ── */
    .modal-summary { padding: 4px 0; }
    .summary-row {
      display: flex; justify-content: space-between; padding: 7px 0;
      font-size: 0.9rem; border-bottom: 1px solid var(--line);
    }
    .summary-row:last-child { border-bottom: none; }
    .summary-label { color: var(--muted); }
    .summary-value { font-weight: 600; text-align: right; }

    /* ── Modal Result / Error ── */
    #modal-result { text-align: center; padding: 16px 0; }
    #modal-result .result-icon { font-size: 3.5rem; margin-bottom: 10px; }
    #modal-result h3 { margin: 0 0 6px; font-size: 1.1rem; }
    #modal-result p { margin: 0 0 4px; color: var(--muted); font-size: 0.9rem; }
    .modal-error-state { text-align: center; padding: 16px 0; }
    .modal-error-state .error-icon { font-size: 3.5rem; margin-bottom: 10px; }
    .modal-error-state p { color: #dc2626; font-size: 0.95rem; margin: 0; }

    /* ── Progress ── */
    .spinner {
      display: inline-block; width: 28px; height: 28px; border: 3px solid var(--line);
      border-top-color: var(--accent); border-radius: 50%;
      animation: spin 0.7s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .progress-bar {
      width: 100%; height: 6px; background: var(--line); border-radius: 3px;
      overflow: hidden; margin: 12px 0;
    }
    .progress-bar-fill {
      height: 100%; background: var(--accent); border-radius: 3px;
      transition: width 0.3s ease;
    }
    #modal-error { color: #dc2626; margin-top: 10px; font-size: 0.9rem; }

    /* ── Empty States ── */
    .empty-state {
      text-align: center; padding: 40px 20px; color: var(--muted);
    }
    .empty-state p { margin: 0 0 12px; font-size: 0.95rem; }

    /* ── Error Banner ── */
    .error-banner {
      padding: 12px 16px; border-radius: 10px;
      background: rgba(220,38,38,0.08); border: 1px solid rgba(220,38,38,0.2);
      color: #dc2626; font-size: 0.9rem; margin-bottom: 14px;
      display: flex; align-items: center; gap: 10px;
    }
    .error-banner button {
      margin-left: auto; padding: 4px 12px; border-radius: 6px;
      border: 1px solid #dc2626; background: transparent; color: #dc2626;
      font-weight: 600; font-size: 0.8rem; cursor: pointer;
    }
    .error-banner button:hover { background: rgba(220,38,38,0.08); }

    /* ── Skeleton ── */
    .skeleton {
      background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
      background-size: 200% 100%; animation: shimmer 1.5s infinite;
      border-radius: 8px;
    }
    @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
    .skeleton-card {
      height: 78px; border-radius: 14px;
    }
    .skeleton-row { height: 40px; border-radius: 8px; margin-bottom: 6px; }

    /* ── Animations ── */
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }

    /* ── Responsive ── */
    @media (max-width: 640px) {
      .drawer { width: 100%; }
      .add-source-grid { grid-template-columns: 1fr; }
      .cards-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <!-- NAVBAR -->
  <nav id="navbar">
    <span class="logo">&#9675; Video Analytics</span>
    <div class="tabs">
      <button class="tab active" data-tab="sources">Sources</button>
      <button class="tab" data-tab="jobs">Jobs</button>
    </div>
  </nav>

  <!-- TAB: SOURCES -->
  <section id="tab-sources" class="tab-content active">
    <div class="section-header">
      <h2>SOURCES</h2>
      <button id="add-source-btn">+ Add Source</button>
    </div>
    <div id="sources-error" class="error-banner" style="display:none">
      <span id="sources-error-msg"></span>
      <button id="sources-retry-btn">Retry</button>
    </div>
    <div id="sources-grid" class="cards-grid"></div>
    <div id="add-source-form" style="display:none">
      <div class="add-source-grid">
        <input name="new_name" placeholder="Name" class="full-row">
        <select name="new_type">
          <option value="file">FILE</option>
          <option value="youtube_vod">YOUTUBE</option>
          <option value="youtube_live">LIVE</option>
          <option value="rtsp">RTSP</option>
        </select>
        <input name="new_uri" placeholder="URI / path">
      </div>
      <div class="add-source-actions">
        <button id="save-source-btn">Save</button>
        <button id="cancel-source-btn">Cancel</button>
      </div>
      <div id="add-source-error"></div>
    </div>
  </section>

  <!-- TAB: JOBS -->
  <section id="tab-jobs" class="tab-content">
    <div class="section-header">
      <h2>RECENT JOBS</h2>
    </div>
    <div id="jobs-error" class="error-banner" style="display:none">
      <span id="jobs-error-msg"></span>
      <button id="jobs-retry-btn">Retry</button>
    </div>
    <div id="jobs-content"></div>
  </section>

  <!-- DRAWER OVERLAY -->
  <div id="drawer-overlay" class="overlay"></div>

  <!-- DRAWER -->
  <aside id="drawer" class="drawer">
    <div class="drawer-header">
      <span id="drawer-title">Source Name</span>
      <button id="drawer-close">&times;</button>
    </div>
    <div class="drawer-tabs">
      <button class="drawer-tab active" data-dtab="preview">Preview</button>
      <button class="drawer-tab" data-dtab="areas">Areas</button>
      <button class="drawer-tab" data-dtab="settings">Settings</button>
    </div>
    <div class="drawer-body">
      <!-- Preview tab -->
      <div id="dt-preview" class="dt-content active">
        <div class="preview-wrap">
          <img id="preview-img" src="" alt="Preview">
          <canvas id="preview-canvas"></canvas>
        </div>
        <button id="draw-area-btn" class="btn-sm">Draw Area</button>
        <div id="draw-actions" class="draw-actions" style="display:none">
          <button id="save-polygon-btn" class="btn-primary btn-sm">Save Area</button>
          <button id="cancel-polygon-btn" class="btn-sm">Cancel</button>
        </div>
      </div>
      <!-- Areas tab -->
      <div id="dt-areas" class="dt-content">
        <div id="areas-list"></div>
      </div>
      <!-- Settings tab -->
      <div id="dt-settings" class="dt-content">
        <div id="settings-content"></div>
      </div>
    </div>
    <div class="drawer-footer">
      <button id="run-analysis-btn" class="btn-primary">Run Analysis</button>
    </div>
  </aside>

  <!-- MODAL -->
  <div id="modal" class="modal">
    <div class="modal-content">
      <span id="modal-title">Run Analysis</span>
      <div id="modal-body"></div>
    </div>
  </div>

  <script>
  // ── STATE ──
  const state = {
    tab: 'sources',
    sources: [],
    sessions: [],
    sourcesLoading: false,
    sessionsLoading: false,
    sourcesError: null,
    sessionsError: null,
    selectedSourceId: null,
    drawerOpen: false,
    drawerTab: 'preview',
    drawMode: false,
    currentPolygon: [],
    sourceSettings: {},
    modalOpen: false,
    modalState: 'summary',   // 'summary' | 'progress' | 'result' | 'error'
    modalSourceId: null,
    modalSessionId: null,
    modalError: null,
    pollingInterval: null,
  };

  // ── ROI Colors ──
  const roiColors = [
    { fill: 'rgba(59,130,246,0.15)', stroke: '#3b82f6' },
    { fill: 'rgba(16,185,129,0.15)', stroke: '#10b981' },
    { fill: 'rgba(245,158,11,0.15)', stroke: '#f59e0b' },
    { fill: 'rgba(239,68,68,0.15)', stroke: '#ef4444' },
    { fill: 'rgba(139,92,246,0.15)', stroke: '#8b5cf6' },
    { fill: 'rgba(236,72,153,0.15)', stroke: '#ec4899' },
  ];

  // ── HELPERS ──
  function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function fetchJSON(url, opts) {
    return fetch(url, opts).then(r => r.json().then(d => ({status: r.status, data: d})));
  }

  function getSource(id) {
    return state.sources.find(s => s.id === id);
  }

  function formatDate(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
  }

  function formatDuration(sec) {
    if (sec == null) return '-';
    if (sec < 60) return Math.round(sec) + 's';
    if (sec < 3600) return Math.floor(sec/60) + 'm ' + Math.round(sec%60) + 's';
    return Math.floor(sec/3600) + 'h ' + Math.floor((sec%3600)/60) + 'm';
  }

  function sourceTypeLabel(t) {
    const labels = {file:'FILE', youtube_vod:'YOUTUBE', youtube_live:'LIVE', rtsp:'RTSP'};
    return labels[t] || t;
  }

  function getSourceSettings(sourceId) {
    if (!state.sourceSettings[sourceId]) {
      state.sourceSettings[sourceId] = {
        tracking_classes: ['person'],
        frame_skip: 1,
        max_frames: null,
      };
    }
    return state.sourceSettings[sourceId];
  }

  // ── RENDER ──
  function render() {
    renderNav();
    if (state.tab === 'sources') renderSourcesTab();
    else if (state.tab === 'jobs') renderJobsTab();
  }

  function renderNav() {
    document.querySelectorAll('.tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === state.tab);
    });
  }

  function renderSourcesTab() {
    const grid = document.getElementById('sources-grid');
    const err = document.getElementById('sources-error');

    if (state.sourcesError) {
      err.style.display = 'flex';
      document.getElementById('sources-error-msg').textContent = state.sourcesError;
      grid.innerHTML = '';
      return;
    }
    err.style.display = 'none';

    if (state.sourcesLoading) {
      grid.innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
      return;
    }

    if (state.sources.length === 0) {
      grid.innerHTML = '<div class="empty-state"><p>Add your first video source</p><button id="inline-add-btn" class="btn-primary" style="padding:8px 20px;display:inline-block;width:auto">+ Add Source</button></div>';
      const inlineBtn = document.getElementById('inline-add-btn');
      if (inlineBtn) inlineBtn.onclick = () => { document.getElementById('add-source-form').style.display = 'block'; };
      return;
    }

    grid.innerHTML = state.sources.map(s => `
      <div class="source-card${state.selectedSourceId === s.id ? ' selected' : ''}" data-id="${s.id}">
        <img class="source-thumb" src="/api/sources/${s.id}/preview" alt="${esc(s.name)}" loading="lazy"
             onerror="this.style.display='none'">
        <div class="source-info">
          <div class="source-name">${esc(s.name)}</div>
          <div class="source-meta">
            <span class="source-type-badge type-${s.source_type === 'youtube_vod' || s.source_type === 'youtube_live' ? 'youtube' : s.is_live ? 'live' : 'file'}">
              ${s.is_live ? '<span class="live-dot"></span>' : ''}${esc(sourceTypeLabel(s.source_type))}
            </span>
            <span>&middot; ${(s.rois || []).length} areas</span>
          </div>
        </div>
      </div>
    `).join('');

    grid.querySelectorAll('.source-card').forEach(card => {
      card.onclick = () => selectSource(card.dataset.id);
    });
  }

  function renderJobsTab() {
    const content = document.getElementById('jobs-content');
    const err = document.getElementById('jobs-error');

    if (state.sessionsError) {
      err.style.display = 'flex';
      document.getElementById('jobs-error-msg').textContent = state.sessionsError;
      content.innerHTML = '';
      return;
    }
    err.style.display = 'none';

    if (state.sessionsLoading) {
      content.innerHTML = '<div class="skeleton skeleton-row"></div><div class="skeleton skeleton-row"></div><div class="skeleton skeleton-row"></div>';
      return;
    }

    if (state.sessions.length === 0) {
      content.innerHTML = '<div class="empty-state"><p>No analysis jobs yet. Run an analysis from a source.</p></div>';
      return;
    }

    content.innerHTML = '<div class="jobs-table-wrap"><table class="jobs-table"><thead><tr><th>Source</th><th>Status</th><th>Date</th><th>Duration</th><th>Entities</th><th>Events</th><th></th></tr></thead><tbody id="jobs-tbody"></tbody></table></div>';

    const tbody = document.getElementById('jobs-tbody');
    tbody.innerHTML = state.sessions.map(s => {
      const status = (s.status || 'completed').toLowerCase();
      let badge = '';
      if (status === 'completed') {
        badge = '<span class="badge badge-green">Completed</span>';
      } else if (status === 'failed') {
        badge = '<span class="badge badge-red">Failed</span>';
      } else if (status === 'running') {
        badge = '<span class="badge badge-amber"><span class="mini-spinner"></span> Running</span>';
      } else {
        badge = '<span class="badge">' + esc(status) + '</span>';
      }

      const hasReport = status === 'completed';
      const reportLink = hasReport
        ? '<a href="/api/sessions/' + esc(s.id) + '/report" target="_blank" class="report-link">Report</a>'
        : '<span class="report-link disabled">Report</span>';

      return '<tr>'
        + '<td>' + esc(s.source_name || '-') + '</td>'
        + '<td>' + badge + '</td>'
        + '<td>' + formatDate(s.started_at) + '</td>'
        + '<td>' + formatDuration(s.duration_seconds) + '</td>'
        + '<td>' + (s.total_entities != null ? s.total_entities : '-') + '</td>'
        + '<td>' + (s.total_events != null ? s.total_events : '-') + '</td>'
        + '<td>' + reportLink + '</td>'
        + '</tr>';
    }).join('');
  }

  // ── DRAWER ──

  function selectSource(id) {
    state.selectedSourceId = id;
    state.drawerOpen = true;
    state.drawerTab = 'preview';
    state.drawMode = false;
    state.currentPolygon = [];
    renderSourcesTab();
    renderDrawer();
  }

  function closeDrawer() {
    if (state.drawMode) cancelDrawing();
    state.drawMode = false;
    state.currentPolygon = [];
    state.drawerOpen = false;
    state.selectedSourceId = null;
    state.drawerTab = 'preview';
    document.getElementById('draw-actions').style.display = 'none';
    renderDrawer();
    renderSourcesTab();
  }

  function renderDrawer() {
    const src = getSource(state.selectedSourceId);
    const drawer = document.getElementById('drawer');
    const overlay = document.getElementById('drawer-overlay');

    if (!src || !state.drawerOpen) {
      drawer.classList.remove('open');
      overlay.classList.remove('open');
      return;
    }

    document.getElementById('drawer-title').textContent = src.name;

    // Set preview image
    const img = document.getElementById('preview-img');
    img.style.display = '';
    img.src = '/api/sources/' + src.id + '/preview';
    img.onerror = function() { this.style.display = 'none'; };

    // Canvas init when image loads
    const initCanvasOnLoad = function() {
      const canvas = document.getElementById('preview-canvas');
      if (!canvas || !img) return;
      const rect = img.getBoundingClientRect();
      if (rect.width === 0) return;
      canvas.width = rect.width;
      canvas.height = rect.height;
      if (state.drawMode) {
        drawCanvasDuringDrawMode();
      } else {
        drawExistingROIs();
      }
    };

    img.onload = initCanvasOnLoad;
    if (img.complete && img.naturalWidth > 0) {
      setTimeout(initCanvasOnLoad, 50);
    }

    // Update drawer tabs
    document.querySelectorAll('.drawer-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.dtab === state.drawerTab);
    });

    // Show active tab
    showDrawerTab(state.drawerTab);
    document.getElementById('draw-area-btn').textContent = 'Draw Area';

    drawer.classList.add('open');
    overlay.classList.add('open');
  }

  function switchTab(tab) {
    state.tab = tab;
    document.querySelectorAll('.tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === tab);
    });
    document.querySelectorAll('.tab-content').forEach(c => {
      c.classList.toggle('active', c.id === 'tab-' + tab);
    });
    if (tab === 'jobs') fetchSessions();
  }

  function switchDrawerTab(tab) {
    state.drawerTab = tab;
    document.querySelectorAll('.drawer-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.dtab === tab);
    });
    showDrawerTab(tab);
  }

  function showDrawerTab(tab) {
    document.querySelectorAll('.dt-content').forEach(c => c.classList.remove('active'));
    const el = document.getElementById('dt-' + tab);
    if (el) el.classList.add('active');

    switch (tab) {
      case 'areas': renderAreasTab(); break;
      case 'settings': renderSettingsTab(); break;
      case 'preview': break; // canvas handles itself
    }
  }

  // ── PREVIEW TAB: CANVAS ──

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

    const scaleX = canvas.width / srcW;
    const scaleY = canvas.height / srcH;

    src.rois.forEach((roi, idx) => {
      const color = roiColors[idx % roiColors.length];
      ctx.beginPath();
      roi.polygon.forEach((pt, i) => {
        const x = pt[0] * scaleX;
        const y = pt[1] * scaleY;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = color.fill;
      ctx.fill();
      ctx.strokeStyle = color.stroke;
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }

  function drawCanvasDuringDrawMode() {
    const canvas = document.getElementById('preview-canvas');
    if (!canvas) return;

    // Draw existing ROIs underneath first
    drawExistingROIs();

    const ctx = canvas.getContext('2d');
    const pts = state.currentPolygon;
    if (pts.length === 0) return;

    // Draw polygon lines
    ctx.beginPath();
    pts.forEach((pt, i) => {
      i === 0 ? ctx.moveTo(pt.x, pt.y) : ctx.lineTo(pt.x, pt.y);
    });
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw vertices
    pts.forEach(pt => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#10b981';
      ctx.fill();
    });

    // Draw close target indicator
    if (pts.length >= 3) {
      const first = pts[0];
      ctx.beginPath();
      ctx.arc(first.x, first.y, 8, 0, Math.PI * 2);
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  function handleCanvasClick(e) {
    if (!state.drawMode) return;

    const canvas = document.getElementById('preview-canvas');
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check if clicking near first vertex to close polygon
    if (state.currentPolygon.length >= 3) {
      const first = state.currentPolygon[0];
      const dist = Math.sqrt((x - first.x) ** 2 + (y - first.y) ** 2);
      if (dist <= 10) {
        document.getElementById('draw-actions').style.display = 'flex';
        drawCanvasDuringDrawMode();
        return;
      }
    }

    state.currentPolygon.push({ x, y });
    drawCanvasDuringDrawMode();
  }

  function savePolygon() {
    const src = getSource(state.selectedSourceId);
    if (!src || state.currentPolygon.length < 3) return;

    const canvas = document.getElementById('preview-canvas');
    const img = document.getElementById('preview-img');
    const srcW = src.frame_width || img.naturalWidth;
    const srcH = src.frame_height || img.naturalHeight;
    if (!srcW || !srcH) return;

    // Scale polygon from canvas coords to original frame coords
    const scaleX = srcW / canvas.width;
    const scaleY = srcH / canvas.height;

    const polygon = state.currentPolygon.map(pt => [
      Math.round(pt.x * scaleX),
      Math.round(pt.y * scaleY)
    ]);

    const areaName = 'Area ' + ((src.rois || []).length + 1);

    fetchJSON('/api/sources/' + src.id + '/rois', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name: areaName, polygon }),
    }).then(({status, data}) => {
      if (status >= 400) {
        alert('Error saving area: ' + (data.error || 'Unknown error'));
        return;
      }
      // Reset draw state
      state.drawMode = false;
      state.currentPolygon = [];
      document.getElementById('draw-actions').style.display = 'none';
      document.getElementById('draw-area-btn').textContent = 'Draw Area';

      // Re-fetch sources, then switch to Areas tab
      fetchSources().then(() => {
        state.drawerTab = 'areas';
        switchDrawerTab('areas');
      });
    }).catch(err => {
      alert('Network error saving area: ' + err.message);
    });
  }

  function cancelDrawing() {
    state.drawMode = false;
    state.currentPolygon = [];
    document.getElementById('draw-actions').style.display = 'none';
    document.getElementById('draw-area-btn').textContent = 'Draw Area';
    drawExistingROIs();
  }

  // ── AREAS TAB ──

  function renderAreasTab() {
    const src = getSource(state.selectedSourceId);
    const container = document.getElementById('areas-list');

    if (!src || !src.rois || src.rois.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No areas defined yet. Draw one in the Preview tab.</p></div>';
      return;
    }

    container.innerHTML = src.rois.map(roi => `
      <details class="area-details" data-roi-id="${esc(roi.id)}">
        <summary>${esc(roi.name)}</summary>
        <div class="area-config">
          <label><input type="checkbox" class="area-chk" data-field="detect_entry" ${roi.detect_entry ? 'checked' : ''}> Entry Detection</label>
          <label><input type="checkbox" class="area-chk" data-field="detect_exit" ${roi.detect_exit ? 'checked' : ''}> Exit Detection</label>
          <label><input type="checkbox" class="area-chk" data-field="detect_occupancy" ${roi.detect_occupancy ? 'checked' : ''}> Occupancy</label>
          <label><input type="checkbox" class="area-chk" data-field="detect_dwell" ${roi.detect_dwell ? 'checked' : ''}> Dwell Time</label>
          <div class="alert-config">
            <h4>Alerts</h4>
            <div id="alerts-${esc(roi.id)}"></div>
            <button class="btn-sm" onclick="addAlert('${esc(roi.id)}')">+ Add Alert</button>
          </div>
          <button class="btn-primary btn-sm" onclick="saveROIConfig('${esc(roi.id)}')">Save Config</button>
          <span id="config-msg-${esc(roi.id)}" style="font-size:0.8rem;color:var(--accent);margin-left:8px;"></span>
        </div>
      </details>
    `).join('');
  }

  function addAlert(roiId) {
    const container = document.getElementById('alerts-' + roiId);
    if (!container) return;
    const div = document.createElement('div');
    div.className = 'alert-row';
    div.innerHTML = `
      <select class="alert-type">
        <option value="overcapacity">Overcapacity</option>
        <option value="dwell_exceeded">Dwell Exceeded</option>
        <option value="area_empty">Area Empty</option>
      </select>
      <input type="number" class="alert-threshold" placeholder="Threshold" min="1" value="10" style="width:80px">
      <button class="btn-sm" style="padding:4px 8px" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(div);
  }

  function saveROIConfig(roiId) {
    const details = document.querySelector('.area-details[data-roi-id="' + roiId + '"]');
    if (!details) return;

    const config = {
      detect_entry: details.querySelector('.area-chk[data-field="detect_entry"]').checked,
      detect_exit: details.querySelector('.area-chk[data-field="detect_exit"]').checked,
      detect_occupancy: details.querySelector('.area-chk[data-field="detect_occupancy"]').checked,
      detect_dwell: details.querySelector('.area-chk[data-field="detect_dwell"]').checked,
    };

    const alerts = [];
    const alertContainer = document.getElementById('alerts-' + roiId);
    if (alertContainer) {
      alertContainer.querySelectorAll('.alert-row').forEach(row => {
        alerts.push({
          alert_type: row.querySelector('.alert-type').value,
          threshold: parseInt(row.querySelector('.alert-threshold').value) || 10,
        });
      });
    }
    config.alerts = alerts;

    const msgEl = document.getElementById('config-msg-' + roiId);
    if (msgEl) {
      msgEl.style.color = 'var(--accent)';
      msgEl.textContent = 'Saving...';
    }

    fetchJSON('/api/rois/' + roiId + '/config', {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(config),
    }).then(({status}) => {
      if (msgEl) {
        if (status === 200) {
          msgEl.textContent = 'Saved!';
        } else {
          msgEl.textContent = 'Error saving';
          msgEl.style.color = '#dc2626';
        }
        setTimeout(() => { if (msgEl) msgEl.textContent = ''; }, 2000);
      }
    }).catch(() => {
      if (msgEl) {
        msgEl.textContent = 'Network error';
        msgEl.style.color = '#dc2626';
      }
    });
  }

  // ── SETTINGS TAB ──

  function renderSettingsTab() {
    const src = getSource(state.selectedSourceId);
    if (!src) return;
    const settings = getSourceSettings(src.id);

    document.getElementById('settings-content').innerHTML = `
      <div class="settings-group">
        <h3>Tracking Classes</h3>
        ${['person','car','bicycle','backpack'].map(cls => `
          <label><input type="checkbox" class="settings-chk" data-class="${cls}" onchange="onTrackingClassChange('${esc(src.id)}')" ${(settings.tracking_classes||[]).includes(cls)?'checked':''}> ${cls.charAt(0).toUpperCase()+cls.slice(1)}</label>
        `).join('')}
      </div>
      <div class="settings-group">
        <h3>Frame Skip</h3>
        <select id="settings-frameskip" onchange="updateSourceSetting('${esc(src.id)}','frame_skip',parseInt(this.value))">
          ${[1,2,4,8].map(v => `<option value="${v}" ${settings.frame_skip===v?'selected':''}>Every ${v} frame${v>1?'s':''}</option>`).join('')}
        </select>
      </div>
      <div class="settings-group">
        <h3>Max Frames</h3>
        <div class="settings-inline">
          <input type="number" id="settings-maxframes" min="100" step="100" value="${settings.max_frames||1000}" ${settings.max_frames===null?'disabled':''} onchange="updateSourceSetting('${esc(src.id)}','max_frames',this.value?parseInt(this.value):null)">
          <label><input type="checkbox" id="settings-unlimited" ${settings.max_frames===null?'checked':''} onchange="toggleUnlimited('${esc(src.id)}')"> Unlimited</label>
        </div>
      </div>
      <div class="settings-group">
        <h3>Global Alerts</h3>
        <p style="color:var(--muted);font-size:0.85rem">Coming soon...</p>
      </div>
    `;
  }

  function onTrackingClassChange(sourceId) {
    const settings = getSourceSettings(sourceId);
    const checked = Array.from(document.querySelectorAll('.settings-chk:checked')).map(cb => cb.dataset.class);
    settings.tracking_classes = checked;
  }

  function updateSourceSetting(sourceId, key, value) {
    const settings = getSourceSettings(sourceId);
    settings[key] = value;
  }

  function toggleUnlimited(sourceId) {
    const input = document.getElementById('settings-maxframes');
    const checkbox = document.getElementById('settings-unlimited');
    if (checkbox.checked) {
      input.disabled = true;
      input.value = '';
      updateSourceSetting(sourceId, 'max_frames', null);
    } else {
      input.disabled = false;
      input.value = input.value || '1000';
      updateSourceSetting(sourceId, 'max_frames', parseInt(input.value) || null);
    }
  }

  // ── MODAL ──

  function openModal(sourceId) {
    state.modalOpen = true;
    state.modalState = 'summary';
    state.modalSourceId = sourceId;
    state.modalSessionId = null;
    state.modalError = null;
    state.pollingInterval = null;
    renderModal();
  }

  function closeModal() {
    if (state.pollingInterval) {
      clearInterval(state.pollingInterval);
      state.pollingInterval = null;
    }
    state.modalOpen = false;
    state.modalState = 'summary';
    state.modalSourceId = null;
    state.modalSessionId = null;
    state.modalError = null;
    renderModal();
  }

  function renderModal() {
    const modal = document.getElementById('modal');
    const body = document.getElementById('modal-body');

    if (!state.modalOpen) {
      modal.classList.remove('open');
      return;
    }
    modal.classList.add('open');

    const src = state.modalSourceId ? getSource(state.modalSourceId) : null;
    const srcName = src ? src.name : '...';

    if (state.modalState === 'summary') {
      const settings = getSourceSettings(state.modalSourceId);
      document.getElementById('modal-title').textContent = 'Run Analysis \u2014 ' + srcName;
      body.innerHTML = `
        <div class="modal-summary">
          <div class="summary-row"><span class="summary-label">Source</span><span class="summary-value">${esc(srcName)}</span></div>
          <div class="summary-row"><span class="summary-label">Tracking Classes</span><span class="summary-value">${(settings.tracking_classes||['person']).join(', ')}</span></div>
          <div class="summary-row"><span class="summary-label">Frame Skip</span><span class="summary-value">Every ${settings.frame_skip||1} frame${settings.frame_skip>1?'s':''}</span></div>
          <div class="summary-row"><span class="summary-label">Max Frames</span><span class="summary-value">${settings.max_frames ? settings.max_frames : 'Unlimited'}</span></div>
          <div class="summary-row"><span class="summary-label">Areas</span><span class="summary-value">${(src&&src.rois?src.rois.length:0)} area${src&&src.rois&&src.rois.length!==1?'s':''}</span></div>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" id="modal-cancel-btn">Cancel</button>
          <button class="btn-primary" id="modal-generate-btn">Generate &rarr;</button>
        </div>
      `;
      document.getElementById('modal-cancel-btn').onclick = closeModal;
      document.getElementById('modal-generate-btn').onclick = startAnalysis;

    } else if (state.modalState === 'progress') {
      document.getElementById('modal-title').textContent = 'Processing';
      body.innerHTML = `
        <div style="text-align:center;padding:20px 0">
          <div class="spinner"></div>
          <p style="margin-top:14px;color:var(--muted)">Processing video analysis...</p>
          <div class="progress-bar"><div class="progress-bar-fill" id="progress-fill"></div></div>
          <p id="progress-text" style="font-size:0.85rem;color:var(--muted)">Starting...</p>
        </div>
      `;

    } else if (state.modalState === 'result') {
      document.getElementById('modal-title').textContent = 'Analysis Complete';
      body.innerHTML = `
        <div id="modal-result">
          <div class="result-icon" style="color:#16a34a">&#10003;</div>
          <h3>Analysis Complete!</h3>
          <p>Session ID: ${esc(state.modalSessionId)}</p>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" id="modal-close-btn">Close</button>
          <a href="/api/sessions/${esc(state.modalSessionId)}/report" target="_blank" class="btn-primary" style="display:inline-block;text-align:center;padding:10px;border-radius:10px;text-decoration:none">View Report</a>
        </div>
      `;
      document.getElementById('modal-close-btn').onclick = closeModal;

    } else if (state.modalState === 'error') {
      document.getElementById('modal-title').textContent = 'Analysis Failed';
      body.innerHTML = `
        <div class="modal-error-state">
          <div class="error-icon" style="color:#dc2626">&#10007;</div>
          <p>${esc(state.modalError)}</p>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" id="modal-cancel-btn-2">Close</button>
          <button class="btn-primary" id="modal-retry-btn">Retry</button>
        </div>
      `;
      document.getElementById('modal-cancel-btn-2').onclick = closeModal;
      document.getElementById('modal-retry-btn').onclick = () => {
        state.modalState = 'summary';
        state.modalError = null;
        renderModal();
      };
    }
  }

  // ── ANALYSIS FLOW ──

  function startAnalysis() {
    if (!state.modalSourceId) return;

    const settings = getSourceSettings(state.modalSourceId);
    state.modalState = 'progress';
    renderModal();

    const body = {
      video_source_id: state.modalSourceId,
      tracking_classes: settings.tracking_classes || ['person'],
      frame_skip: settings.frame_skip || 1,
      max_frames: settings.max_frames,
      metrics: { entries: true, exits: true, occupancy: true, dwell_time: false, heatmap: false },
      output: { report: true, annotated_video: true },
    };

    fetchJSON('/process', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    }).then(({status, data}) => {
      if (status >= 400) {
        state.modalState = 'error';
        state.modalError = data.error || 'Failed to start analysis';
        renderModal();
        return;
      }
      // Started — begin polling job status
      state.pollingInterval = setInterval(pollJobStatus, 2000);
    }).catch(err => {
      state.modalState = 'error';
      state.modalError = 'Network error: ' + err.message;
      renderModal();
    });
  }

  function pollJobStatus() {
    fetchJSON('/api/job/status').then(({status, data}) => {
      if (status >= 400) {
        clearInterval(state.pollingInterval);
        state.pollingInterval = null;
        state.modalState = 'error';
        state.modalError = 'Failed to check job status';
        renderModal();
        return;
      }

      // Update progress display
      const progressText = document.getElementById('progress-text');
      const progressFill = document.getElementById('progress-fill');
      if (progressText) {
        progressText.textContent = data.message || 'Processed ' + (data.frames_done||0) + '/' + (data.total_frames||'?') + ' frames';
      }
      if (progressFill && data.progress > 0) {
        progressFill.style.width = (data.progress * 100) + '%';
      }

      if (data.running) return; // still processing

      // Job finished
      clearInterval(state.pollingInterval);
      state.pollingInterval = null;

      if (data.error) {
        state.modalState = 'error';
        state.modalError = data.error;
        renderModal();
      } else {
        state.modalState = 'result';
        state.modalSessionId = data.session_id;
        renderModal();
        fetchSessions();
      }
    }).catch(err => {
      clearInterval(state.pollingInterval);
      state.pollingInterval = null;
      state.modalState = 'error';
      state.modalError = 'Network error: ' + err.message;
      renderModal();
    });
  }

  // ── DATA FETCHING ──

  function fetchSources() {
    state.sourcesLoading = true;
    state.sourcesError = null;
    renderSourcesTab();
    return fetchJSON('/api/sources').then(({status, data}) => {
      state.sourcesLoading = false;
      if (status === 200) {
        state.sources = data;
        state.sourcesError = null;
      } else {
        state.sourcesError = 'Failed to load sources';
      }
      renderSourcesTab();
    }).catch(() => {
      state.sourcesLoading = false;
      state.sourcesError = 'Network error loading sources';
      renderSourcesTab();
    });
  }

  function fetchSessions() {
    state.sessionsLoading = true;
    state.sessionsError = null;
    renderJobsTab();
    fetchJSON('/api/sessions').then(({status, data}) => {
      state.sessionsLoading = false;
      if (status === 200) {
        state.sessions = data;
        state.sessionsError = null;
      } else {
        state.sessionsError = 'Failed to load sessions';
      }
      renderJobsTab();
    }).catch(() => {
      state.sessionsLoading = false;
      state.sessionsError = 'Network error loading sessions';
      renderJobsTab();
    });
  }

  // ── INIT ──
  function init() {
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
      tab.onclick = () => switchTab(tab.dataset.tab);
    });

    // Drawer tab switching
    document.querySelectorAll('.drawer-tab').forEach(tab => {
      tab.onclick = () => switchDrawerTab(tab.dataset.dtab);
    });

    // Drawer close
    document.getElementById('drawer-close').onclick = closeDrawer;
    document.getElementById('drawer-overlay').onclick = closeDrawer;

    // Draw Area toggle
    document.getElementById('draw-area-btn').onclick = () => {
      if (!state.drawerOpen || !state.selectedSourceId) return;
      state.drawMode = !state.drawMode;
      if (state.drawMode) {
        state.currentPolygon = [];
        document.getElementById('draw-area-btn').textContent = 'Cancel Drawing';
        const canvas = document.getElementById('preview-canvas');
        const img = document.getElementById('preview-img');
        if (canvas && img) {
          const rect = img.getBoundingClientRect();
          if (rect.width > 0) {
            canvas.width = rect.width;
            canvas.height = rect.height;
          }
        }
        drawCanvasDuringDrawMode();
      } else {
        cancelDrawing();
      }
    };

    // Save polygon
    document.getElementById('save-polygon-btn').onclick = savePolygon;
    document.getElementById('cancel-polygon-btn').onclick = () => {
      state.drawMode = false;
      state.currentPolygon = [];
      document.getElementById('draw-actions').style.display = 'none';
      document.getElementById('draw-area-btn').textContent = 'Draw Area';
      drawExistingROIs();
    };

    // Canvas click
    document.getElementById('preview-canvas').onclick = handleCanvasClick;

    // Run Analysis from drawer footer
    document.getElementById('run-analysis-btn').onclick = () => {
      if (state.selectedSourceId) {
        const sid = state.selectedSourceId;
        closeDrawer();
        openModal(sid);
      }
    };

    // Modal close on overlay click
    document.getElementById('modal').onclick = (e) => {
      if (e.target === document.getElementById('modal')) closeModal();
    };

    // Add Source form
    const addBtn = document.getElementById('add-source-btn');
    if (addBtn) addBtn.onclick = () => { document.getElementById('add-source-form').style.display = 'block'; };
    document.getElementById('cancel-source-btn').onclick = () => {
      document.getElementById('add-source-form').style.display = 'none';
      document.getElementById('add-source-error').textContent = '';
    };
    document.getElementById('save-source-btn').onclick = () => {
      const name = document.querySelector('[name="new_name"]').value.trim();
      const type = document.querySelector('[name="new_type"]').value;
      const uri = document.querySelector('[name="new_uri"]').value.trim();
      const errDiv = document.getElementById('add-source-error');
      fetchJSON('/api/sources', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, source_type: type, source_uri: uri})
      }).then(({status, data}) => {
        if (status >= 400) {
          errDiv.textContent = data.error || 'Error creating source';
        } else {
          document.querySelector('[name="new_name"]').value = '';
          document.querySelector('[name="new_uri"]').value = '';
          document.getElementById('add-source-form').style.display = 'none';
          errDiv.textContent = '';
          fetchSources();
        }
      }).catch(() => { errDiv.textContent = 'Network error'; });
    };

    // Retry buttons
    document.getElementById('sources-retry-btn').onclick = fetchSources;
    document.getElementById('jobs-retry-btn').onclick = fetchSessions;

    // Keyboard: Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (state.drawMode) {
          cancelDrawing();
        } else if (state.modalOpen) {
          closeModal();
        } else if (state.drawerOpen) {
          closeDrawer();
        }
      }
    });

    // Initial fetch
    fetchSources();
  }

  document.addEventListener('DOMContentLoaded', init);
  </script>
</body>
</html>"""
