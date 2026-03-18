# CLAUDE.md — Stratagem Launcher

## Проект
Мобильный пульт управления стратагемами Helldivers 2. PWA на телефоне → Python-сервер на ноутбуке → эмуляция клавиш в игре.

## Стек (строго бесплатный, без регистраций)
- **Сервер**: Python 3.10+, Flask, pynput, flask-cors
- **Фронтенд**: Vanilla HTML/CSS/JS (PWA), без фреймворков, без npm
- **Иконки**: SVG-заглушки, потом замена на реальные (путь или URL в stratagems.json)
- **Связь**: HTTP REST (WiFi/USB/ngrok), опционально WebSocket позже
- **Тестирование**: pytest для сервера, ручное тестирование PWA в Chrome DevTools

## ⚠️ КРИТИЧНО: Два окружения (WSL + Windows)

Проект работает в **двух средах одновременно**. Это НЕ опционально — pynput НЕ МОЖЕТ нажимать клавиши Windows-игре из WSL.

```
┌─────────────────────────────────────────────────────────────────┐
│  WSL2 (Ubuntu, fish)          │  Windows (PowerShell/CMD)       │
│  ─────────────────            │  ──────────────────────         │
│  • Claude Code (разработка)   │  • Запуск сервера (app.py)      │
│  • git, коммиты               │  • pynput → клавиши в игру      │
│  • pytest (unit-тесты)        │  • Helldivers 2                 │
│  • линтинг, рефакторинг       │  • .venv_win/ (Windows venv)    │
│                               │                                 │
│  venv: .venv/                 │  venv: .venv_win\               │
│  activate: source             │  activate:                      │
│    .venv/bin/activate.fish    │    .venv_win\Scripts\activate   │
└───────────────┬───────────────┴────────────────┬────────────────┘
                │         ОБЩИЕ ФАЙЛЫ            │
                │  /mnt/c/Users/arsup/Desktop/   │
                │  claude_playground/             │
                │  stratagem_launcher/            │
                └────────────────────────────────┘
```

### Правило для Claude Code:
- **Писать код, коммитить, запускать тесты** → делай в WSL как обычно
- **Запускать сервер для реального тестирования** → ВСЕГДА напоминай пользователю открыть PowerShell и запустить `scripts\start_server.bat`
- **Никогда** не пытайся запустить `app.py` из WSL для тестирования клавиш — pynput не достучится до Windows
- pytest с mock-клавишами работает нормально в WSL (мы мокаем pynput)

### Настройка Windows venv (один раз, пользователь делает сам):
```powershell
# В PowerShell, из папки проекта:
cd C:\Users\arsup\Desktop\claude_playground\stratagem_launcher
python -m venv .venv_win
.venv_win\Scripts\activate
pip install -r requirements.txt
```

## Окружение разработки (WSL — для Claude Code)
- ОС: Windows + WSL2 (Ubuntu), терминал: fish
- IDE: VS Code
- Перед запуском Python (в WSL) — активировать venv: `source .venv/bin/activate.fish`
- Зависимости для WSL: `pip install -r requirements-dev.txt` (без pynput)
- Не трогать системный Python, работать только в .venv
- **НЕ ставить pynput в WSL** — у evdev нет kernel headers, и он не нужен для тестов (мокаем)

## Структура проекта
```
stratagem_launcher/
├── CLAUDE.md                  # ← этот файл
├── PROJECT_SPEC.md            # полная спецификация
├── README.md                  # инструкция для пользователя
├── .gitignore
├── requirements.txt           # полный список (для Windows venv)
├── requirements-dev.txt       # без pynput (для WSL venv и тестов)
├── server/
│   ├── app.py                 # Flask-приложение
│   ├── keypress.py            # модуль эмуляции клавиш (pynput)
│   ├── stratagems.py          # загрузка и валидация стратагем из JSON
│   └── config.py              # конфигурация (порт, задержки)
├── data/
│   └── stratagems.json        # база стратагем (названия, коды, иконки)
├── web/                       # PWA фронтенд (раздаётся Flask'ом)
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── manifest.json
│   ├── sw.js                  # Service Worker для оффлайна
│   └── icons/                 # иконки приложения + стратагем
│       ├── app-192.png
│       ├── app-512.png
│       └── stratagems/        # по 1 файлу на стратагему (id.svg или id.png)
├── scripts/
│   ├── start_server.bat       # запуск сервера на Windows (localhost)
│   ├── start_server_wifi.bat  # запуск + --host 0.0.0.0 для WiFi
│   ├── setup_usb.bat          # adb reverse для USB
│   └── setup_wsl_venv.sh      # создание WSL venv без pynput
├── tests/
│   ├── test_keypress.py       # мокает pynput — работает в WSL
│   ├── test_stratagems.py
│   └── test_api.py
└── docs/
    ├── decisions.md            # архитектурные решения (Claude пишет сюда)
    ├── progress.md             # прогресс задач (Claude обновляет)
    └── changelog.md            # что изменилось (Claude дополняет)
```

## Правила разработки

