# Architecture Decisions — Stratagem Launcher

## Format
Each decision includes: date, context, decision, alternatives considered, rationale.

---

## ADR-001: PWA instead of native Android app
**Date**: Project start  
**Context**: Need a mobile interface on Samsung S23 Ultra to trigger stratagems.  
**Decision**: Use PWA (Progressive Web App) served by the Python server.  
**Alternatives**: React Native, Flutter, native Android (Kotlin), Electron.  
**Rationale**: Zero build tools, no Android Studio, no APK signing, no Play Store. Just open a URL in Chrome and "Add to Home Screen". Same codebase serves the UI and the API. The phone only needs to send HTTP requests — a browser does this perfectly.

## ADR-002: Flask + pynput for server
**Date**: Project start  
**Context**: Need HTTP server + keyboard simulation on Windows.  
**Decision**: Flask for HTTP, pynput for key simulation.  
**Alternatives**: FastAPI (async, but overkill), Django (too heavy), pyautogui (less control over timing).  
**Rationale**: Flask is minimal, well-documented, single-file friendly. pynput gives precise control over key press/release timing which is critical for stratagem input. Both install via pip with no native dependencies on Windows.

## ADR-003: REST over WebSocket for MVP
**Date**: Project start  
**Context**: Need to send stratagem commands from phone to server.  
**Decision**: Simple HTTP POST for MVP. WebSocket as optional Phase 6 enhancement.  
**Rationale**: Local WiFi HTTP round-trip is <10ms. The bottleneck is key simulation delay (50ms × N keys), not network. REST is simpler to implement, test, and debug. WebSocket adds value only for real-time feedback (execution progress), which isn't critical for MVP.

## ADR-004: stratagems.json as single source of truth
**Date**: Project start  
**Context**: Need a maintainable database of all stratagems with codes, names, icons.  
**Decision**: Single JSON file in data/ directory. Server loads at startup, PWA fetches via API.  
**Alternatives**: Python dict in code, SQLite database, YAML.  
**Rationale**: JSON is human-readable, easy to edit, version-controllable, and natively supported by both Python and JavaScript. No database overhead. Community can contribute corrections via PRs on GitHub.

## ADR-005: Dual-environment development (WSL + Windows)
**Date**: 2026-03-16  
**Context**: pynput cannot send keystrokes to a Windows application (Helldivers 2) when running inside WSL. The evdev library also fails to build in WSL due to missing kernel headers. Claude Code runs in WSL.  
**Decision**: Split environments — Claude Code develops/tests in WSL, server runs on Windows via PowerShell. Project files live on Windows filesystem (`/mnt/c/...`), accessible from both sides.  
**Alternatives**: (1) Move everything to Windows (Claude Code supports native Windows), (2) Use pyautogui instead of pynput.  
**Rationale**: Claude Code is already set up in WSL with fish shell. Moving to Windows would require reconfiguring. The dual-env approach requires no migration — just a separate PowerShell terminal for running the server. `keypress.py` uses try/except for pynput import so tests work in WSL with mocks. Two separate requirements files: `requirements.txt` (full, for Windows) and `requirements-dev.txt` (no pynput, for WSL).

## ADR-006: tkinter for desktop GUI (server manager)
**Date**: 2026-03-17
**Context**: Need a desktop GUI (.exe) so users can start/stop the server without a terminal.
**Decision**: Use Python's built-in tkinter + PyInstaller for the standalone .exe.
**Alternatives considered**:
- **Electron**: Cross-platform and polished, but requires Node.js toolchain, adds ~150MB to bundle, and is overkill for a single-machine utility.
- **PyQt6 / wxPython**: More capable GUI toolkits, but require separate pip installs and add size. PyQt6 has GPL/commercial licensing complexity.
- **Dear PyGui**: Modern and GPU-accelerated, but not bundled with Python — extra dependency with no benefit for this simple layout.
- **Web UI (Flask + browser window)**: Would reuse existing stack, but needs a browser and can't be a simple double-click .exe.
**Rationale**: tkinter is included with every Python installation — zero extra dependencies for the GUI itself. PyInstaller bundles everything (tkinter, Flask, pynput, the web/ frontend) into a single .exe. For a utility app with a modest layout (status, connection info, log), tkinter is entirely sufficient and keeps the install story trivial.

---

(Claude Code adds new decisions below)
