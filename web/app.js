/**
 * Stratagem Launcher — PWA frontend
 */

// ------------------------------------------------------------------ constants

const ARROW = { up: '▲', down: '▼', left: '◀', right: '▶' };
const STORAGE_KEY = 'sl_settings';
const HEALTH_INTERVAL = 10_000;
const COOLDOWN_MOD_KEY = 'sl_cooldown_modifier';
const SHOW_COOLDOWNS_KEY = 'sl_show_cooldowns';

// ------------------------------------------------------------------ settings

function loadSettings() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function saveSettings(obj) {
  const current = loadSettings();
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...current, ...obj }));
}

function getServerBase() {
  const saved = loadSettings().serverIp;
  if (saved) return `http://${saved}`;
  return `${location.protocol}//${location.host}`;
}

function getCooldownModifier() {
  return parseInt(localStorage.getItem(COOLDOWN_MOD_KEY) || '0', 10);
}

function isShowCooldowns() {
  const val = localStorage.getItem(SHOW_COOLDOWNS_KEY);
  return val === null ? true : val === 'true';
}

function getEffectiveCooldown(s) {
  const mod = getCooldownModifier();
  return Math.round(s.cooldown * (1 - mod / 100));
}

// ------------------------------------------------------------------ state

let allStratagems = [];
let categories = {};
let iconRepo = '';
let activeCategory = 'all';
let searchQuery = '';

// Loadout state
const LOADOUTS_KEY = 'sl_loadouts';
let loadouts = [];          // [{ id, name, stratagems: [id, ...] }]
let activeLoadoutId = null; // null = show All
let editLoadoutId = null;   // null = not editing
let editSelection = [];     // ids selected during edit

// ------------------------------------------------------------------ API

async function apiFetch(path, options = {}) {
  const base = getServerBase();
  const res = await fetch(`${base}${path}`, options);
  if (!res.ok) throw Object.assign(new Error(res.statusText), { status: res.status });
  return res.json();
}

async function loadStratagems() {
  const data = await apiFetch('/api/stratagems');
  allStratagems = data.stratagems || [];
  categories = data.categories || {};
  iconRepo = data.icon_repo || '';
}

async function executeStratagem(id) {
  return apiFetch('/api/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  });
}

async function checkHealth() {
  try {
    await apiFetch('/api/health');
    setStatus('ok', 'Connected');
  } catch {
    setStatus('error', 'Offline');
  }
}

// ------------------------------------------------------------------ status

function setStatus(state, _text) {
  document.getElementById('status-dot').className = `status-dot status-dot--${state}`;
}

// ---------------------------------------------------------------- loadouts

function loadLoadoutsFromStorage() {
  try {
    const raw = JSON.parse(localStorage.getItem(LOADOUTS_KEY));
    if (Array.isArray(raw)) loadouts = raw;
  } catch { /* ignore */ }
}

function saveLoadoutsToStorage() {
  localStorage.setItem(LOADOUTS_KEY, JSON.stringify(loadouts));
  // Push to server so loadouts survive IP/origin changes
  apiFetch('/api/loadouts', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(loadouts),
  }).catch(() => {});
}

async function syncLoadoutsFromServer() {
  try {
    const data = await apiFetch('/api/loadouts');
    if (Array.isArray(data) && data.length > 0) {
      loadouts = data;
      localStorage.setItem(LOADOUTS_KEY, JSON.stringify(loadouts));
    }
  } catch { /* offline — keep localStorage version */ }
}

function getLoadout(id) {
  return loadouts.find(l => l.id === id) || null;
}

function makeLoadoutId() {
  return 'l_' + Date.now();
}

function buildLoadoutBar() {
  const tabsEl = document.getElementById('loadout-tabs');
  tabsEl.innerHTML = '';

  // "All" tab
  tabsEl.appendChild(makeLoadoutTab(null, 'All'));

  for (const l of loadouts) {
    tabsEl.appendChild(makeLoadoutTab(l.id, l.name));
  }
}

