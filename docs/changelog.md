# Changelog — Stratagem Launcher

## Format
Entries added by Claude Code after each completed task.

---

## [Unreleased]

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
