#!/usr/bin/env python3
"""
QiBi Dashboard HTML Builder — Generates client_sales.html and client_wastage.html
from dashboard_data.json. Applies all QiBi branding and UI features.

v3.0 — Sales dashboard: venue aggregation, all-2026-weeks display, cumulative PoP,
        % Change metric, Avg per Location row.
"""
import json

with open("dashboard_data.json", "r") as f:
    DATA = json.load(f)

DATA_JSON = json.dumps(DATA, ensure_ascii=False)

# ============================================================
# SHARED CSS + JS UTILITIES
# ============================================================
SHARED_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100vh;overflow:hidden}
body{background:#0a0a0a;color:#fff;font-family:Inter,-apple-system,sans-serif;font-size:13px;line-height:1.5;display:flex;flex-direction:column}
.header{display:flex;align-items:center;justify-content:space-between;padding:20px 32px;border-bottom:1px solid #1a1a1a;flex-shrink:0}
.header img{height:32px}
.header h1{font-size:18px;font-weight:700}
.header .meta{color:#888;font-size:12px}
.back-btn{display:flex;flex-direction:column;align-items:center;gap:4px;text-decoration:none;transition:transform 0.15s,opacity 0.15s;flex-shrink:0}
.back-btn:hover{transform:scale(1.05);opacity:0.9}
.back-btn .back-icon{width:44px;height:44px;border-radius:12px;background:#20ff00;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(32,255,0,0.25)}
.back-btn .back-icon svg{width:22px;height:22px}
.back-btn .back-label{font-size:10px;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap}
.controls{display:flex;flex-wrap:wrap;gap:10px;padding:16px 32px;border-bottom:1px solid #1a1a1a;align-items:center;flex-shrink:0}
.controls select,.controls input{background:#1a1a1a;color:#fff;border:1px solid #333;border-radius:8px;padding:6px 12px;font-size:12px;font-family:inherit}
.controls select:focus,.controls input:focus{outline:none;border-color:#20ff00}
.controls label{color:#888;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}
.pill{display:inline-block;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;cursor:pointer;border:1px solid #333;color:#aaa;transition:all 0.2s}
.pill.active{background:#20ff00;color:#000;border-color:#20ff00}
.pill:hover{border-color:#20ff00}
.content{padding:16px 32px;flex:1;overflow:hidden;display:flex;flex-direction:column;min-height:0}
.table-wrap{overflow:auto;flex:1;min-height:0;border-radius:14px;border:1px solid #1a1a1a;margin-top:12px}
table{width:100%;border-collapse:collapse;white-space:nowrap}
thead th{background:#1a1a1a;color:#888;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;padding:10px 12px;text-align:right;position:sticky;top:0;z-index:10;cursor:pointer;user-select:none}
thead th:first-child{text-align:left;min-width:180px}
thead th:hover{color:#20ff00}
thead th .sort-arrow{margin-left:4px;font-size:10px;opacity:0.5}
thead th .week-date{font-weight:400;font-size:9px;color:#555;display:block;line-height:1.2}
thead th.sorted .sort-arrow{opacity:1;color:#20ff00}
tbody td{padding:8px 12px;border-top:1px solid #1a1a1a;text-align:right;font-variant-numeric:tabular-nums}
tbody td:first-child{text-align:left;font-weight:500;position:sticky;left:0;background:#0a0a0a;z-index:1}
tbody tr:hover td:first-child{background:#1a1a1a}
tbody tr:hover{background:#1a1a1a}
tbody tr.global-row{background:#111;font-weight:700;border-top:2px solid #20ff00}
tbody tr.global-row td{color:#20ff00}
tbody tr.global-row td:first-child{background:#111}
tbody tr.avg-row{background:#0d0d0d;border-top:1px solid #333}
tbody tr.avg-row td{color:#888;font-style:italic;position:sticky;top:48px;z-index:8;background:#0d0d0d}
tbody tr.avg-row td:first-child{position:sticky;left:0;top:48px;z-index:9;background:#0d0d0d}
tbody tr.avg-row:hover td{background:#0d0d0d}
tbody tr.avg-row:hover td:first-child{background:#0d0d0d}
thead th:first-child{position:sticky;left:0;z-index:12;background:#1a1a1a}
thead th.ytd-col{position:sticky;right:0;z-index:13;background:#1a1a1a;box-shadow:-2px 0 4px rgba(0,0,0,0.4)}
tbody td.ytd-col{position:sticky;right:0;z-index:2;background:#0a0a0a;box-shadow:-2px 0 4px rgba(0,0,0,0.4)}
tbody tr:hover td.ytd-col{background:#1a1a1a}
tbody tr.global-row td.ytd-col{background:#111}
tbody tr.avg-row td.ytd-col{background:#0d0d0d}
.green{color:#20ff00}
.red{color:#ff4444}
.orange{color:#ff9900}
.dim{color:#888}
.new-tag{color:#20ff00;font-size:10px;font-weight:700;letter-spacing:1px}
.fridge-name{font-size:15px;font-weight:700;color:#fff}
.machine-name{font-size:11px;color:#666;font-weight:400;margin-top:1px}
.summary-cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;flex-shrink:0}
.summary-card{background:#111;border:1px solid #1a1a1a;border-radius:14px;padding:16px 20px;min-width:180px;flex:1}
.summary-card .label{color:#888;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}
.summary-card .value{font-size:24px;font-weight:700;margin-top:4px}
.summary-card .sub{color:#888;font-size:12px;margin-top:2px}
.l4l-controls{display:flex;gap:8px;align-items:center}
#searchInput{width:200px}
.footer{text-align:center;padding:12px;color:#555;font-size:11px;border-top:1px solid #1a1a1a;flex-shrink:0}
.waste-bar{display:inline-block;height:6px;border-radius:3px;vertical-align:middle;margin-left:4px}
.delta-pos{color:#20ff00}
.delta-neg{color:#ff4444}
.loc-dropdown{position:relative;display:inline-block}
.loc-btn{background:#1a1a1a;color:#fff;border:1px solid #333;border-radius:8px;padding:6px 12px;font-size:12px;cursor:pointer;font-family:inherit;min-width:160px;text-align:left}
.loc-btn:hover{border-color:#20ff00}
.loc-panel{display:none;position:absolute;top:100%;left:0;background:#111;border:1px solid #333;border-radius:8px;padding:8px;max-height:400px;overflow-y:auto;z-index:20;min-width:280px;margin-top:4px;box-shadow:0 8px 24px rgba(0,0,0,0.5)}
.loc-panel.open{display:block}
.loc-panel label{display:block;padding:3px 8px;cursor:pointer;font-size:12px;color:#ccc;border-radius:4px}
.loc-panel label:hover{background:#1a1a1a;color:#fff}
.loc-panel input[type="checkbox"]{margin-right:8px;accent-color:#20ff00}
.loc-actions{display:flex;gap:8px;padding:4px 8px 8px;border-bottom:1px solid #1a1a1a;margin-bottom:4px}
.loc-actions button{background:none;border:1px solid #333;color:#888;border-radius:4px;padding:2px 10px;font-size:11px;cursor:pointer;font-family:inherit}
.loc-actions button:hover{color:#20ff00;border-color:#20ff00}
"""

QIBI_LOGO_BASE64 = "PHN2ZyB2aWV3Qm94PSIwIDAgMTIwIDQwIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjAiIHk9IjMwIiBmb250LWZhbWlseT0iSW50ZXIsc2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9IjgwMCIgZm9udC1zaXplPSIzMiIgZmlsbD0iI2ZmZiI+UWk8dHNwYW4gZmlsbD0iIzIwZmYwMCI+Qmk8L3RzcGFuPjwvdGV4dD48L3N2Zz4="

SHARED_JS = """
function fmt(n) { return n.toLocaleString('en-CH'); }
function fmtCHF(n) { return 'CHF ' + n.toLocaleString('en-CH', {minimumFractionDigits:0, maximumFractionDigits:0}); }
function fmtPct(n) { return n.toFixed(1) + '%'; }
function fmtDelta(n) {
  var sign = n >= 0 ? '+' : '';
  return sign + n.toFixed(1) + '%';
}
function fmtDeltaCHF(n) {
  var sign = n >= 0 ? '+' : '';
  return sign + 'CHF ' + Math.abs(n).toLocaleString('en-CH', {minimumFractionDigits:0, maximumFractionDigits:0});
}
function deltaClass(n, inverted) {
  if (n === 0 || isNaN(n)) return 'dim';
  if (inverted) return n < 0 ? 'delta-pos' : 'delta-neg';
  return n > 0 ? 'delta-pos' : 'delta-neg';
}

function getWeekYear(wk) {
  var parts = wk.split('-W');
  return [parseInt(parts[0]), parseInt(parts[1])];
}

function getMatchingWeekLastYear(wk) {
  var p = getWeekYear(wk);
  return (p[0]-1) + '-W' + String(p[1]).padStart(2,'0');
}

function getWeekMonday(wk) {
  var parts = wk.split('-W');
  var year = parseInt(parts[0]);
  var week = parseInt(parts[1]);
  var jan4 = new Date(year, 0, 4);
  var dow = jan4.getDay() || 7;
  var w1Mon = new Date(year, 0, 4 - dow + 1);
  var target = new Date(w1Mon.getTime() + (week - 1) * 7 * 86400000);
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return months[target.getMonth()] + ' ' + target.getDate();
}

var currentMode = 'sequential';
var sortCol = null;
var sortDir = 'desc';

function weekHasData(wk) {
  return DATA.meta.weeks.indexOf(wk) !== -1;
}

// ── Checkbox panel helpers (Location, Category, Year) ──
function _togglePanel(id) { document.getElementById(id).classList.toggle('open'); }
function _selectAll(cls) { document.querySelectorAll('.' + cls).forEach(function(cb) { cb.checked = true; }); }
function _deselectAll(cls) { document.querySelectorAll('.' + cls).forEach(function(cb) { cb.checked = false; }); }
function _getSelected(cls) {
  var all = document.querySelectorAll('.' + cls);
  var checked = document.querySelectorAll('.' + cls + ':checked');
  if (checked.length === 0 || checked.length === all.length) return null;
  var out = [];
  checked.forEach(function(cb) { out.push(cb.value); });
  return out;
}

// Location panel
function toggleLocPanel() { _togglePanel('locPanel'); }
function locSelectAll() { _selectAll('loc-cb'); updateLocBtn(); render(); }
function locDeselectAll() { _deselectAll('loc-cb'); updateLocBtn(); render(); }
function onLocChange() { updateLocBtn(); render(); }
function updateLocBtn() {
  var all = document.querySelectorAll('.loc-cb');
  var checked = document.querySelectorAll('.loc-cb:checked');
  var btn = document.getElementById('locBtn');
  if (checked.length === 0 || checked.length === all.length) {
    btn.textContent = 'All Locations (' + all.length + ')';
  } else {
    btn.textContent = 'Locations (' + checked.length + '/' + all.length + ')';
  }
}
function getSelectedLocs() { return _getSelected('loc-cb'); }

// Category panel
function toggleCatPanel() { _togglePanel('catPanel'); }
function catSelectAll() { _selectAll('cat-cb'); updateCatBtn(); render(); }
function catDeselectAll() { _deselectAll('cat-cb'); updateCatBtn(); render(); }
function onCatChange() { updateCatBtn(); render(); }
function updateCatBtn() {
  var all = document.querySelectorAll('.cat-cb');
  var checked = document.querySelectorAll('.cat-cb:checked');
  var btn = document.getElementById('catBtn');
  if (checked.length === 0 || checked.length === all.length) {
    btn.textContent = 'All Categories (' + all.length + ')';
  } else {
    btn.textContent = 'Categories (' + checked.length + '/' + all.length + ')';
  }
}
function getSelectedCats() { return _getSelected('cat-cb'); }

// Year panel
function toggleYearPanel() { _togglePanel('yearPanel'); }
function yearSelectAll() { _selectAll('year-cb'); updateYearBtn(); render(); }
function yearDeselectAll() { _deselectAll('year-cb'); updateYearBtn(); render(); }
function onYearChange() { updateYearBtn(); render(); }
function updateYearBtn() {
  var all = document.querySelectorAll('.year-cb');
  var checked = document.querySelectorAll('.year-cb:checked');
  var btn = document.getElementById('yearBtn');
  if (checked.length === 0 || checked.length === all.length) {
    btn.textContent = 'All Years (' + all.length + ')';
  } else {
    var names = [];
    checked.forEach(function(cb) { names.push(cb.value); });
    btn.textContent = names.join(', ');
  }
}
function getSelectedYears() { return _getSelected('year-cb'); }

// Close any open panel on outside click
document.addEventListener('click', function(e) {
  [['locPanel','locBtn'],['catPanel','catBtn'],['yearPanel','yearBtn']].forEach(function(pair) {
    var p = document.getElementById(pair[0]);
    var b = document.getElementById(pair[1]);
    if (p && !p.contains(e.target) && e.target !== b) p.classList.remove('open');
  });
});

function setMode(el) {
  document.querySelectorAll('.pill').forEach(function(p) { p.classList.remove('active'); });
  el.classList.add('active');
  currentMode = el.getAttribute('data-mode');
  sortCol = null;
  sortDir = 'desc';
  render();
}

function toggleSort(colIdx) {
  if (sortCol === colIdx) {
    sortDir = sortDir === 'desc' ? 'asc' : 'desc';
  } else {
    sortCol = colIdx;
    sortDir = 'desc';
  }
  render();
}
"""

# ============================================================
# HEADER HTML
# ============================================================
BACK_BUTTON_HTML = """<a href="index.html" class="back-btn">
  <div class="back-icon"><svg viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg></div>
  <span class="back-label">All Dashboards</span>
</a>"""

def build_header(title, meta_text):
    return f"""<div class="header">
  <div style="display:flex;align-items:center;gap:12px">
    <img src="data:image/svg+xml;base64,{QIBI_LOGO_BASE64}" alt="QiBi">
    <div>
      <h1>{title}</h1>
      <div class="meta">{meta_text}</div>
    </div>
  </div>
  {BACK_BUTTON_HTML}
</div>"""

# ============================================================
# LOCATION PANEL BUILDER (shared by both dashboards)
# ============================================================
def build_location_panel(venues):
    """Build the location checkbox dropdown panel HTML"""
    html = '<div class="loc-dropdown">\n'
    html += f'  <button id="locBtn" class="loc-btn" onclick="toggleLocPanel()">All Locations ({len(venues)})</button>\n'
    html += '  <div id="locPanel" class="loc-panel">\n'
    html += '    <div class="loc-actions"><button onclick="locSelectAll()">Select All</button><button onclick="locDeselectAll()">Deselect All</button></div>\n'
    for v in sorted(venues):
        safe_v = v.replace("'", "\\'").replace('"', '&quot;')
        html += f'    <label><input type="checkbox" class="loc-cb" value="{safe_v}" checked onchange="onLocChange()">{v}</label>\n'
    html += '  </div>\n</div>'
    return html

# ============================================================
# CATEGORY FILTER BUILDER (shared by both dashboards)
# ============================================================
def build_category_filter(categories):
    """Build the category checkbox dropdown panel HTML"""
    cats = sorted(categories) if categories else []
    html = '<div>\n  <label>Category</label><br>\n  <div class="loc-dropdown">\n'
    html += f'    <button id="catBtn" class="loc-btn" onclick="toggleCatPanel()">All Categories ({len(cats)})</button>\n'
    html += '    <div id="catPanel" class="loc-panel">\n'
    html += '      <div class="loc-actions"><button onclick="catSelectAll()">Select All</button><button onclick="catDeselectAll()">Deselect All</button></div>\n'
    for cat in cats:
        html += f'      <label><input type="checkbox" class="cat-cb" value="{cat}" checked onchange="onCatChange()">{cat}</label>\n'
    html += '    </div>\n  </div>\n</div>'
    return html

# ============================================================
# YEAR FILTER BUILDER (shared by both dashboards)
# ============================================================
def build_year_filter(weeks):
    """Build the year checkbox dropdown panel HTML — current year checked by default"""
    years = sorted(set(w.split('-')[0] for w in weeks), reverse=True)
    current_year = years[0] if years else '2026'
    html = '<div>\n  <label>Year</label><br>\n  <div class="loc-dropdown">\n'
    html += f'    <button id="yearBtn" class="loc-btn" onclick="toggleYearPanel()">{current_year}</button>\n'
    html += '    <div id="yearPanel" class="loc-panel">\n'
    html += '      <div class="loc-actions"><button onclick="yearSelectAll()">Select All</button><button onclick="yearDeselectAll()">Deselect All</button></div>\n'
    for y in years:
        checked = ' checked' if y == current_year else ''
        html += f'      <label><input type="checkbox" class="year-cb" value="{y}"{checked} onchange="onYearChange()">{y}</label>\n'
    html += '    </div>\n  </div>\n</div>'
    return html

# ============================================================
# FRIDGE FILTER BUILDER (All vs Active — excludes Office/Bureau/Team)
# ============================================================
def build_fridge_filter():
    """Build All/Active fridges dropdown"""
    html = '<div>\n  <label>Fridges</label><br>\n  <select id="fridgeFilter" onchange="render()">\n'
    html += '    <option value="active">Active Fridges</option>\n'
    html += '    <option value="all">All Fridges</option>\n'
    html += '  </select>\n</div>'
    return html

# ============================================================
# BUILD SALES DASHBOARD (v4.0)
# ============================================================
def build_sales_html():
    meta = DATA["meta"]
    weeks = meta["weeks"]
    venues = meta.get("venues", list(DATA["sales"]["by_fridge"].keys()))
    n_locations = len(venues)

    meta_text = f"Generated: {meta['generated']} | {len(weeks)} weeks | {n_locations} locations"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QiBi — Client Sales Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
{SHARED_CSS}
</style>
</head>
<body>
{build_header("Client Sales Dashboard", meta_text)}

<div class="controls">
  {build_year_filter(weeks)}
  {build_category_filter(DATA.get("meta",{}).get("categories",[]))}
  <div>
    <label>Locations</label><br>
    {build_location_panel(venues)}
  </div>
  <div>
    <label>View</label><br>
    <div class="l4l-controls">
      <span class="pill active" data-mode="sequential" onclick="setMode(this)">Sequential</span>
      <span class="pill" data-mode="yoy" onclick="setMode(this)">YoY</span>
      <span class="pill" data-mode="pop" onclick="setMode(this)">Cumulative</span>
    </div>
  </div>
  <div>
    <label>Show</label><br>
    <select id="showFilter" onchange="render()">
      <option value="all">All Locations</option>
      <option value="top10">Top 10 (Revenue)</option>
      <option value="bottom10">Bottom 10 (Revenue)</option>
    </select>
  </div>
  <div>
    <label>Metric</label><br>
    <select id="metricFilter" onchange="render()">
      <option value="revenue">Revenue (CHF)</option>
      <option value="units">Units Sold</option>
      <option value="pct">% Change</option>
    </select>
  </div>
</div>

<div class="content" id="mainContent"></div>

<div class="footer">QiBi Analytics — Sales Dashboard v3.0</div>

<script>
var DATA = {DATA_JSON};
{SHARED_JS}

function render() {{
  var selectedCats = getSelectedCats(); // null = all
  var selectedLocs = getSelectedLocs(); // null = all
  var show = document.getElementById('showFilter').value;
  var metric = document.getElementById('metricFilter').value;
  var mode = currentMode;

  var salesData = DATA.sales.by_fridge;
  var weeks = DATA.meta.weeks;

  // In sequential mode, pct metric falls back to revenue
  if (mode === 'sequential' && metric === 'pct') metric = 'revenue';

  // Helper: extract values from a week entry, respecting category filter
  function getWV(weekEntry) {{
    if (!weekEntry) return {{u:0, r:0}};
    if (!selectedCats) return {{u: weekEntry.u || 0, r: weekEntry.r || 0}};
    var su=0, sr=0, cats = weekEntry.cats || {{}};
    selectedCats.forEach(function(k) {{ var c = cats[k]; if (c) {{ su += c.u||0; sr += c.r||0; }} }});
    return {{u: su, r: sr}};
  }}
  function getYTD(venueData) {{
    if (!selectedCats) return {{u: venueData.ytd_u || 0, r: venueData.ytd_r || 0}};
    var su=0, sr=0, cats = venueData.ytd_cats || {{}};
    selectedCats.forEach(function(k) {{ var c = cats[k]; if (c) {{ su += c.u||0; sr += c.r||0; }} }});
    return {{u: su, r: sr}};
  }}

  var venueMap = salesData;
  var officeRe = /office|bureau|team/i;
  var allVenueKeys = Object.keys(venueMap);

  // ── 2. Determine display weeks (year filter — multi-select) ──
  var selectedYears = getSelectedYears(); // null = all
  var displayWeeks;
  if (!selectedYears) {{
    displayWeeks = weeks;
  }} else {{
    displayWeeks = weeks.filter(function(w) {{ return selectedYears.indexOf(w.split('-')[0]) !== -1; }});
  }}
  var weeks2026 = weeks.filter(function(w) {{ return w.startsWith('2026-'); }});

  // ── 3. Build venue rows (all venues — location checkboxes control visibility) ──
  var rows = [];
  allVenueKeys.forEach(function(venue) {{
    var vd = venueMap[venue];

    // Location checkbox filter
    if (selectedLocs && selectedLocs.indexOf(venue) === -1) return;

    var weekValues = [];
    var ytdVal = 0, ytdDelta = 0, ytdPctDelta = null;

    if (mode === 'yoy') {{
      displayWeeks.forEach(function(wk) {{
        var d = getWV(vd.weeks[wk]);
        var lyWk = getMatchingWeekLastYear(wk);
        var lyD = getWV(vd.weeks[lyWk]);
        weekValues.push({{
          tyR: d.r, tyU: d.u, lyR: lyD.r, lyU: lyD.u,
          deltaR: d.r - lyD.r, deltaU: d.u - lyD.u,
          pctR: lyD.r > 0 ? ((d.r - lyD.r) / lyD.r * 100) : (d.r > 0 ? null : 0),
          pctU: lyD.u > 0 ? ((d.u - lyD.u) / lyD.u * 100) : (d.u > 0 ? null : 0)
        }});
      }});

      var tyR = 0, lyR = 0, tyU = 0, lyU = 0;
      weeks2026.filter(weekHasData).forEach(function(wk) {{
        var d = getWV(vd.weeks[wk]);
        tyR += d.r; tyU += d.u;
        var lyWk = getMatchingWeekLastYear(wk);
        var lyD = getWV(vd.weeks[lyWk]);
        lyR += lyD.r; lyU += lyD.u;
      }});
      ytdVal = metric === 'units' ? tyU : tyR;
      ytdDelta = metric === 'units' ? (tyU - lyU) : (tyR - lyR);
      var lyBase = metric === 'units' ? lyU : lyR;
      ytdPctDelta = lyBase > 0 ? (ytdDelta / lyBase * 100) : (ytdVal > 0 ? null : 0);

    }} else if (mode === 'pop') {{
      var cumTyR = 0, cumLyR = 0, cumTyU = 0, cumLyU = 0;
      displayWeeks.forEach(function(wk) {{
        var d = getWV(vd.weeks[wk]);
        cumTyR += d.r; cumTyU += d.u;
        var lyWk = getMatchingWeekLastYear(wk);
        var lyD = getWV(vd.weeks[lyWk]);
        cumLyR += lyD.r; cumLyU += lyD.u;
        weekValues.push({{
          tyR: cumTyR, tyU: cumTyU, lyR: cumLyR, lyU: cumLyU,
          deltaR: cumTyR - cumLyR, deltaU: cumTyU - cumLyU,
          pctR: cumLyR > 0 ? ((cumTyR - cumLyR) / cumLyR * 100) : (cumTyR > 0 ? null : 0),
          pctU: cumLyU > 0 ? ((cumTyU - cumLyU) / cumLyU * 100) : (cumTyU > 0 ? null : 0)
        }});
      }});
      ytdVal = metric === 'units' ? cumTyU : cumTyR;
      ytdDelta = metric === 'units' ? (cumTyU - cumLyU) : (cumTyR - cumLyR);
      var lyBase = metric === 'units' ? cumLyU : cumLyR;
      ytdPctDelta = lyBase > 0 ? (ytdDelta / lyBase * 100) : (ytdVal > 0 ? null : 0);

    }} else {{
      displayWeeks.forEach(function(wk) {{
        var d = getWV(vd.weeks[wk]);
        weekValues.push({{tyR: d.r, tyU: d.u}});
      }});
      var ytd = getYTD(vd);
      ytdVal = metric === 'units' ? ytd.u : ytd.r;
    }}

    rows.push({{
      venue: venue,
      weekValues: weekValues,
      ytdVal: ytdVal,
      ytdDelta: ytdDelta,
      ytdPctDelta: ytdPctDelta,
      sortYtd: ytdVal
    }});
  }});

  // ── 4. Top/bottom filter ──
  if (show === 'top10') {{
    rows.sort(function(a,b) {{ return b.sortYtd - a.sortYtd; }});
    rows = rows.slice(0, 10);
  }} else if (show === 'bottom10') {{
    rows.sort(function(a,b) {{ return a.sortYtd - b.sortYtd; }});
    rows = rows.slice(0, 10);
  }}

  // ── 5. Column sorting ──
  if (sortCol !== null) {{
    rows.sort(function(a, b) {{
      var va, vb;
      if (sortCol === 0) {{
        va = a.venue.toLowerCase(); vb = b.venue.toLowerCase();
        return sortDir === 'asc' ? (va < vb ? -1 : 1) : (va > vb ? -1 : 1);
      }}
      if (sortCol === displayWeeks.length + 1) {{
        // YTD column
        if (mode !== 'sequential' && metric === 'pct') {{ va = a.ytdPctDelta || 0; vb = b.ytdPctDelta || 0; }}
        else if (mode !== 'sequential') {{ va = a.ytdDelta; vb = b.ytdDelta; }}
        else {{ va = a.ytdVal; vb = b.ytdVal; }}
      }} else {{
        var idx = sortCol - 1;
        if (idx < 0 || idx >= a.weekValues.length) return 0;
        var wa = a.weekValues[idx], wb = b.weekValues[idx];
        if (mode === 'sequential') {{
          va = metric === 'units' ? wa.tyU : wa.tyR;
          vb = metric === 'units' ? wb.tyU : wb.tyR;
        }} else if (metric === 'pct') {{
          va = wa.pctR != null ? wa.pctR : -9999;
          vb = wb.pctR != null ? wb.pctR : -9999;
        }} else if (metric === 'units') {{
          va = wa.deltaU; vb = wb.deltaU;
        }} else {{
          va = wa.deltaR; vb = wb.deltaR;
        }}
      }}
      return sortDir === 'desc' ? vb - va : va - vb;
    }});
  }}

  // ── 6. Compute Global Total ──
  var globalWV = [];
  var globalYtdVal = 0, globalYtdDelta = 0, globalYtdPctDelta = null;

  displayWeeks.forEach(function(wk, wi) {{
    var gTyR = 0, gLyR = 0, gTyU = 0, gLyU = 0;
    rows.forEach(function(r) {{
      gTyR += r.weekValues[wi].tyR;
      gTyU += r.weekValues[wi].tyU;
      if (mode !== 'sequential') {{
        gLyR += r.weekValues[wi].lyR;
        gLyU += r.weekValues[wi].lyU;
      }}
    }});
    globalWV.push({{
      tyR: gTyR, tyU: gTyU, lyR: gLyR, lyU: gLyU,
      deltaR: gTyR - gLyR, deltaU: gTyU - gLyU,
      pctR: gLyR > 0 ? ((gTyR - gLyR) / gLyR * 100) : (gTyR > 0 ? null : 0),
      pctU: gLyU > 0 ? ((gTyU - gLyU) / gLyU * 100) : (gTyU > 0 ? null : 0)
    }});
  }});

  rows.forEach(function(r) {{ globalYtdVal += r.ytdVal; globalYtdDelta += r.ytdDelta; }});
  // Compute global YTD pct from summed LY base
  if (mode !== 'sequential') {{
    var gYtdLy = globalYtdVal - globalYtdDelta; // ytdVal = TY, delta = TY - LY, so LY = TY - delta
    globalYtdPctDelta = gYtdLy > 0 ? (globalYtdDelta / gYtdLy * 100) : (globalYtdVal > 0 ? null : 0);
  }}

  // ── 7. Compute Avg per Location row ──
  var avgWV = [];
  displayWeeks.forEach(function(wk, wi) {{
    // Count locations active this week (non-zero TY units)
    var activeCount = 0;
    rows.forEach(function(r) {{
      // For sequential, check raw TY units; for delta modes, check tyU
      if (r.weekValues[wi].tyU > 0) activeCount++;
    }});
    var g = globalWV[wi];
    var div = activeCount || 1;
    avgWV.push({{
      tyR: g.tyR / div, tyU: g.tyU / div, lyR: g.lyR / div, lyU: g.lyU / div,
      deltaR: g.deltaR / div, deltaU: g.deltaU / div,
      pctR: g.pctR, pctU: g.pctU, // % is same as global (it's a rate, not summable)
      active: activeCount
    }});
  }});
  var avgYtdActive = rows.length || 1;
  var avgYtdVal = globalYtdVal / avgYtdActive;
  var avgYtdDelta = globalYtdDelta / avgYtdActive;

  // ── 8. Summary cards (category + location aware) ──
  var totalRev = 0, totalUnits = 0;
  rows.forEach(function(r) {{
    var vd = venueMap[r.venue];
    var ytd = getYTD(vd);
    totalRev += ytd.r;
    totalUnits += ytd.u;
  }});
  var activeLocCount = rows.length || 1;
  var avgPerLocation = totalRev / activeLocCount;
  var avgPerWeek = totalRev / (weeks.length || 1);

  // Active fridge count for card: ALL venues, excluding office — independent of table filters
  var latestActiveWeek = null;
  for (var li = displayWeeks.length - 1; li >= 0; li--) {{
    var wk = displayWeeks[li];
    var anyActive = false;
    allVenueKeys.forEach(function(v) {{
      var raw = getWV(venueMap[v].weeks[wk]);
      if (raw.u > 0) anyActive = true;
    }});
    if (anyActive) {{ latestActiveWeek = wk; break; }}
  }}
  var activeFridges = 0;
  if (latestActiveWeek) {{
    allVenueKeys.forEach(function(v) {{
      if (!officeRe.test(v)) {{
        var raw = getWV(venueMap[v].weeks[latestActiveWeek]);
        if (raw.u > 0) activeFridges++;
      }}
    }});
  }}
  var latestWkLabel = latestActiveWeek ? latestActiveWeek.replace(/^\\d{{4}}-/, '') : '—';

  var cardsHtml = '<div class="summary-cards">' +
    '<div class="summary-card"><div class="label">Total Revenue</div><div class="value green">' + fmtCHF(totalRev) + '</div><div class="sub">' + fmt(totalUnits) + ' units</div></div>' +
    '<div class="summary-card"><div class="label">Active Fridges</div><div class="value">' + activeFridges + '</div><div class="sub">' + latestWkLabel + ' (excl. office)</div></div>' +
    '<div class="summary-card"><div class="label">Avg / Location</div><div class="value">' + fmtCHF(avgPerLocation) + '</div></div>' +
    '<div class="summary-card"><div class="label">Avg / Week</div><div class="value">' + fmtCHF(avgPerWeek) + '</div></div>' +
    '</div>';

  // ── 9. Helper: render a cell value ──
  function cellHtml(wv, isGlobal) {{
    if (mode === 'sequential') {{
      if (metric === 'units') return fmt(Math.round(wv.tyU));
      return fmtCHF(wv.tyR);
    }}
    // Delta mode (YoY or Cumulative)
    if (metric === 'pct') {{
      if (wv.pctR === null) return '<span class="new-tag">NEW</span>';
      var cls = deltaClass(wv.pctR, false);
      return '<span class="' + cls + '">' + fmtDelta(wv.pctR) + '</span>';
    }}
    if (metric === 'units') {{
      var cls = deltaClass(wv.deltaU, false);
      return '<span class="' + cls + '">' + (wv.deltaU >= 0 ? '+' : '') + fmt(Math.round(wv.deltaU)) + '</span>';
    }}
    // revenue
    var cls = deltaClass(wv.deltaR, false);
    return '<span class="' + cls + '">' + fmtDeltaCHF(wv.deltaR) + '</span>';
  }}

  function ytdCellHtml(val, delta, pctDelta) {{
    if (mode === 'sequential') {{
      if (metric === 'units') return fmt(Math.round(val));
      return fmtCHF(val);
    }}
    if (metric === 'pct') {{
      if (pctDelta === null) return '<span class="new-tag">NEW</span>';
      var cls = deltaClass(pctDelta, false);
      return '<span class="' + cls + '">' + fmtDelta(pctDelta) + '</span>';
    }}
    if (metric === 'units') {{
      var cls = deltaClass(delta, false);
      return '<span class="' + cls + '">' + (delta >= 0 ? '+' : '') + fmt(Math.round(delta)) + '</span>';
    }}
    var cls = deltaClass(delta, false);
    return '<span class="' + cls + '">' + fmtDeltaCHF(delta) + '</span>';
  }}

  // ── 10. Build table ──
  var sa = function(ci) {{
    return sortCol === ci ? (sortDir === 'asc' ? '▲' : '▼') : '⇅';
  }};

  var headerHtml = '<tr><th onclick="toggleSort(0)">Location <span class="sort-arrow">' + sa(0) + '</span></th>';
  displayWeeks.forEach(function(wk, i) {{
    var ci = i + 1;
    var label = wk.replace(/^\\d{{4}}-/, '');
    var dateLabel = getWeekMonday(wk);
    headerHtml += '<th onclick="toggleSort(' + ci + ')">' + label + '<span class="week-date">' + dateLabel + '</span><span class="sort-arrow">' + sa(ci) + '</span></th>';
  }});
  var ytdCI = displayWeeks.length + 1;
  headerHtml += '<th class="ytd-col" onclick="toggleSort(' + ytdCI + ')">YTD <span class="sort-arrow">' + sa(ytdCI) + '</span></th></tr>';

  var bodyHtml = '';

  // ── Avg / Location row (TOP of table) ──
  bodyHtml += '<tr class="avg-row"><td><div class="fridge-name">Avg / Location</div><div class="machine-name">' + rows.length + ' active locations</div></td>';
  avgWV.forEach(function(av) {{
    if (mode === 'sequential') {{
      if (metric === 'units') bodyHtml += '<td>' + fmt(Math.round(av.tyU)) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
      else bodyHtml += '<td>' + fmtCHF(Math.round(av.tyR)) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
    }} else if (metric === 'pct') {{
      if (av.pctR === null) bodyHtml += '<td><span class="new-tag">NEW</span></td>';
      else {{
        var cls = deltaClass(av.pctR, false);
        bodyHtml += '<td class="' + cls + '">' + fmtDelta(av.pctR) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
      }}
    }} else if (metric === 'units') {{
      var cls = deltaClass(av.deltaU, false);
      bodyHtml += '<td class="' + cls + '">' + (av.deltaU >= 0 ? '+' : '') + fmt(Math.round(av.deltaU)) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
    }} else {{
      var cls = deltaClass(av.deltaR, false);
      bodyHtml += '<td class="' + cls + '">' + fmtDeltaCHF(Math.round(av.deltaR)) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
    }}
  }});
  if (mode === 'sequential') {{
    bodyHtml += '<td class="ytd-col">' + (metric === 'units' ? fmt(Math.round(avgYtdVal)) : fmtCHF(Math.round(avgYtdVal))) + '</td>';
  }} else if (metric === 'pct') {{
    bodyHtml += '<td class="ytd-col">' + (globalYtdPctDelta !== null ? fmtDelta(globalYtdPctDelta) : '<span class="new-tag">NEW</span>') + '</td>';
  }} else {{
    bodyHtml += '<td class="ytd-col">' + (metric === 'units' ? ((avgYtdDelta >= 0 ? '+' : '') + fmt(Math.round(avgYtdDelta))) : fmtDeltaCHF(Math.round(avgYtdDelta))) + '</td>';
  }}
  bodyHtml += '</tr>';

  // ── Location rows ──
  rows.forEach(function(r) {{
    bodyHtml += '<tr><td><div class="fridge-name">' + r.venue + '</div></td>';
    r.weekValues.forEach(function(wv) {{
      bodyHtml += '<td>' + cellHtml(wv) + '</td>';
    }});
    bodyHtml += '<td class="ytd-col">' + ytdCellHtml(r.ytdVal, r.ytdDelta, r.ytdPctDelta) + '</td></tr>';
  }});

  // ── Global Total row (BOTTOM) ──
  bodyHtml += '<tr class="global-row"><td><div class="fridge-name">Global Total</div><div class="machine-name">All ' + rows.length + ' locations</div></td>';
  globalWV.forEach(function(gv) {{
    bodyHtml += '<td>' + cellHtml(gv, true) + '</td>';
  }});
  bodyHtml += '<td class="ytd-col">' + ytdCellHtml(globalYtdVal, globalYtdDelta, globalYtdPctDelta) + '</td></tr>';

  document.getElementById('mainContent').innerHTML = cardsHtml +
    '<div class="table-wrap"><table><thead>' + headerHtml + '</thead><tbody>' + bodyHtml + '</tbody></table></div>';

  // Freeze panes: set avg-row sticky top to actual thead height
  requestAnimationFrame(function() {{
    var th = document.querySelector('.table-wrap thead');
    if (th) {{
      var h = th.offsetHeight;
      document.querySelectorAll('.avg-row td').forEach(function(td) {{ td.style.top = h + 'px'; }});
    }}
  }});
}}

render();
</script>
</body>
</html>"""
    return html


# ============================================================
# BUILD WASTAGE DASHBOARD (unchanged — v2.0)
# ============================================================
def build_wastage_html():
    meta = DATA["meta"]
    weeks = meta["weeks"]
    venues = meta.get("venues", list(DATA["wastage"]["by_fridge"].keys()))

    meta_text = f"Generated: {meta['generated']} | {len(weeks)} weeks | {len(venues)} locations"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QiBi — Client Wastage Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
{SHARED_CSS}
</style>
</head>
<body>
{build_header("Client Wastage Dashboard", meta_text)}

<div class="controls">
  {build_year_filter(weeks)}
  {build_category_filter(DATA.get("meta",{}).get("categories",[]))}
  <div>
    <label>Locations</label><br>
    {build_location_panel(venues)}
  </div>
  <div>
    <label>View</label><br>
    <div class="l4l-controls">
      <span class="pill active" data-mode="sequential" onclick="setMode(this)">Sequential</span>
      <span class="pill" data-mode="yoy" onclick="setMode(this)">YoY</span>
      <span class="pill" data-mode="pop" onclick="setMode(this)">PoP</span>
    </div>
  </div>
  <div>
    <label>Show</label><br>
    <select id="showFilter" onchange="render()">
      <option value="all">All Locations</option>
      <option value="top10worst">Top 10 Worst (Waste %)</option>
      <option value="top10best">Top 10 Best (Waste %)</option>
    </select>
  </div>
  <div>
    <label>Metric</label><br>
    <select id="metricFilter" onchange="render()">
      <option value="pct">Waste % + Units</option>
      <option value="cost">Waste Cost (CHF)</option>
      <option value="units">Wasted Units</option>
    </select>
  </div>
</div>

<div class="content" id="mainContent"></div>

<div class="footer">QiBi Analytics — Wastage Dashboard v2.0</div>

<script>
var DATA = {DATA_JSON};
{SHARED_JS}

function wasteColor(pct) {{
  if (pct <= 15) return '#20ff00';
  if (pct <= 25) return '#ff9900';
  return '#ff4444';
}}

function wasteColorClass(pct) {{
  if (pct <= 15) return 'green';
  if (pct <= 25) return 'orange';
  return 'red';
}}

function render() {{
  var selectedCats = getSelectedCats(); // null = all
  var selectedLocs = getSelectedLocs(); // null = all
  var show = document.getElementById('showFilter').value;
  var metric = document.getElementById('metricFilter').value;
  var mode = currentMode;

  var wastageData = DATA.wastage.by_fridge;
  var weeks = DATA.meta.weeks;
  var officeRe = /office|bureau|team/i;
  var allVenueKeys = Object.keys(wastageData);

  // Helper: extract values from a week entry, respecting category filter
  function getWW(weekEntry) {{
    if (!weekEntry) return {{i:0, w:0, c:0}};
    if (!selectedCats) return {{i: weekEntry.i || 0, w: weekEntry.w || 0, c: weekEntry.c || 0}};
    var si=0, sw=0, sc=0, cats = weekEntry.cats || {{}};
    selectedCats.forEach(function(k) {{ var cc = cats[k]; if (cc) {{ si += cc.i||0; sw += cc.w||0; sc += cc.c||0; }} }});
    return {{i: si, w: sw, c: sc}};
  }}
  function getWasteYTD(venueData) {{
    if (!selectedCats) return {{i: venueData.ytd_i || 0, w: venueData.ytd_w || 0, c: venueData.ytd_c || 0}};
    var si=0, sw=0, sc=0, cats = venueData.ytd_cats || {{}};
    selectedCats.forEach(function(k) {{ var cc = cats[k]; if (cc) {{ si += cc.i||0; sw += cc.w||0; sc += cc.c||0; }} }});
    return {{i: si, w: sw, c: sc}};
  }}

  // Display weeks (year filter — multi-select)
  var selectedYears = getSelectedYears(); // null = all
  var displayWeeks;
  if (!selectedYears) {{
    displayWeeks = weeks;
  }} else {{
    displayWeeks = weeks.filter(function(w) {{ return selectedYears.indexOf(w.split('-')[0]) !== -1; }});
  }}

  // Build venue rows (all venues — location checkboxes control visibility)
  var rows = [];
  allVenueKeys.forEach(function(venue) {{
    var fd = wastageData[venue];

    // Location checkbox filter
    if (selectedLocs && selectedLocs.indexOf(venue) === -1) return;

    var weekValues = [];
    var ytd = getWasteYTD(fd);
    var ytdIntro = ytd.i;
    var ytdWasted = ytd.w;
    var ytdCost = ytd.c;
    var ytdPct = ytdIntro > 0 ? (ytdWasted / ytdIntro * 100) : 0;

    displayWeeks.forEach(function(wk) {{
      var d = getWW(fd.weeks[wk]);
      var pct = d.i > 0 ? (d.w / d.i * 100) : 0;

      if (mode === 'yoy') {{
        var lyWk = getMatchingWeekLastYear(wk);
        var lyD = getWW(fd.weeks[lyWk]);
        var lyPct = lyD.i > 0 ? (lyD.w / lyD.i * 100) : 0;
        weekValues.push({{intro: d.i, wasted: d.w, cost: d.c, pct: pct, lyPct: lyPct, deltaPct: pct - lyPct, deltaCost: d.c - lyD.c, deltaUnits: d.w - lyD.w}});
      }} else if (mode === 'pop') {{
        var wkIdx = weeks.indexOf(wk);
        var prevWk = wkIdx >= 12 ? weeks[wkIdx - 12] : null;
        var prevD = prevWk ? getWW(fd.weeks[prevWk]) : {{i:0, w:0, c:0}};
        var prevPct = prevD.i > 0 ? (prevD.w / prevD.i * 100) : 0;
        weekValues.push({{intro: d.i, wasted: d.w, cost: d.c, pct: pct, prevPct: prevPct, deltaPct: pct - prevPct, deltaCost: d.c - prevD.c, deltaUnits: d.w - prevD.w}});
      }} else {{
        weekValues.push({{intro: d.i, wasted: d.w, cost: d.c, pct: pct}});
      }}
    }});

    // YTD delta for YoY
    var ytdDeltaPct = 0, ytdDeltaCost = 0, ytdDeltaUnits = 0;
    if (mode === 'yoy') {{
      var tyWeeks = weeks.filter(function(w) {{ return w.startsWith('2026-'); }});
      var tyIntro = 0, tyWasted = 0, tyCost = 0, lyIntro = 0, lyWasted = 0, lyCost = 0;
      tyWeeks.forEach(function(wk) {{
        var d = getWW(fd.weeks[wk]);
        tyIntro += d.i; tyWasted += d.w; tyCost += d.c;
        var lyWk = getMatchingWeekLastYear(wk);
        var lyD = getWW(fd.weeks[lyWk]);
        lyIntro += lyD.i; lyWasted += lyD.w; lyCost += lyD.c;
      }});
      var tyPct = tyIntro > 0 ? (tyWasted / tyIntro * 100) : 0;
      var lyPct = lyIntro > 0 ? (lyWasted / lyIntro * 100) : 0;
      ytdPct = tyPct;
      ytdDeltaPct = tyPct - lyPct;
      ytdDeltaCost = tyCost - lyCost;
      ytdDeltaUnits = tyWasted - lyWasted;
      ytdCost = tyCost;
      ytdWasted = tyWasted;
      ytdIntro = tyIntro;
    }}

    rows.push({{
      venue: venue,
      weekValues: weekValues,
      ytdPct: ytdPct,
      ytdCost: ytdCost,
      ytdWasted: ytdWasted,
      ytdIntro: ytdIntro,
      ytdDeltaPct: ytdDeltaPct,
      ytdDeltaCost: ytdDeltaCost,
      ytdDeltaUnits: ytdDeltaUnits,
      sortYtd: ytdPct
    }});
  }});

  // Top/bottom filter
  if (show === 'top10worst') {{
    rows.sort(function(a,b) {{ return b.ytdPct - a.ytdPct; }});
    rows = rows.slice(0, 10);
  }} else if (show === 'top10best') {{
    rows.sort(function(a,b) {{ return a.ytdPct - b.ytdPct; }});
    rows = rows.slice(0, 10);
  }}

  // Sort by column
  if (sortCol !== null) {{
    rows.sort(function(a, b) {{
      var va, vb;
      if (sortCol === 0) {{ va = a.venue.toLowerCase(); vb = b.venue.toLowerCase(); return sortDir === 'asc' ? (va < vb ? -1 : 1) : (va > vb ? -1 : 1); }}
      var idx = sortCol - 1;
      if (sortCol === displayWeeks.length + 1) {{
        if (mode === 'yoy') {{ va = a.ytdDeltaPct; vb = b.ytdDeltaPct; }}
        else if (metric === 'pct') {{ va = a.ytdPct; vb = b.ytdPct; }}
        else if (metric === 'cost') {{ va = a.ytdCost; vb = b.ytdCost; }}
        else {{ va = a.ytdWasted; vb = b.ytdWasted; }}
      }} else {{
        if (idx < 0 || idx >= a.weekValues.length) return 0;
        if (mode !== 'sequential') {{
          if (metric === 'pct') {{ va = a.weekValues[idx].deltaPct; vb = b.weekValues[idx].deltaPct; }}
          else if (metric === 'cost') {{ va = a.weekValues[idx].deltaCost; vb = b.weekValues[idx].deltaCost; }}
          else {{ va = a.weekValues[idx].deltaUnits; vb = b.weekValues[idx].deltaUnits; }}
        }} else {{
          if (metric === 'pct') {{ va = a.weekValues[idx].pct; vb = b.weekValues[idx].pct; }}
          else if (metric === 'cost') {{ va = a.weekValues[idx].cost; vb = b.weekValues[idx].cost; }}
          else {{ va = a.weekValues[idx].wasted; vb = b.weekValues[idx].wasted; }}
        }}
      }}
      return sortDir === 'desc' ? vb - va : va - vb;
    }});
  }}

  // Compute global totals
  var globalWeekValues = [];
  displayWeeks.forEach(function(wk, wi) {{
    var totalIntro = 0, totalWasted = 0, totalCost = 0;
    var lyTotalIntro = 0, lyTotalWasted = 0, lyTotalCost = 0;
    var prevTotalIntro = 0, prevTotalWasted = 0, prevTotalCost = 0;

    rows.forEach(function(r) {{
      totalIntro += r.weekValues[wi].intro;
      totalWasted += r.weekValues[wi].wasted;
      totalCost += r.weekValues[wi].cost;
    }});

    var pct = totalIntro > 0 ? (totalWasted / totalIntro * 100) : 0;

    if (mode === 'yoy') {{
      var lyWk = getMatchingWeekLastYear(wk);
      rows.forEach(function(r) {{
        var lyD = getWW(wastageData[r.venue].weeks[lyWk]);
        lyTotalIntro += lyD.i; lyTotalWasted += lyD.w; lyTotalCost += lyD.c;
      }});
      var lyPct = lyTotalIntro > 0 ? (lyTotalWasted / lyTotalIntro * 100) : 0;
      globalWeekValues.push({{intro: totalIntro, wasted: totalWasted, cost: totalCost, pct: pct, deltaPct: pct - lyPct, deltaCost: totalCost - lyTotalCost, deltaUnits: totalWasted - lyTotalWasted}});
    }} else if (mode === 'pop') {{
      var wkIdx = weeks.indexOf(wk);
      var prevWk = wkIdx >= 12 ? weeks[wkIdx - 12] : null;
      if (prevWk) {{
        rows.forEach(function(r) {{
          var prevD = getWW(wastageData[r.venue].weeks[prevWk]);
          prevTotalIntro += prevD.i; prevTotalWasted += prevD.w; prevTotalCost += prevD.c;
        }});
      }}
      var prevPct = prevTotalIntro > 0 ? (prevTotalWasted / prevTotalIntro * 100) : 0;
      globalWeekValues.push({{intro: totalIntro, wasted: totalWasted, cost: totalCost, pct: pct, deltaPct: pct - prevPct, deltaCost: totalCost - prevTotalCost, deltaUnits: totalWasted - prevTotalWasted}});
    }} else {{
      globalWeekValues.push({{intro: totalIntro, wasted: totalWasted, cost: totalCost, pct: pct}});
    }}
  }});

  // Global YTD
  var gYtdIntro = 0, gYtdWasted = 0, gYtdCost = 0;
  rows.forEach(function(r) {{ gYtdIntro += r.ytdIntro; gYtdWasted += r.ytdWasted; gYtdCost += r.ytdCost; }});
  var gYtdPct = gYtdIntro > 0 ? (gYtdWasted / gYtdIntro * 100) : 0;

  var gYtdDeltaPct = 0, gYtdDeltaCost = 0, gYtdDeltaUnits = 0;
  if (mode === 'yoy') {{
    var tyWeeks = weeks.filter(function(w) {{ return w.startsWith('2026-'); }});
    var gTyIntro = 0, gTyWasted = 0, gTyCost = 0, gLyIntro2 = 0, gLyWasted2 = 0, gLyCost2 = 0;
    rows.forEach(function(r) {{
      tyWeeks.forEach(function(wk) {{
        var d = getWW(wastageData[r.venue].weeks[wk]);
        gTyIntro += d.i; gTyWasted += d.w; gTyCost += d.c;
        var lyWk = getMatchingWeekLastYear(wk);
        var lyD = getWW(wastageData[r.venue].weeks[lyWk]);
        gLyIntro2 += lyD.i; gLyWasted2 += lyD.w; gLyCost2 += lyD.c;
      }});
    }});
    var gTyPct = gTyIntro > 0 ? (gTyWasted / gTyIntro * 100) : 0;
    var gLyPct = gLyIntro2 > 0 ? (gLyWasted2 / gLyIntro2 * 100) : 0;
    gYtdPct = gTyPct;
    gYtdDeltaPct = gTyPct - gLyPct;
    gYtdDeltaCost = gTyCost - gLyCost2;
    gYtdDeltaUnits = gTyWasted - gLyWasted2;
  }}

  // ── Avg per Location ──
  var avgWeekValues = [];
  displayWeeks.forEach(function(wk, wi) {{
    var activeCount = 0;
    rows.forEach(function(r) {{ if (r.weekValues[wi].intro > 0) activeCount++; }});
    var g = globalWeekValues[wi];
    var div = activeCount || 1;
    avgWeekValues.push({{
      intro: g.intro / div, wasted: g.wasted / div, cost: g.cost / div,
      pct: g.pct, deltaPct: g.deltaPct || 0, deltaCost: (g.deltaCost || 0) / div,
      deltaUnits: (g.deltaUnits || 0) / div, active: activeCount
    }});
  }});
  var avgLocCount = rows.length || 1;
  var avgYtdPct = gYtdPct;
  var avgYtdCost = gYtdCost / avgLocCount;
  var avgYtdWasted = gYtdWasted / avgLocCount;

  // Active fridge count for card: ALL venues, excluding office — independent of table filters
  var latestActiveWeek = null;
  for (var li = displayWeeks.length - 1; li >= 0; li--) {{
    var wk = displayWeeks[li];
    var anyActive = false;
    allVenueKeys.forEach(function(v) {{
      var raw = getWW(wastageData[v].weeks[wk]);
      if (raw.i > 0) anyActive = true;
    }});
    if (anyActive) {{ latestActiveWeek = wk; break; }}
  }}
  var activeFridges = 0;
  if (latestActiveWeek) {{
    allVenueKeys.forEach(function(v) {{
      if (!officeRe.test(v)) {{
        var raw = getWW(wastageData[v].weeks[latestActiveWeek]);
        if (raw.i > 0) activeFridges++;
      }}
    }});
  }}
  var latestWkLabel = latestActiveWeek ? latestActiveWeek.replace(/^\\d{{4}}-/, '') : '—';

  // Summary cards (filter-aware)
  var cardsHtml = '<div class="summary-cards">' +
    '<div class="summary-card"><div class="label">Total Introduced</div><div class="value">' + fmt(gYtdIntro) + '</div></div>' +
    '<div class="summary-card"><div class="label">Total Wasted</div><div class="value red">' + fmt(gYtdWasted) + '</div><div class="sub">' + fmtPct(gYtdPct) + ' waste rate</div></div>' +
    '<div class="summary-card"><div class="label">Waste Cost (COGS)</div><div class="value orange">' + fmtCHF(gYtdCost) + '</div></div>' +
    '<div class="summary-card"><div class="label">Active Fridges</div><div class="value">' + activeFridges + '</div><div class="sub">' + latestWkLabel + ' (excl. office)</div></div>' +
    '</div>';

  // Build table header
  var sa = function(ci) {{ return sortCol === ci ? (sortDir === 'asc' ? '▲' : '▼') : '⇅'; }};
  var headerHtml = '<tr><th onclick="toggleSort(0)">Location <span class="sort-arrow">' + sa(0) + '</span></th>';
  displayWeeks.forEach(function(wk, i) {{
    var colIdx = i + 1;
    var label = wk.replace(/^\\d{{4}}-/, '');
    var dateLabel = getWeekMonday(wk);
    headerHtml += '<th onclick="toggleSort(' + colIdx + ')">' + label + '<span class="week-date">' + dateLabel + '</span><span class="sort-arrow">' + sa(colIdx) + '</span></th>';
  }});
  var ytdColIdx = displayWeeks.length + 1;
  headerHtml += '<th class="ytd-col" onclick="toggleSort(' + ytdColIdx + ')">YTD <span class="sort-arrow">' + sa(ytdColIdx) + '</span></th></tr>';

  // Cell rendering helpers
  function wasteCellHtml(wv) {{
    if (mode !== 'sequential') {{
      if (metric === 'pct') {{
        var cls = deltaClass(wv.deltaPct, true);
        return '<span class="' + cls + '">' + fmtDelta(wv.deltaPct) + '</span>';
      }} else if (metric === 'cost') {{
        var cls = deltaClass(wv.deltaCost, true);
        return '<span class="' + cls + '">' + fmtDeltaCHF(wv.deltaCost) + '</span>';
      }} else {{
        var cls = deltaClass(wv.deltaUnits, true);
        return '<span class="' + cls + '">' + (wv.deltaUnits >= 0 ? '+' : '') + fmt(Math.round(wv.deltaUnits)) + '</span>';
      }}
    }} else {{
      if (metric === 'pct') {{
        var cls = wasteColorClass(wv.pct);
        var barW = Math.min(wv.pct * 2, 100);
        return '<span class="' + cls + '">' + fmtPct(wv.pct) + '</span><span class="waste-bar" style="width:' + barW + 'px;background:' + wasteColor(wv.pct) + '"></span>';
      }} else if (metric === 'cost') {{
        return fmtCHF(wv.cost);
      }} else {{
        return fmt(Math.round(wv.wasted));
      }}
    }}
  }}

  function wasteYtdCellHtml(r) {{
    if (mode === 'yoy') {{
      if (metric === 'pct') {{ var cls = deltaClass(r.ytdDeltaPct, true); return '<span class="' + cls + '">' + fmtDelta(r.ytdDeltaPct) + '</span>'; }}
      if (metric === 'cost') {{ var cls = deltaClass(r.ytdDeltaCost, true); return '<span class="' + cls + '">' + fmtDeltaCHF(r.ytdDeltaCost) + '</span>'; }}
      var cls = deltaClass(r.ytdDeltaUnits, true); return '<span class="' + cls + '">' + (r.ytdDeltaUnits >= 0 ? '+' : '') + fmt(r.ytdDeltaUnits) + '</span>';
    }}
    if (metric === 'pct') {{ var cls = wasteColorClass(r.ytdPct); return '<span class="' + cls + '">' + fmtPct(r.ytdPct) + '</span>'; }}
    if (metric === 'cost') return fmtCHF(r.ytdCost);
    return fmt(r.ytdWasted);
  }}

  var bodyHtml = '';

  // ── Avg / Location row (TOP) ──
  bodyHtml += '<tr class="avg-row"><td><div class="fridge-name">Avg / Location</div><div class="machine-name">' + rows.length + ' active locations</div></td>';
  avgWeekValues.forEach(function(av) {{
    if (mode !== 'sequential') {{
      if (metric === 'pct') {{
        var cls = deltaClass(av.deltaPct, true);
        bodyHtml += '<td class="' + cls + '">' + fmtDelta(av.deltaPct) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
      }} else if (metric === 'cost') {{
        var cls = deltaClass(av.deltaCost, true);
        bodyHtml += '<td class="' + cls + '">' + fmtDeltaCHF(Math.round(av.deltaCost)) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
      }} else {{
        var cls = deltaClass(av.deltaUnits, true);
        bodyHtml += '<td class="' + cls + '">' + (av.deltaUnits >= 0 ? '+' : '') + fmt(Math.round(av.deltaUnits)) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
      }}
    }} else {{
      if (metric === 'pct') {{
        var cls = wasteColorClass(av.pct);
        var barW = Math.min(av.pct * 2, 100);
        bodyHtml += '<td class="' + cls + '">' + fmtPct(av.pct) + '<span class="waste-bar" style="width:' + barW + 'px;background:' + wasteColor(av.pct) + '"></span> <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
      }} else if (metric === 'cost') {{
        bodyHtml += '<td>' + fmtCHF(Math.round(av.cost)) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
      }} else {{
        bodyHtml += '<td>' + fmt(Math.round(av.wasted)) + ' <span style="color:#555;font-size:10px">(' + av.active + ')</span></td>';
      }}
    }}
  }});
  // Avg YTD
  if (mode === 'yoy') {{
    if (metric === 'pct') {{ var cls = deltaClass(gYtdDeltaPct, true); bodyHtml += '<td class="ytd-col ' + cls + '">' + fmtDelta(gYtdDeltaPct) + '</td>'; }}
    else if (metric === 'cost') {{ bodyHtml += '<td class="ytd-col">' + fmtCHF(Math.round(avgYtdCost)) + '</td>'; }}
    else {{ bodyHtml += '<td class="ytd-col">' + fmt(Math.round(avgYtdWasted)) + '</td>'; }}
  }} else {{
    if (metric === 'pct') {{ var cls = wasteColorClass(avgYtdPct); bodyHtml += '<td class="ytd-col ' + cls + '">' + fmtPct(avgYtdPct) + '</td>'; }}
    else if (metric === 'cost') {{ bodyHtml += '<td class="ytd-col">' + fmtCHF(Math.round(avgYtdCost)) + '</td>'; }}
    else {{ bodyHtml += '<td class="ytd-col">' + fmt(Math.round(avgYtdWasted)) + '</td>'; }}
  }}
  bodyHtml += '</tr>';

  // ── Location rows ──
  rows.forEach(function(r) {{
    bodyHtml += '<tr><td><div class="fridge-name">' + r.venue + '</div></td>';
    r.weekValues.forEach(function(wv) {{
      bodyHtml += '<td>' + wasteCellHtml(wv) + '</td>';
    }});
    bodyHtml += '<td class="ytd-col">' + wasteYtdCellHtml(r) + '</td></tr>';
  }});

  // ── Global Total row (BOTTOM) ──
  bodyHtml += '<tr class="global-row"><td><div class="fridge-name">Global Total</div><div class="machine-name">All ' + rows.length + ' locations</div></td>';
  globalWeekValues.forEach(function(gv) {{
    bodyHtml += '<td>' + wasteCellHtml(gv) + '</td>';
  }});
  // Global YTD
  if (mode === 'yoy') {{
    if (metric === 'pct') {{ var cls = deltaClass(gYtdDeltaPct, true); bodyHtml += '<td class="ytd-col ' + cls + '">' + fmtDelta(gYtdDeltaPct) + '</td>'; }}
    else if (metric === 'cost') {{ var cls = deltaClass(gYtdDeltaCost, true); bodyHtml += '<td class="ytd-col ' + cls + '">' + fmtDeltaCHF(gYtdDeltaCost) + '</td>'; }}
    else {{ var cls = deltaClass(gYtdDeltaUnits, true); bodyHtml += '<td class="ytd-col ' + cls + '">' + (gYtdDeltaUnits >= 0 ? '+' : '') + fmt(gYtdDeltaUnits) + '</td>'; }}
  }} else {{
    if (metric === 'pct') {{ var cls = wasteColorClass(gYtdPct); bodyHtml += '<td class="ytd-col ' + cls + '">' + fmtPct(gYtdPct) + '</td>'; }}
    else if (metric === 'cost') {{ bodyHtml += '<td class="ytd-col">' + fmtCHF(gYtdCost) + '</td>'; }}
    else {{ bodyHtml += '<td class="ytd-col">' + fmt(gYtdWasted) + '</td>'; }}
  }}
  bodyHtml += '</tr>';

  document.getElementById('mainContent').innerHTML = cardsHtml +
    '<div class="table-wrap"><table><thead>' + headerHtml + '</thead><tbody>' + bodyHtml + '</tbody></table></div>';

  // Freeze panes: set avg-row sticky top to actual thead height
  requestAnimationFrame(function() {{
    var th = document.querySelector('.table-wrap thead');
    if (th) {{
      var h = th.offsetHeight;
      document.querySelectorAll('.avg-row td').forEach(function(td) {{ td.style.top = h + 'px'; }});
    }}
  }});
}}

render();
</script>
</body>
</html>"""
    return html


# ============================================================
# WRITE FILES
# ============================================================
print("Building client_sales.html...")
sales_html = build_sales_html()
with open("client_sales.html", "w", encoding="utf-8") as f:
    f.write(sales_html)
print(f"  Saved: {len(sales_html):,} bytes")

print("Building client_wastage.html...")
wastage_html = build_wastage_html()
with open("client_wastage.html", "w", encoding="utf-8") as f:
    f.write(wastage_html)
print(f"  Saved: {len(wastage_html):,} bytes")

print("\nDone!")
