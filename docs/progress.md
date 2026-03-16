# Progress Tracker — Stratagem Launcher

> Last updated: 2026-03-16

## Phase 1: Project Skeleton
- [x] Initialize project structure (directories, files)
- [x] Create .venv, requirements.txt, .gitignore
- [x] Validate stratagems.json loads correctly (58 stratagems, 6 categories — OK)
- [x] Create docs/ templates
- [x] First git commit

## Phase 2: Server Core
- [ ] config.py — settings dataclass with CLI overrides
- [ ] stratagems.py — load, validate, query stratagems
- [ ] keypress.py — pynput key simulation with Ctrl+sequence
- [ ] app.py — Flask app with /api/execute, /api/stratagems, /api/health
- [ ] tests/ — pytest for all server modules
- [ ] Manual test: POST request → keys appear in Notepad

## Phase 3: PWA Minimal
- [ ] index.html — basic page with 5 stratagem buttons
- [ ] app.js — fetch /api/stratagems, render buttons, POST on tap
- [ ] style.css — dark theme, mobile-optimized grid
- [ ] Flask serves web/ as static files
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
