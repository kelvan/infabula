// ── i18n ──
const I18N = {
  de: {
    types: { diaper:'Windel', nursing:'Stillen', bottle:'Fläschchen', sleep:'Schlaf', weight:'Gewicht', note:'Notiz', walk:'Spaziergang', clothing:'Kleidung', feeding:'Fütterung' },
    tab_log:'Verlauf', tab_stats:'Auswertung', tab_settings:'Einstellungen',
    modal_new:'Neuer Eintrag',
    tile_diaper:'Windel', tile_nursing:'Stillen', tile_bottle:'Fläschchen',
    tile_sleep_start:'Eingeschlafen', tile_weight:'Gewicht', tile_note:'Notiz', tile_wakeup:'Aufgewacht',
    tile_walk:'Spaziergang', tile_clothing:'Kleidung wechseln', tile_walk_end:'Zurück',
    fab_title:'Neuer Eintrag',
    lbl_time:'Zeitpunkt', lbl_note:'Notiz', lbl_type:'Art', lbl_amount:'Menge (ml)',
    lbl_content:'Inhalt', lbl_side:'Seite', lbl_start:'Beginn', lbl_end:'Ende', lbl_weight_g:'Gewicht (g)',
    opt_wet:'Nass', opt_dirty:'Schmutzig', opt_both:'Beides',
    opt_left:'Links', opt_right:'Rechts', opt_both_sides:'Beide',
    opt_pumped:'Abgepumpte Milch', opt_formula:'Formulamilch',
    btn_save_sleep:'Eingeschlafen speichern', btn_save:'Speichern',
    banner_since:'Schläft seit', banner_so_far:'Schlaf bisher', banner_wakeup:'Aufgewacht',
    banner_walk_since:'Spaziergang seit', banner_walk_so_far:'Spaziergang bisher',
    still_sleeping:'noch schläft', still_walking:'läuft noch',
    no_entries:'Keine Einträge für diesen Tag',
    section_last:'Letztes Ereignis', section_intervals:'Abstände',
    section_sleep:'Schlafdauer (letzte 10)',
    stat_interval:'Abstand', stat_avg:'Ø diesen Tag',
    stat_awake_since:'Wach seit', stat_back_since:'Zurück seit',
    stat_asleep_since:'Schläft seit', stat_walking_since:'Läuft seit',
    no_data:'Keine Daten', not_enough_data:'Zu wenig Daten', no_sleep_data:'Noch keine Schlafdaten',
    settings_ip_names_title:'Geräte', settings_name_placeholder:'Name eingeben', settings_no_ips:'Noch keine Geräte bekannt',
    today:'Heute', yesterday:'Gestern',
    just_now:'gerade eben',
    ago_min: n=>`vor ${n} min`, ago_hour: n=>`vor ${n} h`, ago_day: n=>`vor ${n} d`,
    confirm_delete:'Eintrag löschen?',
    toast_no_time:'Bitte Zeitpunkt angeben', toast_deleted:'Gelöscht',
    toast_error:'Fehler beim Speichern', toast_saved:'✓ Gespeichert',
    toast_wakeup: dur=>`Aufgewacht – ${dur} Schlaf`,
    toast_walk_end: dur=>`Zurück – ${dur} Spaziergang`,
    diaper_count: n=>`Windeln: ${n}`,
    diaper_poo_count: n=>`Kacka: ${n}`,
    feeding_ml: n=>`Fläschchen: ${n} ml`,
    lang_switch:'EN',
  },
  en: {
    types: { diaper:'Diaper', nursing:'Nursing', bottle:'Bottle', sleep:'Sleep', weight:'Weight', note:'Note', walk:'Walk', clothing:'Clothing', feeding:'Feeding' },
    tab_log:'Log', tab_stats:'Stats', tab_settings:'Settings',
    modal_new:'New Entry',
    tile_diaper:'Diaper', tile_nursing:'Nursing', tile_bottle:'Bottle',
    tile_sleep_start:'Fell asleep', tile_weight:'Weight', tile_note:'Note', tile_wakeup:'Woke up',
    tile_walk:'Walk', tile_clothing:'Clothing change', tile_walk_end:'Back',
    fab_title:'New Entry',
    lbl_time:'Time', lbl_note:'Note', lbl_type:'Type', lbl_amount:'Amount (ml)',
    lbl_content:'Content', lbl_side:'Side', lbl_start:'Start', lbl_end:'End', lbl_weight_g:'Weight (g)',
    opt_wet:'Wet', opt_dirty:'Dirty', opt_both:'Both',
    opt_left:'Left', opt_right:'Right', opt_both_sides:'Both',
    opt_pumped:'Pumped milk', opt_formula:'Formula',
    btn_save_sleep:'Save fell asleep', btn_save:'Save',
    banner_since:'Sleeping since', banner_so_far:'sleep so far', banner_wakeup:'Woke up',
    banner_walk_since:'Walking since', banner_walk_so_far:'walk so far',
    still_sleeping:'still sleeping', still_walking:'still walking',
    no_entries:'No entries for this day',
    section_last:'Last event', section_intervals:'Intervals',
    section_sleep:'Sleep duration (last 10)',
    stat_interval:'Interval', stat_avg:'avg this day',
    stat_awake_since:'Awake since', stat_back_since:'Back since',
    stat_asleep_since:'Asleep since', stat_walking_since:'Walking since',
    no_data:'No data', not_enough_data:'Not enough data', no_sleep_data:'No sleep data yet',
    settings_ip_names_title:'Devices', settings_name_placeholder:'Enter name', settings_no_ips:'No devices seen yet',
    today:'Today', yesterday:'Yesterday',
    just_now:'just now',
    ago_min: n=>`${n} min ago`, ago_hour: n=>`${n} h ago`, ago_day: n=>`${n} d ago`,
    confirm_delete:'Delete entry?',
    toast_no_time:'Please enter a time', toast_deleted:'Deleted',
    toast_error:'Error saving', toast_saved:'✓ Saved',
    toast_wakeup: dur=>`Woke up – ${dur} sleep`,
    toast_walk_end: dur=>`Back – ${dur} walk`,
    diaper_count: n=>`Diapers: ${n}`,
    diaper_poo_count: n=>`Poo: ${n}`,
    feeding_ml: n=>`Bottle: ${n} ml`,
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

const ICONS = {
  diaper: '<path d="M4.5 8h15c.3 0 .5.2.5.5C20 13.7 16.4 18 12 18S4 13.7 4 8.5c0-.3.2-.5.5-.5Z"/><path d="M6.2 8.8c1.7 1 3.8 1.5 5.8 1.5s4.1-.5 5.8-1.5"/><path d="M3 9.3h1.7M19.3 9.3H21"/>',
  nursing: '<path d="M12 20.5S4.5 15.8 4.5 10.2A4.2 4.2 0 0 1 12 7.4a4.2 4.2 0 0 1 7.5 2.8c0 5.6-7.5 10.3-7.5 10.3Z"/>',
  bottle: '<rect x="7" y="8.5" width="10" height="11.5" rx="3"/><path d="M9.3 8.5V6.6a1 1 0 0 1 1-1h3.4a1 1 0 0 1 1 1v1.9"/><path d="M10.3 5.6c0-1.5.8-2.6 1.7-2.6s1.7 1.1 1.7 2.6"/><path d="M9 12.3h1.6M9 15.3h1.6M9 18.3h1.6"/>',
  feeding: '<rect x="7" y="8.5" width="10" height="11.5" rx="3"/><path d="M9.3 8.5V6.6a1 1 0 0 1 1-1h3.4a1 1 0 0 1 1 1v1.9"/><path d="M10.3 5.6c0-1.5.8-2.6 1.7-2.6s1.7 1.1 1.7 2.6"/><path d="M9 12.3h1.6M9 15.3h1.6M9 18.3h1.6"/>',
  sleep: '<path d="M20 14.3A8 8 0 1 1 9.7 4a6.3 6.3 0 0 0 10.3 10.3Z"/>',
  zzz: '<path d="M3 15h6l-6 6h6"/><path d="M10 9h5l-5 5h5"/><path d="M16 4h4l-4 4h4"/>',
  walk: '<ellipse cx="15" cy="16" rx="2.6" ry="3.6" transform="rotate(12 15 16)"/><circle cx="12.6" cy="12.4" r=".9"/><circle cx="14" cy="11.3" r=".95"/><circle cx="15.6" cy="11.1" r=".95"/><circle cx="17" cy="11.8" r=".85"/><ellipse cx="8" cy="7.5" rx="2" ry="2.8" transform="rotate(-12 8 7.5)"/><circle cx="6" cy="4.6" r=".7"/><circle cx="7.3" cy="3.8" r=".75"/><circle cx="8.7" cy="3.9" r=".7"/>',
  weight: '<circle cx="12" cy="12" r="8.2"/><path d="M12 8.6v3.8l2.6 1.6"/>',
  note: '<path d="M6 3.5h9L19.5 8v12.5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z"/><path d="M8.5 12h7M8.5 15.5h7M8.5 8.5h3"/>',
  clothing: '<path d="M8.5 4 5.8 5.7a1.4 1.4 0 0 0-.5 1.8L6.6 10l1.9-.9v9.4a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1V9.1l1.9.9 1.3-2.5a1.4 1.4 0 0 0-.5-1.8L15.5 4a4 4 0 0 1-7 0Z"/>',
  sun: '<circle cx="12" cy="12" r="4.2"/><path d="M12 3v2.2M12 18.8V21M21 12h-2.2M5.2 12H3M18.4 5.6l-1.5 1.5M7.1 16.9l-1.5 1.5M18.4 18.4l-1.5-1.5M7.1 7.1 5.6 5.6"/>',
  home: '<path d="M4 11 12 4l8 7"/><path d="M6 10v9.5a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V10"/><path d="M10 20.5V15h4v5.5"/>',
};
function icon(name) { return `<svg viewBox="0 0 24 24" class="ic">${ICONS[name] || ''}</svg>`; }
function typeIcon(name) { return name === 'sleep' ? icon('zzz') : icon(name); }
function typeTint(type) {
  if (type === 'sleep') return 'sleep';
  if (type === 'walk') return 'walk';
  if (type === 'nursing' || type === 'bottle' || type === 'feeding') return 'feed';
  return 'accent';
}

let lang = localStorage.getItem('lang') || (navigator.language.startsWith('de') ? 'de' : 'en');

function t(key, arg) {
  const val = I18N[lang][key];
  return typeof val === 'function' ? val(arg) : (val ?? key);
}
function tMeta(val) { return (META_VALS[val] && META_VALS[val][lang]) || val; }
function getType(key) { return { label: (I18N[lang].types[key] || key), icon: key in ICONS ? key : 'note' }; }

function switchLang() {
  lang = lang === 'de' ? 'en' : 'de';
  localStorage.setItem('lang', lang);
  initUI();
  loadLog();
  if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
  if (document.getElementById('tab-settings').classList.contains('active')) loadSettings();
}

function initUI() {
  document.getElementById('html-root').lang = lang;
  document.getElementById('lang-btn').textContent = t('lang_switch');
  document.querySelector('#tab-btn-log .tab-lbl').textContent = t('tab_log');
  document.querySelector('#tab-btn-stats .tab-lbl').textContent = t('tab_stats');
  document.querySelector('#tab-btn-settings .tab-lbl').textContent = t('tab_settings');
  document.getElementById('fab').title = t('fab_title');
  ['diaper','nursing','bottle','sleep_start','weight','note','walk','clothing'].forEach(k => {
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
let ipNameMap = {};
let currentDate = todayStr();
let openSleepEntry = null;
let openWalkEntry = null;
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
// Split/join instead of relying on <input type="datetime-local">, whose time
// step is unreliable on Android WebView/Chrome — plain date+time inputs work everywhere.
function splitDT(dt) {
  if (!dt) return { date: '', time: '' };
  const [date, time] = dt.split('T');
  return { date, time: time || '' };
}
function joinDT(date, time) {
  return (date && time) ? `${date}T${time}` : '';
}
function dtField(idPrefix, label, value) {
  const { date, time } = splitDT(value);
  return `
    <div class="field"><label>${label}</label>
      <div class="dt-row">
        <input type="date" id="${idPrefix}-date" value="${date}">
        <input type="time" id="${idPrefix}-time" value="${time}">
      </div>
    </div>`;
}
function readDT(idPrefix) {
  const date = document.getElementById(`${idPrefix}-date`)?.value;
  const time = document.getElementById(`${idPrefix}-time`)?.value;
  return joinDT(date, time);
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
function displayKey(ip) { return ipNameMap[ip] || ip; }
function getIpColor(ip) {
  if (!ipColorMap[ip]) { ipColorMap[ip] = IP_COLORS[colorIndex % IP_COLORS.length]; colorIndex++; }
  return ipColorMap[ip];
}
function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }

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
  if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
}
function jumpToDate(val) {
  if (!val) return;
  currentDate = val;
  updateDayNav();
  loadLog();
  if (document.getElementById('tab-stats').classList.contains('active')) loadStats();
}
function openDatePicker() {
  const el = document.getElementById('date-picker');
  try {
    if (el.showPicker) el.showPicker();
    else el.focus();
  } catch {
    el.focus();
  }
}

// ── Tab switching ──
function switchTab(name, btn) {
  document.querySelectorAll('.tab-page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  (btn || document.getElementById('tab-btn-'+name)).classList.add('active');
  location.hash = name;
  if (name === 'stats') loadStats();
  if (name === 'settings') loadSettings();
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
      <div class="sl-icon">${icon('sleep')}<span class="sl-dot"></span></div>
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

// ── Walk banner ──
async function checkOpenWalk() {
  const res = await fetch('/api/walk/open');
  openWalkEntry = res.ok ? await res.json() : null;
  renderWalkBanner();
}
function renderWalkBanner() {
  const wrap = document.getElementById('walk-banner-wrap');
  if (!openWalkEntry) { wrap.innerHTML = ''; return; }
  const since = fmtTime(openWalkEntry.ts_start);
  const dur = Math.round(durMin(openWalkEntry.ts_start, new Date().toISOString()));
  wrap.innerHTML = `
    <div class="sleep-banner walk">
      <div class="sl-icon">${icon('walk')}<span class="sl-dot"></span></div>
      <div class="sl-info">
        <div class="sl-label">${t('banner_walk_since')} ${since}</div>
        <div class="sl-since">${fmtDur(dur)} ${t('banner_walk_so_far')}</div>
      </div>
      <button class="wake-btn" onclick="endWalk()">${t('tile_walk_end')}</button>
    </div>
  `;
  setTimeout(renderWalkBanner, 60000);
}
async function endWalk() {
  if (!openWalkEntry) return;
  const now = nowLocal();
  await fetch(`/api/entries/${openWalkEntry.id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ts_end: now })
  });
  const dur = Math.round(durMin(openWalkEntry.ts_start, now));
  toast(t('toast_walk_end', fmtDur(dur)));
  openWalkEntry = null;
  document.getElementById('walk-banner-wrap').innerHTML = '';
  loadLog();
}

// ── Log ──
async function loadLog() {
  await checkOpenSleep();
  await checkOpenWalk();
  const namesRes = await fetch('/api/ip-names');
  ipNameMap = await namesRes.json();
  const allRes = await fetch('/api/entries?limit=500');
  const allEntries = await allRes.json();
  ipColorMap = {}; colorIndex = 0;
  allEntries.forEach(e => getIpColor(displayKey(e.ip)));

  const res = await fetch(`/api/entries?date=${currentDate}`);
  const entries = await res.json();
  currentEntries = entries;

  const todayKeys = [...new Set(entries.map(e => displayKey(e.ip)))];
  const legend = document.getElementById('ip-legend');
  legend.innerHTML = todayKeys.map(key => `
    <div class="ip-legend-item">
      <div class="ip-dot" style="background:${getIpColor(key)}"></div>${esc(key)}
    </div>
  `).join('');

  const diaperEntries = entries.filter(e => e.type === 'diaper');
  const pooCount = diaperEntries.filter(e => ['schmutzig','beides','dirty','both'].includes(e.meta?.diaper_type)).length;
  const feedingMl = entries.filter(e => e.type === 'bottle').reduce((sum, e) => sum + (Number(e.meta?.amount) || 0), 0);
  const chip = (iconName, label) => `<div class="count-chip">${icon(iconName)}<span>${esc(label)}</span></div>`;
  const chips = [];
  if (diaperEntries.length) chips.push(chip('diaper', t('diaper_count', diaperEntries.length)));
  if (pooCount) chips.push(chip('diaper', t('diaper_poo_count', pooCount)));
  if (feedingMl) chips.push(chip('bottle', t('feeding_ml', feedingMl)));
  document.getElementById('diaper-count').innerHTML = chips.join('');

  const list = document.getElementById('entry-list');
  if (!entries.length) {
    list.innerHTML = `<div class="empty">${t('no_entries')}</div>`;
    return;
  }

  list.innerHTML = entries.map(e => {
    const color = getIpColor(displayKey(e.ip));
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
    if (e.type === 'walk') {
      if (e.ts_end) {
        const dur = Math.round(durMin(e.ts_start, e.ts_end));
        timeStr = `${fmtTime(e.ts_start)} – ${fmtTime(e.ts_end)}`;
        metaStr = fmtDur(dur);
      } else {
        timeStr = `${fmtTime(e.ts_start)} – ${t('still_walking')}`;
      }
    }

    return `
      <div class="entry-item" onclick="openEditModal(${e.id})">
        <div class="entry-icon tint-${typeTint(e.type)}">${typeIcon(tp.icon)}</div>
        <div class="entry-body">
          <div class="entry-type">${tp.label}</div>
          <div class="entry-time">${timeStr}</div>
          ${metaStr ? `<div class="entry-meta">${esc(metaStr)}</div>` : ''}
          ${e.note ? `<div class="entry-note">${esc(e.note)}</div>` : ''}
        </div>
        <span class="ip-badge" style="background:${color}" title="${esc(e.ip)}"></span>
        <button class="del-btn" onclick="event.stopPropagation(); deleteEntry(${e.id})" title="${t('confirm_delete')}"><svg viewBox="0 0 24 24" class="ic"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
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
  const res = await fetch('/api/stats?date=' + currentDate);
  const data = await res.json();
  const el = document.getElementById('stats-content');

  const lastTypes = ['diaper','feeding','sleep','walk','weight'];
  let lastCards = '';
  lastTypes.forEach(key => {
    const e = data.last[key];
    if (!e) return;
    const tp = getType(key);
    let valStr = fmtAgo(e.ts_start);
    let sub = fmtTime(e.ts_start);
    if (key === 'sleep') {
      if (e.ts_end) {
        valStr = `${t('stat_awake_since')} ${fmtDur(Math.round(durMin(e.ts_end, new Date().toISOString())))}`;
        sub = fmtTime(e.ts_end);
      } else {
        valStr = `${t('stat_asleep_since')} ${fmtDur(Math.round(durMin(e.ts_start, new Date().toISOString())))}`;
      }
    }
    if (key === 'walk') {
      if (e.ts_end) {
        valStr = `${t('stat_back_since')} ${fmtDur(Math.round(durMin(e.ts_end, new Date().toISOString())))}`;
        sub = fmtTime(e.ts_end);
      } else {
        valStr = `${t('stat_walking_since')} ${fmtDur(Math.round(durMin(e.ts_start, new Date().toISOString())))}`;
      }
    }
    if (key === 'weight' && e.meta?.weight) { valStr = e.meta.weight + ' g'; sub = fmtAgo(e.ts_start); }
    const active = (key === 'sleep' || key === 'walk') && !e.ts_end;
    lastCards += `
      <div class="stat-card${active ? ' tint-'+key : ''}">
        <div class="s-label">${typeIcon(tp.icon)}${tp.label}</div>
        <div class="s-val" style="font-size:1rem;padding-top:2px">${valStr}</div>
        <div class="s-sub">${sub}</div>
      </div>`;
  });

  let ivCards = '';
  ['diaper','feeding'].forEach(key => {
    const iv = data.intervals[key];
    if (!iv) return;
    const tp = getType(key);
    ivCards += `
      <div class="stat-card">
        <div class="s-label">${typeIcon(tp.icon)}${tp.label} · ${t('stat_interval')}</div>
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

  if (document.getElementById('tab-stats').classList.contains('active')) setTimeout(loadStats, 60000);
}

// ── Settings ──
async function loadSettings() {
  const res = await fetch('/api/ips');
  const ips = await res.json();
  const el = document.getElementById('settings-content');
  if (!ips.length) {
    el.innerHTML = `<div class="empty">${t('settings_no_ips')}</div>`;
    return;
  }
  el.innerHTML = `
    <div class="section-title">${t('settings_ip_names_title')}</div>
    ${ips.map(({ ip, name }) => `
      <div class="ip-name-row">
        <div class="ip-avatar" style="background:${getIpColor(name || ip)}">${esc(name ? name.charAt(0).toUpperCase() : '?')}</div>
        <div class="ip-name-fields">
          <div class="ip-name-inline">
            <input type="text" class="ip-name-input" data-ip="${esc(ip)}" value="${esc(name)}" placeholder="${t('settings_name_placeholder')}">
            <button class="btn-small" onclick="saveIpName(this)">${t('btn_save')}</button>
          </div>
          <span class="ip-name-ip">${esc(ip)}</span>
        </div>
      </div>
    `).join('')}
  `;
}

async function saveIpName(btn) {
  const input = btn.closest('.ip-name-row').querySelector('.ip-name-input');
  const ip = input.dataset.ip;
  const name = input.value.trim();
  await fetch(`/api/ip-names/${encodeURIComponent(ip)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  toast(t('toast_saved'));
  loadLog();
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
    tile.innerHTML = `<div class="t-icon">${icon('sun')}</div><div class="t-label">${t('tile_wakeup')}</div>`;
    tile.onclick = () => wakeUpFromModal();
    grid.appendChild(tile);
  } else if (!openSleepEntry && existing) {
    existing.remove();
  } else if (openSleepEntry && existing) {
    existing.querySelector('.t-label').textContent = t('tile_wakeup');
  }

  document.getElementById('tile-walk').style.display = openWalkEntry ? 'none' : '';
  const existingWalk = grid.querySelector('[data-type=walk_end]');
  if (openWalkEntry && !existingWalk) {
    const tile = document.createElement('div');
    tile.className = 'type-tile';
    tile.dataset.type = 'walk_end';
    tile.innerHTML = `<div class="t-icon">${icon('home')}</div><div class="t-label">${t('tile_walk_end')}</div>`;
    tile.onclick = () => endWalkFromModal();
    grid.appendChild(tile);
  } else if (!openWalkEntry && existingWalk) {
    existingWalk.remove();
  } else if (openWalkEntry && existingWalk) {
    existingWalk.querySelector('.t-label').textContent = t('tile_walk_end');
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

function endWalkFromModal() {
  closeModal();
  endWalk();
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
    document.getElementById('modal-title').textContent = t('tile_sleep_start');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save_sleep')}</button>
    `;
  } else if (type === 'diaper') {
    document.getElementById('modal-title').textContent = t('tile_diaper');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_type')}</label>
        <select id="f-diaper-type">
          <option value="nass">${t('opt_wet')}</option>
          <option value="schmutzig">${t('opt_dirty')}</option>
          <option value="beides">${t('opt_both')}</option>
        </select>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'nursing') {
    document.getElementById('modal-title').textContent = t('tile_nursing');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_start'), now)}
      ${dtField('f-end', t('lbl_end'), '')}
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
    document.getElementById('modal-title').textContent = t('tile_bottle');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_amount')}</label><input type="number" id="f-amount" min="0" step="5" placeholder="120"></div>
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
    document.getElementById('modal-title').textContent = t('tile_weight');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_weight_g')}</label><input type="number" id="f-weight" min="0" step="10" placeholder="3450"></div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'walk') {
    document.getElementById('modal-title').textContent = t('tile_walk');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else if (type === 'clothing') {
    document.getElementById('modal-title').textContent = t('tile_clothing');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  } else {
    document.getElementById('modal-title').textContent = t('tile_note');
    fields.innerHTML = `
      ${dtField('f-start', t('lbl_time'), now)}
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="3"></textarea></div>
      <button class="btn" onclick="submitEntry()">${t('btn_save')}</button>
    `;
  }
}

async function submitEntry() {
  const start = readDT('f-start');
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
    ts_end: readDT('f-end') || null,
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
    if (apiType === 'walk' && !saved.ts_end) {
      openWalkEntry = saved;
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
  document.getElementById('modal-title').textContent = tp.label;
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
      ${dtField('f-start', t('lbl_time'), start)}
      <div class="field"><label>${t('lbl_type')}</label>
        <select id="f-diaper-type">
          <option value="nass" ${m.diaper_type === 'nass' ? 'selected' : ''}>${t('opt_wet')}</option>
          <option value="schmutzig" ${m.diaper_type === 'schmutzig' ? 'selected' : ''}>${t('opt_dirty')}</option>
          <option value="beides" ${m.diaper_type === 'beides' ? 'selected' : ''}>${t('opt_both')}</option>
        </select>
      </div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2">${note}</textarea></div>
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'nursing') {
    return `
      ${dtField('f-start', t('lbl_start'), start)}
      ${dtField('f-end', t('lbl_end'), end)}
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
      ${dtField('f-start', t('lbl_time'), start)}
      <div class="field"><label>${t('lbl_amount')}</label><input type="number" id="f-amount" min="0" step="5" value="${m.amount || ''}"></div>
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
      ${dtField('f-start', t('lbl_start'), start)}
      ${dtField('f-end', t('lbl_end'), end)}
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2">${note}</textarea></div>
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'weight') {
    return `
      ${dtField('f-start', t('lbl_time'), start)}
      <div class="field"><label>${t('lbl_weight_g')}</label><input type="number" id="f-weight" min="0" step="10" value="${m.weight || ''}"></div>
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2">${note}</textarea></div>
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  if (entry.type === 'walk') {
    return `
      ${dtField('f-start', t('lbl_start'), start)}
      ${dtField('f-end', t('lbl_end'), end)}
      <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="2">${note}</textarea></div>
      <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
    `;
  }
  return `
    ${dtField('f-start', t('lbl_time'), start)}
    <div class="field"><label>${t('lbl_note')}</label><textarea id="f-note" rows="3">${note}</textarea></div>
    <button class="btn" onclick="submitEditEntry()">${t('btn_save')}</button>
  `;
}

async function submitEditEntry() {
  const start = readDT('f-start');
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
    ts_end: readDT('f-end') || null,
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

// ── Swipe to switch tabs ──
const TAB_ORDER = ['log', 'stats', 'settings'];
function initSwipe() {
  const main = document.querySelector('.main');
  let sx = 0, sy = 0, tracking = false;
  main.addEventListener('touchstart', (e) => {
    if (e.touches.length !== 1) return;
    sx = e.touches[0].clientX;
    sy = e.touches[0].clientY;
    tracking = true;
  }, { passive: true });
  main.addEventListener('touchend', (e) => {
    if (!tracking) return;
    tracking = false;
    const dx = e.changedTouches[0].clientX - sx;
    const dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
    const current = document.querySelector('.tab-page.active').id.replace('tab-', '');
    const idx = TAB_ORDER.indexOf(current) + (dx < 0 ? 1 : -1);
    if (idx < 0 || idx >= TAB_ORDER.length) return;
    const name = TAB_ORDER[idx];
    switchTab(name, document.getElementById('tab-btn-' + name));
  }, { passive: true });
  main.addEventListener('touchcancel', () => { tracking = false; }, { passive: true });
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
initSwipe();
const initialTab = TAB_ORDER.includes(location.hash.slice(1)) ? location.hash.slice(1) : 'log';
if (initialTab !== 'log') switchTab(initialTab);
