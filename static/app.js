// ── i18n ──
const I18N = {
  de: {
    types: { diaper:'Windel', nursing:'Stillen', bottle:'Fläschchen', sleep:'Schlaf', weight:'Gewicht', note:'Notiz' },
    tab_log:'📋 Verlauf', tab_stats:'📊 Auswertung',
    modal_new:'Neuer Eintrag',
    tile_diaper:'Windel', tile_nursing:'Stillen', tile_bottle:'Fläschchen',
    tile_sleep_start:'Eingeschlafen', tile_weight:'Gewicht', tile_note:'Notiz', tile_wakeup:'Aufgewacht',
    fab_title:'Neuer Eintrag',
    lbl_time:'Zeitpunkt', lbl_note:'Notiz', lbl_type:'Art', lbl_amount:'Menge (ml)',
    lbl_content:'Inhalt', lbl_side:'Seite', lbl_start:'Beginn', lbl_end:'Ende', lbl_weight_g:'Gewicht (g)',
    opt_wet:'Nass', opt_dirty:'Schmutzig', opt_both:'Beides',
    opt_left:'Links', opt_right:'Rechts', opt_both_sides:'Beide',
    opt_pumped:'Abgepumpte Milch', opt_formula:'Formulamilch',
    btn_save_sleep:'Eingeschlafen speichern', btn_save:'Speichern',
    banner_since:'Schläft seit', banner_so_far:'Schlaf bisher', banner_wakeup:'☀️ Aufgewacht',
    still_sleeping:'noch schläft',
    no_entries:'Keine Einträge für diesen Tag',
    section_last:'Letztes Ereignis', section_intervals:'Abstände',
    section_sleep:'Schlafdauer (letzte 10)',
    stat_interval:'Abstand', stat_avg:'Ø letzte 5',
    no_data:'Keine Daten', not_enough_data:'Zu wenig Daten', no_sleep_data:'Noch keine Schlafdaten',
    today:'Heute', yesterday:'Gestern',
    just_now:'gerade eben',
    ago_min: n=>`vor ${n} min`, ago_hour: n=>`vor ${n} h`, ago_day: n=>`vor ${n} d`,
    confirm_delete:'Eintrag löschen?',
    toast_no_time:'Bitte Zeitpunkt angeben', toast_deleted:'Gelöscht',
    toast_error:'Fehler beim Speichern', toast_saved:'✓ Gespeichert',
    toast_wakeup: dur=>`☀️ Aufgewacht – ${dur} Schlaf`,
    lang_switch:'EN',
  },
  en: {
    types: { diaper:'Diaper', nursing:'Nursing', bottle:'Bottle', sleep:'Sleep', weight:'Weight', note:'Note' },
    tab_log:'📋 Log', tab_stats:'📊 Stats',
    modal_new:'New Entry',
    tile_diaper:'Diaper', tile_nursing:'Nursing', tile_bottle:'Bottle',
    tile_sleep_start:'Fell asleep', tile_weight:'Weight', tile_note:'Note', tile_wakeup:'Woke up',
    fab_title:'New Entry',
    lbl_time:'Time', lbl_note:'Note', lbl_type:'Type', lbl_amount:'Amount (ml)',
    lbl_content:'Content', lbl_side:'Side', lbl_start:'Start', lbl_end:'End', lbl_weight_g:'Weight (g)',
    opt_wet:'Wet', opt_dirty:'Dirty', opt_both:'Both',
    opt_left:'Left', opt_right:'Right', opt_both_sides:'Both',
    opt_pumped:'Pumped milk', opt_formula:'Formula',
    btn_save_sleep:'Save fell asleep', btn_save:'Save',
    banner_since:'Sleeping since', banner_so_far:'sleep so far', banner_wakeup:'☀️ Woke up',
    still_sleeping:'still sleeping',
    no_entries:'No entries for this day',
    section_last:'Last event', section_intervals:'Intervals',
    section_sleep:'Sleep duration (last 10)',
    stat_interval:'Interval', stat_avg:'avg last 5',
    no_data:'No data', not_enough_data:'Not enough data', no_sleep_data:'No sleep data yet',
    today:'Today', yesterday:'Yesterday',
    just_now:'just now',
    ago_min: n=>`${n} min ago`, ago_hour: n=>`${n} h ago`, ago_day: n=>`${n} d ago`,
    confirm_delete:'Delete entry?',
    toast_no_time:'Please enter a time', toast_deleted:'Deleted',
    toast_error:'Error saving', toast_saved:'✓ Saved',
    toast_wakeup: dur=>`☀️ Woke up – ${dur} sleep`,
    lang_switch:'DE',
  },
};

