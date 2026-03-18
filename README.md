# Stratagem Launcher

Mobile remote control for Helldivers 2 stratagems.

**Tap a stratagem on your phone → keys are pressed on your PC → stratagem activates in-game.**

```
┌──────────────────┐   HTTP (WiFi / USB)   ┌──────────────────────┐   pynput   ┌───────────────┐
│  Phone (Chrome)  │ ◄───────────────────► │  Stratagem Launcher  │ ─────────► │  Helldivers 2 │
│  PWA             │                       │  (.exe or Python)    │            │  (focused)    │
└──────────────────┘                       └──────────────────────┘            └───────────────┘
```

---

## Requirements

- **PC**: Windows 10/11
- **Phone**: Chrome on Android (or any modern mobile browser)
- Same WiFi network — or USB cable with ADB

---

## Quick Start — Desktop App (.exe)

### 1. Build the .exe (one time)

You need Python 3.10+ and the Windows venv set up first:

```powershell
cd C:\path\to\stratagem_launcher

python -m venv .venv_win
.venv_win\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-build.txt

scripts\build_exe.bat
```

This creates `dist\Stratagem Launcher.exe`. Copy it anywhere — it is fully self-contained.

### 2. Launch

Double-click **`Stratagem Launcher.exe`**.

The Server Manager window opens:


<img width="1280" height="971" alt="image" src="https://github.com/user-attachments/assets/07a89723-3fd7-4b1b-a25c-100cca21e636" />


### 3. Start the server

Click **▶ Start** (WiFi mode selected by default).

- The status dot turns green: **RUNNING**
- A QR code appears in the left panel

### 4. Connect your phone

**Option A — WiFi (easiest):**
1. Make sure phone and PC are on the **same WiFi network**
2. Scan the QR code with your phone's camera — or open the URL shown below the QR
3. Tap **⋮ → Add to Home Screen** in Chrome to install as a PWA

**Option B — USB (no WiFi needed):**
1. Select **USB (ADB)** mode in Settings
2. If ADB is not installed, click **Install ADB** — it downloads automatically, no admin rights needed
3. Connect phone via USB and enable **USB Debugging** *(Settings → Developer Options)*
4. Click OK when prompted — ADB port forwarding runs automatically
5. Open `http://127.0.0.1:5000` on your phone

### 5. Play

1. Alt-Tab to Helldivers 2 — make sure the game window is **focused**
2. Tap a stratagem on your phone — it activates in-game

---

## Using the PWA

### All Stratagems view

Browse all stratagems by category. Tap any card to execute.
Use the search bar to filter by name.

### Loadouts

Create loadout tabs (up to 4 stratagems each) for quick in-game access:

1. Tap **＋** to add a new loadout
2. Tap **✎** to edit — select up to 4 stratagems
3. Tap the loadout tab to switch to loadout view
4. In loadout view: 4 large cards + embedded D-pad on screen at once

### D-pad (Manual Input)

For stratagems not in your loadout, use manual D-pad input:

- **All view**: tap **✛** (bottom right) → D-pad overlay appears
- **Loadout view**: D-pad is embedded on the right side of the screen
- Swipe the D-pad area to enter directions
- Auto-release timer (1–5s, adjustable) — Ctrl releases automatically after inactivity
- Yellow outline = Ctrl is currently held

### PWA Settings (⚙)

| Setting | Default | Description |
|---------|---------|-------------|
| Server IP | auto | Custom IP if auto-connect fails (e.g. `192.168.1.5:5000`) |
| Key delay | 50 ms | Delay between key presses. Increase to 80–100ms if inputs drop |
| Cooldown reduction | 0% | Ship module upgrades (0–50%) |
| Show cooldowns | on | Cooldown timer on each card |
| Auto-throw after input | off | LMB click after sequence (auto-throw marker) |

---

## Troubleshooting

**Keys not registering in game**
- Make sure Helldivers 2 window is **focused** when you tap
- Try increasing key delay to 80–100ms in ⚙ Settings
- Server must run on **Windows** (not WSL) — pynput needs native Windows

**Phone can't reach server**
- Check Windows Firewall: allow Python/the exe on port 5000
- Try USB mode as a fallback
- Verify the IP in PWA Settings matches what the Server Manager shows

**QR code not appearing**
- Click ▶ Start first — QR is only generated once the server is running
- If it shows "qrcode not installed": activate `.venv_win` and run `pip install qrcode`

**Stratagems with `?` badge**
- Key code unverified — test in-game before relying on it in a mission

---

## Console Launch (Advanced / Development)

If you prefer running without the GUI, or are developing:

```powershell
# WiFi mode
.venv_win\Scripts\activate
scripts\start_server_wifi.bat

# Localhost only
scripts\start_server.bat

# Custom options
python -m server.app --host 0.0.0.0 --port 5000
```

---

## Development (WSL)

```fish
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements-dev.txt

# Run tests (pynput mocked)
pytest tests/   # 82 tests
```

Run the server on **Windows** for real key injection — pynput cannot inject keys into Windows games from WSL.

---

## Stratagem Database

Edit `data/stratagems.json` to add or correct stratagems:

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
| `keys` | Directions after Ctrl: `"up"` `"down"` `"left"` `"right"` |
| `cooldown` | Seconds — drives the UI countdown timer |
| `verified` | `false` = untested, shows `?` badge |

---

## License

MIT
