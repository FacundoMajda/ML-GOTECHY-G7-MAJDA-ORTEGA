# src/utils/html_utils.py
import html as html_module


def escape(text: str) -> str:
    """Escape HTML special characters."""
    return html_module.escape(text, quote=True)


def render_home() -> str:
    """Home page — single-page vertical layout with 5 sections.
    JS fetches /api/sources and populates the UI dynamically.
    """
    return """<!DOCTYPE html>
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
      margin: 0;
      font-family: "Trebuchet MS", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    .wrap { max-width: 1280px; margin: 0 auto; padding: 28px 18px 40px; }

    /* ── Page Header ── */
    .page-header { margin-bottom: 28px; }
    .page-header h1 { margin: 0 0 6px; font-family: Georgia, serif; font-size: 2.2rem; }
    .page-header p { margin: 0; color: var(--muted); font-size: 0.95rem; }

    /* ── Sections (cards) ── */
    section.card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 20px;
      margin-bottom: 20px;
    }
    section.card h2 {
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--accent-2);
      font-weight: 700;
      margin: 0 0 14px;
    }

    /* ── Sources ── */
    .sources-list { display: flex; flex-direction: column; gap: 10px; max-height: 420px; overflow-y: auto; }
    .source-card {
      display: flex; align-items: center; gap: 12px;
      padding: 12px 14px; border-radius: 14px; border: 1px solid var(--line);
      cursor: pointer; transition: background 0.15s;
    }
    .source-card:hover { background: rgba(15,118,110,0.06); }
    .source-card.selected { border-color: var(--accent); background: rgba(15,118,110,0.08); }
    .source-thumb {
      width: 72px; height: 54px; object-fit: cover; border-radius: 8px;
      background: #e5e7eb; flex-shrink: 0;
    }
    .source-info { flex: 1; min-width: 0; }
    .source-name { font-weight: 700; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .source-meta { font-size: 0.8rem; color: var(--muted); margin-top: 2px; }
    .source-type-badge {
      display: inline-block; font-size: 0.7rem; padding: 1px 6px; border-radius: 4px;
      background: rgba(15,118,110,0.12); color: var(--accent); text-transform: uppercase; letter-spacing: 0.05em;
    }

    /* ── Add Source Form ── */
    #add-source-btn {
      margin-top: 12px; width: 100%; padding: 10px 14px;
      border-radius: 12px; border: 1px dashed var(--accent);
      background: transparent; color: var(--accent); font-weight: 600; font-size: 0.9rem;
      cursor: pointer; transition: background 0.15s;
    }
    #add-source-btn:hover { background: rgba(15,118,110,0.06); }
    .add-source-grid {
      margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
    }
    .add-source-grid input,
    .add-source-grid select {
      width: 100%; border-radius: 10px; border: 1px solid var(--line);
      padding: 10px 12px; font-size: 0.9rem; background: #fff;
    }
    .add-source-grid .full-row { grid-column: 1 / -1; }
    .add-source-actions {
      display: flex; gap: 10px; margin-top: 10px;
    }
    .add-source-actions button {
      flex: 1; border-radius: 10px; border: none; padding: 10px 14px;
      font-weight: 600; font-size: 0.9rem; cursor: pointer;
    }
    #save-source-btn { background: var(--accent); color: white; }
    #cancel-source-btn { background: #e5e7eb; color: var(--ink); }

    /* ── Preview ── */
    #preview-img { width: 100%; border-radius: 12px; aspect-ratio: 16/9; object-fit: cover; background: #e5e7eb; }
    #preview-placeholder {
      width: 100%; aspect-ratio: 16/9; border-radius: 12px; background: #e5e7eb;
      display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 0.85rem;
    }

    /* ── Areas / ROI Badges ── */
    #areas-list { display: flex; flex-wrap: wrap; gap: 6px; }
    .roi-badge {
      padding: 4px 10px; border-radius: 20px; font-size: 0.8rem;
      border: 1px solid var(--line); background: white;
    }

    /* ── Metrics (checkboxes) ── */
    .metrics-grid { display: flex; flex-wrap: wrap; gap: 14px; }
    .metrics-grid label {
      display: flex; align-items: center; gap: 6px;
      font-size: 0.9rem; cursor: pointer;
    }
    .metrics-grid input[type="checkbox"] {
      width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer;
    }
    .metrics-grid label.disabled { color: var(--muted); cursor: not-allowed; }
    .metrics-grid label.disabled input { cursor: not-allowed; }

    /* ── Output ── */
    .output-grid { display: flex; flex-wrap: wrap; gap: 14px; align-items: center; }
    .output-grid label {
      display: flex; align-items: center; gap: 6px;
      font-size: 0.9rem; cursor: pointer;
    }
    .output-grid input[type="checkbox"] {
      width: 18px; height: 18px; accent-color: var(--accent); cursor: pointer;
    }
    #generate-btn {
      width: 100%; margin-top: 14px;
      background: linear-gradient(135deg, var(--accent), #115e59);
      color: white; font-weight: 700; border: none;
      font-size: 1rem; padding: 12px 14px; border-radius: 12px;
      cursor: pointer; transition: filter 0.15s;
    }
    #generate-btn:hover { filter: brightness(1.05); }
    #generate-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    /* ── Responsive ── */
    @media (max-width: 640px) {
      .add-source-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="page-header">
      <h1>Video Analytics</h1>
      <p>Generate operational reports from video sources</p>
    </div>

    <!-- SECTION: SOURCES -->
    <section id="sources" class="card">
      <h2>DATA SOURCES</h2>
      <div id="sources-list" class="sources-list"></div>
      <button id="add-source-btn">+ Add Source</button>
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
        <div id="add-source-error" style="color:#dc2626;margin-top:8px;font-size:0.85rem"></div>
      </div>
    </section>

    <!-- SECTION: PREVIEW -->
    <section id="preview" class="card">
      <h2>PREVIEW</h2>
      <img id="preview-img" src="" style="display:none" alt="Video preview" onerror="this.style.display='none';document.getElementById('preview-placeholder').style.display='flex'">
      <div id="preview-placeholder">Select a source to preview</div>
    </section>

    <!-- SECTION: OBSERVATION AREAS -->
    <section id="areas" class="card">
      <h2>OBSERVATION AREAS</h2>
      <div id="areas-list"></div>
    </section>

    <!-- FORM wraps metrics + output sections -->
    <form method="post" action="/process">
      <input type="hidden" name="video_source_id">

      <!-- SECTION: METRICS -->
      <section id="metrics" class="card">
        <h2>METRICS</h2>
        <div class="metrics-grid">
          <label><input type="checkbox" name="metric_entries" checked> Entries</label>
          <label><input type="checkbox" name="metric_exits" checked> Exits</label>
          <label><input type="checkbox" name="metric_occupancy" checked> Occupancy</label>
          <label class="disabled"><input type="checkbox" disabled title="Coming soon"> Dwell Time</label>
          <label class="disabled"><input type="checkbox" disabled title="Coming soon"> Heatmap</label>
        </div>
      </section>

      <!-- SECTION: OUTPUT -->
      <section id="output" class="card">
        <h2>OUTPUT</h2>
        <div class="output-grid">
          <label><input type="checkbox" name="output_report" checked> Report</label>
          <label><input type="checkbox" name="output_video" checked> Annotated Video</label>
        </div>
        <button id="generate-btn" type="submit" disabled>Generate Report</button>
      </section>
    </form>
  </div>

  <script>
  let sources = [];

  function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function renderSourceCards() {
    const list = document.getElementById('sources-list');
    if (sources.length === 0) {
      list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted)">No sources loaded. Add one below.</div>';
      return;
    }
    list.innerHTML = sources.map(s => `
      <div class="source-card" data-id="${s.id}" onclick="selectSource('${s.id}')">
        <img class="source-thumb" src="/api/sources/${s.id}/preview" alt="${esc(s.name)}">
        <div class="source-info">
          <div class="source-name">${esc(s.name)}</div>
          <div class="source-meta">
            <span class="source-type-badge">${esc(s.source_type)}</span>
            <span> · ${(s.rois || []).length} areas</span>
          </div>
        </div>
      </div>
    `).join('');
  }

  function selectSource(id) {
    const src = sources.find(s => s.id === id);
    if (!src) return;

    // Highlight card
    document.querySelectorAll('.source-card').forEach(c => c.classList.remove('selected'));
    const card = document.querySelector(`[data-id="${id}"]`);
    if (card) card.classList.add('selected');

    // Update hidden input
    document.querySelector('[name="video_source_id"]').value = id;

    // Enable generate button
    document.getElementById('generate-btn').disabled = false;

    // Preview
    const img = document.getElementById('preview-img');
    img.src = `/api/sources/${id}/preview`;
    img.style.display = 'block';
    document.getElementById('preview-placeholder').style.display = 'none';

    // Area badges
    const areasList = document.getElementById('areas-list');
    if (src.rois && src.rois.length) {
      areasList.innerHTML = src.rois.map(r =>
        `<span class="roi-badge">${esc(r.name)}</span>`
      ).join('');
    } else {
      areasList.innerHTML = '<span style="color:var(--muted);font-size:0.85rem">No observation areas configured</span>';
    }
  }

  // On load: fetch sources
  fetch('/api/sources')
    .then(r => r.json())
    .then(data => {
      sources = data;
      renderSourceCards();
      // Auto-select if only one source
      if (data.length === 1) selectSource(data[0].id);
    });

  // Add Source flow
  document.getElementById('add-source-btn').onclick = () => {
    document.getElementById('add-source-form').style.display = 'block';
  };
  document.getElementById('cancel-source-btn').onclick = () => {
    document.getElementById('add-source-form').style.display = 'none';
    document.getElementById('add-source-error').textContent = '';
  };
  document.getElementById('save-source-btn').onclick = () => {
    const name = document.querySelector('[name="new_name"]').value.trim();
    const type = document.querySelector('[name="new_type"]').value;
    const uri = document.querySelector('[name="new_uri"]').value.trim();
    const errorDiv = document.getElementById('add-source-error');

    fetch('/api/sources', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, source_type: type, source_uri: uri})
    })
    .then(r => r.json().then(data => ({status: r.status, data})))
    .then(({status, data}) => {
      if (status >= 400) {
        errorDiv.textContent = data.error || 'Error creating source';
      } else {
        // Refresh sources
        fetch('/api/sources').then(r => r.json()).then(s => {
          sources = s;
          renderSourceCards();
        });
        document.getElementById('add-source-form').style.display = 'none';
        document.querySelector('[name="new_name"]').value = '';
        document.querySelector('[name="new_uri"]').value = '';
        errorDiv.textContent = '';
      }
    })
    .catch(() => { errorDiv.textContent = 'Network error'; });
  };
  </script>
</body>
</html>"""
