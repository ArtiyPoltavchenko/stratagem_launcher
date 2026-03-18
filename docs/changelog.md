# Changelog — Stratagem Launcher

## Format
Entries added by Claude Code after each completed task.

---

## [Unreleased]

### 2026-03-18 — feat: delete loadout button in edit mode

- `web/index.html`: added `#edit-delete-btn` between Cancel and Save in edit header
- `web/style.css`: added `.btn-edit-action--danger` (dark red, visually distinct)
- `web/app.js`: delete handler — confirms, removes from `loadouts`, saves to localStorage + server, resets activeLoadoutId if deleted was active, exits edit mode

### 2026-03-17 — Fix: stratagems.json — all icon paths filled

- `data/stratagems.json`: filled icon paths for 23 stratagems (airburst_rocket_launcher, wasp_launcher, de_escalator, sterilizer, one_true_flag, solo_silo, expendable_napalm, speargun, maxigun, epoch, guard_dog_dog_breath, guard_dog_k9, portable_hellbomb, directional_shield, hover_pack, warp_pack, hot_dog, flame_sentry, anti_tank_emplacement, grenadier_battlement, anti_tank_mines, gas_mines, emancipator_exosuit, fast_recon_vehicle)
- Fixed warbonds: `flame_sentry` Freedom's Flame → Urban Legends; `de_escalator` Urban Legends → Force of Law; `warp_pack` Borderline Justice → Control Group
- Added 2 new stratagems: `laser_sentry` (Control Group, defensive) and `defoliation_tool` (Python Commandos, support)
- 6 stratagems intentionally remain `"icon": ""` (no entry in nvigneux repo): leveller, belt_fed_grenade_launcher, cremator, c4_pack, gas_mortar_sentry, bastion
- Total: 84 stratagems, 82 tests passing

### 2026-03-17 — Fix: Icon HEAD-check, D-pad 409, README count

- `web/app.js`: `resolveIconUrl` is now `async` — for stratagems with `"icon": ""`, probes candidate URLs via `fetch({method:'HEAD'})` across Bridge/Hangar/PAC/Engineering Bay/Robotics Workshop folders; returns first 200 OK or null
- `web/app.js`: added `buildIconCandidates()` with per-stratagem `knownFolders` map and prefix-strip logic to find bare name (e.g. "AC-8 Autocannon" → "Autocannon")
- `web/app.js`: `makeFallbackIcon()` now renders letter icon immediately, then async-swaps in real icon when `resolveIconUrl` resolves
- `web/app.js`: `dpadTap()` — set `dpadActive = true` optimistically before `await apiFetch('/api/manual/start')` to prevent race condition where two rapid taps both send `/start`, causing 409 on the `/key` call
- `README.md`: already correct ("Browse all stratagems" — no hard-coded count)

### 2026-03-17 — Data: Full Stratagem List (DLC + Warbonds)

- `data/stratagems.json`: expanded from 59 to 82 stratagems across 6 categories
- Categories updated: `defense` → `defensive`, `mission` removed, `vehicle` added (`#795548`)
- All base-game stratagems updated with full weapon designations (e.g. "AC-8 Autocannon")
- Eagle cooldowns corrected to rearm cooldown (120–150s) with `"uses"` field per charge count
- `"orbital_laser"` gets `"uses": 3`; `"eagle_500kg_bomb"` gets `"uses": 1`; etc.
- Warbond stratagems: `"warbond"` field added (Truth Enforcers, Chemical Agents, Dust Devils, etc.)
- New vehicle category: Patriot Exosuit, Emancipator Exosuit, Fast Recon Vehicle, Bastion
- New backpack entries: Guard Dog K-9, Dog Breath, Hover Pack, Warp Pack, Portable Hellbomb, etc.
- New defensive entries: Flame Sentry, Anti-Tank Emplacement, Gas Mines, Anti-Tank Mines, etc.
- `tests/test_api.py`: updated `test_correct_keys_passed_to_keypress` to use `orbital_precision_strike` (removed `reinforce` which was in the now-deleted `mission` category)