function makeLoadoutTab(id, name) {
  const btn = document.createElement('button');
  btn.className = 'loadout-tab' + (activeLoadoutId === id ? ' loadout-tab--active' : '');
  btn.dataset.lid = id ?? '';

  const label = document.createElement('span');
  label.textContent = name;
  btn.appendChild(label);

  // Edit pencil (not on "All")
  if (id !== null) {
    const edit = document.createElement('button');
    edit.className = 'loadout-tab__edit';
    edit.textContent = '✎';
    edit.title = 'Edit loadout';
    edit.addEventListener('click', e => {
      e.stopPropagation();
      enterEditMode(id);
    });
    btn.appendChild(edit);
  }

  btn.addEventListener('click', () => {
    if (editLoadoutId !== null) return;
    activeLoadoutId = id;
    buildLoadoutBar();
    updateAllModeVisibility();
    renderGrid();
  });

  return btn;
}

function updateAllModeVisibility() {
  const isAll = activeLoadoutId === null;
  document.getElementById('tabs').style.display = isAll ? '' : 'none';
  document.querySelector('.search-wrap').style.display = isAll ? '' : 'none';
}

// ----------------------------------------------------------- edit mode

function enterEditMode(loadoutId) {
  editLoadoutId = loadoutId;
  editSelection = [...(getLoadout(loadoutId)?.stratagems ?? [])];
  activeLoadoutId = null; // show all cards for selection

  document.getElementById('edit-header').classList.remove('hidden');
  document.getElementById('loadout-bar').style.opacity = '0.4';
  document.getElementById('loadout-bar').style.pointerEvents = 'none';
  updateEditCounter();
  updateAllModeVisibility();
  renderGrid();
}

function exitEditMode(save) {
  if (save && editLoadoutId !== null) {
    const l = getLoadout(editLoadoutId);
    if (l) {
      l.stratagems = [...editSelection];
      saveLoadoutsToStorage();
    }
  }
  editLoadoutId = null;
  editSelection = [];

  document.getElementById('edit-header').classList.add('hidden');
  document.getElementById('loadout-bar').style.opacity = '';
  document.getElementById('loadout-bar').style.pointerEvents = '';
  buildLoadoutBar();
  updateAllModeVisibility();
  renderGrid();
}

function updateEditCounter() {
  document.getElementById('edit-counter').textContent =
    `${editSelection.length} / 4`;
}

function toggleEditSelection(id) {
  const idx = editSelection.indexOf(id);
  if (idx >= 0) {
    editSelection.splice(idx, 1);
  } else {
    if (editSelection.length >= 4) {
      showToast('Max 4 stratagems per loadout', 'busy');
      return;
    }
    editSelection.push(id);
  }
  updateEditCounter();

  // Update just this card's visual without full re-render
  const card = document.querySelector(`.card[data-id="${id}"]`);
  if (card) {
    card.classList.toggle('card--selected', editSelection.includes(id));
  }
}

// ------------------------------------------------------------------ render

function buildTabs() {
  const nav = document.getElementById('tabs');
  nav.innerHTML = '';

  const allBtn = makeTab('all', 'All', '#f5c518', activeCategory === 'all');
  nav.appendChild(allBtn);

  for (const [id, cat] of Object.entries(categories)) {
    nav.appendChild(makeTab(id, cat.name, cat.color, activeCategory === id));
  }
}

function makeTab(id, name, color, active) {
  const btn = document.createElement('button');
  btn.className = 'tab' + (active ? ' tab--active' : '');
  btn.dataset.cat = id;
  btn.style.setProperty('--tab-color', color);
  btn.role = 'tab';
  btn.textContent = name;
  btn.addEventListener('click', () => {
    activeCategory = id;
    buildTabs();
    renderGrid();
  });
  return btn;
}

