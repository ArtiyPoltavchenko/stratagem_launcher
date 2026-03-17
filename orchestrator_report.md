# Orchestrator Report — Stratagem Launcher

> Auto-updated by Claude Code at the end of each phase.
> Last updated: 2026-03-17

---

## Project Summary

Mobile PWA remote control for Helldivers 2 stratagems.
Phone → HTTP → Python/Flask server → pynput → keystrokes in game.

**Stack:** Python 3.10+, Flask, pynput, Vanilla JS/HTML/CSS (no npm), tkinter (desktop GUI).
**Environments:** WSL2 for development/tests, Windows for running the server (pynput requires native Windows).
**Tests:** 82 passing (pytest, WSL).

---

## Architecture

```
Phone (Chrome PWA)
  ├─ HTTP POST /api/execute {id}          → server presses Ctrl + key sequence
  ├─ HTTP POST /api/manual/start          → server presses and holds Ctrl
  ├─ HTTP POST /api/manual/key {dir}      → server presses one directional key
  ├─ HTTP POST /api/manual/stop           → server releases Ctrl
  └─ GET/PUT   /api/loadouts              → server-side loadout persistence

Flask server (Windows, .venv_win)
  └─ keypress.py → pynput → KeyCode.from_vk() → Helldivers 2

Desktop GUI (primary user entry point)
  └─ desktop/server_manager.py (tkinter)
       ├─ werkzeug.make_server() in daemon thread → same Flask app
       ├─ QR code (tk.PhotoImage.put, no PIL)
       ├─ ADB auto-install (urllib, no admin rights)
       └─ dual log output: GUI ScrolledText + stdout
```

---

## File Structure

```
stratagem_launcher/
├── CLAUDE.md                        # Project rules, dev workflow, phase specs
├── PROJECT_SPEC.md                  # Technical specification
├── orchestrator_report.md           # ← this file
├── README.md                        # User-facing setup + usage guide
├── INITIAL_PROMPT.md                # Bootstrap prompt for new Claude sessions
├── .gitignore
├── requirements.txt                 # Windows venv: flask, flask-cors, pynput, qrcode>=7.0
├── requirements-dev.txt             # WSL venv: flask, flask-cors, pytest (no pynput)
├── requirements-build.txt           # Build only: pyinstaller>=6.0
│
├── server/
│   ├── __init__.py
│   ├── app.py                       # Flask app factory + all routes (incl. /api/loadouts)
│   ├── keypress.py                  # pynput simulation (VK codes, execute + manual mode)
│   ├── stratagems.py                # JSON loader + validator + query functions
│   └── config.py                    # Config dataclass (delays, host, port, key_hold, auto_click)
│
├── data/
│   ├── stratagems.json              # 59 stratagems, 6 categories, icon_repo URL
│   └── loadouts.json                # Server-side loadout persistence (created on first save)
│
├── web/                             # PWA frontend (served by Flask as static)
│   ├── index.html                   # App shell: header, loadout bar, tabs, grid, D-pad
│   ├── app.js                       # All frontend logic
│   ├── style.css                    # Dark Helldivers theme + all component styles
│   ├── manifest.json                # PWA manifest
│   ├── sw.js                        # Service Worker (cache-first shell, network-first API)
│   └── icons/
│       ├── app-192.png
│       ├── app-512.png
│       └── stratagems/              # empty — icons loaded from GitHub CDN at runtime
│
├── desktop/
│   ├── __init__.py
│   └── server_manager.py            # tkinter GUI — primary user entry point
│
├── scripts/
│   ├── start_server.bat             # Windows: launch server on localhost (console)
│   ├── start_server_wifi.bat        # Windows: launch server on 0.0.0.0 (console)
│   ├── setup_usb.bat                # ADB reverse tcp:5000; respects ADB_PATH env var
│   ├── build_exe.bat                # PyInstaller: build Stratagem Launcher.exe
│   ├── setup_wsl_venv.sh            # WSL: create .venv without pynput
│   ├── validate_json.py             # Validate stratagems.json integrity
│   └── generate_icons.py            # Generate app-192.png / app-512.png (stdlib only)
│
├── tests/
│   ├── __init__.py
│   ├── test_stratagems.py           # JSON load, validation, query (14 tests)
│   ├── test_keypress.py             # pynput mocked: execute + manual mode (39 tests)
│   └── test_api.py                  # Flask test client: all endpoints (29 tests)
│
├── prompts/                         # Feature/bugfix prompt files for Claude sessions
└── docs/
    ├── progress.md                  # Phase tracker
    ├── changelog.md                 # What changed and when
    ├── decisions.md                 # Architectural decisions (ADR-001–006)
    └── testing_checklist.md         # Manual testing checklist
```

---

## Completed Phases

### Phase 1 — Project Skeleton ✅
Directory structure, venv setup, requirements files, `scripts/validate_json.py`.

