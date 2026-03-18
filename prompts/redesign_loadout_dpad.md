# Redesign: Loadout Quick-Access + D-pad Combined View

## Контекст
Сейчас Loadout view показывает 4 карточки в 2-col grid с кучей пустого места (скриншот). D-pad — отдельный overlay по кнопке ✛. Нужно объединить.

## Новый дизайн: Loadout = Quick-Access экран

Когда пользователь выбирает лоадаут (таб), экран превращается в **игровой пульт**:

### Portrait layout (вертикальный):
```
┌──────────────────────────────┐
│  STRATAGEMS   🟢  ⚙️        │  ← header (компактный)
│  [All] [Loadout 1 ×] [+]    │  ← табы
├──────────────────────────────┤
│ ┌──────┐┌──────┐┌──────┐┌──────┐ │
│ │ icon ││ icon ││ icon ││ icon │ │  ← 4 карточки в ряд,
│ │ name ││ name ││ name ││ name │ │     максимально широкие,
│ │ ▲▶▶  ││ ▲▶▼▶ ││ ▼▼▲▶ ││ ▼▲▼▲ │ │     занимают всю ширину
│ └──────┘└──────┘└──────┘└──────┘ │
├──────────────────────────────┤
│            [  ▲  ]           │
│                              │
│      [ ◄ ]  [  ]  [ ► ]     │  ← D-pad, БОЛЬШИЕ кнопки
│                              │
│            [  ▼  ]           │
│                              │
│    Sequence: ▲ ► ►           │  ← введённые стрелки
│    Auto-execute: 3s [====●]  │  ← таймер + ползунок
└──────────────────────────────┘
```

### Landscape layout (горизонтальный):
```
┌──────────────────────────────────────────────────────┐
│ ┌────┐┌────┐│           │  [▲]  │                    │
│ │icon││icon││  Seq: ▲►► │[◄]  [►]│  или зеркально   │
│ │name││name││  3s [=●]  │  [▼]  │  для правой руки  │
│ ┌────┐┌────┐│           │       │                    │
│ │icon││icon││           │       │                    │
│ │name││name││           │       │                    │
│ └────┘└────┘│           │       │                    │
└──────────────────────────────────────────────────────┘
```

Landscape: D-pad справа (или слева — по настройке). Карточки лоадаута слева в 2×2 grid. Sequence и таймер — по центру.

## Механика D-pad (переделка)

Текущая механика: Start → тапы → Execute/timeout. Новая:

1. **Первый тап стрелки** → автоматически `POST /api/manual/start` (зажать Ctrl) + отправить эту стрелку `POST /api/manual/key`
2. **Последующие тапы** → `POST /api/manual/key` каждый
3. **Авто-execute** → через N секунд без тапа → `POST /api/manual/stop` (отпустить Ctrl)
4. **Кнопка Execute НЕ НУЖНА** — убрать. В игре после ввода кода игрок сам кидает стратагему

Т.е. пользователь просто тапает стрелки: `▲ ► ►` — первый тап зажимает Ctrl, через 3 секунды молчания Ctrl отпускается. Всё.

### Таймер авто-release
- Ползунок рядом с sequence display: 1s — 5s, шаг 0.5s, default 3s
- Сохранять в localStorage (`sl_manual_timeout`)
- При каждом тапе — сброс таймера
- Визуально: маленькая полоска-countdown рядом с sequence

### Кнопка отмены
Вместо Execute — кнопка **✕ Cancel** (маленькая, рядом с sequence). Нажатие → `POST /api/manual/stop` + очистка sequence. На случай если набрал не ту комбинацию.

## Header redesign

### Было:
```
STRATAGEMS   ● Connected   ✛   +   ⚙️
```
✛ мелкая и незаметная, "Connected" занимает место.

### Стало:
```
STRATAGEMS   📶🟢   ⚙️
```

- **Убрать** текст "Connected" / "Disconnected"
- **Заменить на**: иконка сигнала (📶 или SVG antenna) + цветной индикатор:
  - 🟢 зелёный = подключено (health check OK)
  - 🔴 красный = нет связи
  - 🟡 жёлтый = connecting/slow
- Иконку делать как маленький SVG inline или Unicode, не текстом
- **Убрать кнопку ✛** из header — D-pad теперь встроен в loadout view

### Кнопка D-pad для All view
Когда выбран таб "All" (не лоадаут), D-pad скрыт. Показать кнопку **"Manual Input ✛"** как плавающую внизу экрана (FAB — floating action button):

```css
.fab-dpad {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--accent-yellow);
  color: #000;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  z-index: 100;
}
```
Нажатие → переключает в D-pad overlay (полный экран, как было).

## Карточки лоадаута — адаптивные, максимально большие

### Sizing: заполнить весь экран

На мобильном карточки должны быть **максимально большими** — занять всё доступное пространство экрана. Не фиксированные px, а расчёт от viewport:

```css
/* Loadout view: cards + D-pad делят экран */
.loadout-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - var(--tabs-height));
  /* Всё что осталось после header и табов */
}

.loadout-cards {
  flex: 0 0 auto; /* не растягиваются */
}

.loadout-dpad-area {
  flex: 1 1 auto; /* D-pad занимает оставшееся */
  min-height: 200px;
}
```

**Portrait (4 карточки в ряд):**
```css
.loadout-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  padding: 6px;
}

.loadout-card {
  aspect-ratio: 3/4;  /* пропорции, не фиксированные px */
  /* карточка растягивается под доступную ширину */
}
```