function filteredStratagems() {
  let list = allStratagems;

  // In edit mode: show all (for selection), filtered by category/search
  // In loadout mode: show only loadout stratagems
  if (editLoadoutId === null && activeLoadoutId !== null) {
    const ids = getLoadout(activeLoadoutId)?.stratagems ?? [];
    // Preserve loadout order
    list = ids.map(id => allStratagems.find(s => s.id === id)).filter(Boolean);
    return list;
  }

  if (activeCategory !== 'all') {
    list = list.filter(s => s.category === activeCategory);
  }
  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    list = list.filter(s => s.name.toLowerCase().includes(q));
  }
  return list;
}

function renderGrid() {
  const grid = document.getElementById('grid');
  const list = filteredStratagems();
  const inLoadoutView = editLoadoutId === null && activeLoadoutId !== null;
  const inEditMode = editLoadoutId !== null;

  grid.className = 'grid' + (inLoadoutView ? ' grid--loadout' : '');
  document.body.classList.toggle('body--loadout-view', inLoadoutView);
  grid.innerHTML = '';

  if (!list.length) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = inLoadoutView
      ? 'Loadout is empty — tap ✎ to add stratagems'
      : 'No stratagems found';
    grid.appendChild(empty);
    return;
  }

  const frag = document.createDocumentFragment();
  for (const s of list) {
    frag.appendChild(makeCard(s, inEditMode));
  }
  grid.appendChild(frag);
}

function makeCard(s, inEditMode = false) {
  const catColor = categories[s.category]?.color || '#888';

  const isSelected = inEditMode && editSelection.includes(s.id);
  const card = document.createElement('div');
  card.className = [
    'card',
    s.verified === false ? 'card--unverified' : '',
    inEditMode ? 'card--edit-mode' : '',
    isSelected ? 'card--selected' : '',
  ].filter(Boolean).join(' ');
  card.style.setProperty('--card-accent', catColor);
  card.role = 'listitem';
  card.setAttribute('aria-label', s.name);
  card.dataset.id = s.id;

  // Unverified badge
  if (s.verified === false) {
    const badge = document.createElement('span');
    badge.className = 'card__badge';
    badge.textContent = '?';
    badge.title = 'Key sequence unverified in-game';
    card.appendChild(badge);
  }

  // Icon
  const iconWrap = document.createElement('div');
  iconWrap.className = 'card__icon';
  iconWrap.appendChild(makeFallbackIcon(s, catColor));
  card.appendChild(iconWrap);

  // Name
  const name = document.createElement('div');
  name.className = 'card__name';
  name.textContent = s.name;
  card.appendChild(name);

  // Key arrows
  const keys = document.createElement('div');
  keys.className = 'card__keys';
  for (const k of s.keys) {
    const span = document.createElement('span');
    span.className = 'arrow';
    span.textContent = ARROW[k] || k;
    keys.appendChild(span);
  }
  card.appendChild(keys);

  // Static cooldown label (base or modified)
  if (s.cooldown > 0 && isShowCooldowns()) {
    const cdLabel = document.createElement('div');
    cdLabel.className = 'card__cd-label';
    const modifier = getCooldownModifier();
    const effective = getEffectiveCooldown(s);
    if (modifier > 0) {
      cdLabel.innerHTML = `<s>${s.cooldown}s</s> ${effective}s`;
    } else {
      cdLabel.textContent = `${s.cooldown}s`;
    }
    card.appendChild(cdLabel);
  }

  // Cooldown overlay (hidden by default)
  if (s.cooldown > 0) {
    const cd = document.createElement('div');
    cd.className = 'card__cooldown hidden';
    card.appendChild(cd);
  }

  // Tap handler
  card.addEventListener('click', () => {
    if (editLoadoutId !== null) {
      toggleEditSelection(s.id);
    } else {
      onCardTap(card, s);
    }
  });

  return card;
}

