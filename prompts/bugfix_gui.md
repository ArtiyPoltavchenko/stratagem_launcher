# Bugfix: Desktop GUI — QR Code, DPI Scaling, Dev Launch

Три бага в `desktop/server_manager.py`. Фикси по одному, коммить после каждого.

---

## Bug 1: Мыло/размытый текст на мониторах с высоким DPI (2K, 4K)

**Проблема:** tkinter на Windows по умолчанию не учитывает DPI scaling. На 2K+ мониторах текст и виджеты размытые — Windows растягивает окно как картинку.

**Фикс:** Добавить в самое начало `server_manager.py`, ДО создания `tk.Tk()`:

```python
import ctypes
import sys

# Windows DPI awareness — must be called BEFORE Tk() initialization
if sys.platform == 'win32':
    try:
        # Per-monitor DPI awareness (Windows 10 1703+)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            # System DPI awareness (fallback for older Windows)
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
```

Это ДОЛЖНО быть до любого вызова `tk.Tk()`. Проверь что `SetProcessDpiAwareness(2)` вызывается — это Per-Monitor V2, лучшее качество.

После этого размеры окна и шрифтов могут потребовать корректировки — окно станет меньше на HiDPI (потому что теперь пиксели реальные, а не масштабированные). Подкорректируй если нужно.

---

## Bug 2: QR-код не рендерится в окне приложения

**Проблема:** QR-код показывается в консоли ASCII-артом или просто URL текстом вместо картинки внутри tkinter окна. Из отчёта: `except Exception` ловит ошибку PIL и показывает fallback текст.

**Диагностика — добавь временно:**
```python
def _refresh_qr(self):
    try:
        import qrcode
        from PIL import Image, ImageTk
        print(f"DEBUG: qrcode={qrcode.__version__}, PIL={Image.__version__}")
        # ... generate QR ...
    except Exception as e:
        print(f"DEBUG QR FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
```
Запусти, посмотри что конкретно падает.

**Вероятные причины и фиксы:**

### Причина A: PIL.ImageTk не установлен
```powershell
# В активированном .venv_win:
pip install Pillow
pip install "qrcode[pil]"
```
Проверь что `from PIL import ImageTk` работает:
```powershell
python -c "from PIL import ImageTk; print('OK')"
```

### Причина B: Неправильная конвертация PIL Image → tkinter
Правильный паттерн:
```python
import qrcode
from PIL import Image, ImageTk

def _refresh_qr(self):
    url = f"http://{self.lan_ip}:{self.port}"
    
    # Generate QR
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    
    # PIL Image (RGB, not 1-bit!)
    pil_img = qr.make_image(fill_color="white", back_color="#1a1a1a").convert("RGB")
    
    # Resize to fit widget
    pil_img = pil_img.resize((200, 200), Image.NEAREST)
    
    # Convert to tkinter — MUST keep reference!
    self._qr_photo = ImageTk.PhotoImage(pil_img)
    
    # Show in Label
    self.qr_label.configure(image=self._qr_photo, text="")
```

**Критично:** `self._qr_photo` — нужно хранить ссылку на объект! Если записать в локальную переменную, Python garbage-collector удалит картинку и Label покажет пустоту. Это самая частая ошибка с ImageTk.

### Причина C: Label не настроен для изображений
```python
self.qr_label = tk.Label(parent, bg="#1a1a1a")
self.qr_label.pack(...)
```
Не ставь `text=` при создании если планируешь показывать `image=`. Или используй `.configure(image=..., text="")`.

**Проверь текущий код**, найди где `_qr_photo` хранится. Если это локальная переменная в методе — вот и баг. Сделай `self._qr_photo`.

---

## Bug 3: Dev-запуск без venv

**Проблема:** `python desktop\server_manager.py` без активации venv → `ModuleNotFoundError: No module named 'flask'`.

**Фикс:** В начало `server_manager.py` (после DPI fix, до импортов flask/server) добавить проверку:

