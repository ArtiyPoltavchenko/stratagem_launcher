# Changelog — Stratagem Launcher

## Format
Entries added by Claude Code after each completed task.

---

## [Unreleased]

### 2026-03-16 — Phase 8: Ship Module Cooldown Modifier
- `web/app.js`: getCooldownModifier(), isShowCooldowns(), getEffectiveCooldown(); updated makeCard() with .card__cd-label (strikethrough old + new value when modifier > 0); startCooldown() applies modifier and skips if show_cooldowns off; initSettings() wires up new controls with live renderGrid()
- `web/index.html`: cooldown reduction row (range slider 0–50% + number input), show cooldowns checkbox in Settings panel
- `web/style.css`: .card__cd-label, .settings-range-row, .range-num-input, .settings-check-label
- localStorage keys: sl_cooldown_modifier (default 0), sl_show_cooldowns (default true)

### 2026-03-16 — Phase 7: Manual D-pad Input
- `server/keypress.py`: manual_start(), manual_key(), manual_stop(), is_manual_active(); threading.Timer auto-release
- `server/app.py`: POST /api/manual/start, /api/manual/key, /api/manual/stop, GET /api/manual/status
- `web/index.html`: D-pad overlay (full-screen), ✛ button in header
- `web/app.js`: initDpad(), openDpad(), closeDpad(), dpadTap(), dpadExecute(), renderDpadSequence()
- `web/style.css`: .dpad-overlay, .dpad-cross (3×3 grid), portrait + landscape layouts
- `tests/test_keypress.py` + `test_api.py`: 24 new tests (67 total, all passing)

### 2026-03-16 — Phase 6: Loadouts
- `index.html`: added loadout-bar (tabs + add button) and edit-header (counter + Save/Cancel)
- `app.js`: loadout data model in localStorage, buildLoadoutBar(), enterEditMode(),
  exitEditMode(), toggleEditSelection(), loadout-aware filteredStratagems() and renderGrid()
- `style.css`: .loadout-bar, .loadout-tab, .edit-header, .card--edit-mode,
  .card--selected, .grid--loadout (2-col large cards)

### 2026-03-16 — Phase 5: Polish & Docs
- `README.md`: full rewrite — Windows+WSL setup, WiFi/USB connection, troubleshooting
- `server/app.py`: added `_print_wifi_info()` — prints IPs + QR code when `--host 0.0.0.0`
- `requirements.txt`: added `qrcode>=7.0`
- `docs/testing_checklist.md`: full manual testing checklist

### 2026-03-16 — Phase 4: Full UI
- `app.js`: added cooldown overlay per card (local countdown after tap, re-tap resets)
- `app.js`: added unverified badge (`?` in corner) for stratagems with `verified: false`
- `app.js`: added `startCooldown()`, `_cooldownTimers` map; tap blocked during cooldown
- `style.css`: added `.card__badge`, `.card__cooldown`, `.card--on-cooldown` styles
- `scripts/generate_icons.py`: pure-stdlib PNG generator (no Pillow needed)
- Generated `web/icons/app-192.png` and `web/icons/app-512.png`

### 2026-03-16 — Phase 3: PWA Minimal
- Added `web/style.css` — dark theme, CSS variables, 4-col responsive grid, card flash animation, toast, settings panel
- Replaced `web/index.html` placeholder with full PWA structure (header, tabs, search, grid, settings overlay)
- Added `web/app.js` — fetch stratagems from API, render cards with fallback SVG icons, POST execute on tap, vibration, toasts, settings panel with localStorage persistence
- Added `web/manifest.json` — PWA manifest
- Added `web/sw.js` — Service Worker: cache-first for shell, network-first for API

### 2026-03-16 — Phase 2: Server Core
- Added `requirements-dev.txt` (without pynput, for WSL)
- Added `server/config.py` — Config dataclass (key_delay_ms, ctrl_hold_delay_ms, host, port, debug)
- Added `server/stratagems.py` — JSON loader with validation, get_all/get_by_id/get_categories
- Added `server/keypress.py` — pynput key simulation; importable from WSL (Controller/Key = None fallback)
- Added `server/app.py` — Flask: GET /, GET /api/stratagems, POST /api/execute, GET /api/health, GET+POST /api/settings
- Added `tests/test_stratagems.py`, `test_keypress.py`, `test_api.py` — 42 tests, all passing
- Updated `scripts/start_server.bat` and `start_server_wifi.bat` to use `python -m server.app`

### 2026-03-16 — Phase 1: Project Skeleton
- Created directory structure: server/, web/, web/icons/stratagems/, tests/, scripts/
- Added server/__init__.py, tests/__init__.py, web/index.html placeholders
- Added scripts/validate_json.py — validates stratagems.json
- First git commit

### Project Init
- Created project structure and documentation
- Added stratagems.json with 50+ stratagems across 6 categories
- Set up CLAUDE.md, PROJECT_SPEC.md, docs/

---

(Claude Code adds entries below as work progresses)
