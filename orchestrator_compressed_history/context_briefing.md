# Stratagem Launcher — Context Briefing for New Chat

> Сжатая сводка проекта для продолжения в новом чате.
> Дата: 2026-03-17

## Кто я
Оркестратор проекта. Пишу промпты и инструкции для Claude Code (работает в WSL). Пользователь (V) — разработчик, Windows + WSL2/fish, Samsung Galaxy S23 Ultra для тестирования.

## Что за проект
Мобильный пульт для Helldivers 2 — PWA на телефоне отправляет HTTP-запросы → Python/Flask сервер на ноутбуке → pynput нажимает клавиши в игре.

## Стек
- Server: Python 3.10+, Flask, pynput, flask-cors (Windows only — pynput не работает в WSL/Docker)
- Frontend: Vanilla HTML/CSS/JS (PWA), zero npm
- Desktop GUI: tkinter + PyInstaller → .exe
- Icons: SVG из github.com/nvigneux/Helldivers-2-Stratagems-icons-svg (raw.githubusercontent CDN)
- Data: data/stratagems.json (59 стратагем, 6 категорий)

## Два окружения (КРИТИЧНО)
- **WSL2 (Ubuntu, fish)**: Claude Code, git, pytest, разработка
- **Windows (PowerShell)**: запуск сервера, pynput → клавиши → Helldivers 2
- Файлы общие: `/mnt/c/Users/arsup/Desktop/claude_playground/stratagem_launcher`
- WSL venv: `.venv/` (requirements-dev.txt, без pynput)
- Windows venv: `.venv_win/` (requirements.txt, с pynput)

## GitHub
Репо: `git@github.com:ArtiyPoltavchenko/<имя-репо>.git` (SSH ключ настроен)

## Завершённые фазы (1–9)
1. Project Skeleton
2. Server Core (Flask, pynput KeyCode.from_vk VK codes, config)
3. PWA Minimal
4. Full UI (icons, cooldown timers, categories, search)
5. Polish (README, QR, ADB scripts)
6. Loadouts (4 stratagems, tabs, localStorage + server-side /api/loadouts)
7. Manual D-pad (Ctrl hold → arrow taps → auto-release timeout)
8. Cooldown Modifier (slider 0-50%, frontend-only)
9. Desktop EXE (tkinter GUI, PyInstaller, start/stop/restart, log viewer)

**72+ тестов**, все проходят.

## Текущие баги (активные)

### Desktop GUI (server_manager.py):
1. **QR код не рендерится** — Canvas рисует белый фон, модули не появляются. Используется qrcode + tk.Canvas (без PIL). Вероятно canvas size = 1px до первого рендера, box=0
2. **WiFi IP неверный** — метод определения LAN IP возвращает не тот адрес. Нужен socket-метод (connect to 8.8.8.8, getsockname)
3. **USB кнопка** — не запускает scripts\setup_usb.bat. Нужен subprocess.Popen + messagebox
4. **Stop** — нет лога в консоль при остановке
5. **Закрытие окна** — сервер не останавливается. WM_DELETE_WINDOW → _stop(callback=destroy)

### Keypress (игра):
6. **WASD проходят не все** — Ctrl зажимается, но клавиши пропускаются. Нужен key_hold_ms (40-50ms удержания нажатой) + пауза после release. Текущие дефолты слишком быстрые
7. **Auto-click LMB** — нужен опциональный клик после последовательности (чекбокс в настройках)

### PWA:
8. **Manual mode sequence не очищается** после timeout — клиентский таймер не сбрасывает UI
9. **Key delay slider** — непонятно применяется ли, нет фидбэка (toast)
10. **Landscape loadout layout** — D-pad сжат, ползунок наезжает на стрелки

## Запланированные фичи (промпты готовы в prompts/)
- `prompts/feature_cooldowns.md` — Phase 8 (уже сделан)
- `prompts/feature_exe_manager.md` — Phase 9 (уже сделан)
- `prompts/redesign_loadout_dpad.md` — Loadout + D-pad объединение, свайпы, адаптивные карточки
- `prompts/bugfix_gui.md` — DPI fix, QR canvas, flexible layout (PanedWindow)
- `prompts/bugfix_qr_canvas.md` — QR через Canvas rectangles без PIL
- `prompts/debug_keypress.md` — timing fix, key_hold_ms, auto-click LMB

## Ключевые архитектурные решения
- PWA вместо native Android (zero build tools)
- Flask + pynput (Windows only)
- REST для MVP, WebSocket — future
- stratagems.json = единственный источник правды
- keypress.py: KeyCode.from_vk(0x57) — VK коды, не символы (WM_KEYDOWN)
- Desktop GUI: tkinter (встроен в Python, zero deps) + PyInstaller
- QR: qrcode + tk.Canvas (НЕ PIL — не работает стабильно)

## Файловая структура (актуальная)
```
stratagem_launcher/
├── CLAUDE.md, PROJECT_SPEC.md, orchestrator_report.md, README.md, INITIAL_PROMPT.md
├── requirements.txt / requirements-dev.txt / requirements-build.txt
├── server/ (app.py, keypress.py, stratagems.py, config.py)
├── data/ (stratagems.json, loadouts.json)
├── web/ (index.html, app.js, style.css, manifest.json, sw.js, icons/)
├── desktop/ (server_manager.py)
├── scripts/ (start_server.bat, start_server_wifi.bat, setup_usb.bat, build_exe.bat, ...)
├── tests/ (test_stratagems.py, test_keypress.py, test_api.py)
├── prompts/ (feature_*.md, bugfix_*.md, redesign_*.md, debug_*.md)
└── docs/ (progress.md, changelog.md, decisions.md, testing_checklist.md)
```

## API Reference
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Serve PWA |
| GET/POST | /api/settings | Key delays, auto_click |
| GET | /api/stratagems | All stratagems + icon_repo |
| POST | /api/execute | {id} → key sequence |
| POST | /api/manual/start | Hold Ctrl |
| POST | /api/manual/key | {direction} → one key |
| POST | /api/manual/stop | Release Ctrl |
| GET | /api/manual/status | {active: bool} |
| GET/PUT | /api/loadouts | Server-side loadout persistence |
| GET | /api/health | Health check |

## Как работать с Claude Code
- Промпты лежат в `prompts/` — говоришь ему "Прочитай prompts/xxx.md и реализуй"
- Он читает CLAUDE.md при старте (правила, workflow)
- Обновляет docs/progress.md и docs/changelog.md после каждой задачи
- Коммитит в формате `type: description`
- orchestrator_report.md — просишь обновить для меня (оркестратора)