### Phase 2 — Server Core ✅
- `server/config.py` — Config dataclass, CLI overrides
- `server/stratagems.py` — JSON load/validate/query, `get_icon_repo()`
- `server/keypress.py` — pynput via `KeyCode.from_vk()` (WM_KEYDOWN, not Unicode); threading Lock
- `server/app.py` — Flask: `/api/stratagems`, `/api/execute`, `/api/health`, `/api/settings`
- `scripts/start_server.bat` + `start_server_wifi.bat`

### Phase 3 — PWA Minimal ✅
Full `index.html`, `app.js`, `style.css`. Dark Helldivers theme, 4-col mobile grid, CSS variables. `manifest.json` + `sw.js` (PWA installable).

### Phase 4 — Full UI ✅
SVG icons via `icon_repo` (GitHub CDN), letter-SVG fallback offline. Cooldown timer overlay per card. Unverified badge (`?`) for `verified: false` stratagems. `app-192.png` + `app-512.png`.

### Phase 5 — Polish & Docs ✅
`README.md`, QR code on server startup, `setup_usb.bat`, `docs/testing_checklist.md`.

### Phase 6 — Loadouts ✅
Loadout bar (tabs + `＋`), edit mode with card selection overlay, `X/4` counter. Loadout view: 2-col large-card grid. Persistence in localStorage + `GET/PUT /api/loadouts` server-side sync.

### Phase 7 — Manual D-pad Input ✅
`manual_start()` / `manual_key()` / `manual_stop()` in keypress.py. Threading.Timer auto-release. D-pad overlay in PWA. Portrait + landscape layouts. Visual sequence bar, haptic feedback.

### Phase 8 — Ship Module Cooldown Modifier ✅
Cooldown reduction slider (0–50%, step 5%) + show/hide toggle. `getEffectiveCooldown()` in app.js. `~~100s~~ 75s` strikethrough on card when modifier > 0. localStorage persistence.

### Phase 9 — Desktop EXE — Server Manager ✅
`desktop/server_manager.py` — tkinter GUI with status dot, connection panel, QR code, log viewer, Start/Stop/Restart, mode radio (WiFi/Localhost/USB), key delay slider. `ServerThread` wraps `werkzeug.make_server()`. `TkLogHandler` → `queue.Queue` → `ScrolledText`. `resource_path()` for PyInstaller. `scripts/build_exe.bat`.

### Phase 10 — Loadout D-pad Redesign ✅
Combined loadout view + manual D-pad into one gaming screen. Removed separate D-pad overlay for loadout context. Embedded D-pad (`#loadout-dpad-area`) with countdown bar, auto-release slider (1–5s), swipe detection. FAB `#fab-dpad` for All view. Signal-bars SVG icon in header.

**Portrait:** 4×1 cards + D-pad below.
**Landscape (S23 Ultra, 915×412dp):** 45vw cards (2×2) + 55vw D-pad. `--cell: clamp(48px, min(52vw/3.2, (100dvh-164px)/3), 82px)`.

### Phase 11 — Keypress Debug & Fixes ✅
Root cause: press+release was instantaneous, Ctrl delay too short for Helldivers 2.

**Timing model:**
```
Ctrl DOWN → [ctrl_delay 150ms] → key DOWN → [key_hold 50ms] → key UP → [key_delay 80ms] → next key …
```

- `_VK_CODES` dict: `up=0x57 / down=0x53 / left=0x41 / right=0x44`
- `execute_stratagem(key_hold=0.05, key_delay=0.08, ctrl_delay=0.15, auto_click=False)`
- Diagnostic `[KEYPRESS]` log: `[KEYPRESS] 0.150s 'right' (VK=0x44) DOWN`
- Auto-click LMB option (auto-throw stratagem marker)
- `GET/POST /api/settings` extended with `key_hold_ms`, `auto_click`
- PWA: "Auto-throw after input" checkbox; settings toast feedback

### Phase 12 — Server Manager Bug Fixes ✅
Five bugs fixed in `desktop/server_manager.py`:

| # | Bug | Root cause | Fix |
|---|-----|-----------|-----|
| 1 | QR white square | `winfo_width()=1` before mainloop | Moved to `tk.PhotoImage.put()` (see below) |
| 2 | USB button no-op | No subprocess call on mode change | `_setup_usb()` with `messagebox` + `Popen` |
| 3 | Wrong WiFi IP (WSL/VPN) | `getaddrinfo(gethostname())` returned virtual NIC | UDP socket `connect("8.8.8.8",80)` → `getsockname()` |
| 4 | Start/Stop no log | No logging calls | `_log()` helper; both actions log to panel |
| 5 | Close with stopped server hung | `_on_close` always called `_stop()` | Check `is_alive()` first; destroy directly if not running |

---

## Post-Phase Features & Fixes

