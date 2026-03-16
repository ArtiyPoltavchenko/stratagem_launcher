/**
 * Stratagem Launcher — PWA frontend
 */

// ------------------------------------------------------------------ constants

const ARROW = { up: '▲', down: '▼', left: '◀', right: '▶' };
const STORAGE_KEY = 'sl_settings';
const HEALTH_INTERVAL = 10_000;

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

// ------------------------------------------------------------------ state

let allStratagems = [];
let categories = {};
let iconRepo = '';
let activeCategory = 'all';
let searchQuery = '';

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

function setStatus(state, text) {
  const dot = document.getElementById('status-dot');
  const label = document.getElementById('status-text');
  dot.className = `status-dot status-dot--${state}`;
  label.textContent = text;
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
  grid.innerHTML = '';

  if (!list.length) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = 'No stratagems found';
    grid.appendChild(empty);
    return;
  }

  const frag = document.createDocumentFragment();
  for (const s of list) {
    frag.appendChild(makeCard(s));
  }
  grid.appendChild(frag);
}

function makeCard(s) {
  const catColor = categories[s.category]?.color || '#888';

  const card = document.createElement('div');
  card.className = 'card' + (s.verified === false ? ' card--unverified' : '');
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

  // Cooldown overlay (hidden by default)
  if (s.cooldown > 0) {
    const cd = document.createElement('div');
    cd.className = 'card__cooldown hidden';
    card.appendChild(cd);
  }

  // Tap handler
  card.addEventListener('click', () => onCardTap(card, s));

  return card;
}

function resolveIconUrl(s) {
  if (!s.icon) return null;
  // If icon_repo is set, build full GitHub raw URL
  if (iconRepo) {
    const encoded = s.icon.split('/').map(encodeURIComponent).join('/');
    return `${iconRepo}/${encoded}`;
  }
  // Fallback: treat as local path served by Flask
  return s.icon;
}

function makeFallbackIcon(s, color) {
  const svg = buildLetterSvg(s.name[0], color);
  const url = resolveIconUrl(s);
  if (!url) return svg;

  const img = new Image();
  img.width = 36;
  img.height = 36;
  img.alt = '';
  img.style.cssText = 'width:36px;height:36px;object-fit:contain';
  img.onerror = () => img.replaceWith(svg);
  img.src = url;
  return img;
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

  const overlay = card.querySelector('.card__cooldown');
  if (!overlay) return;

  // Cancel existing timer for this card (re-tap resets cooldown)
  if (_cooldownTimers.has(s.id)) {
    clearInterval(_cooldownTimers.get(s.id));
  }

  let remaining = s.cooldown;
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

  // Load saved values
  const s = loadSettings();
  if (s.serverIp) ipInput.value = s.serverIp;
  if (s.keyDelayMs) {
    delayInput.value = s.keyDelayMs;
    delayValue.textContent = s.keyDelayMs;
  }

  delayInput.addEventListener('input', () => {
    delayValue.textContent = delayInput.value;
  });

  openBtn.addEventListener('click', () => overlay.classList.remove('hidden'));
  closeBtn.addEventListener('click', () => overlay.classList.add('hidden'));
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.add('hidden');
  });

  applyBtn.addEventListener('click', async () => {
    const ip = ipInput.value.trim();
    const delay = parseInt(delayInput.value, 10);
    saveSettings({ serverIp: ip || null, keyDelayMs: delay });

    // Push delay to server
    try {
      await apiFetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key_delay_ms: delay }),
      });
    } catch { /* ignore — server might be unreachable */ }

    overlay.classList.add('hidden');
    showToast('Settings saved');
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

// ------------------------------------------------------------------ boot

async function boot() {
  initSettings();
  initSearch();
  setStatus('checking', 'Connecting…');

  try {
    await loadStratagems();
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
