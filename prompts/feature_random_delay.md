# Feature: рандомизация задержки клавиш (anti-macro protection)

## Файлы для изменения
- `server/keypress.py`
- `server/config.py`
- `server/app.py`
- `web/index.html`
- `web/app.js`
- `web/style.css`

## Контекст
Читай `CLAUDE.md` перед началом.

Цель: вместо фиксированной задержки `key_delay_ms` использовать
случайную задержку из диапазона [min, max], чтобы имитировать
живой ввод и затруднить определение макроса.

Seed рандома = `time.time_ns()` (наносекунды) — новый seed на каждое нажатие.

---

## Часть 1 — `server/config.py`

Замени поле `key_delay_ms: int = 50` на два поля:

```python
key_delay_min_ms: int = 50
key_delay_max_ms: int = 80
```

Обратная совместимость: если в запросе приходит старый `key_delay_ms` —
устанавливай оба поля в это значение (min == max → без рандома).

---

## Часть 2 — `server/keypress.py`

### Функция `_random_delay(min_ms, max_ms)`

```python
import random as _random

def _random_delay(min_ms: float, max_ms: float) -> None:
    """Sleep for a random duration in [min_ms, max_ms] milliseconds.
    Seeds RNG with nanosecond timestamp for each call.
    """
    rng = _random.Random(time.time_ns())
    if max_ms <= min_ms:
        delay = min_ms
    else:
        delay = rng.uniform(min_ms, max_ms)
    time.sleep(delay / 1000.0)
```

### Замена вызовов `time.sleep(key_delay)` в `execute_stratagem()`

Везде где сейчас используется фиксированная задержка между клавишами —
замени на `_random_delay(cfg.key_delay_min_ms, cfg.key_delay_max_ms)`.

Аналогично для `ctrl_hold_delay` — он остаётся фиксированным
(это задержка до первой клавиши, не между клавишами).

Сигнатура `execute_stratagem()` обновляется:
```python
def execute_stratagem(
    keys: list[str],
    key_hold_ms: float = 50,
    key_delay_min_ms: float = 50,
    key_delay_max_ms: float = 80,
    ctrl_hold_delay_ms: float = 150,
    auto_click: bool = False,
) -> None:
```

Лог-строка должна показывать фактически использованную задержку:
```
[KEYPRESS] 73.2ms 'right' (VK=0x44) DOWN  (range: 50-80ms)
```

---

## Часть 3 — `server/app.py`

### GET /api/settings

Добавь в ответ:
```json
{
  "key_delay_min_ms": 50,
  "key_delay_max_ms": 80,
  "key_delay_ms": 50  // deprecated, = min для совместимости
}
```

### POST /api/settings

Принимай оба новых поля + старый `key_delay_ms` для совместимости:

```python
if 'key_delay_min_ms' in data:
    cfg.key_delay_min_ms = int(data['key_delay_min_ms'])
if 'key_delay_max_ms' in data:
    cfg.key_delay_max_ms = int(data['key_delay_max_ms'])
# backward compat
if 'key_delay_ms' in data and 'key_delay_min_ms' not in data:
    cfg.key_delay_min_ms = int(data['key_delay_ms'])
    cfg.key_delay_max_ms = int(data['key_delay_ms'])
# enforce min <= max
if cfg.key_delay_min_ms > cfg.key_delay_max_ms:
    cfg.key_delay_max_ms = cfg.key_delay_min_ms
```

---

## Часть 4 — PWA Settings (`index.html` + `app.js` + `style.css`)

### Заменить старый single-slider на dual-range

В `index.html` найди строку с `Key delay` слайдером.
**Замени** его на двойной ползунок:

```html
<div class="settings-row">
  <span class="settings-label">Key delay</span>
  <div class="dual-range" id="delay-range-wrap">
    <input type="range" id="delay-min" min="10" max="200" step="5" value="50">
    <input type="range" id="delay-max" min="10" max="200" step="5" value="80">
    <div class="dual-range__track"></div>
    <div class="dual-range__fill" id="delay-fill"></div>
  </div>
  <span class="settings-value" id="delay-label">50–80 ms</span>
</div>
```

### CSS (`.dual-range`)

```css
.dual-range {
  position: relative;
  width: 160px;
  height: 20px;
}
.dual-range input[type=range] {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0; left: 0;
  appearance: none;
  background: transparent;
  pointer-events: none;
}
.dual-range input[type=range]::-webkit-slider-thumb {
  appearance: none;
  width: 16px; height: 16px;
  border-radius: 50%;
  background: var(--accent-yellow);
  cursor: pointer;
  pointer-events: all;
}
.dual-range__track {
  position: absolute;
  top: 50%; transform: translateY(-50%);
  width: 100%; height: 4px;
  background: #333;
  border-radius: 2px;
}
.dual-range__fill {
  position: absolute;
  top: 50%; transform: translateY(-50%);
  height: 4px;
  background: var(--accent-yellow);
  border-radius: 2px;
}
```

### JS (`app.js`)

```js
function initDelaySlider() {
  const minEl = document.getElementById('delay-min');
  const maxEl = document.getElementById('delay-max');
  const fill  = document.getElementById('delay-fill');
  const label = document.getElementById('delay-label');
  const wrap  = document.getElementById('delay-range-wrap');

  // Загружаем из localStorage
  minEl.value = localStorage.getItem('sl_delay_min') ?? 50;
  maxEl.value = localStorage.getItem('sl_delay_max') ?? 80;

  function update() {
    let mn = parseInt(minEl.value);
    let mx = parseInt(maxEl.value);
    // Не даём пересечься
    if (mn > mx) { [mn, mx] = [mx, mn]; minEl.value = mn; maxEl.value = mx; }
    // Обновляем заливку
    const pct = (v) => (v - 10) / (200 - 10) * 100;
    fill.style.left  = pct(mn) + '%';
    fill.style.width = (pct(mx) - pct(mn)) + '%';
    // Лейбл
    label.textContent = mn === mx ? `${mn} ms` : `${mn}–${mx} ms`;
    // Сохраняем
    localStorage.setItem('sl_delay_min', mn);
    localStorage.setItem('sl_delay_max', mx);
  }

  minEl.addEventListener('input', update);
  maxEl.addEventListener('input', update);
  update(); // начальная отрисовка

  // Отправка на сервер при отпускании
  function send() {
    apiFetch('/api/settings', 'POST', {
      key_delay_min_ms: parseInt(minEl.value),
      key_delay_max_ms: parseInt(maxEl.value),
    }).then(() => showToast(`Delay: ${label.textContent}`));
  }
  minEl.addEventListener('change', send);
  maxEl.addEventListener('change', send);
}
```

Вызови `initDelaySlider()` внутри `initSettings()`.

---

## Что НЕ трогать
- `ctrl_hold_delay_ms` — фиксированный, не рандомизируется
- `key_hold_ms` — фиксированный (время удержания клавиши)
- Тесты — нужно обновить: `test_keypress.py` использует старые параметры `key_delay_ms` — замени на `key_delay_min_ms` / `key_delay_max_ms`

## После правок
1. `pytest tests/` — все зелёные
2. Запусти сервер, открой PWA → в Settings двойной слайдер вместо одного
3. Подвигай ползунки — label обновляется `50–80 ms`
4. Выполни стратагему — в логе видны разные задержки в указанном диапазоне
5. Поставь min == max → задержка фиксированная (нет рандома)
6. Обнови `docs/changelog.md` и `orchestrator_report.md`
7. Коммит: `feat: randomized key delay with dual-range slider (anti-macro)`