// stored meta values → translated display (both old German keys and neutral keys)
const META_VALS = {
  nass:{de:'Nass',en:'Wet'}, schmutzig:{de:'Schmutzig',en:'Dirty'}, beides:{de:'Beides',en:'Both'},
  wet:{de:'Nass',en:'Wet'}, dirty:{de:'Schmutzig',en:'Dirty'}, both:{de:'Beides',en:'Both'},
  links:{de:'Links',en:'Left'}, rechts:{de:'Rechts',en:'Right'}, beide:{de:'Beide',en:'Both'},
  left:{de:'Links',en:'Left'}, right:{de:'Rechts',en:'Right'},
  abgepumpt:{de:'Abgepumpt',en:'Pumped'}, formula:{de:'Formula',en:'Formula'},
};

const TYPE_ICONS = { diaper:'🧷', nursing:'🤱', bottle:'🍼', sleep:'😴', weight:'⚖️', note:'📝' };

let lang = localStorage.getItem('lang') || (navigator.language.startsWith('de') ? 'de' : 'en');

function t(key, arg) {
  const val = I18N[lang][key];
  return typeof val === 'function' ? val(arg) : (val ?? key);
}
function tMeta(val) { return (META_VALS[val] && META_VALS[val][lang]) || val; }
function getType(key) { return { label: (I18N[lang].types[key] || key), icon: TYPE_ICONS[key] || '❓' }; }

function switchLang() {
  lang = lang === 'de' ? 'en' : 'de';
  localStorage.setItem('lang', lang);
  initUI();
  loadLog();
  if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
}

function initUI() {
  document.getElementById('html-root').lang = lang;
  document.getElementById('lang-btn').textContent = t('lang_switch');
  document.getElementById('tab-btn-log').textContent = t('tab_log');
  document.getElementById('tab-btn-stats').textContent = t('tab_stats');
  document.getElementById('fab').title = t('fab_title');
  ['diaper','nursing','bottle','sleep_start','weight','note'].forEach(k => {
    const el = document.getElementById('tile-'+k);
    if (el) el.querySelector('.t-label').textContent = t('tile_'+k);
  });
}

const IP_COLORS = [
  '#c8602a','#3a7d6b','#5b4fa8','#b04040','#2e6fa8',
  '#8a6a1f','#4a7a2e','#8a2e6a','#2e6a8a','#6a3a2e',
];

let ipColorMap = {};
let colorIndex = 0;
let currentDate = todayStr();
let openSleepEntry = null;
let selectedType = null;
let currentEntries = [];
let editEntryId = null;

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
  if (s === today) return t('today');
  if (s === yesterday) return t('yesterday');
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
  if (diff < 1) return t('just_now');
  if (diff < 60) return t('ago_min', Math.round(diff));
  if (diff < 1440) return t('ago_hour', Math.round(diff/60));
  return t('ago_day', Math.round(diff/1440));
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
function openDatePicker() {
  const el = document.getElementById('date-picker');
  if (el.showPicker) el.showPicker();
  else el.focus();
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
        <div class="sl-label">${t('banner_since')} ${since}</div>
        <div class="sl-since">${fmtDur(dur)} ${t('banner_so_far')}</div>
      </div>
      <button class="wake-btn" onclick="wakeUp()">${t('banner_wakeup')}</button>
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
  toast(t('toast_wakeup', fmtDur(dur)));
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
  currentEntries = entries;

  const todayIps = [...new Set(entries.map(e => e.ip))];
  const legend = document.getElementById('ip-legend');
  legend.innerHTML = todayIps.map(ip => `
    <div class="ip-legend-item">
      <div class="ip-dot" style="background:${getIpColor(ip)}"></div>${ip}
    </div>
  `).join('');

  const list = document.getElementById('entry-list');
  if (!entries.length) {
    list.innerHTML = `<div class="empty">${t('no_entries')}</div>`;
    return;
  }

  list.innerHTML = entries.map(e => {
    const color = getIpColor(e.ip);
    const tp = getType(e.type);
    const m = e.meta || {};
    let timeStr = fmtTime(e.ts_start);
    let metaStr = '';

    if (e.type === 'sleep') {
      if (e.ts_end) {
        const dur = Math.round(durMin(e.ts_start, e.ts_end));
        timeStr = `${fmtTime(e.ts_start)} – ${fmtTime(e.ts_end)}`;
        metaStr = fmtDur(dur);
      } else {
        timeStr = `${fmtTime(e.ts_start)} – ${t('still_sleeping')}`;
      }
    }
    if (e.type === 'diaper' && m.diaper_type) metaStr = tMeta(m.diaper_type);
    if (e.type === 'nursing') {
      if (e.ts_end) timeStr = `${fmtTime(e.ts_start)} – ${fmtTime(e.ts_end)}`;
      if (m.side) metaStr = tMeta(m.side);
    }
    if (e.type === 'bottle' && m.amount) metaStr = `${m.amount} ml`;
    if (e.type === 'weight' && m.weight) metaStr = `${m.weight} g`;

    return `
      <div class="entry-item" style="border-left-color:${color}" onclick="openEditModal(${e.id})">
        <div class="entry-icon">${tp.icon}</div>
        <div class="entry-body">
          <div class="entry-type">${tp.label}</div>
          <div class="entry-time">${timeStr}</div>
          ${metaStr ? `<div class="entry-meta">${esc(metaStr)}</div>` : ''}
          ${e.note ? `<div class="entry-note">${esc(e.note)}</div>` : ''}
        </div>
        <span class="ip-badge" style="background:${color}" title="${e.ip}">${shortIp(e.ip)}</span>
        <button class="del-btn" onclick="event.stopPropagation(); deleteEntry(${e.id})" title="${t('confirm_delete')}">✕</button>
      </div>
    `;
  }).join('');
}