### 2026-03-17 — Feature: Auto-Install ADB

- `desktop/server_manager.py`: "Install ADB" button in Settings row — downloads Android Platform Tools (~10 MB) via `urllib.request.urlretrieve` to `%LOCALAPPDATA%\StratagramLauncher\platform-tools\adb.exe`; no admin rights required; progress % shown on button; button turns green "ADB ✓ Installed" and disables on success
- `_get_adb_path()`: checks local install first, then `shutil.which("adb")` on system PATH
- `_setup_usb()`: replaces inline subprocess; passes `ADB_PATH` env var to bat; shows warning if adb not found
- `scripts/setup_usb.bat`: reads `ADB_PATH` env var if set, falls back to system `adb`

### 2026-03-17 — QR PhotoImage rewrite

- `desktop/server_manager.py`: replaced `tk.Canvas` QR renderer with `tk.PhotoImage.put()` approach — builds pixel rows as `"{#000000 #ffffff ...}"` strings, calls `img.put()` once; no `winfo_width()`, no PIL, no geometry race condition
- `self._qr_photo` holds the image reference (prevents GC); `self._qr_label` (tk.Label) shows it
- White-bg `qr_frame` provides quiet zone; `QR_CANVAS_SIZE` renamed to `QR_IMG_SIZE`

### 2026-03-17 — QR Canvas Fix + Landscape Layout Fix

**QR (`desktop/server_manager.py`):**
- `QR_CANVAS_SIZE = 260` constant — canvas always created with explicit pixel size, no `winfo_width()` dependence
- `_draw_qr(url)` — new method using `qr.modules` + `QR_CANVAS_SIZE // (side + 4)` for box size; catches all exceptions and shows error text in red
- `_refresh_qr()` now only computes URL, calls `root.update_idletasks()` then `_draw_qr()`
- Fixed-height `qr_frame` (`height=QR_CANVAS_SIZE+8`, `pack_propagate=False`) prevents QR being squished on window resize
- Left panel: `width=420` + `pack_propagate(False)` — stable layout regardless of content
- `WINDOW_MIN_W/H` updated to 1000×740

**Landscape PWA (`web/style.css`):**
- Cards panel: 40vw → 45vw; `min-width: 0` added (required for flex shrink)
- Cards: `height:100%` → `min-height:0; height:auto; overflow:hidden` — cells shrink on short screens
- Card icon/name scaled to cell width: `clamp(28px, calc(45vw/5), 48px)` / `clamp(0.5rem, calc(45vw/20), 0.72rem)`
- D-pad area: `overflow:hidden` added
- Timer row: `flex-shrink:1` — yields space to the cross when screen is short
- `--cell` formula updated for S23 Ultra (915×412 dp): `clamp(48px, min(52vw/3.2, (100dvh-164px)/3), 82px)`

### 2026-03-17 — Phase 11: Keypress Debug & Fixes
- `server/keypress.py`: `execute_stratagem()` now takes `key_hold` (default 40ms) — holds each key before releasing; `auto_click` (default False) — LMB click after Ctrl release for auto-throw; diagnostic `[KEYPRESS]` debug log lines with timestamps; updated default `ctrl_delay=0.1`, `key_delay=0.06`; `manual_key()` takes `key_hold` too; imports `pynput.mouse` in the try block
- `server/config.py`: new fields `key_hold_ms=40`, `auto_click=False`; updated `key_delay_ms=60`, `ctrl_hold_delay_ms=100`; added `key_hold` property
- `server/app.py`: passes `key_hold`/`auto_click` to `execute_stratagem` and `manual_key`; `POST /api/settings` accepts `key_hold_ms`/`auto_click`, logs `[SETTINGS] Received` and `[SETTINGS] Applied`; `GET /api/settings` returns `key_hold_ms`/`auto_click`
- `web/index.html`: "Auto-throw after input (LMB click)" checkbox in Settings panel
- `web/app.js`: apply button shows "Settings saved ✓" on success, "server unreachable" hint if fetch fails; saves/reads `autoClick` from localStorage; sends `auto_click` in POST
- `tests/test_keypress.py`: 3 new tests — key_hold between press/release, key_delay after release, manual_key hold timing
- `tests/test_api.py`: 7 new tests — key_hold_ms GET/POST/persist, auto_click GET/POST, settings logging

