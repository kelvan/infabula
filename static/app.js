const TYPES = {
  diaper:      { label: 'Windel', icon: '🧷' },
  nursing:     { label: 'Stillen', icon: '🤱' },
  bottle:      { label: 'Fläschchen', icon: '🍼' },
  sleep:       { label: 'Schlaf', icon: '😴' },
  weight:      { label: 'Gewicht', icon: '⚖️' },
  note:        { label: 'Notiz', icon: '📝' },
};

const IP_COLORS = [
  '#c8602a','#3a7d6b','#5b4fa8','#b04040','#2e6fa8',
  '#8a6a1f','#4a7a2e','#8a2e6a','#2e6a8a','#6a3a2e',
];

let ipColorMap = {};
let colorIndex = 0;
let currentDate = todayStr();
let openSleepEntry = null;
let selectedType = null;

// ── Date helpers ──
function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
}
function pad(n) { return String(n).padStart(2,'0'); }
function nowLocal() {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function fmtDate(s) {
  const [y,m,d] = s.split('-');
  const today = todayStr();
  const yesterday = (() => { const dt = new Date(); dt.setDate(dt.getDate()-1); return `${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())}`; })();
  if (s === today) return 'Heute';
  if (s === yesterday) return 'Gestern';
  return `${d}.${m}.${y}`;
}
function fmtTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function fmtDur(min) {
  if (!min && min !== 0) return '—';
  const h = Math.floor(min/60), m = Math.round(min%60);
  return h === 0 ? `${m} min` : `${h}h ${m}m`;
}
function durMin(a, b) { return Math.abs((new Date(b)-new Date(a))/60000); }
function fmtAgo(iso) {
  const diff = (Date.now()-new Date(iso))/60000;
  if (diff < 1) return 'gerade eben';
  if (diff < 60) return `vor ${Math.round(diff)} min`;
  if (diff < 1440) return `vor ${Math.round(diff/60)} h`;
  return `vor ${Math.round(diff/1440)} d`;
}
function getIpColor(ip) {
  if (!ipColorMap[ip]) { ipColorMap[ip] = IP_COLORS[colorIndex % IP_COLORS.length]; colorIndex++; }
  return ipColorMap[ip];
}
function shortIp(ip) {
  if (!ip) return '?';
  const p = ip.split('.');
  return p.length === 4 ? p.slice(2).join('.') : ip.slice(-5);
}
function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ── Day navigation ──
function updateDayNav() {
  document.getElementById('day-label').textContent = fmtDate(currentDate);
  document.getElementById('date-picker').value = currentDate;
  document.getElementById('btn-next').disabled = currentDate >= todayStr();
}
function changeDay(delta) {
  const d = new Date(currentDate);
  d.setDate(d.getDate() + delta);
  currentDate = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
  updateDayNav();
  loadLog();
}
function jumpToDate(val) {
  if (!val) return;
  currentDate = val;
  updateDayNav();
  loadLog();
}

// ── Tab switching ──
function switchTab(name, btn) {
  document.querySelectorAll('.tab-page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  btn.classList.add('active');
  if (name === 'stats') loadStats();
}

// ── Sleep banner ──
async function checkOpenSleep() {
  const res = await fetch('/api/sleep/open');
  openSleepEntry = res.ok ? await res.json() : null;
  renderSleepBanner();
}
function renderSleepBanner() {
  const wrap = document.getElementById('sleep-banner-wrap');
  if (!openSleepEntry) { wrap.innerHTML = ''; return; }
  const since = fmtTime(openSleepEntry.ts_start);
  const dur = Math.round(durMin(openSleepEntry.ts_start, new Date().toISOString()));
  wrap.innerHTML = `
    <div class="sleep-banner">
      <div class="sl-icon">😴</div>
      <div class="sl-info">
        <div class="sl-label">Schläft seit ${since}</div>
        <div class="sl-since">${fmtDur(dur)} Schlaf bisher</div>
      </div>
      <button class="wake-btn" onclick="wakeUp()">☀️ Aufgewacht</button>
    </div>
  `;
  setTimeout(renderSleepBanner, 60000);
}
async function wakeUp() {
  if (!openSleepEntry) return;
  const now = nowLocal();
  await fetch(`/api/entries/${openSleepEntry.id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ts_end: now })
  });
  const dur = Math.round(durMin(openSleepEntry.ts_start, now));
  toast(`☀️ Aufgewacht – ${fmtDur(dur)} Schlaf`);
  openSleepEntry = null;
  document.getElementById('sleep-banner-wrap').innerHTML = '';
  loadLog();
}

// ── Log ──
async function loadLog() {
  await checkOpenSleep();
  const allRes = await fetch('/api/entries?limit=500');
  const allEntries = await allRes.json();
  ipColorMap = {}; colorIndex = 0;
  allEntries.forEach(e => getIpColor(e.ip));

  const res = await fetch(`/api/entries?date=${currentDate}`);
  const entries = await res.json();

  const todayIps = [...new Set(entries.map(e => e.ip))];
  const legend = document.getElementById('ip-legend');
  legend.innerHTML = todayIps.map(ip => `
    <div class="ip-legend-item">
      <div class="ip-dot" style="background:${getIpColor(ip)}"></div>${ip}
    </div>
  `).join('');

  const list = document.getElementById('entry-list');
  if (!entries.length) {
    list.innerHTML = '<div class="empty">Keine Einträge für diesen Tag</div>';
    return;
  }

  list.innerHTML = entries.map(e => {
    const color = getIpColor(e.ip);
    const t = TYPES[e.type] || { label: e.type, icon: '❓' };
    const m = e.meta || {};
    let timeStr = fmtTime(e.ts_start);
    let metaStr = '';

    if (e.type === 'sleep') {
      if (e.ts_end) {
        const dur = Math.round(durMin(e.ts_start, e.ts_end));
        timeStr = `${fmtTime(e.ts_start)} – ${fmtTime(e.ts_end)}`;
        metaStr = fmtDur(dur);
      } else {
        timeStr = `${fmtTime(e.ts_start)} – noch schläft`;
      }
    }
    if (e.type === 'diaper' && m.diaper_type) metaStr = m.diaper_type;
    if (e.type === 'nursing') {
      if (e.ts_end) timeStr = `${fmtTime(e.ts_start)} – ${fmtTime(e.ts_end)}`;
      if (m.side) metaStr = m.side;
    }
    if (e.type === 'bottle' && m.amount) metaStr = `${m.amount} ml`;
    if (e.type === 'weight' && m.weight) metaStr = `${m.weight} g`;

    return `
      <div class="entry-item" style="border-left-color:${color}">
        <div class="entry-icon">${t.icon}</div>
        <div class="entry-body">
          <div class="entry-type">${t.label}</div>
          <div class="entry-time">${timeStr}</div>
          ${metaStr ? `<div class="entry-meta">${esc(metaStr)}</div>` : ''}
          ${e.note ? `<div class="entry-note">${esc(e.note)}</div>` : ''}
        </div>
        <span class="ip-badge" style="background:${color}" title="${e.ip}">${shortIp(e.ip)}</span>
        <button class="del-btn" onclick="deleteEntry(${e.id})" title="Löschen">✕</button>
      </div>
    `;
  }).join('');
}

async function deleteEntry(id) {
  if (!confirm('Eintrag löschen?')) return;
  await fetch('/api/entries/'+id, { method: 'DELETE' });
  toast('Gelöscht');
  loadLog();
}

// ── Stats ──
async function loadStats() {
  const res = await fetch('/api/stats');
  const data = await res.json();
  const el = document.getElementById('stats-content');

  const lastTypes = ['diaper','nursing','bottle','sleep','weight'];
  let lastCards = '';
  lastTypes.forEach(key => {
    const e = data.last[key];
    if (!e) return;
    const t = TYPES[key] || { label: key, icon: '❓' };
    let valStr = fmtAgo(e.ts_start);
    let sub = fmtTime(e.ts_start);
    if (key === 'sleep' && e.ts_end) sub += ` (${fmtDur(Math.round(durMin(e.ts_start, e.ts_end)))})`;
    if (key === 'weight' && e.meta?.weight) { valStr = e.meta.weight + ' g'; sub = fmtAgo(e.ts_start); }
    lastCards += `
      <div class="stat-card">
        <div class="s-label">${t.icon} ${t.label}</div>
        <div class="s-val" style="font-size:1rem;padding-top:2px">${valStr}</div>
        <div class="s-sub">${sub}</div>
      </div>`;
  });

  const intTypes = [
    {key:'diaper', icon:'🧷', label:'Windel'},
    {key:'nursing', icon:'🤱', label:'Stillen'},
    {key:'bottle', icon:'🍼', label:'Fläschchen'},
  ];
  let ivCards = '';
  intTypes.forEach(({key,icon,label}) => {
    const iv = data.intervals[key];
    if (!iv) return;
    ivCards += `
      <div class="stat-card">
        <div class="s-label">${icon} ${label} · Abstand</div>
        <div class="s-val">${fmtDur(iv.last)}</div>
        <div class="s-sub">Ø letzte 5: ${fmtDur(iv.avg)}</div>
      </div>`;
  });

  let sleepBars = '<div class="empty">Noch keine Schlafdaten</div>';
  if (data.sleep_durations.length) {
    const max = Math.max(...data.sleep_durations.map(s => s.minutes));
    sleepBars = data.sleep_durations.map(s => `
      <div class="sleep-row">
        <span class="sleep-time">${fmtTime(s.start)}&thinsp;–&thinsp;${fmtTime(s.end)}</span>
        <div class="sleep-bar-bg"><div class="sleep-bar" style="width:${Math.round(s.minutes/max*100)}%"></div></div>
        <span class="sleep-dur">${fmtDur(s.minutes)}</span>
      </div>`).join('');
  }

  el.innerHTML = `
    <div class="section-title">Letztes Ereignis</div>
    <div class="stats-grid">${lastCards||'<div class="empty">Keine Daten</div>'}</div>
    <div class="section-title">Abstände</div>
    <div class="stats-grid">${ivCards||'<div class="empty">Zu wenig Daten</div>'}</div>
    <div class="section-title">Schlafdauer (letzte 10)</div>
    ${sleepBars}
  `;
}

// ── Modal ──
function openModal() {
  selectedType = null;
  document.querySelectorAll('.type-tile').forEach(t => t.classList.remove('selected'));
  document.getElementById('form-fields').innerHTML = '';
  document.getElementById('form-fields').classList.remove('visible');
  document.getElementById('modal-title').textContent = 'Neuer Eintrag';

  const grid = document.getElementById('type-grid');
  const existing = grid.querySelector('[data-type=sleep_end]');
  if (openSleepEntry && !existing) {
    const tile = document.createElement('div');
    tile.className = 'type-tile';
    tile.dataset.type = 'sleep_end';
    tile.innerHTML = '<div class="t-icon">☀️</div><div class="t-label">Aufgewacht</div>';
    tile.onclick = () => wakeUpFromModal();
    grid.appendChild(tile);
  } else if (!openSleepEntry && existing) {
    existing.remove();
  }

  document.getElementById('modal-overlay').classList.add('open');
}
function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
}
function overlayClick(e) {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
}

function wakeUpFromModal() {
  closeModal();
  wakeUp();
}

function selectType(type) {
  selectedType = type;
  document.querySelectorAll('.type-tile').forEach(t => t.classList.remove('selected'));
  const found = [...document.querySelectorAll('.type-tile')].find(t =>
    t.onclick?.toString().includes(`'${type}'`) || t.dataset.type === type
  );
  if (found) found.classList.add('selected');

  const now = nowLocal();
  const fields = document.getElementById('form-fields');
  fields.classList.add('visible');

  if (type === 'sleep_start') {
    document.getElementById('modal-title').textContent = '😴 Eingeschlafen';
    fields.innerHTML = `
      <div class="field"><label>Zeitpunkt</label><input type="datetime-local" id="f-start" value="${now}"></div>
      <div class="field"><label>Notiz</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">Eingeschlafen speichern</button>
    `;
  } else if (type === 'diaper') {
    document.getElementById('modal-title').textContent = '🧷 Windel';
    fields.innerHTML = `
      <div class="fields-row">
        <div class="field"><label>Zeitpunkt</label><input type="datetime-local" id="f-start" value="${now}"></div>
        <div class="field"><label>Art</label>
          <select id="f-diaper-type">
            <option value="nass">Nass</option>
            <option value="schmutzig">Schmutzig</option>
            <option value="beides">Beides</option>
          </select>
        </div>
      </div>
      <div class="field"><label>Notiz</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">Speichern</button>
    `;
  } else if (type === 'nursing') {
    document.getElementById('modal-title').textContent = '🤱 Stillen';
    fields.innerHTML = `
      <div class="fields-row">
        <div class="field"><label>Beginn</label><input type="datetime-local" id="f-start" value="${now}"></div>
        <div class="field"><label>Ende</label><input type="datetime-local" id="f-end"></div>
      </div>
      <div class="field"><label>Seite</label>
        <select id="f-side">
          <option value="">—</option>
          <option value="links">Links</option>
          <option value="rechts">Rechts</option>
          <option value="beide">Beide</option>
        </select>
      </div>
      <div class="field"><label>Notiz</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">Speichern</button>
    `;
  } else if (type === 'bottle') {
    document.getElementById('modal-title').textContent = '🍼 Fläschchen';
    fields.innerHTML = `
      <div class="fields-row">
        <div class="field"><label>Zeitpunkt</label><input type="datetime-local" id="f-start" value="${now}"></div>
        <div class="field"><label>Menge (ml)</label><input type="number" id="f-amount" min="0" step="5" placeholder="120"></div>
      </div>
      <div class="field"><label>Inhalt</label>
        <select id="f-content">
          <option value="abgepumpt">Abgepumpte Milch</option>
          <option value="formula">Formulamilch</option>
        </select>
      </div>
      <div class="field"><label>Notiz</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">Speichern</button>
    `;
  } else if (type === 'weight') {
    document.getElementById('modal-title').textContent = '⚖️ Gewicht';
    fields.innerHTML = `
      <div class="fields-row">
        <div class="field"><label>Zeitpunkt</label><input type="datetime-local" id="f-start" value="${now}"></div>
        <div class="field"><label>Gewicht (g)</label><input type="number" id="f-weight" min="0" step="10" placeholder="3450"></div>
      </div>
      <div class="field"><label>Notiz</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">Speichern</button>
    `;
  } else {
    document.getElementById('modal-title').textContent = '📝 Notiz';
    fields.innerHTML = `
      <div class="field"><label>Zeitpunkt</label><input type="datetime-local" id="f-start" value="${now}"></div>
      <div class="field"><label>Notiz</label><textarea id="f-note" rows="3"></textarea></div>
      <button class="btn" onclick="submitEntry()">Speichern</button>
    `;
  }
}

async function submitEntry() {
  const start = document.getElementById('f-start')?.value;
  if (!start) { toast('Bitte Zeitpunkt angeben'); return; }
  const meta = {};
  if (selectedType === 'diaper') meta.diaper_type = document.getElementById('f-diaper-type')?.value;
  if (selectedType === 'nursing') meta.side = document.getElementById('f-side')?.value;
  if (selectedType === 'bottle') {
    meta.amount = document.getElementById('f-amount')?.value;
    meta.content = document.getElementById('f-content')?.value;
  }
  if (selectedType === 'weight') meta.weight = document.getElementById('f-weight')?.value;

  const apiType = selectedType === 'sleep_start' ? 'sleep' : selectedType;

  const body = {
    type: apiType,
    ts_start: start,
    ts_end: document.getElementById('f-end')?.value || null,
    note: document.getElementById('f-note')?.value || '',
    meta,
  };

  const res = await fetch('/api/entries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (res.ok) {
    const saved = await res.json();
    if (apiType === 'sleep' && !saved.ts_end) {
      openSleepEntry = saved;
    }
    closeModal();
    toast('✓ Gespeichert');
    const entryDate = start.slice(0,10);
    if (entryDate !== currentDate) { currentDate = entryDate; updateDayNav(); }
    loadLog();
  } else {
    toast('Fehler beim Speichern');
  }
}

// ── Toast ──
function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

// ── Init ──
updateDayNav();
loadLog();
