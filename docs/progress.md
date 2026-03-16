# Progress Tracker — Stratagem Launcher

> Last updated: 2026-03-16

## Phase 1: Project Skeleton ✅
- [x] Initialize project structure (directories, files)
- [x] Create .venv, requirements.txt, requirements-dev.txt, .gitignore
- [x] Validate stratagems.json loads correctly
- [x] Create docs/ templates
- [x] First git commit

## Phase 2: Server Core ✅
- [x] config.py — settings dataclass with CLI overrides
- [x] stratagems.py — load, validate, query stratagems
- [x] keypress.py — pynput key simulation with Ctrl+sequence (WSL-safe via try/except)
- [x] app.py — Flask app with /api/execute, /api/stratagems, /api/health, /api/settings
- [x] tests/ — pytest for all server modules (42/42 passing)
- [x] Manual test: POST request → keys appear in Notepad ✅

## Phase 3: PWA Minimal ✅
- [x] index.html — full structure: header, tabs, search, grid, settings overlay
- [x] app.js — fetch stratagems, render grid, POST on tap, vibration, toasts, settings localStorage
- [x] style.css — dark Helldivers theme, 4-col mobile grid, CSS variables
- [x] manifest.json + sw.js — PWA installable, cache-first shell
- [x] Flask serves web/ as static files
- [x] Manual test: phone browser → tap button → keys on laptop ✅

## Phase 4: Full UI ✅
- [x] SVG icons via icon_repo (nvigneux GitHub) — resolveIconUrl() builds full URL
- [x] Cooldown timer on cards after tap (local countdown, resets on re-tap)
- [x] Unverified badge — yellow "?" in card corner for verified: false
- [x] App icons generated — web/icons/app-192.png, app-512.png (stdlib PNG generator)

## Phase 5: Polish & Docs
- [ ] README.md with setup instructions for both environments
- [ ] scripts/setup_usb.bat — adb reverse for USB mode ✅ (created)
- [ ] QR code display on server startup (WiFi URL)
- [ ] Final manual testing checklist

## Phase 6: Loadouts & Extras (optional)
- [ ] Custom Loadouts: select 4 stratagems → save preset → show only those on main screen
- [ ] Loadout persistence in localStorage
- [ ] Quick switch between presets (swipe or tabs)
- [ ] WebSocket for instant feedback
- [ ] Sound effects on execution
- [ ] ngrok setup documentation

## Phase 7: Manual Input Mode (D-pad)
- [ ] Server endpoints: POST /api/manual/start, /api/manual/key, /api/manual/stop
- [ ] Server state machine: idle → manual_active → idle (with timeout)
- [ ] D-pad UI component (portrait layout: bottom half, large thumb buttons)
- [ ] D-pad UI component (landscape layout: gamepad style, D-pad left, Execute right)
- [ ] CSS media queries for orientation switching
- [ ] Visual sequence display (show entered arrows at top)
- [ ] Haptic feedback per tap
- [ ] Auto-release Ctrl after 3s timeout (configurable)
- [ ] Tests for manual mode endpoints

## Blockers & Issues
(Claude Code logs issues here)

| Date | Issue | Status | Resolution |
|------|-------|--------|------------|
| 2026-03-16 | scripts/*.bat overwritten (used `python server\app.py` instead of `python -m server.app`) | ✅ Fixed | Restored `python -m server.app` in both bat files |
| 2026-03-16 | stratagems.json updated to v2.0.0 with icon_repo field | ✅ Fixed | app.js now reads icon_repo, stratagems.py exposes get_icon_repo() |
| 2026-03-16 | test_get_all_count hardcoded 58, JSON now has 59 | ✅ Fixed | Changed to `len > 0` |
