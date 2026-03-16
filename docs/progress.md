# Progress Tracker — Stratagem Launcher

> Last updated: (Claude Code updates this)

## Phase 1: Project Skeleton
- [ ] Initialize project structure (directories, files)
- [ ] Create .venv, requirements.txt, .gitignore
- [ ] Validate stratagems.json loads correctly
- [ ] Create docs/ templates
- [ ] First git commit

## Phase 2: Server Core
- [x] config.py — settings dataclass with CLI overrides
- [x] stratagems.py — load, validate, query stratagems
- [x] keypress.py — pynput key simulation with Ctrl+sequence (importable from WSL via try/except)
- [x] app.py — Flask app with /api/execute, /api/stratagems, /api/health, /api/settings
- [x] tests/ — pytest for all server modules (42/42 passed)
- [ ] Manual test: POST request → keys appear in Notepad (requires Windows + .venv_win)

## Phase 3: PWA Minimal
- [x] index.html — full structure: header, tabs, search, grid, settings panel
- [x] app.js — fetch stratagems, render grid, POST on tap, toast feedback, settings localStorage
- [x] style.css — dark Helldivers theme, 4-col mobile grid, CSS variables
- [x] manifest.json + sw.js — PWA installable, cache-first shell
- [x] Flask serves web/ as static files (already in app.py)
- [ ] Manual test: phone browser → tap button → keys on laptop

## Phase 4: Full UI
- [ ] All stratagems rendered from JSON
- [ ] Category tabs with filtering
- [ ] Search bar
- [ ] Visual feedback on tap (flash, vibrate)
- [ ] manifest.json + sw.js (PWA installable)
- [ ] Connection status indicator
- [ ] Settings panel (IP, delay, test connection)

## Phase 5: Polish & Docs
- [ ] SVG icons for stratagems (placeholder arrows + category color)
- [ ] App icons (192px, 512px)
- [ ] README.md with setup instructions
- [ ] scripts/setup_usb.bat
- [ ] scripts/start.sh
- [ ] QR code generation for WiFi URL
- [ ] Final testing checklist

## Phase 6: Extras (optional, after MVP)
- [ ] WebSocket for instant feedback
- [ ] Favorites / custom loadouts
- [ ] Sound effects on execution
- [ ] ngrok setup documentation
- [ ] Stratagem cooldown timers on UI

## Blockers & Issues
(Claude Code logs issues here)

| Date | Issue | Status | Resolution |
|------|-------|--------|------------|