async function resolveIconUrl(s, repo) {
  // If JSON has a non-empty icon path — use it directly (onerror handles 404)
  if (s.icon) {
    const encoded = s.icon.split('/').map(encodeURIComponent).join('/');
    return `${repo}/${encoded}`;
  }

  // Empty icon — probe candidates with HEAD requests
  const candidates = buildIconCandidates(s, repo);
  for (const url of candidates) {
    try {
      const res = await fetch(url, { method: 'HEAD' });
      if (res.ok) return url;
    } catch (_) {
      // network error — try next
    }
  }
  return null;
}

function buildIconCandidates(s, repo) {
  const folderMap = {
    orbital:   'Bridge',
    eagle:     'Hangar',
    support:   'Patriotic Administration Center',
    backpack:  'Patriotic Administration Center',
    defensive: 'Engineering Bay',
    vehicle:   'Robotics Workshop',
  };

  const knownFolders = {
    'Gatling Sentry':           'Robotics Workshop',
    'Machine Gun Sentry':       'Robotics Workshop',
    'Autocannon Sentry':        'Robotics Workshop',
    'Rocket Sentry':            'Robotics Workshop',
    'Mortar Sentry':            'Robotics Workshop',
    'EMS Mortar Sentry':        'Robotics Workshop',
    'Tesla Tower':              'Robotics Workshop',
    'Flame Sentry':             'Robotics Workshop',
    'Gas Mortar Sentry':        'Robotics Workshop',
    'Grenadier Battlement':     'Robotics Workshop',
    'Shield Generator Relay':   'Engineering Bay',
    'HMG Emplacement':          'Engineering Bay',
    'Anti-Tank Emplacement':    'Engineering Bay',
    'Anti-Personnel Minefield': 'Engineering Bay',
    'Anti-Tank Mines':          'Engineering Bay',
    'Incendiary Mines':         'Engineering Bay',
    'Gas Mines':                'Engineering Bay',
    'Patriot Exosuit':          'Patriotic Administration Center',
    'Emancipator Exosuit':      'Patriotic Administration Center',
    'Fast Recon Vehicle':       'Patriotic Administration Center',
    'Bastion MK XVI':           'Patriotic Administration Center',
  };

  // Strip weapon designation prefix to get bare name (e.g. "AC-8 Autocannon" → "Autocannon")
  const baseName = s.name
    .replace(/^(A\/|E\/|AX\/AR-23 |AX\/LAS-5 |AX\/ARC-3 |AX\/TX-13 |AX\/FLAM-75 |A\/M-\d+ |A\/MG-\d+ |A\/G-\d+ |A\/MLS-\d+ |A\/AC-\d+ |A\/ARC-\d+ |E\/MG-\d+ |E\/AT-\d+ |E\/GL-\d+ |E\/FLAM-\d+ |FX-\d+ |\w+-\w+ )/i, '')
    .trim();

  const folder = knownFolders[s.name] ?? knownFolders[baseName] ?? folderMap[s.category] ?? 'Patriotic Administration Center';
  const enc = str => encodeURIComponent(str);

  return [
    `${repo}/${enc(folder)}/${enc(s.name)}.svg`,
    `${repo}/${enc(folder)}/${enc(baseName)}.svg`,
    `${repo}/Bridge/${enc(s.name)}.svg`,
    `${repo}/Hangar/${enc(s.name)}.svg`,
    `${repo}/Patriotic%20Administration%20Center/${enc(s.name)}.svg`,
    `${repo}/Engineering%20Bay/${enc(s.name)}.svg`,
    `${repo}/Robotics%20Workshop/${enc(s.name)}.svg`,
  ];
}

