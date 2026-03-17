# PROJECT_SPEC.md — Stratagem Launcher Technical Specification

## Overview

**Stratagem Launcher** — a mobile remote control for Helldivers 2 stratagems.

```
┌──────────────────┐     HTTP/WebSocket      ┌──────────────────┐     pynput      ┌──────────────┐
│  Samsung S23 Ultra│ ◄──── WiFi / USB ────► │  Python Server   │ ─────────────► │ Helldivers 2  │
│  Chrome PWA       │     (LAN / localhost)   │  Flask + pynput  │   key press     │ (focused)     │
└──────────────────┘                          └──────────────────┘                 └──────────────┘
```

The phone sends a stratagem ID via HTTP. The server holds Ctrl, types the directional keys (WASD mapped to arrows), releases Ctrl. The game registers the stratagem input.

## Game Mechanics: How Stratagems Work

1. Player holds **Ctrl** (opens stratagem input mode)
2. Player presses directional keys in sequence:
   - **W** = Up
   - **A** = Left  
   - **S** = Down
   - **D** = Right
3. Player releases **Ctrl** (stratagem activates)
4. Each stratagem has a unique sequence of 3-6 directional inputs

**Timing**: The game requires ~30-80ms between key presses. Too fast = inputs dropped. Too slow = feels laggy. Default: **50ms**, configurable via settings.

## API Design

### Endpoints

#### `GET /` 
Serve the PWA (index.html from web/ directory)

#### `GET /api/stratagems`
Return all stratagems from stratagems.json.
```json
{
  "stratagems": [...],
  "categories": ["orbital", "eagle", "support", "backpack", "defense", "mission"]
}
```

#### `POST /api/execute`
Execute a stratagem by ID.
```json
// Request
{ "id": "orbital_precision_strike" }

// Response 200
{ "status": "ok", "stratagem": "Orbital Precision Strike", "keys": ["right", "right", "up"] }

// Response 404
{ "status": "error", "message": "Stratagem not found: xyz" }

// Response 503 (if another stratagem is currently executing)
{ "status": "busy", "message": "Another stratagem is being executed" }
```

#### `GET /api/settings`
Return current server settings.
```json
{ "key_delay_ms": 50, "ctrl_hold_delay_ms": 30, "version": "1.0.0" }
```

#### `POST /api/settings`
Update settings at runtime.
```json
{ "key_delay_ms": 80 }
```

#### `GET /api/health`
Health check for connection testing.
```json
{ "status": "ok", "timestamp": 1234567890 }
```

### Manual Input Mode Endpoints (Phase 7)

#### `POST /api/manual/start`
Enter manual mode — server holds Ctrl down.
```json
// Response 200
{ "status": "manual_active", "timeout_ms": 3000 }

// Response 409 (already in manual mode or stratagem executing)
{ "status": "error", "message": "Already in manual mode" }
```

#### `POST /api/manual/key`
Send a single directional key press while in manual mode. Resets the auto-release timeout.
```json
// Request
{ "direction": "up" }

// Response 200
{ "status": "ok", "direction": "up", "sequence": ["up", "down", "right"] }

// Response 400
{ "status": "error", "message": "Not in manual mode. Call /api/manual/start first" }
```

#### `POST /api/manual/stop`
Exit manual mode — server releases Ctrl. Also called automatically on timeout.
```json
// Response 200
{ "status": "ok", "sequence": ["up", "down", "right", "left", "up"], "total_keys": 5 }
```

## Server Architecture

### app.py
- Flask application factory pattern
- CORS configured for local network
- Static file serving for PWA from `web/` directory
- Logging to console with timestamps
- Graceful error handling

### keypress.py
- `execute_stratagem(keys: list[str], key_delay: float, ctrl_delay: float) -> bool`
- Uses pynput.keyboard.Controller
- Thread-safe with a Lock (prevent concurrent executions)
- Sequence: press Ctrl → wait ctrl_delay → for each key: press→release→wait key_delay → release Ctrl
- Key mapping: {"up": "w", "down": "s", "left": "a", "right": "d"}
- Returns True on success, raises on error

### stratagems.py
- Load and validate stratagems.json at startup
- `get_all() -> list[dict]`
- `get_by_id(id: str) -> dict | None`
- `get_categories() -> list[str]`
- Validation: required fields, valid key values, unique IDs

### config.py
- Dataclass with defaults
- KEY_DELAY_MS = 50
- CTRL_HOLD_DELAY_MS = 30
- HOST = "127.0.0.1" (safe default)
- PORT = 5000
- DEBUG = False
- Overridable via CLI args or environment variables

## PWA Architecture

### index.html
- Single page, no routing
- Sections: header, category tabs, stratagem grid, settings panel
- Responsive grid: 4 columns on phone, auto-resize
- Dark theme matching Helldivers aesthetic (blacks, yellows, reds)