### 2026-03-17 — Phase 10: Loadout D-pad Redesign
- `web/index.html`: header — removed `#status-text`, `#dpad-open-btn`; added inline SVG signal-bars icon; embedded D-pad (`#loadout-dpad-area`) with topbar/countdown/timer/status/cross; removed `dpad-execute-btn` from overlay; added FAB `#fab-dpad`
- `web/style.css`: `.signal-icon` (16×12 SVG); CSS `:has()` signal colouring; `body--loadout-view` full-viewport flex layout; `.grid--loadout` 4×1 portrait + 2×2 landscape; embedded cross `clamp(72px,26vw,110px)`; ldpad countdown bar; swipe active outline; north marker `::after` on `.dpad-btn--up`; landscape loadout media query (45vw/55vw split); FAB `.fab-dpad` (56px circle, fixed bottom-right); FAB hidden in loadout view
- `web/app.js`: `setStatus()` icon-only; `initDpad()` FAB wiring; auto-release timer (`_scheduleAutoRelease`, `_cancelAutoRelease`, `_tickCountdown`); `dpadTap()` auto-start on first tap; dual sequence/status display (overlay + embedded); `setDpadStatus()` toggles `manual-active` on `#grid`; `_stopManualMode()` shared cleanup; `initSwipe()` touch detection (30px threshold)

### 2026-03-17 — QR Code: Canvas renderer, no PIL
- `desktop/server_manager.py`: replaced PIL/ImageTk QR with `tk.Canvas` — draws QR matrix via `qr.get_matrix()` directly as rectangles; no PIL dependency, no GC issues, auto-redraws on `<Configure>` resize
- `desktop/server_manager.py`: replaced `qr_label` + `qr_hint` Labels with `qr_canvas` (Canvas) + `qr_url_label` (yellow URL below)
- `scripts/build_exe.bat`: removed `--collect-all PIL`, `--hidden-import PIL.ImageTk/PIL.Image`
- `requirements.txt`: `qrcode[pil]` → `qrcode>=7.0` (no Pillow extras needed)

### 2026-03-17 — Phase 9 Post-Release: GUI Bug Fixes
- `desktop/server_manager.py`: `SetProcessDpiAwareness(2)` in `main()` before `Tk()` — crisp text on 2K/4K
- `desktop/server_manager.py`: QR code fix — `QRCode(box_size=6, border=2)` + `.convert("RGB")` + `Image.NEAREST`; `self._qr_image` ref prevents GC blank-label bug
- `desktop/server_manager.py`: venv check on startup — friendly error + instructions if not in venv; skipped in PyInstaller bundle
- `desktop/server_manager.py`: replaced static `left.pack_propagate(False)` layout with `PanedWindow(HORIZONTAL)` — draggable sash, log panel `stretch="always"`, `minsize=800×500`; QR area fills remaining space via `expand=True`

### 2026-03-17 — Phase 9: Desktop EXE — Server Manager
- `desktop/__init__.py`, `desktop/server_manager.py`: tkinter GUI wrapping Flask server
- `ServerThread`: werkzeug make_server() in daemon thread; shutdown() for clean stop
- `TkLogHandler`: thread-safe log forwarding via queue.Queue + root.after(100) poll
- GUI: status dot, connection frame (WiFi/USB URLs + Copy, port input, QR code), mode radio, key delay slider (live Config update), Start/Stop/Restart, ScrolledText log + Clear
- `resource_path()`: PyInstaller _MEIPASS-aware path resolution; sys.path fixup for 'server' package
- `scripts/build_exe.bat`: PyInstaller --onefile --windowed, bundles data/ web/ server/
- `requirements-build.txt`: pyinstaller>=6.0 (build-only)
- `requirements.txt`: qrcode>=7.0 → qrcode[pil]>=7.0 (PIL needed for ImageTk QR display)

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
