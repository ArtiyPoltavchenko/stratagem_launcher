# Debug & Fix: Keypress не проходят в игре + Manual Mode баги

## Приоритет: ВЫСОКИЙ — основная функциональность не работает в реальной игре

---

## Bug 1: WASD не регистрируются в Helldivers 2

### Симптомы:
- Ctrl зажимается правильно (меню стратагем открывается)
- WASD нажатия либо не проходят вообще, либо регистрируется только 1 из N
- Стратагема не выбирается

### Вероятные причины и что проверить:

#### A) Задержка слишком маленькая
Игра может не успевать обрабатывать нажатия при 50ms. Добавь **диагностический лог** в `keypress.py`:

```python
def execute_stratagem(keys, key_delay_ms, ctrl_delay_ms):
    """Log every keypress with timestamp for debugging."""
    import time
    
    print(f"[KEYPRESS] Starting stratagem: {keys}")
    print(f"[KEYPRESS] key_delay={key_delay_ms}ms, ctrl_delay={ctrl_delay_ms}ms")
    
    controller.press(CTRL_KEY)
    print(f"[KEYPRESS] {time.time():.3f} Ctrl DOWN")
    time.sleep(ctrl_delay_ms / 1000)
    
    for i, key in enumerate(keys):
        vk = KEY_MAP[key]
        k = KeyCode.from_vk(vk)
        controller.press(k)
        print(f"[KEYPRESS] {time.time():.3f} '{key}' (VK=0x{vk:02X}) DOWN")
        time.sleep(key_delay_ms / 1000)
        controller.release(k)
        print(f"[KEYPRESS] {time.time():.3f} '{key}' (VK=0x{vk:02X}) UP")
        time.sleep(key_delay_ms / 1000)  # ← ПАУЗА ПОСЛЕ release тоже нужна
    
    controller.release(CTRL_KEY)
    print(f"[KEYPRESS] {time.time():.3f} Ctrl UP")
```

**Проверь**: есть ли пауза ПОСЛЕ `release()` каждой клавиши? Если сейчас пауза только перед `press()` — игра может пропускать нажатия, потому что release+press сливаются.

#### B) Press+Release слишком быстрые — нужен hold time
Некоторые игры требуют минимальное время удержания клавиши (не только delay между нажатиями). Добавь **key_hold_ms**:

```python
for key in keys:
    vk = KEY_MAP[key]
    k = KeyCode.from_vk(vk)
    controller.press(k)
    time.sleep(key_hold_ms / 1000)    # удержание клавиши (30-50ms)
    controller.release(k)
    time.sleep(key_delay_ms / 1000)   # пауза между клавишами (50-100ms)
```

Рекомендуемые значения для Helldivers 2:
- `key_hold_ms` = 40 (время удержания нажатой клавиши)
- `key_delay_ms` = 60 (пауза между release текущей и press следующей)
- `ctrl_delay_ms` = 100 (пауза после зажатия Ctrl, перед первой клавишей)

#### C) VK коды правильные?
Проверь маппинг:
```python
KEY_MAP = {
    "up":    0x57,  # W
    "down":  0x53,  # S
    "left":  0x41,  # A
    "right": 0x44,  # D
}
```
Открой Notepad, выполни стратагему — должны появиться буквы `wwasd` и т.д. Если в Notepad работает а в игре нет — проблема в timing.

#### D) Тест в Notepad — обязательно
Запусти сервер, открой Notepad, поставь курсор. С телефона нажми стратагему. В Notepad должны появиться все буквы. Если да — timing проблема. Если нет — VK/pynput проблема.

### Фикс: добавить LMB клик в конце последовательности

В игре после ввода кода стратагемы игрок кидает маркер кликом мыши. Добавить **опциональный** клик ЛКМ после последовательности:

```python
from pynput.mouse import Button as MouseButton, Controller as MouseController
mouse = MouseController()

def execute_stratagem(keys, key_delay_ms, ctrl_delay_ms, auto_click=False):
    # ... existing key sequence ...
    
    controller.release(CTRL_KEY)
    
    if auto_click:
        time.sleep(50 / 1000)  # небольшая пауза
        mouse.click(MouseButton.left)
        print(f"[KEYPRESS] LMB click (auto-throw)")
```