async function deleteEntry(id) {
  if (!confirm(t('confirm_delete'))) return;
  await fetch('/api/entries/'+id, { method: 'DELETE' });
  toast(t('toast_deleted'));
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
    const tp = getType(key);
    let valStr = fmtAgo(e.ts_start);
    let sub = fmtTime(e.ts_start);
    if (key === 'sleep' && e.ts_end) sub += ` (${fmtDur(Math.round(durMin(e.ts_start, e.ts_end)))})`;
    if (key === 'weight' && e.meta?.weight) { valStr = e.meta.weight + ' g'; sub = fmtAgo(e.ts_start); }
    lastCards += `
      <div class="stat-card">
        <div class="s-label">${tp.icon} ${tp.label}</div>
        <div class="s-val" style="font-size:1rem;padding-top:2px">${valStr}</div>
        <div class="s-sub">${sub}</div>
      </div>`;
  });

  let ivCards = '';
  ['diaper','nursing','bottle'].forEach(key => {
    const iv = data.intervals[key];
    if (!iv) return;
    const tp = getType(key);
    ivCards += `
      <div class="stat-card">
        <div class="s-label">${tp.icon} ${tp.label} · ${t('stat_interval')}</div>
        <div class="s-val">${fmtDur(iv.last)}</div>
        <div class="s-sub">${t('stat_avg')}: ${fmtDur(iv.avg)}</div>
      </div>`;
  });

  let sleepBars = `<div class="empty">${t('no_sleep_data')}</div>`;
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
    <div class="section-title">${t('section_last')}</div>
    <div class="stats-grid">${lastCards||`<div class="empty">${t('no_data')}</div>`}</div>
    <div class="section-title">${t('section_intervals')}</div>
    <div class="stats-grid">${ivCards||`<div class="empty">${t('not_enough_data')}</div>`}</div>
    <div class="section-title">${t('section_sleep')}</div>
    ${sleepBars}
  `;
}

// ── Modal ──
function openModal() {
  editEntryId = null;
  selectedType = null;
  document.querySelectorAll('.type-tile').forEach(tp => tp.classList.remove('selected'));
  document.getElementById('form-fields').innerHTML = '';
  document.getElementById('form-fields').classList.remove('visible');
  document.getElementById('modal-title').textContent = t('modal_new');

  const grid = document.getElementById('type-grid');
  grid.style.display = '';
  document.getElementById('tile-sleep_start').style.display = openSleepEntry ? 'none' : '';
  const existing = grid.querySelector('[data-type=sleep_end]');
  if (openSleepEntry && !existing) {
    const tile = document.createElement('div');
    tile.className = 'type-tile';
    tile.dataset.type = 'sleep_end';
    tile.innerHTML = `<div class="t-icon">☀️</div><div class="t-label">${t('tile_wakeup')}</div>`;
    tile.onclick = () => wakeUpFromModal();
    grid.appendChild(tile);
  } else if (!openSleepEntry && existing) {
    existing.remove();
  } else if (openSleepEntry && existing) {
    existing.querySelector('.t-label').textContent = t('tile_wakeup');
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
  document.querySelectorAll('.type-tile').forEach(tp => tp.classList.remove('selected'));
  const found = [...document.querySelectorAll('.type-tile')].find(tp =>
    tp.onclick?.toString().includes(`'${type}'`) || tp.dataset.type === type
  );
  if (found) found.classList.add('selected');

  const now = nowLocal();
  const fields = document.getElementById('form-fields');
  fields.classList.add('visible');

  if (type === 'sleep_start') {
    document.getElementById('modal-title').textContent = `😴 ${t('tile_sleep_start')}`;
    fields.innerHTML = `
      <div class="field"><label>${t('lbl_time')}</label><input type="datetime-local" id="f-start" value="${now}"></div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save_sleep')}</button>
    `;
  } else if (type === 'diaper') {
    document.getElementById('modal-title').textContent = `🧷 ${t('tile_diaper')}`;
    fields.innerHTML = `
      <div class="fields-row">
        <div class="field"><label>${t('lbl_time')}</label><input type="datetime-local" id="f-start" value="${now}"></div>
        <div class="field"><label>${t('lbl_type')}</label>
          <select id="f-diaper-type">
            <option value="nass">${t('opt_wet')}</option>
            <option value="schmutzig">${t('opt_dirty')}</option>
            <option value="beides">${t('opt_both')}</option>
          </select>
        </div>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'nursing') {
    document.getElementById('modal-title').textContent = `🤱 ${t('tile_nursing')}`;
    fields.innerHTML = `
      <div class="fields-row">
        <div class="field"><label>${t('lbl_start')}</label><input type="datetime-local" id="f-start" value="${now}"></div>
        <div class="field"><label>${t('lbl_end')}</label><input type="datetime-local" id="f-end"></div>
      </div>
      <div class="field"><label>${t('lbl_side')}</label>
        <select id="f-side">
          <option value="">—</option>
          <option value="links">${t('opt_left')}</option>
          <option value="rechts">${t('opt_right')}</option>
          <option value="beide">${t('opt_both_sides')}</option>
        </select>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'bottle') {
    document.getElementById('modal-title').textContent = `🍼 ${t('tile_bottle')}`;
    fields.innerHTML = `
      <div class="fields-row">
        <div class="field"><label>${t('lbl_time')}</label><input type="datetime-local" id="f-start" value="${now}"></div>
        <div class="field"><label>${t('lbl_amount')}</label><input type="number" id="f-amount" min="0" step="5" placeholder="120"></div>
      </div>
      <div class="field"><label>${t('lbl_content')}</label>
        <select id="f-content">
          <option value="abgepumpt">${t('opt_pumped')}</option>
          <option value="formula">${t('opt_formula')}</option>
        </select>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'weight') {
    document.getElementById('modal-title').textContent = `⚖️ ${t('tile_weight')}`;
    fields.innerHTML = `
      <div class="fields-row">
        <div class="field"><label>${t('lbl_time')}</label><input type="datetime-local" id="f-start" value="${now}"></div>
        <div class="field"><label>${t('lbl_weight_g')}</label><input type="number" id="f-weight" min="0" step="10" placeholder="3450"></div>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else {
    document.getElementById('modal-title').textContent = `📝 ${t('tile_note')}`;
    fields.innerHTML = `
      <div class="field"><label>${t('lbl_time')}</label><input type="datetime-local" id="f-start" value="${now}"></div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="3"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  }
}