### QR Rendering — tk.PhotoImage.put() (final approach)
All Canvas-based approaches discarded. Final implementation:
- `QR_IMG_SIZE = 260` — fixed pixel size, no geometry queries
- `_draw_qr(url)`: `qr.modules` → scale factor → pixel rows as `"{#000000 #ffffff ...}"` strings → `img.put()`
- `self._qr_photo` holds reference (prevents GC collection)
- `_refresh_qr()`: updates URL StringVars, checks `server_running`, calls `_draw_qr()` only when server is alive
- QR not shown before first Start — displays "Press Start to show QR" placeholder
- White-bg `qr_frame` provides quiet zone
- On mode change while running: QR regenerated for new URL

### Console Logging
`_attach_log_handler()` adds both `TkLogHandler` (GUI) and `StreamHandler(sys.stdout)` (console). Logs appear in both simultaneously.

### ADB Auto-Install
- `PLATFORM_TOOLS_DIR = %LOCALAPPDATA%\StratagramLauncher\platform-tools`
- "Install ADB" button in Settings — disabled/green if adb already found
- `_install_adb()`: daemon thread; `urlretrieve` (~10 MB) with live `%` progress on button
- Extracts zip to parent dir; no admin rights required
- `_get_adb_path()`: local install first → `shutil.which("adb")`
- `_setup_usb()`: passes `ADB_PATH` env var to `setup_usb.bat`; warns if not found
- `setup_usb.bat`: uses `%ADB_PATH%` if set, else system `adb`

### Landscape Layout (S23 Ultra)
- `min-width: 0` on both flex children (required for shrink)
- Cards: `height: auto` + `overflow: hidden` (no fixed height overflow)
- D-pad area: `overflow: hidden`
- Timer row: `flex-shrink: 1` yields to cross
- `inset box-shadow` replaces `outline` for manual-active indicator (no viewport overflow)
- Cancel button moved out of `ldpad-topbar` to direct flex child of `loadout-dpad-area`

---

## Known Issues / Bugs Log

| Date | Issue | Fix |
|------|-------|-----|
| 2026-03-16 | `start_server*.bat` used `python server\app.py` (breaks relative imports) | Restored `python -m server.app` |
| 2026-03-16 | pynput sent raw chars → `KEYEVENTF_UNICODE`, unreliable in games | `KeyCode.from_vk()` → `WM_KEYDOWN` |
| 2026-03-17 | Loadouts lost when WiFi IP changes (localStorage is origin-scoped) | `GET/PUT /api/loadouts` server-side sync |
| 2026-03-17 | Stop button / window close hangs (threading deadlock on main thread) | `_stop()` runs shutdown in daemon thread |
| 2026-03-17 | `localhost:5000` fails (Windows 11 `localhost` → IPv6 `::1`) | Always use `127.0.0.1` explicitly |
| 2026-03-17 | QR white square (winfo_width=1, box_size=0) | `tk.PhotoImage.put()`, fixed `QR_IMG_SIZE` |
| 2026-03-17 | WiFi IP returned WSL/VPN NIC address | UDP socket route trick to 8.8.8.8 |
| 2026-03-17 | QR generated before Start (showed error immediately) | `server_running` check in `_refresh_qr()` |
| 2026-03-17 | Duplicate "Server started" log on each start | Removed duplicate from `ServerThread.run()` |
| 2026-03-17 | keys not registering in Helldivers 2 | key_hold=50ms, key_delay=80ms, ctrl_delay=150ms |
| 2026-03-17 | Landscape: cross overlapped slider, outline out of viewport | Cancel to direct child; inset box-shadow |
| 2026-03-17 | Landscape: cards/dpad overlapping on S23 Ultra | `min-width:0`, `height:auto`, dvh-based `--cell` |
| 2026-03-17 | USB button had no action | `_setup_usb()` with messagebox + Popen |
| 2026-03-17 | ADB not installed on clean machine | "Install ADB" button — urllib download, no admin |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve PWA |
| GET | `/api/health` | Health check |
| GET | `/api/stratagems` | All stratagems + categories + icon_repo |
| POST | `/api/execute` | `{id}` → execute stratagem key sequence |
| GET | `/api/settings` | `key_delay_ms`, `ctrl_hold_delay_ms`, `key_hold_ms`, `auto_click` |
| POST | `/api/settings` | Update any settings field |
| POST | `/api/manual/start` | Hold Ctrl, start manual mode |
| POST | `/api/manual/key` | `{direction}` → press one key while Ctrl held |
| POST | `/api/manual/stop` | Release Ctrl, end manual mode |
| GET | `/api/manual/status` | `{active: bool}` |
| GET | `/api/loadouts` | Return saved loadouts array |
| PUT | `/api/loadouts` | Replace + persist loadouts array |

---

## Running the Project

**Primary — Desktop GUI (.exe):**
```
dist\Stratagem Launcher.exe   ← double-click
```
Or build first (once): `scripts\build_exe.bat`

**Dev — console server:**
```powershell
.venv_win\Scripts\activate
scripts\start_server_wifi.bat
```

**WSL — tests:**
```fish
source .venv/bin/activate.fish
pytest tests/   # 82 tests, all green
```
