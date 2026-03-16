# Stratagem Launcher

Mobile remote control for Helldivers 2 stratagems.

**Tap a stratagem on your phone → keys are pressed on your PC → stratagem activates in-game.**

```
┌──────────────────┐     HTTP (WiFi / USB)     ┌──────────────────┐   pynput   ┌───────────────┐
│  Phone (Chrome)  │ ◄────────────────────────► │  Python Server   │ ─────────► │  Helldivers 2 │
│  PWA             │                            │  Flask + pynput  │            │  (focused)    │
└──────────────────┘                            └──────────────────┘            └───────────────┘
```

---

## Requirements

- **PC**: Windows 10/11 with Python 3.10+
- **Phone**: Chrome on Android (or any modern mobile browser)
- Same WiFi network — or USB cable with ADB

---

## Setup (Windows — one time)

Open **PowerShell** or **CMD** in the project folder:

```powershell
cd C:\path\to\stratagem_launcher

# Create Windows virtual environment
python -m venv .venv_win
.venv_win\Scripts\activate

# Install dependencies (includes pynput for key simulation)
pip install -r requirements.txt
```

---

## Running the Server

### WiFi mode (phone on same network)

Double-click **`scripts\start_server_wifi.bat`** — or run in PowerShell:

```powershell
.venv_win\Scripts\activate
python -m server.app --host 0.0.0.0
```

The server prints your local IP addresses. Open `http://192.168.x.x:5000` on your phone.

### Localhost only (for development/testing)

```powershell
scripts\start_server.bat
```

---

## Connecting Your Phone

### Option A — WiFi (easiest)

1. Make sure phone and PC are on the **same WiFi network**
2. Start server with `start_server_wifi.bat`
3. Open `http://<PC-IP>:5000` in Chrome on your phone
4. Tap **⋮ → Add to Home Screen** to install as PWA

### Option B — USB (no WiFi needed)

1. Enable **USB Debugging** on your phone
   *(Settings → Developer Options → USB Debugging)*
2. Connect phone to PC via USB
3. Run `scripts\setup_usb.bat`
4. Open `http://localhost:5000` in Chrome on your phone

---

## Usage

1. **Start server** on your PC (see above)
2. **Open the PWA** on your phone
3. **Alt-Tab** to Helldivers 2 on your PC — make sure the game window is focused
4. **Tap a stratagem** on your phone:
   - The server holds Ctrl, types the key sequence, releases Ctrl
   - Stratagem activates in-game
5. Stratagems with a **yellow `?`** badge have unverified key codes — test in-game before relying on them

### Settings (⚙ button)

| Setting | Description |
|---------|-------------|
| Server IP | Custom IP if app can't auto-connect (e.g. `192.168.1.5:5000`) |
| Key delay | Milliseconds between key presses. Default 50ms. Increase if inputs are dropped. |
| Test Connection | Verify the phone can reach the server |

---

## Project Structure

```
stratagem_launcher/
├── server/          # Python Flask server
│   ├── app.py       # Routes and application factory
│   ├── keypress.py  # pynput key simulation
│   ├── stratagems.py# JSON loader
│   └── config.py    # Settings dataclass
├── web/             # PWA frontend (served by Flask)
│   ├── index.html
│   ├── app.js
│   └── style.css
├── data/
│   └── stratagems.json  # Stratagem database (single source of truth)
├── scripts/
│   ├── start_server.bat       # Start (localhost)
│   ├── start_server_wifi.bat  # Start (WiFi, 0.0.0.0)
│   └── setup_usb.bat          # ADB port forwarding
└── tests/           # pytest test suite
```

---

## Adding / Editing Stratagems

Edit `data/stratagems.json`. Each entry:

```json
{
  "id": "orbital_precision_strike",
  "name": "Orbital Precision Strike",
  "category": "orbital",
  "keys": ["right", "right", "up"],
  "icon": "Bridge/Orbital Precision Strike.svg",
  "cooldown": 90,
  "verified": true
}
```

| Field | Description |
|-------|-------------|
| `id` | Unique snake_case identifier |
| `keys` | Directions after holding Ctrl: `"up"` `"down"` `"left"` `"right"` |
| `icon` | Path relative to `icon_repo` (GitHub SVGs) |
| `cooldown` | Seconds — used for the UI countdown timer |
| `verified` | `false` = untested key code, shows `?` badge |

---

## Troubleshooting

**Keys not registering in game**
- Make sure Helldivers 2 window is **focused** when you tap
- Try increasing key delay in Settings (80–100ms)
- Server must run on **Windows** (not WSL) — pynput needs native Windows

**Phone can't reach server**
- Check firewall: allow Python on port 5000 (`Windows Defender Firewall → Allow an app`)
- Try USB mode as fallback
- Verify IP in Settings matches the one printed at server startup

**"Stratagem not found" error**
- Restart server — stratagems.json is loaded once at startup

---

## Development (WSL)

If you develop in WSL (Linux), use `requirements-dev.txt` (no pynput):

```fish
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements-dev.txt

# Run tests (pynput is mocked)
pytest tests/
```

Run the actual server **on Windows** using the `.bat` files above — pynput cannot inject keys into Windows games from WSL.

---

## License

MIT