function makeFallbackIcon(s, color) {
  // Render letter immediately; swap in real icon asynchronously
  const svg = buildLetterSvg(s.name[0], color);

  resolveIconUrl(s, iconRepo).then(url => {
    if (!url) return; // no icon found — keep letter
    const img = new Image();
    img.width = 36;
    img.height = 36;
    img.alt = '';
    img.style.cssText = 'width:36px;height:36px;object-fit:contain';
    img.onerror = () => img.replaceWith(buildLetterSvg(s.name[0], color));
    img.src = url;
    svg.replaceWith(img);
  });

  return svg;
}

function buildLetterSvg(letter, color) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 36 36');
  svg.setAttribute('width', '36');
  svg.setAttribute('height', '36');

  const rect = document.createElementNS(ns, 'rect');
  rect.setAttribute('width', '36');
  rect.setAttribute('height', '36');
  rect.setAttribute('rx', '6');
  rect.setAttribute('fill', color + '30'); // 30 = ~19% opacity hex
  svg.appendChild(rect);

  const text = document.createElementNS(ns, 'text');
  text.setAttribute('x', '18');
  text.setAttribute('y', '24');
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('font-size', '18');
  text.setAttribute('font-family', 'system-ui');
  text.setAttribute('fill', color);
  text.textContent = letter.toUpperCase();
  svg.appendChild(text);

  return svg;
}

// ------------------------------------------------------------------ cooldown

const _cooldownTimers = new Map(); // id → intervalId

function startCooldown(card, s) {
  if (!s.cooldown || s.cooldown <= 0) return;
  if (!isShowCooldowns()) return;

  const overlay = card.querySelector('.card__cooldown');
  if (!overlay) return;

  // Cancel existing timer for this card (re-tap resets cooldown)
  if (_cooldownTimers.has(s.id)) {
    clearInterval(_cooldownTimers.get(s.id));
  }

  let remaining = getEffectiveCooldown(s);
  overlay.textContent = remaining + 's';
  overlay.classList.remove('hidden');
  card.classList.add('card--on-cooldown');

  const timer = setInterval(() => {
    remaining--;
    if (remaining <= 0) {
      clearInterval(timer);
      _cooldownTimers.delete(s.id);
      overlay.classList.add('hidden');
      card.classList.remove('card--on-cooldown');
    } else {
      overlay.textContent = remaining + 's';
    }
  }, 1000);

  _cooldownTimers.set(s.id, timer);
}

// ------------------------------------------------------------------ tap

async function onCardTap(card, s) {
  // Ignore taps during cooldown
  if (card.classList.contains('card--on-cooldown')) {
    const remaining = card.querySelector('.card__cooldown')?.textContent;
    showToast(`Cooldown: ${remaining}`, 'busy');
    return;
  }

  // Haptic feedback
  if (navigator.vibrate) navigator.vibrate(40);

  // Flash animation — remove & re-add class to re-trigger
  card.classList.remove('card--flash');
  void card.offsetWidth; // reflow
  card.classList.add('card--flash');

  try {
    await executeStratagem(s.id);
    startCooldown(card, s);
  } catch (err) {
    if (err.status === 503) {
      showToast('Busy — wait for current stratagem', 'busy');
    } else if (err.status !== undefined) {
      showToast('Key sim unavailable (run on Windows)', 'error');
    } else {
      showToast('Server error — check connection', 'error');
      setStatus('error', 'Offline');
    }
  }
}

// ------------------------------------------------------------------ toast

function showToast(msg, type = '') {
  const container = document.getElementById('toasts');
  const toast = document.createElement('div');
  toast.className = 'toast' + (type ? ` toast--${type}` : '');
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 2000);
}

// ------------------------------------------------------------------ settings UI

