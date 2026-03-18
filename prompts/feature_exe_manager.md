# Phase 8: Desktop EXE — Server Manager

## Контекст
Сейчас сервер запускается через `scripts\start_server_wifi.bat`. Нужен десктопный GUI — один .exe, двойной клик → работает. Без PowerShell, без терминала.

**Текущее состояние проекта:**
- 7 фаз завершены, 67 тестов проходят
- Сервер: `python -m server.app` (Flask, factory pattern)
- keypress.py: `KeyCode.from_vk()` (VK codes, WM_KEYDOWN)
- QR-код уже генерируется при `--host 0.0.0.0` (в start_server_wifi.bat)
- `requirements.txt` уже содержит `qrcode[pil]` (если добавлено в Phase 5)

## Стек
- **Python** + **tkinter** (встроен в Python, ноль зависимостей)
- **PyInstaller** для сборки в .exe
- QR: библиотека `qrcode` (уже может быть в requirements.txt — проверь)

## Новые файлы
```
desktop/
├── server_manager.py      # главный GUI + server thread
└── __init__.py
scripts/
└── build_exe.bat          # PyInstaller build script
```

## GUI Layout (tkinter)

```
┌──────────────────────────────────────────────────────────────┐
│  Stratagem Launcher — Server Manager               [—][□][×] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Server Status:  ● STOPPED                                   │
│                                                              │
│  ┌─── Connection ────────────────────────────────────────┐   │
│  │  WiFi:  http://192.168.1.42:5000       [ Copy ]       │   │
│  │  USB:   http://localhost:5000          [ Copy ]       │   │
│  │  Port:  [5000]                                        │   │
│  │                                                       │   │
│  │  ┌──────────┐                                         │   │
│  │  │ QR CODE  │  ← Сканируй телефоном                   │   │
│  │  │          │                                         │   │
│  │  └──────────┘                                         │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  Mode: (●) WiFi (0.0.0.0)  ( ) Localhost only                │
│  Key delay: [====●=========] 50ms                            │
│                                                              │
│  [ ▶ Start ]  [ ■ Stop ]  [ ↻ Restart ]                     │
│                                                              │
│  ┌─── Log ───────────────────────────────────────────────┐   │
│  │ [12:34:56] Server started on 0.0.0.0:5000             │   │
│  │ [12:34:58] POST /api/execute orbital_precision_strike  │   │
│  │ [12:35:01] Keys: Ctrl+[right,right,up] ✓              │   │
│  │ [12:35:03] POST /api/manual/start                     │   │
│  │ ...                                         [Clear]   │   │
│  └───────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Компоненты

### 1. Server Control
- Flask сервер запускается в **daemon thread** (`threading.Thread(daemon=True)`)
- Используй существующий `server.app.create_app()` (или как он называется — проверь `app.py`)
- `werkzeug.serving.make_server()` для controllable shutdown (не `app.run()` — его нельзя остановить)
- Кнопки:
  - **Start**: создать server thread, запустить. Disable Start, enable Stop/Restart
  - **Stop**: вызвать `server.shutdown()`, join thread. Enable Start, disable Stop/Restart
  - **Restart**: Stop + Start
- Индикатор: `●` красный = STOPPED, зелёный = RUNNING

### 2. Connection Info
- Автодетект LAN IP: `socket.gethostbyname(socket.gethostname())` или перебор `socket.getaddrinfo()`
- WiFi URL и localhost URL — текстовые лейблы
- Кнопки [Copy] — `root.clipboard_clear(); root.clipboard_append(url)`
- Поле ввода порта — по умолчанию 5000, применяется при следующем Start
- **QR-код**: `qrcode.make(wifi_url)` → PIL Image → `ImageTk.PhotoImage` → tkinter Label
- QR обновляется при смене порта или mode

### 3. Log Viewer
- `tkinter.scrolledtext.ScrolledText`, readonly
- Custom `logging.Handler` подкласс: перехватывает Flask/werkzeug логи → `widget.insert(END, ...)`
- Автоскролл вниз (`widget.see(END)`)
- Кнопка [Clear] — очистка текста
- Формат: `[HH:MM:SS] message`
- **Важно**: вставка текста в tkinter ТОЛЬКО из main thread. Использовать `root.after()` или `queue.Queue`

### 4. Settings
- Radio buttons: WiFi mode (`0.0.0.0`) / Localhost only (`127.0.0.1`)
- Slider: Key delay (20ms — 200ms) — при изменении обновляет `config` объект сервера
- Эти настройки должны влиять на работающий сервер в реальном времени (config — shared object)

### 5. Сборка в .exe

`scripts/build_exe.bat`:
```bat
@echo off
echo Building Stratagem Launcher...
cd /d "%~dp0\.."

if not exist ".venv_win\Scripts\activate.bat" (
    echo [ERROR] Windows venv not found.
    pause
    exit /b 1
)

call .venv_win\Scripts\activate.bat
pip install pyinstaller

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "Stratagem Launcher" ^
    --add-data "data;data" ^
    --add-data "web;web" ^
    --add-data "server;server" ^
    desktop\server_manager.py

echo.
echo Built: dist\Stratagem Launcher.exe
echo Copy it anywhere and run — data/ and web/ are bundled inside.
pause
```

### 6. PyInstaller: доступ к bundled data
Внутри `server_manager.py` нужен helper для путей:
```python
import sys, os

def resource_path(relative_path: str) -> str:
    """Get path to resource, works for dev and for PyInstaller bundle."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)
```
Передать этот base_path в Flask app при создании, чтобы он нашёл `data/stratagems.json` и `web/`.

## Важные ограничения
- **tkinter mainloop** занимает main thread. Flask — только в daemon thread
- **Logging в tkinter** — thread-safe вставка через `root.after(0, callback)` или `Queue`
- **При закрытии окна** (`WM_DELETE_WINDOW`): остановить сервер, потом `root.destroy()`
- **Не ломать существующую архитектуру**: `server/app.py`, `server/keypress.py` и т.д. должны работать и без GUI (из .bat). GUI — это обёртка, не замена
- **67 тестов должны проходить** после всех изменений

## Зависимости
Добавить в `requirements.txt` (если ещё нет):
```
qrcode[pil]>=7.0
pyinstaller>=6.0
```
`pyinstaller` нужен только для сборки, не для runtime. Можно вынести в отдельный `requirements-build.txt`.

## Progress tracking
Добавь в `docs/progress.md`:
```
## Phase 8: Desktop EXE — Server Manager
- [ ] desktop/server_manager.py — tkinter GUI skeleton (window, frames, widgets)
- [ ] Server thread management (start/stop/restart with werkzeug.make_server)
- [ ] Connection info panel (auto IP, copy buttons)
- [ ] QR code display (qrcode → PIL → ImageTk)
- [ ] Log viewer (ScrolledText + custom logging handler + thread-safe insert)
- [ ] Settings panel (mode radio, key delay slider)
- [ ] Resource path helper for PyInstaller bundling
- [ ] scripts/build_exe.bat
- [ ] Test: build .exe, run standalone, start server, connect from phone
- [ ] Verify: 67+ existing tests still pass
```

### Обнови docs/progress.md, docs/decisions.md (ADR для tkinter vs electron vs etc) и docs/changelog.md.