async function submitEntry() {
  const start = document.getElementById('f-start')?.value;
  if (!start) { toast(t('toast_no_time')); return; }
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
    toast(t('toast_saved'));
    const entryDate = start.slice(0,10);
    if (entryDate !== currentDate) { currentDate = entryDate; updateDayNav(); }
    loadLog();
  } else {
    toast(t('toast_error'));
  }
}

// ── Edit existing entry ──
function openEditModal(id) {
  const entry = currentEntries.find(e => e.id === id);
  if (!entry) return;
  editEntryId = id;
  selectedType = null;
  document.querySelectorAll('.type-tile').forEach(tp => tp.classList.remove('selected'));
  document.getElementById('type-grid').style.display = 'none';
  const tp = getType(entry.type);
  document.getElementById('modal-title').textContent = `${tp.icon} ${tp.label}`;
  const fields = document.getElementById('form-fields');
  fields.classList.add('visible');
  fields.innerHTML = editFieldsHtml(entry);
  document.getElementById('modal-overlay').classList.add('open');
}

function editFieldsHtml(entry) {
  const m = entry.meta || {};
  const start = entry.ts_start ? entry.ts_start.slice(0, 16) : '';
  const end = entry.ts_end ? entry.ts_end.slice(0, 16) : '';
  const note = esc(entry.note || '');

  if (entry.type === 'diaper') {
    return `
      <div class="fields-row">
        <div class="field"><label>${t('lbl_time')}</label><input type="datetime-local" id="f-start" value="${start}"></div>
        <div class="field"><label>${t('lbl_type')}</label>
          <select id="f-diaper-type">
            <option value="nass" ${m.diaper_type === 'nass' ? 'selected' : ''}>${t('opt_wet')}</option>
            <option value="schmutzig" ${m.diaper_type === 'schmutzig' ? 'selected' : ''}>${t('opt_dirty')}</option>
            <option value="beides" ${m.diaper_type === 'beides' ? 'selected' : ''}>${t('opt_both')}</option>
          </select>
        </div>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2">${note}</textarea></div>
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'nursing') {
    return `
      <div class="fields-row">
        <div class="field"><label>${t('lbl_start')}</label><input type="datetime-local" id="f-start" value="${start}"></div>
        <div class="field"><label>${t('lbl_end')}</label><input type="datetime-local" id="f-end" value="${end}"></div>
      </div>
      <div class="field"><label>${t('lbl_side')}</label>
        <select id="f-side">
          <option value="">—</option>
          <option value="links" ${m.side === 'links' ? 'selected' : ''}>${t('opt_left')}</option>
          <option value="rechts" ${m.side === 'rechts' ? 'selected' : ''}>${t('opt_right')}</option>
          <option value="beide" ${m.side === 'beide' ? 'selected' : ''}>${t('opt_both_sides')}</option>
        </select>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2">${note}</textarea></div>
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'bottle') {
    return `
      <div class="fields-row">
        <div class="field"><label>${t('lbl_time')}</label><input type="datetime-local" id="f-start" value="${start}"></div>
        <div class="field"><label>${t('lbl_amount')}</label><input type="number" id="f-amount" min="0" step="5" value="${m.amount || ''}"></div>
      </div>
      <div class="field"><label>${t('lbl_content')}</label>
        <select id="f-content">
          <option value="abgepumpt" ${m.content === 'abgepumpt' ? 'selected' : ''}>${t('opt_pumped')}</option>
          <option value="formula" ${m.content === 'formula' ? 'selected' : ''}>${t('opt_formula')}</option>
        </select>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2">${note}</textarea></div>
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'sleep') {
    return `
      <div class="fields-row">
        <div class="field"><label>${t('lbl_start')}</label><input type="datetime-local" id="f-start" value="${start}"></div>
        <div class="field"><label>${t('lbl_end')}</label><input type="datetime-local" id="f-end" value="${end}"></div>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2">${note}</textarea></div>
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'weight') {
    return `
      <div class="fields-row">
        <div class="field"><label>${t('lbl_time')}</label><input type="datetime-local" id="f-start" value="${start}"></div>
        <div class="field"><label>${t('lbl_weight_g')}</label><input type="number" id="f-weight" min="0" step="10" value="${m.weight || ''}"></div>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2">${note}</textarea></div>
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  return `
    <div class="field"><label>${t('lbl_time')}</label><input type="datetime-local" id="f-start" value="${start}"></div>
    <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="3">${note}</textarea></div>
    <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
  `;
}

async function submitEditEntry() {
  const start = document.getElementById('f-start')?.value;
  if (!start) { toast(t('toast_no_time')); return; }
  const entry = currentEntries.find(e => e.id === editEntryId);
  if (!entry) return;

  const meta = {};
  if (entry.type === 'diaper') meta.diaper_type = document.getElementById('f-diaper-type')?.value;
  if (entry.type === 'nursing') meta.side = document.getElementById('f-side')?.value;
  if (entry.type === 'bottle') {
    meta.amount = document.getElementById('f-amount')?.value;
    meta.content = document.getElementById('f-content')?.value;
  }
  if (entry.type === 'weight') meta.weight = document.getElementById('f-weight')?.value;

  const body = {
    ts_start: start,
    ts_end: document.getElementById('f-end')?.value || null,
    note: document.getElementById('f-note')?.value || '',
    meta,
  };

  const res = await fetch(`/api/entries/${editEntryId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (res.ok) {
    closeModal();
    toast(t('toast_saved'));
    const entryDate = start.slice(0, 10);
    if (entryDate !== currentDate) { currentDate = entryDate; updateDayNav(); }
    loadLog();
  } else {
    toast(t('toast_error'));
  }
}

// ── Toast ──
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2200);
}

// ── Live sync (SSE) ──
function initEvents() {
  const es = new EventSource('/api/events');
  es.onmessage = () => {
    loadLog();
    if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
  };
  es.onerror = () => {};
}

// ── Init ──
initUI();
updateDayNav();
loadLog();
initEvents();