function initSettings() {
  const overlay = document.getElementById('settings-overlay');
  const openBtn = document.getElementById('settings-btn');
  const closeBtn = document.getElementById('settings-close');
  const applyBtn = document.getElementById('apply-btn');
  const testBtn = document.getElementById('test-conn-btn');
  const ipInput = document.getElementById('setting-ip');
  const delayInput = document.getElementById('setting-delay');
  const delayValue = document.getElementById('delay-value');
  const cdModSlider = document.getElementById('setting-cd-modifier');
  const cdModNum = document.getElementById('setting-cd-modifier-num');
  const cdModValue = document.getElementById('cd-modifier-value');
  const showCdCheck = document.getElementById('setting-show-cooldowns');

  // Load saved values
  const s = loadSettings();
  if (s.serverIp) ipInput.value = s.serverIp;
  if (s.keyDelayMs) {
    delayInput.value = s.keyDelayMs;
    delayValue.textContent = s.keyDelayMs;
  }
  const autoClickEl = document.getElementById('setting-auto-click');
  if (autoClickEl) autoClickEl.checked = s.autoClick ?? false;

  const savedMod = getCooldownModifier();
  cdModSlider.value = savedMod;
  cdModNum.value = savedMod;
  cdModValue.textContent = savedMod;

  showCdCheck.checked = isShowCooldowns();

  delayInput.addEventListener('input', () => {
    delayValue.textContent = delayInput.value;
  });

  function applyModifier(val) {
    const clamped = Math.min(50, Math.max(0, Math.round(val / 5) * 5));
    cdModSlider.value = clamped;
    cdModNum.value = clamped;
    cdModValue.textContent = clamped;
    localStorage.setItem(COOLDOWN_MOD_KEY, clamped);
    renderGrid();
  }

  cdModSlider.addEventListener('input', () => applyModifier(parseInt(cdModSlider.value, 10)));
  cdModNum.addEventListener('input', () => applyModifier(parseInt(cdModNum.value, 10) || 0));

  showCdCheck.addEventListener('change', () => {
    localStorage.setItem(SHOW_COOLDOWNS_KEY, showCdCheck.checked);
    renderGrid();
  });

  openBtn.addEventListener('click', () => overlay.classList.remove('hidden'));
  closeBtn.addEventListener('click', () => overlay.classList.add('hidden'));
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.add('hidden');
  });

  applyBtn.addEventListener('click', async () => {
    const ip = ipInput.value.trim();
    const delay = parseInt(delayInput.value, 10);
    const autoClick = document.getElementById('setting-auto-click')?.checked ?? false;
    saveSettings({ serverIp: ip || null, keyDelayMs: delay, autoClick });

    // Push settings to server; show feedback based on success/failure
    try {
      await apiFetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key_delay_ms: delay, auto_click: autoClick }),
      });
      overlay.classList.add('hidden');
      showToast('Settings saved ✓');
    } catch {
      showToast('Settings saved locally (server unreachable)', 'busy');
      overlay.classList.add('hidden');
    }
  });

  testBtn.addEventListener('click', async () => {
    testBtn.textContent = 'Testing…';
    testBtn.disabled = true;
    try {
      await apiFetch('/api/health');
      showToast('Connection OK', '');
      setStatus('ok', 'Connected');
    } catch {
      showToast('Cannot reach server', 'error');
      setStatus('error', 'Offline');
    } finally {
      testBtn.textContent = 'Test Connection';
      testBtn.disabled = false;
    }
  });
}

// ------------------------------------------------------------------ search

function initSearch() {
  const input = document.getElementById('search');
  input.addEventListener('input', () => {
    searchQuery = input.value.trim();
    renderGrid();
  });
}

// ------------------------------------------------------------------- d-pad

const SWIPE_THRESHOLD = 30;  // px — below this = tap, above = swipe

let dpadActive = false;
let dpadSequence = [];
let _swipeTouchStartX = 0;
let _swipeTouchStartY = 0;

// Auto-release timer state
let _autoReleaseTimer = null;
let _autoReleaseStart = null;
let _autoReleaseDuration = 3000;
let _countdownRaf = null;

function getManualTimeout() {
  const v = parseFloat(localStorage.getItem('sl_manual_timeout'));
  return isNaN(v) ? 3.0 : Math.min(5.0, Math.max(1.0, v));
}