```python
# Check that we're running in a virtual environment
import os
if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
    # Not in venv — try to find and activate one
    venv_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv_win', 'Scripts', 'python.exe'),
    ]
    for venv_python in venv_paths:
        if os.path.exists(venv_python):
            print(f"[!] Not running in venv. Please activate first:")
            print(f"    .venv_win\\Scripts\\activate")
            print(f"    python desktop\\server_manager.py")
            sys.exit(1)
    # No venv found — try to continue anyway (maybe deps installed globally)
```

Это не автоактивация (это опасно), а понятное сообщение об ошибке вместо трейсбека.

---

## Порядок работы
1. Пофикси DPI → проверь что текст чёткий → коммит
2. Пофикси QR → проверь что картинка видна в окне → коммит  
3. Добавь venv check → проверь что без venv показывает понятную ошибку → коммит
4. Обнови docs/progress.md и docs/changelog.md

## Bug 4: Статичный layout, ничего не тянется

**Проблема:** Все размеры захардкожены в пикселях. На маленьком экране — не влезает. На большом — пустое место. Вертикальную границу между панелью инструментов и логом нельзя двигать. При ресайзе окна элементы не адаптируются.

**Фикс — переделать layout на `tk.PanedWindow` + `weight`:**

### 1. Заменить статичный grid/pack на PanedWindow

Вместо двух Frame с фиксированной шириной — `tk.PanedWindow(orient=tk.HORIZONTAL)`:

```python
# Главный контейнер — draggable splitter
paned = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=6, 
                         bg="#333", sashrelief=tk.RAISED)
paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

# Левая панель (Connection + Settings + Buttons)
left_frame = tk.Frame(paned, bg="#1a1a1a")
paned.add(left_frame, minsize=350, stretch="never")

# Правая панель (Log)
right_frame = tk.Frame(paned, bg="#1a1a1a")
paned.add(right_frame, minsize=300, stretch="always")
```

`stretch="always"` на правой панели — при ресайзе окна лог растягивается, левая панель сохраняет размер. Пользователь может тянуть разделитель мышкой.

### 2. Внутри левой панели — тоже гибкость

Все вложенные фреймы должны использовать `fill=tk.X` и `expand=False` (кроме QR, который может расти):

```python
# Connection frame
conn_frame = tk.LabelFrame(left_frame, text="Connection", ...)
conn_frame.pack(fill=tk.X, padx=5, pady=5)

# QR — может расти если место есть
qr_frame = tk.Frame(left_frame, ...)
qr_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Settings frame  
settings_frame = tk.LabelFrame(left_frame, text="Settings", ...)
settings_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)

# Buttons frame
btn_frame = tk.Frame(left_frame, ...)
btn_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)
```

### 3. Лог — ScrolledText растягивается

```python
log_label = tk.Label(right_frame, text="Log", ...)
log_label.pack(anchor="w", padx=5)

self.log_text = scrolledtext.ScrolledText(right_frame, ...)
self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))

clear_btn = tk.Button(right_frame, text="Clear", ...)
clear_btn.pack(anchor="e", padx=5, pady=5)
```

### 4. Убрать все захардкоженные width/height в пикселях

Заменить:
- `width=430` на фреймах → убрать, пусть `PanedWindow` контролирует
- `height=700` → убрать, `pack(fill=BOTH, expand=True)` 
- Фиксированные `place(x=, y=)` → заменить на `pack()` или `grid()` с `sticky="nsew"`
- `root.geometry("1160x840")` → оставить как стартовый размер, но НЕ как ограничение
- `root.minsize()` → уменьшить до разумного минимума (800×500)

### 5. Шрифты — относительные, не абсолютные

Если после DPI fix шрифты стали нормальные, оставь текущие размеры. Но НЕ привязывай ширину колонок к количеству символов шрифта.

### Результат
- Окно открывается с разумным размером
- При ресайзе: лог растягивается, панель инструментов сохраняет ширину
- Разделитель тянется мышкой
- На маленьком экране: всё видно, можно уменьшить окно до 800×500
- На большом экране: лог занимает всё доступное пространство

---

## Порядок работы
1. DPI fix → коммит
2. QR fix → коммит
3. Venv check → коммит
4. Layout (PanedWindow + flexible) → коммит
5. Обнови docs/progress.md и docs/changelog.md

## Тесты
72 существующих теста не должны сломаться — все изменения в desktop/server_manager.py, тесты его не покрывают.
