# Bugfix: QR Code — Полная перезапись рендеринга

## Файлы для изменения
- `desktop/server_manager.py`

## Проблема
Canvas-based подход нестабилен в tkinter: размеры виджета недоступны
до первого рендера, `winfo_width()` возвращает 1px, `box_size = 0`.
Все попытки фиксить через `update_idletasks()` и явные константы
тоже дают артефакты (тонкая линия вместо QR).

## Решение: tk.PhotoImage + put()

Вместо Canvas с прямоугольниками — создаём `tk.PhotoImage` нужного
размера, рисуем пиксели через `.put()`, отображаем через `tk.Label`.
Это полностью обходит проблему Canvas-geometry и не требует PIL.

## Реализация

### Константа
```python
QR_IMG_SIZE = 260  # px — финальный размер изображения
```

### Замена виджета
Убери `self._qr_canvas` (tk.Canvas). Вместо него:
```python
self._qr_label = tk.Label(qr_frame, bg=BG, bd=0)
self._qr_label.pack()
self._qr_photo = None  # держим ссылку чтобы GC не убрал
```

### Метод `_draw_qr(url)`
Полностью перепиши:
```python
def _draw_qr(self, url: str) -> None:
    try:
        import qrcode

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=1,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        matrix = qr.modules          # list[list[bool]]
        n = len(matrix)              # количество модулей

        # Масштаб: сколько пикселей на модуль
        scale = QR_IMG_SIZE // n
        if scale < 1:
            scale = 1
        img_side = n * scale         # реальный размер изображения

        # Создаём PhotoImage
        img = tk.PhotoImage(width=img_side, height=img_side)

        # Построчно заполняем пиксели через put()
        # put() принимает строку вида "{#rrggbb #rrggbb ...}" на строку
        rows_data = []
        for row in matrix:
            row_pixels = " ".join(
                "#000000" if cell else "#ffffff"
                for cell in row
                for _ in range(scale)   # повторяем пиксель scale раз
            )
            for _ in range(scale):      # повторяем строку scale раз
                rows_data.append("{" + row_pixels + "}")
        img.put(" ".join(rows_data))

        self._qr_photo = img            # сохраняем ссылку!
        self._qr_label.config(image=img)

    except Exception as e:
        self._qr_photo = None
        self._qr_label.config(
            image="",
            text=f"QR unavailable:\n{e}",
            fg="red",
            font=("Consolas", 9),
        )
```

### Фрейм под QR
```python
qr_frame = tk.Frame(left_panel, bg="white", padx=4, pady=4)
qr_frame.pack(pady=(4, 8))

tk.Label(qr_frame, text="Open on phone:", bg=BG, fg=FG, font=FONT_SM).pack()
self._qr_label = tk.Label(qr_frame, bg="white", bd=0)
self._qr_label.pack()
self._qr_photo = None
```
Белый фон фрейма даёт "тихую зону" вокруг QR-кода.

## Что НЕ трогать
- `get_lan_ip()` — уже исправлена
- `_start()` / `_stop()` / WM_DELETE_WINDOW — уже исправлены
- USB, log, settings — не трогать
- Тесты — не запускать (GUI без тестов)

## После правки
1. `python desktop\server_manager.py` на Windows
2. Режим WiFi → Start → QR появляется и сканируется телефоном
3. Режим Localhost → QR области нет или показывает сообщение (не ломается)
4. Сожми окно — QR не исчезает, просто обрезается фреймом
5. Обнови `docs/changelog.md` и `orchestrator_report.md`
6. Коммит: `fix: rewrite QR rendering via tk.PhotoImage.put(), drop Canvas`