function _scheduleAutoRelease() {
  _cancelAutoRelease();
  const ms = getManualTimeout() * 1000;
  _autoReleaseStart = Date.now();
  _autoReleaseDuration = ms;
  _tickCountdown();
  _autoReleaseTimer = setTimeout(() => _stopManualMode(), ms);
}

function _cancelAutoRelease() {
  if (_autoReleaseTimer !== null) { clearTimeout(_autoReleaseTimer); _autoReleaseTimer = null; }
  if (_countdownRaf  !== null) { cancelAnimationFrame(_countdownRaf); _countdownRaf = null; }
  _autoReleaseStart = null;
}

function _tickCountdown() {
  const fill = document.getElementById('ldpad-countdown-fill');
  if (!fill || _autoReleaseStart === null) return;
  const fraction = Math.max(0, 1 - (Date.now() - _autoReleaseStart) / _autoReleaseDuration);
  fill.style.width = `${fraction * 100}%`;
  if (fraction > 0) _countdownRaf = requestAnimationFrame(_tickCountdown);
}

async function _stopManualMode() {
  _cancelAutoRelease();
  const fill = document.getElementById('ldpad-countdown-fill');
  if (fill) fill.style.width = '0%';
  await apiFetch('/api/manual/stop', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }).catch(() => {});
  dpadActive = false;
  dpadSequence = [];
  renderDpadSequence();
  setDpadStatus(false);
}

function initDpad() {
  const fabBtn = document.getElementById('fab-dpad');
  if (fabBtn) fabBtn.addEventListener('click', openDpad);
  document.getElementById('dpad-close-btn').addEventListener('click', closeDpad);
  document.getElementById('ldpad-cancel-btn').addEventListener('click', cancelInlineDpad);

  document.querySelectorAll('.dpad-btn[data-dir]').forEach(btn => {
    btn.addEventListener('click', () => dpadTap(btn.dataset.dir));
  });

  // Auto-release slider
  const slider = document.getElementById('ldpad-timeout-slider');
  const valLabel = document.getElementById('ldpad-timer-value');
  const saved = getManualTimeout();
  slider.value = saved;
  valLabel.textContent = `${saved.toFixed(1)}s`;
  slider.addEventListener('input', () => {
    const v = parseFloat(slider.value);
    localStorage.setItem('sl_manual_timeout', v);
    valLabel.textContent = `${v.toFixed(1)}s`;
  });
}

async function openDpad() {
  dpadSequence = [];
  renderDpadSequence();
  document.getElementById('dpad-overlay').classList.remove('hidden');

  try {
    await apiFetch('/api/manual/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    dpadActive = true;
    setDpadStatus(true);
  } catch {
    showToast('Cannot start manual mode — check connection', 'error');
    document.getElementById('dpad-overlay').classList.add('hidden');
  }
}

async function closeDpad() {
  await _stopManualMode();
  document.getElementById('dpad-overlay').classList.add('hidden');
}

async function dpadTap(direction) {
  // Auto-start: first tap holds Ctrl automatically (no explicit Start button)
  if (!dpadActive) {
    dpadActive = true; // set optimistically to prevent race on rapid taps
    dpadSequence = [];
    try {
      await apiFetch('/api/manual/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      setDpadStatus(true);
    } catch {
      dpadActive = false;
      showToast('Cannot start manual mode — check connection', 'error');
      return;
    }
    _scheduleAutoRelease();
  }

  if (navigator.vibrate) navigator.vibrate(30);

  // Flash all matching buttons (overlay + embedded)
  document.querySelectorAll(`.dpad-btn[data-dir="${direction}"]`).forEach(btn => {
    btn.classList.add('dpad-btn--flash');
    setTimeout(() => btn.classList.remove('dpad-btn--flash'), 150);
  });

  try {
    await apiFetch('/api/manual/key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ direction }),
    });
    dpadSequence.push(direction);
    renderDpadSequence();
    _scheduleAutoRelease();
  } catch (err) {
    if (err.status === 409) {
      // Manual mode timed out server-side — reflect that in UI
      dpadActive = false;
      setDpadStatus(false);
      showToast('Ctrl released (timeout) — tap to restart', 'busy');
    } else {
      showToast('Connection lost', 'error');
    }
  }
}

function renderDpadSequence() {
  for (const id of ['dpad-sequence', 'ldpad-sequence']) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.innerHTML = '';
    for (const dir of dpadSequence) {
      const span = document.createElement('span');
      span.className = 'dpad-seq-arrow';
      span.textContent = ARROW[dir] || dir;
      el.appendChild(span);
    }
  }
}