### app.js
Key responsibilities:
- Fetch stratagems from server on load
- Render grid of stratagem buttons with icons
- On tap: POST to /api/execute, show visual feedback (flash, vibrate)
- Settings panel: server IP input, delay slider, connection test button
- Store settings in localStorage
- Category filtering via tabs
- Search/filter by name

### style.css
Design system:
```css
:root {
  --bg-primary: #0a0a0a;
  --bg-secondary: #1a1a1a;
  --bg-card: #252525;
  --text-primary: #e0e0e0;
  --text-secondary: #888;
  --accent-yellow: #f5c518;    /* Helldivers yellow */
  --accent-red: #d32f2f;       /* danger/orbital */
  --accent-blue: #1e88e5;      /* eagle */
  --accent-green: #43a047;     /* support */
  --success: #4caf50;
  --error: #f44336;
  --border-radius: 12px;
  --font-main: 'Segoe UI', system-ui, sans-serif;
}
```

### manifest.json
```json
{
  "name": "Stratagem Launcher",
  "short_name": "Stratagems",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0a0a",
  "theme_color": "#f5c518",
  "orientation": "portrait",
  "icons": [
    { "src": "icons/app-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icons/app-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### sw.js (Service Worker)
- Cache app shell (HTML, CSS, JS, manifest)
- Cache stratagem icons on first load
- Network-first for API calls (always need live server for execution)
- Cache-first for static assets

## Connection Methods

### WiFi (Primary)
1. Server starts with `--host 0.0.0.0`
2. Server prints its LAN IP and QR code (URL)
3. Phone opens `http://192.168.x.x:5000` in Chrome
4. "Add to Home Screen" for PWA installation

### USB (via ADB)
1. Connect phone via USB, enable USB debugging
2. Run `adb reverse tcp:5000 tcp:5000`
3. Phone opens `http://localhost:5000`
4. Same experience, zero network dependency

### Internet (via ngrok, optional)
1. Install ngrok: `ngrok http 5000`
2. Use provided URL on phone
3. Document in README, not implement in code

## Data Format: stratagems.json

See `data/stratagems.json` for the full database. Structure:

```json
{
  "version": "1.0.0",
  "game_version": "1.5.x",
  "note": "Verify key codes in-game. Codes may change with patches.",
  "categories": {
    "orbital": { "name": "Orbital", "color": "#d32f2f", "icon": "🔴" },
    "eagle":   { "name": "Eagle",   "color": "#1e88e5", "icon": "🔵" },
    "support": { "name": "Support Weapons", "color": "#43a047", "icon": "🟢" },
    "backpack": { "name": "Backpack", "color": "#7b1fa2", "icon": "🟣" },
    "defense": { "name": "Defensive", "color": "#f57c00", "icon": "🟠" },
    "mission": { "name": "Mission",  "color": "#f5c518", "icon": "🟡" }
  },
  "stratagems": [
    {
      "id": "orbital_precision_strike",
      "name": "Orbital Precision Strike",
      "category": "orbital",
      "keys": ["right", "right", "up"],
      "icon": "icons/stratagems/orbital_precision_strike.svg",
      "cooldown": 90,
      "verified": true
    }
  ]
}
```

## Non-Functional Requirements

- **Latency**: < 100ms from tap to first key press on local WiFi
- **Reliability**: No dropped inputs. Lock prevents concurrent execution
- **Offline**: PWA shell works offline. API calls fail gracefully with clear error
- **Security**: Local-only by default. No authentication needed on home network
- **Compatibility**: Samsung S23 Ultra (Android 13+, Chrome 120+), Windows 10/11 laptop
- **Size**: Total app < 5MB (including icons)

## Testing Strategy

### Server Tests (pytest)
- `test_stratagems.py`: JSON loads, validates, no duplicates, all required fields
- `test_keypress.py`: Mock pynput, verify correct key sequence and timing
- `test_api.py`: Flask test client, all endpoints, error cases

### Manual Testing Checklist
- [ ] Server starts without errors
- [ ] Phone can reach server via WiFi
- [ ] PWA installs on home screen
- [ ] Tap button → keys register in Notepad (test without game first)
- [ ] All categories display correctly
- [ ] Settings persist after refresh
- [ ] USB connection works via ADB
- [ ] Concurrent taps don't crash server

## Future Enhancements (not in scope for MVP)
- WebSocket for real-time status feedback
- Custom Loadouts: pick 4 stratagems → save as preset → show only those 4 on main screen
- Manual Input Mode (D-pad): hold Ctrl, user taps arrows on phone, portrait + landscape layouts
- Haptic feedback patterns per category
- Stratagem cooldown timers
- Voice activation via Web Speech API
- Gamepad input support (trigger stratagems from controller)