### Код
- Python: PEP8, type hints, docstrings на английском
- JS: ES6+, без jQuery, без фреймворков
- CSS: CSS custom properties для темизации
- HTML: семантическая разметка, адаптивный дизайн (mobile-first)
- Все строки/сообщения в UI — на английском (интерфейс для игры)
- Комментарии в коде — на английском
- **keypress.py: импорт pynput обёрнут в try/except** — модуль должен быть importable без pynput (для тестов в WSL). Если pynput недоступен — execute_stratagem() возвращает mock/логирует последовательность

### Git
- Коммиты на английском, формат: `type: short description`
- Типы: feat, fix, refactor, docs, test, chore
- Одна фича = один коммит (можно несколько файлов)
- `.venv/` и `.venv_win/` — в .gitignore

### Безопасность
- Сервер слушает только на локальном интерфейсе по умолчанию (127.0.0.1)
- Для WiFi — запуск с флагом `--host 0.0.0.0` (или через start_server_wifi.bat)
- Никаких секретов в коде, никаких внешних API
- CORS только для localhost и локальной сети

### Тестирование
- Каждый модуль сервера покрыт тестами
- keypress.py — mock pynput в тестах (не нажимать реальные клавиши)
- **pytest запускать в WSL** — это быстрее и удобнее с Claude Code
- API — тестировать через Flask test client
- **Реальный тест клавиш** — только на Windows: запустить .bat, открыть Notepad, POST-запрос → проверить нажатия
- PWA — тестировать вручную в Chrome, документировать шаги в docs/

## Рабочий процесс (ОБЯЗАТЕЛЬНО)

### Задачи
1. Перед началом работы — прочитать `docs/progress.md`
2. Составить план задач (список) → показать мне для утверждения
3. После утверждения — выполнять по одной задаче
4. После каждой завершённой задачи:
   - Обновить `docs/progress.md` (статус: ✅ / 🔄 / ❌)
   - Коммит (если код)
   - Показать что сделано, спросить подтверждение на следующую
5. При архитектурном решении — записать в `docs/decisions.md` с датой и обоснованием

### Память проекта
- `docs/progress.md` — главный трекер задач. Формат:
  ```
  ## Phase N: Название фазы
  - [x] Задача 1
  - [ ] Задача 2
  - [ ] Задача 3 (blocked by: Задача 2)
  ```
- `docs/decisions.md` — почему выбрали X, а не Y
- `docs/changelog.md` — что менялось, когда

### Итеративность
- Не делать всё сразу. Сначала MVP (сервер + одна кнопка), потом расширять
- Каждая фаза должна давать работающий результат
- Если что-то не работает — откатить, записать проблему, предложить альтернативу

## Фазы разработки (ориентир)

### Phase 1: Skeleton ✅
- Инициализация проекта, venv, requirements.txt
- Базовая структура файлов
- stratagems.json с 50+ стратагемами
- docs/ с шаблонами

### Phase 2: Server Core ✅
### Phase 3: PWA Minimal ✅
### Phase 4: Full UI ✅
### Phase 5: Polish ✅
### Phase 6: Loadouts ✅
### Phase 7: Manual D-pad ✅

> Фазы 1–7 завершены. 67 тестов проходят. Подробности — в `orchestrator_report.md`.

### Phase 8: Cooldown Modifier
Чисто фронтенд. Ползунок % снижения кулдауна (Ship Module upgrades) + toggle видимости.
**Полный промпт:** `prompts/feature_cooldowns.md`

### Phase 9: Desktop EXE — Server Manager
tkinter GUI + PyInstaller → один .exe. Start/Stop/Restart, QR-код, логи, настройки.
**Полный промпт:** `prompts/feature_exe_manager.md`

## Данные: stratagems.json
Файл `data/stratagems.json` — единственный источник правды для всех стратагем.

**Иконки**: SVG из репо [nvigneux/Helldivers-2-Stratagems-icons-svg](https://github.com/nvigneux/Helldivers-2-Stratagems-icons-svg). Поле `icon` — относительный путь внутри репо. Полный URL собирается в коде:
```
{icon_repo}/{icon}  →  https://raw.githubusercontent.com/nvigneux/Helldivers-2-Stratagems-icons-svg/master/Bridge/Orbital Precision Strike.svg
```

Формат записи:
```json
{
  "id": "orbital_precision_strike",
  "name": "Orbital Precision Strike",
  "category": "orbital",
  "keys": ["right", "right", "up"],
  "icon": "Bridge/Orbital Precision Strike.svg",
  "cooldown": 100,
  "verified": true
}
```
- `keys` — массив направлений ПОСЛЕ зажатия Ctrl. Значения: "up", "down", "left", "right"
- `icon` — путь относительно icon_repo (папка/имя.svg). URL-encode пробелы при fetch
- `cooldown` — секунды перезарядки в игре
- `verified` — проверен ли код клавиш в игре

## Напоминания
- В WSL: активируй .venv перед Python-командами (source .venv/bin/activate.fish)
- В WSL: используй `pip install -r requirements-dev.txt` (без pynput)
- **НЕ запускай сервер из WSL** для реального тестирования клавиш
- Для реального теста — напомни пользователю: `scripts\start_server.bat` в PowerShell
- Не забывай обновлять docs/ после каждой задачи
- Спрашивай подтверждение перед переходом к следующей фазе
- Если не уверен в коде стратагемы — пометь `"verified": false` в JSON
- keypress.py должен быть importable без pynput (try/except на import)