function setDpadStatus(active) {
  const text = active ? 'Ctrl held — tap arrows to enter sequence' : 'Ctrl released';
  for (const id of ['dpad-status', 'ldpad-status']) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.textContent = text;
    el.classList.toggle('dpad-status--inactive', !active);
  }
  // Visual swipe-zone border: dashed when manual mode is on
  const dpadArea = document.getElementById('loadout-dpad-area');
  if (dpadArea) dpadArea.classList.toggle('manual-active', active);
}

function initSwipe() {
  // Swipe zone is the embedded D-pad area — tap dpad buttons OR swipe anywhere in the area
  const dpadArea = document.getElementById('loadout-dpad-area');
  if (!dpadArea) return;

  dpadArea.addEventListener('touchstart', e => {
    const t = e.changedTouches[0];
    _swipeTouchStartX = t.clientX;
    _swipeTouchStartY = t.clientY;
  }, { passive: true });

  dpadArea.addEventListener('touchend', e => {
    const t  = e.changedTouches[0];
    const dx = t.clientX - _swipeTouchStartX;
    const dy = t.clientY - _swipeTouchStartY;

    if (Math.abs(dx) < SWIPE_THRESHOLD && Math.abs(dy) < SWIPE_THRESHOLD) {
      return; // small movement = tap, let dpad button click fire normally
    }

    e.preventDefault(); // block synthesized click for swipe gesture
    const direction = Math.abs(dx) > Math.abs(dy)
      ? (dx > 0 ? 'right' : 'left')
      : (dy > 0 ? 'down' : 'up');
    dpadTap(direction);
  }, { passive: false });
}

async function cancelInlineDpad() {
  await _stopManualMode();
}

// ------------------------------------------------------------------ boot

function initLoadouts() {
  loadLoadoutsFromStorage();
  buildLoadoutBar();

  document.getElementById('loadout-add-btn').addEventListener('click', () => {
    if (editLoadoutId !== null) return;
    const name = `Loadout ${loadouts.length + 1}`;
    const newL = { id: makeLoadoutId(), name, stratagems: [] };
    loadouts.push(newL);
    saveLoadoutsToStorage();
    buildLoadoutBar();
    enterEditMode(newL.id);
  });

  document.getElementById('edit-save-btn').addEventListener('click', () => exitEditMode(true));
  document.getElementById('edit-cancel-btn').addEventListener('click', () => exitEditMode(false));
}

async function boot() {
  initSettings();
  initSearch();
  initLoadouts();
  initDpad();
  initSwipe();
  setStatus('checking', 'Connecting…');

  try {
    await loadStratagems();
    await syncLoadoutsFromServer();
    buildLoadoutBar();
    buildTabs();
    renderGrid();
    setStatus('ok', 'Connected');
  } catch {
    setStatus('error', 'Offline');
    document.getElementById('loading').textContent =
      'Cannot reach server. Check IP in Settings ⚙';
    return;
  }

  // Register service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }

  // Periodic health check
  setInterval(checkHealth, HEALTH_INTERVAL);
}

document.addEventListener('DOMContentLoaded', boot);