**Landscape (2×2 слева, D-pad справа):**
```css
@media (orientation: landscape) {
  .loadout-view {
    flex-direction: row;
  }
  .loadout-cards {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(2, 1fr);
    width: 45vw;
    height: 100%;
  }
  .loadout-dpad-area {
    width: 55vw;
  }
}
```

**На ПК** (десктоп, `min-width: 768px`): оставить как Claude Code определил — стандартный grid, не растягивать на весь экран.

### Двойное назначение карточек:
- **Тап на карточку** = выполнить всю последовательность автоматически (POST /api/execute)
- **Свайп по карточке** = отдать команду направления на D-pad (см. ниже)

---

## Свайп-ввод (Swipe-to-Input)

Свайпы по карточкам лоадаута = ввод стрелок на D-pad. Это **альтернатива** кнопочному D-pad — можно использовать и то и то.

### Механика:
1. Пользователь **свайпает** по любой карточке (или по свайп-зоне) → определяется направление → отправляется команда
2. Первый свайп → auto-start (`POST /api/manual/start` + `POST /api/manual/key`)
3. Последующие свайпы → `POST /api/manual/key`
4. Auto-release через таймаут (как с D-pad)

### Touch detection:
```javascript
let touchStartX, touchStartY;
const SWIPE_THRESHOLD = 30; // px minimum distance

function onTouchStart(e) {
  const touch = e.changedTouches[0];
  touchStartX = touch.clientX;
  touchStartY = touch.clientY;
}

function onTouchEnd(e) {
  const touch = e.changedTouches[0];
  const dx = touch.clientX - touchStartX;
  const dy = touch.clientY - touchStartY;
  
  // Ignore if distance too small (it's a tap, not swipe)
  if (Math.abs(dx) < SWIPE_THRESHOLD && Math.abs(dy) < SWIPE_THRESHOLD) {
    return; // let tap handler fire instead
  }
  
  e.preventDefault(); // prevent tap from firing
  
  let direction;
  if (Math.abs(dx) > Math.abs(dy)) {
    direction = dx > 0 ? 'right' : 'left';
  } else {
    direction = dy > 0 ? 'down' : 'up';
  }
  
  sendManualKey(direction);
}

// Attach to swipe zone
swipeZone.addEventListener('touchstart', onTouchStart, { passive: true });
swipeZone.addEventListener('touchend', onTouchEnd, { passive: false });
```

### Свайп-зона:
- Вся область карточек = свайп-зона
- Визуальная рамка вокруг карточек когда manual mode активен:
  ```css
  .loadout-cards.manual-active {
    border: 2px dashed var(--accent-yellow);
    border-radius: 8px;
  }
  ```
- Подсказка при первом использовании: "Swipe cards to input directions"

### Конфликт тап vs свайп:
- **Расстояние < 30px** = тап → выполнить стратагему карточки
- **Расстояние ≥ 30px** = свайп → отдать направление D-pad
- `e.preventDefault()` в touchend только при свайпе, чтобы тап работал

---

## Ориентация: индикатор "верх" на D-pad

Телефон может быть повёрнут — пользователь должен знать куда "вверх". На кнопочном D-pad:

### Маркер "верх":
- Маленький треугольник или метка **N** (North) на кнопке ▲
- Или цветовая маркировка: кнопка "вверх" чуть ярче остальных
- При смене ориентации (`orientationchange` event) — обновить маркер если направления маппятся иначе

### Простое решение:
```css
.dpad-btn-up::after {
  content: "▴";  /* маленький треугольник-указатель */
  font-size: 8px;
  position: absolute;
  top: 2px;
  left: 50%;
  transform: translateX(-50%);
  color: var(--accent-yellow);
  opacity: 0.6;
}
```

### Для landscape:
Стрелки на D-pad **НЕ МЕНЯЮТ** маппинг при повороте — "вверх" на D-pad всегда отправляет "up" (W в игре), независимо от ориентации телефона. Маркер помогает ориентироваться визуально.

---

## Что менять

### `web/app.js`:
- D-pad: убрать кнопку Execute, первый тап/свайп стрелки = auto-start
- Swipe detection на карточках лоадаута
- Auto-execute timeout из localStorage
- Loadout view: рендер карточек + D-pad вместе, adaptive sizing
- Header: заменить connection status text на icon+dot
- FAB button для All view

### `web/style.css`:
- Loadout карточки: `calc(100vh - ...)` sizing, grid 4×1 portrait / 2×2 landscape
- D-pad: перенести из overlay в loadout section
- Swipe zone visual: dashed border when manual-active
- D-pad "north" marker on up button
- Header: стили для signal icon + color dot
- FAB button
- Desktop override: стандартные размеры карточек (`@media min-width: 768px`)

### `web/index.html`:
- Header structure update
- Loadout section restructure

### `server/` — не трогать, API ручного ввода уже есть и работает

## Порядок
1. Header redesign (signal icon + color dot) → коммит
2. Loadout cards adaptive sizing (fill viewport on mobile, standard on desktop) → коммит
3. Loadout view + embedded D-pad (portrait) → коммит
4. D-pad auto-start mechanics (первый тап = Ctrl + key, убрать Execute) → коммит
5. Swipe-to-input на карточках (touch detection, visual border) → коммит
6. Ориентация: маркер "верх" на D-pad, landscape layout → коммит
7. FAB button для All view → коммЦ  ит
8. Обнови docs/

## Тесты
72+ тестов не должны сломаться — все изменения в web/ (frontend).