# Bugfix: PWA Landscape Layout

## Файлы для изменения
- `web/style.css`

## Контекст
Читай `CLAUDE.md` перед началом.
Тестовое устройство: Samsung Galaxy S23 Ultra.

В landscape-ориентации компоненты loadout-view налезают друг на друга:
карточки стратагем и D-pad блок перекрываются, либо D-pad выходит
за пределы экрана.

## Диагностика перед правкой

Открой `web/style.css`, найди блок `@media (orientation: landscape)`.
Определи точно, какие свойства конфликтуют. Типичные причины:

1. `flex` / `width` в `%` без `min-width: 0` → блоки не сжимаются
2. Жёсткий `height` у карточек переполняет контейнер на коротком экране
3. `--cell` clamp не учитывает реальную высоту при наличии topbar

## Требования к исправлению

### Общая компоновка в landscape (`.body--loadout-view`)
```
┌─────────────────────────────────────┐
│ header (фиксированная высота ~48px) │
├──────────────┬──────────────────────┤
│  2×2 cards   │   D-pad area         │
│  ~45vw       │   ~55vw              │
│  min-w: 0    │   min-w: 0           │
└──────────────┴──────────────────────┘
```

### Правила
- Оба блока (`#grid`, `#loadout-dpad-area`) должны иметь `min-width: 0`
  и `overflow: hidden` — без этого flexbox не сжимает flex-children.
- Высота карточек: убери фиксированный `height` или `aspect-ratio` для
  landscape. Используй `height: auto` + `flex: 1 1 auto` для grid-ячеек.
- D-pad cross: формула `--cell` должна учитывать высоту доступного
  пространства за вычетом topbar (≈32px) и slider (≈48px) и cancel (≈36px):
  ```css
  --cell: clamp(48px,
    min(calc(52vw / 3.2), calc((100dvh - 48px - 32px - 48px - 36px) / 3)),
    82px);
  ```
- Карточки в grid (`#grid.grid--loadout`): landscape → 2 колонки × 2 строки,
  без `aspect-ratio`, `font-size` и иконка подобраны под `calc(45vw / 2)`.
- Slider и Cancel-кнопка не должны уходить за нижний край экрана. Если
  `loadout-dpad-area` использует `flex-direction: column`, добавь
  `overflow: hidden` контейнеру и `flex-shrink: 1` slider-блоку.

### S23 Ultra Landscape: 1080×411 логических пикселей (dpr≈3.5)
При написании clamp()-значений помни, что viewport ≈ 412×915 dp.
В landscape — ~915px wide, ~412px tall.

## Что НЕ трогать
- Portrait layout — не ломай
- Десктопный breakpoint `@media (min-width: 768px)` — не трогать
- JS-логику — только CSS

## После исправлений
1. Открой PWA на S23 Ultra в landscape
2. Убедись: карточки 2×2 слева, D-pad справа, ничего не выходит за экран
3. Проверь portrait — должен остаться без изменений
4. Обнови `docs/changelog.md` и `orchestrator_report.md`
5. Коммит: `fix: landscape layout overflow, cards and dpad no longer overlap`
