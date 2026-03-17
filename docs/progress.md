# Progress Tracker — Stratagem Launcher

> Last updated: 2026-03-17
> Tests: 72 passing

## Phase 1: Project Skeleton ✅
- [x] Directory structure, venv setup, requirements files
- [x] stratagems.json with 59 stratagems, 6 categories
- [x] scripts/validate_json.py — JSON integrity check
- [x] docs/ templates, CLAUDE.md, PROJECT_SPEC.md

## Phase 2: Server Core ✅
- [x] config.py — Config dataclass, CLI overrides
- [x] stratagems.py — JSON load/validate/query, get_icon_repo()
- [x] keypress.py — pynput via KeyCode.from_vk() (VK codes, WM_KEYDOWN)
- [x] app.py — Flask: /api/stratagems, /api/execute, /api/health, /api/settings
- [x] scripts/start_server.bat + start_server_wifi.bat
- [x] requirements-dev.txt (WSL, no pynput)
- [x] tests/ — 43 tests passing

## Phase 3: PWA Minimal ✅
- [x] index.html, app.js, style.css — full app shell
- [x] Dark Helldivers theme, 4-col mobile grid, CSS variables
- [x] manifest.json + sw.js (PWA installable)
- [x] Manual test: phone → tap → keys on laptop

## Phase 4: Full UI ✅
- [x] SVG icons via icon_repo (GitHub CDN), letter-SVG fallback offline
- [x] Category tabs with filtering
- [x] Search bar
- [x] Cooldown timer overlay per card (local countdown, blocks re-tap)
- [x] Unverified badge (?) for verified: false stratagems
- [x] App icons: app-192.png + app-512.png (scripts/generate_icons.py)

## Phase 5: Polish & Docs ✅
- [x] README.md — Windows + WSL setup, WiFi/USB, troubleshooting
- [x] QR code on server startup (--host 0.0.0.0)
- [x] scripts/setup_usb.bat — ADB port forwarding
- [x] docs/testing_checklist.md

## Phase 6: Loadouts ✅
- [x] Loadout bar (tabs + ＋ button), ✎ edit button per loadout
- [x] Edit mode: card selection overlay, X/4 counter, Save/Cancel
- [x] Loadout view: 2-col large-card grid (in-game optimised)
- [x] Persistence in localStorage (sl_loadouts)

## Phase 7: Manual D-pad Input ✅
- [x] Server: manual_start(), manual_key(), manual_stop(), is_manual_active()
- [x] State machine: idle → active → idle; threading.Timer auto-release 3s
- [x] API: POST /api/manual/start, /key, /stop; GET /api/manual/status
- [x] D-pad overlay: ✛ button → full-screen overlay
- [x] Portrait: cross at bottom, EXECUTE above
- [x] Landscape: cross left, EXECUTE right (@media orientation: landscape)
- [x] Visual sequence bar + haptic feedback (30ms)
- [x] 67 tests total, all passing

---

## Phase 8: Cooldown Modifier (frontend-only)
- [ ] Settings UI: range slider (0–50%) + input field, synced
- [ ] Recalculate cooldown timers using modifier
- [ ] Toggle: "Show cooldowns on cards" checkbox
- [ ] Display modified cooldown on cards (strikethrough old + new)
- [ ] localStorage persistence (sl_cooldown_modifier, sl_show_cooldowns)
- [ ] Works in loadout view too
- [ ] 67+ existing tests still pass

## Phase 9: Desktop EXE — Server Manager
- [ ] desktop/server_manager.py — tkinter GUI skeleton
- [ ] Server thread (werkzeug.make_server, start/stop/restart)
- [ ] Connection info panel (auto IP, copy buttons)
- [ ] QR code display (qrcode → PIL → ImageTk)
- [ ] Log viewer (ScrolledText + custom logging handler + thread-safe)
- [ ] Settings panel (mode radio, key delay slider)
- [ ] Resource path helper for PyInstaller bundling
- [ ] scripts/build_exe.bat
- [ ] Test: build .exe, run standalone, connect from phone
- [ ] 67+ existing tests still pass

## Phase 8: Ship Module Cooldown Modifier ✅
- [x] Cooldown reduction slider in Settings (0–50%, step 5) + synced number input
- [x] `getCooldownModifier()` / `isShowCooldowns()` / `getEffectiveCooldown()` helpers
- [x] Static cooldown label on cards (`~~100s~~ 75s` when modifier > 0)
- [x] Toggle: "Show cooldowns on cards" checkbox — hides labels + disables blocking
- [x] Live grid re-render on modifier/checkbox change; persisted to localStorage
- [x] 67 existing tests unchanged

