# Manual Testing Checklist — Stratagem Launcher

Run through this checklist before each release / after major changes.

---

## Server (Windows)

- [ ] `scripts\start_server.bat` starts without errors
- [ ] Server prints `Loaded N stratagems`
- [ ] `GET http://localhost:5000/api/health` returns `{"status": "ok"}`
- [ ] `GET http://localhost:5000/api/stratagems` returns full list
- [ ] `POST http://localhost:5000/api/execute` `{"id": "reinforce"}` → keys press in Notepad
- [ ] Server handles unknown ID with 404
- [ ] Server handles concurrent request with 503 busy

## Server — WiFi mode

- [ ] `scripts\start_server_wifi.bat` prints local IP addresses
- [ ] QR code appears in terminal (requires `pip install qrcode`)
- [ ] Phone can reach server at printed IP

## PWA — Basic

- [ ] Page loads on phone Chrome
- [ ] All stratagems appear in grid
- [ ] Category tabs filter correctly
- [ ] Search bar filters by name
- [ ] Settings panel opens and closes

## PWA — Execute

- [ ] Tap stratagem → flash animation plays
- [ ] Tap stratagem → phone vibrates (Android)
- [ ] Tap stratagem → correct keys fire in Notepad
- [ ] Tap during cooldown → blocked with toast
- [ ] Cooldown countdown visible on card
- [ ] Cooldown ends → card becomes tappable again

## PWA — Visual

- [ ] Unverified stratagems show `?` badge
- [ ] Stratagem icons load from GitHub (online) or show letter fallback (offline)
- [ ] Connection status dot shows green when server is up
- [ ] Connection status dot shows red when server is unreachable

## PWA — Settings

- [ ] Key delay slider updates server via POST /api/settings
- [ ] Custom IP saved to localStorage, persists after reload
- [ ] "Test Connection" button shows result toast
- [ ] Settings persist after closing and reopening PWA

## PWA — Install

- [ ] Chrome shows "Add to Home Screen" prompt
- [ ] PWA installs and launches in standalone mode (no browser chrome)
- [ ] App icon shows on home screen

## USB mode

- [ ] `scripts\setup_usb.bat` runs `adb reverse` successfully
- [ ] Phone opens `http://localhost:5000` and page loads
- [ ] Execute works over USB tunnel

## WSL (development)

- [ ] `pytest tests/` → all tests pass
- [ ] `python3 scripts/validate_json.py` → OK
- [ ] `python3 scripts/generate_icons.py` → generates icons without errors