- В config.py: `AUTO_CLICK_AFTER_STRATAGEM = False` (по умолчанию выключено)
- В настройках PWA: чекбокс "Auto-throw after input" 
- В API: `/api/settings` принимает `auto_click: bool`

---

## Bug 2: Manual mode — sequence не очищается после timeout

### Симптом:
Ввёл стрелки, прошёл timeout (3 сек), Ctrl отпустился, но на экране sequence (▲►►) остаётся. Новый ввод добавляет к старому.

### Где искать:
В `web/app.js` — найди обработчик timeout / manual stop. После `POST /api/manual/stop` или после получения ответа — sequence display должен очищаться:

```javascript
async function stopManualMode() {
    await fetch('/api/manual/stop', { method: 'POST' });
    // ← ТУТ должна быть очистка:
    manualSequence = [];
    renderSequenceDisplay();  // или как называется функция обновления UI
}
```

Проверь: есть ли клиентский таймер который вызывает `stopManualMode()`? Или клиент полагается на сервер? Если клиент не знает что сервер сделал auto-release — sequence зависает.

**Фикс**: клиент должен иметь свой таймер, синхронизированный с сервером:
```javascript
let manualTimeout;

function onManualKeyTap(direction) {
    // ... send key ...
    
    // Reset client-side timeout
    clearTimeout(manualTimeout);
    manualTimeout = setTimeout(() => {
        // Server already released Ctrl by now
        manualSequence = [];
        renderSequenceDisplay();
        setManualActiveUI(false);
    }, manualTimeoutMs); // то же значение что на сервере
}
```

---

## Bug 3: Key delay slider — изменения не применяются / нет фидбэка

### Симптом:
Двигаешь ползунок Key delay, нажимаешь Apply & Save, но в логе сервера нет сообщения. Не ясно применилось ли.

### Что проверить:

#### A) Отправляется ли POST?
В Chrome DevTools (F12 → Network tab) — после Apply должен быть `POST /api/settings`. Если нет — JS не отправляет запрос.

#### B) Формат данных правильный?
Проверь что JS отправляет:
```javascript
fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key_delay_ms: value })
})
```
А не `key_delay` или другое имя поля.

#### C) Сервер логирует?
В `app.py` обработчик `/api/settings` POST — добавь явный лог:
```python
@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.get_json()
    print(f"[SETTINGS] Received: {data}")
    # ... apply ...
    print(f"[SETTINGS] Applied: key_delay_ms={config.key_delay_ms}")
    return jsonify({"status": "ok", ...})
```

#### D) Визуальный фидбэк в PWA
После успешного POST — показать кратковременное подтверждение:
```javascript
async function saveSettings() {
    const resp = await fetch('/api/settings', { ... });
    if (resp.ok) {
        showToast("Settings saved ✓");  // зелёный тост на 2 сек
    } else {
        showToast("Failed to save settings", "error");
    }
}
```

---

## Порядок работы

1. **Добавь диагностические логи** в `keypress.py` — каждое нажатие с timestamp → коммит
2. **Добавь key_hold_ms** (время удержания клавиши, default 40ms) + паузу после release → коммит
3. **Протестируй в Notepad**: запусти сервер, нажми стратагему с телефона, проверь вывод в консоли + буквы в Notepad
4. **Скажи мне результат** — все буквы появились или нет, какие пропущены
5. **Пофикси manual mode** — client-side timeout + sequence cleanup → коммит
6. **Пофикси settings** — добавь логирование + toast feedback → коммит
7. **Auto-click LMB** — опциональный, чекбокс в настройках → коммит
8. Обнови docs/

## Тесты
- Обнови `test_keypress.py`: добавь тест что `key_hold_ms` пауза вызывается
- Обнови `test_api.py`: тест что `/api/settings` POST логирует и возвращает обновлённые значения
- 72+ существующих тестов не должны сломаться