## Phase 9: Desktop EXE — Server Manager ✅
- [x] desktop/server_manager.py — tkinter GUI (status, connection, QR, log, settings, controls)
- [x] ServerThread — werkzeug make_server() in daemon thread, clean shutdown()
- [x] TkLogHandler — thread-safe logging via queue.Queue + root.after() poll → ScrolledText
- [x] Connection panel — auto LAN IP, WiFi/USB URLs, Copy buttons, port input
- [x] QR code — qrcode → PIL → ImageTk (graceful fallback to URL text if PIL missing)
- [x] Settings — WiFi/Localhost/USB radio, key delay slider (live-updates shared Config)
- [x] resource_path() helper for PyInstaller _MEIPASS bundling
- [x] scripts/build_exe.bat — PyInstaller --onefile --windowed + --collect-all PIL/qrcode
- [x] requirements-build.txt (pyinstaller); requirements.txt: qrcode[pil]
- [x] GET/PUT /api/loadouts — server-side persistence (survives IP changes)
- [x] 72 tests passing (5 new TestLoadouts)
- [ ] Manual test: build .exe, run standalone, connect from phone (Windows only)

## Phase 9 Post-Release: GUI Bug Fixes ✅
- [x] DPI awareness (SetProcessDpiAwareness 2) — sharp text on 2K/4K
- [x] QR code render fixed — QRCode() + convert(RGB) + NEAREST, store ref on self
- [x] Venv check on startup — clear error message if venv not activated
- [x] Flexible PanedWindow layout — draggable splitter, log fills on resize, min 800×500

## Phase 10: Loadout D-pad Redesign ✅
- [x] Step 1 — Header: signal-bars SVG icon + color dot; removed "Connected" text and ✛ button
- [x] Step 2 — Loadout cards: 4×1 portrait grid, aspect-ratio 3/4, fill viewport on mobile; desktop 2-col override
- [x] Step 3 — Embedded D-pad in loadout view: ldpad-topbar, countdown bar, timer row, status, dpad-cross-wrap
- [x] Step 4 — Auto-start mechanics: first dpad tap auto-calls /api/manual/start; Execute button removed; auto-release from localStorage; countdown bar animation
- [x] Step 5 — Swipe-to-input: touchstart/touchend on #grid; <30px = tap (execute); ≥30px = swipe → dpadTap(dir); dashed border when manual-active
- [x] Step 6 — North marker (▴) on dpad-btn--up via CSS ::after; landscape loadout: 45vw cards (2×2) + 55vw dpad
- [x] Step 7 — FAB button (✛, fixed bottom-right, yellow circle) opens D-pad overlay; hidden in loadout view
- [x] 72 tests passing throughout all steps

## Blockers & Issues

| Date | Issue | Status | Resolution |
|------|-------|--------|------------|
| 2026-03-16 | start_server*.bat used wrong python command | ✅ Fixed | Restored `python -m server.app` |
| 2026-03-16 | stratagems.json v2 icon_repo ignored by old app.js | ✅ Fixed | Added resolveIconUrl() |
| 2026-03-16 | pynput raw chars unreliable in games | ✅ Fixed | KeyCode.from_vk() VK codes |
| 2026-03-17 | Loadouts lost on IP change (localStorage origin-scoped) | ✅ Fixed | GET/PUT /api/loadouts server-side |
| 2026-03-17 | Stop/Restart/Close hangs and crashes GUI | ✅ Fixed | shutdown() in daemon thread, callback |
| 2026-03-17 | localhost:5000 ERR_CONNECTION_REFUSED (Win11 localhost→::1) | ✅ Fixed | URLs always use 127.0.0.1 |
| 2026-03-17 | QR not shown in exe (PIL in try/except excluded by PyInstaller) | ✅ Fixed | --collect-all PIL/qrcode + convert(RGB) |
| 2026-03-17 | Blurry text on HiDPI / 2K / 4K | ✅ Fixed | SetProcessDpiAwareness(2) before Tk() |
| 2026-03-17 | Static layout, nothing stretches | ✅ Fixed | PanedWindow, stretch="always" on log |
