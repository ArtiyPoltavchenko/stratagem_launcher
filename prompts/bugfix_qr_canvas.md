# Bugfix: QR Canvas + Window Size Constraints

## Файлы для изменения
- `desktop/server_manager.py`

## Контекст
Читай `CLAUDE.md` перед началом.

Баг: QR-код в .exe отрисовывает белый прямоугольник вместо кода.

## Root cause
`tk.Canvas` возвращает `winfo_width() == 1` до того, как виджет реально
отрендерен (до первого mainloop). Если `box_size` считается через
`winfo_width() // matrix_size`, получаем `box_size = 0` → прямоугольники
нулевого размера → белый холст.

## Исправление 1 — QR-рендеринг

### Требования
- Объяви константу `QR_CANVAS_SIZE = 260` рядом с остальными константами
  вверху файла.
- При создании Canvas передавай явные размеры:
  ```python
  self._qr_canvas = tk.Canvas(
      frame,
      width=QR_CANVAS_SIZE,
      height=QR_CANVAS_SIZE,
      bg="white",
      highlightthickness=0,
  )
  ```
- В методе `_draw_qr(url)`:
  ```python
  def _draw_qr(self, url: str) -> None:
      self._qr_canvas.delete("all")
      try:
          import qrcode
          qr = qrcode.QRCode(
              version=None,
              error_correction=qrcode.constants.ERROR_CORRECT_M,
              box_size=1,      # только для генерации матрицы
              border=2,
          )
          qr.add_data(url)
          qr.make(fit=True)
          matrix = qr.modules   # list[list[bool]]

          side = len(matrix)    # число модулей
          # box_size определяется из фиксированного размера холста
          box = QR_CANVAS_SIZE // (side + 4)  # +4 = border*2
          if box < 1:
              box = 1
          offset = (QR_CANVAS_SIZE - box * side) // 2

          for row_idx, row in enumerate(matrix):
              for col_idx, cell in enumerate(row):
                  if cell:
                      x0 = offset + col_idx * box
                      y0 = offset + row_idx * box
                      self._qr_canvas.create_rectangle(
                          x0, y0,
                          x0 + box, y0 + box,
                          fill="black", outline="",
                      )
      except Exception as e:
          self._qr_canvas.create_text(
              QR_CANVAS_SIZE // 2,
              QR_CANVAS_SIZE // 2,
              text=f"QR error:\n{e}",
              fill="red",
              justify="center",
          )
  ```
- Вызывать `_draw_qr` нужно **после** первого `root.update_idletasks()`,
  чтобы Canvas был уже вставлен в layout. Добавь вызов
  `self._root.update_idletasks()` перед `self._draw_qr(url)` везде,
  где QR перерисовывается.

## Исправление 2 — жёсткие размеры окна (QR всегда читаемый)

### Требования
- Минимальный размер окна: `root.minsize(1000, 740)`
- **Максимальная ширина** левой панели (Connection + QR + Settings):
  зафиксируй `left_frame` через `width=420` + `pack_propagate(False)`.
  Это предотвращает вертикальное сжатие QR-блока при ресайзе окна.
- Фрейм вокруг `_qr_canvas` должен иметь фиксированную высоту:
  ```python
  qr_frame = tk.Frame(left_panel, bg=BG, height=QR_CANVAS_SIZE + 8)
  qr_frame.pack_propagate(False)
  qr_frame.pack(pady=(0, 8))
  self._qr_canvas.pack(in_=qr_frame)
  ```
  Это гарантирует, что при вертикальном сжатии окна QR не теряет место.

## Что НЕ трогать
- Логику `get_lan_ip()` — уже исправлена
- Логику `_start()` / `_stop()` / WM_DELETE_WINDOW — уже исправлены
- Тесты — GUI не покрыт тестами, pytest не запускать

## После исправлений
1. Запусти `python desktop/server_manager.py` на Windows
2. Переключи режим на WiFi — убедись, что QR-код рендерится и сканируется
3. Сожми окно по вертикали — QR не должен исчезать
4. Обнови `docs/changelog.md` и `orchestrator_report.md`
5. Коммит: `fix: qr canvas fixed size, window min constraints`
