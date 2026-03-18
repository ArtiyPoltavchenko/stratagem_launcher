# Feature: Auto-Install ADB Button

## Файлы для изменения
- `desktop/server_manager.py`

## Контекст
Читай `CLAUDE.md` перед началом.

GUI запускается как .exe (PyInstaller). Пользователь может не иметь ADB.
Нужна кнопка, которая скачивает и устанавливает Android Platform Tools
автоматически, без прав администратора, только stdlib.

## Архитектура

### Константы (добавь вверху файла)
```python
PLATFORM_TOOLS_URL = (
    "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
)
PLATFORM_TOOLS_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "StratagramLauncher",
    "platform-tools",
)
ADB_EXE = os.path.join(PLATFORM_TOOLS_DIR, "adb.exe")
```

### Метод `_get_adb_path() -> str | None`
```python
def _get_adb_path(self) -> str | None:
    """Возвращает путь к adb.exe: сначала локальный, потом PATH."""
    if os.path.isfile(ADB_EXE):
        return ADB_EXE
    import shutil
    return shutil.which("adb")
```

### Метод `_install_adb()`
Запускается в отдельном `threading.Thread` (не блокирует UI).
```python
def _install_adb(self) -> None:
    import urllib.request
    import zipfile
    import tempfile

    self._btn_install_adb.config(state="disabled", text="Downloading...")
    self._log("Downloading Android Platform Tools (~10 MB)...")

    try:
        # 1. Скачать во временный файл
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = tmp.name

        urllib.request.urlretrieve(PLATFORM_TOOLS_URL, tmp_path)
        self._log("Download complete. Extracting...")

        # 2. Распаковать
        os.makedirs(os.path.dirname(PLATFORM_TOOLS_DIR), exist_ok=True)
        with zipfile.ZipFile(tmp_path, "r") as zf:
            # Архив содержит папку platform-tools/ внутри
            # Распаковываем в родительский каталог
            parent = os.path.dirname(PLATFORM_TOOLS_DIR)
            zf.extractall(parent)

        os.unlink(tmp_path)
        self._log(f"ADB installed: {ADB_EXE}")
        self._root.after(0, self._on_adb_installed)

    except Exception as e:
        self._log(f"[ERROR] ADB install failed: {e}")
        self._root.after(
            0,
            lambda: self._btn_install_adb.config(
                state="normal", text="Install ADB"
            ),
        )
```

### Метод `_on_adb_installed()`
Вызывается из главного потока через `root.after(0, ...)`:
```python
def _on_adb_installed(self) -> None:
    self._btn_install_adb.config(text="ADB ✓ Installed", state="disabled", fg="green")
    messagebox.showinfo(
        "ADB Ready",
        f"Android Platform Tools installed.\nPath: {ADB_EXE}\n\nNow connect USB cable and click 'Setup USB'.",
    )
```

### Метод `_setup_usb()` — обновить
Используй `_get_adb_path()` для нахождения adb вместо системного PATH:
```python
def _setup_usb(self) -> None:
    adb = self._get_adb_path()
    if not adb:
        messagebox.showwarning(
            "ADB Not Found",
            "ADB is not installed.\nClick 'Install ADB' first.",
        )
        return
    # Запускаем setup_usb.bat с явным путём до adb
    bat = os.path.join(BASE_DIR, "scripts", "setup_usb.bat")
    env = os.environ.copy()
    env["ADB_PATH"] = adb   # передаём путь в bat через переменную окружения
    subprocess.Popen(
        ["cmd.exe", "/c", bat],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        env=env,
    )
    self._log(f"[USB] Running ADB port forwarding (adb: {adb})...")
```

### Обнови `scripts/setup_usb.bat`
```bat
@echo off
:: Использует ADB_PATH если задан, иначе системный adb
if defined ADB_PATH (
    set ADB="%ADB_PATH%"
) else (
    set ADB=adb
)
echo Running: %ADB% reverse tcp:5000 tcp:5000
%ADB% reverse tcp:5000 tcp:5000
if %errorlevel%==0 (
    echo [OK] ADB port forwarding set up.
) else (
    echo [ERROR] ADB failed. Is USB debugging enabled on your phone?
)
pause
```

## UI — где разместить кнопку

В секции Settings, после строки Mode (WiFi/Localhost/USB), добавь строку:
```
[Install ADB]   ← кнопка, disabled если adb уже найден
```

```python
# В методе _build_ui(), в блоке Settings:
adb_row = tk.Frame(settings_frame, bg=BG)
adb_row.pack(fill="x", pady=(4, 0))

self._btn_install_adb = tk.Button(
    adb_row,
    text="Install ADB" if not self._get_adb_path() else "ADB ✓ Installed",
    fg="white" if not self._get_adb_path() else "green",
    bg="#333",
    relief="flat",
    font=FONT_SM,
    state="normal" if not self._get_adb_path() else "disabled",
    command=lambda: threading.Thread(
        target=self._install_adb, daemon=True
    ).start(),
)
self._btn_install_adb.pack(side="left", padx=(0, 8))

tk.Label(
    adb_row,
    text="required for USB mode",
    bg=BG,
    fg="#888",
    font=FONT_SM,
).pack(side="left")
```

## Прогресс-фидбэк (опционально, если влезает в scope)
Если хочешь показывать прогресс скачивания, используй `reporthook`
в `urlretrieve`:
```python
def _reporthook(block_num, block_size, total_size):
    if total_size > 0:
        pct = min(100, block_num * block_size * 100 // total_size)
        self._root.after(
            0,
            lambda p=pct: self._btn_install_adb.config(
                text=f"Downloading... {p}%"
            ),
        )

urllib.request.urlretrieve(PLATFORM_TOOLS_URL, tmp_path, reporthook=_reporthook)
```

## Что НЕ трогать
- QR-рендеринг — уже исправлен
- `_start()` / `_stop()` / WM_DELETE_WINDOW — не трогать
- Тесты — GUI без тестов, pytest не запускать

## После правки
1. Запусти `python desktop\server_manager.py` на Windows
2. Убедись, что кнопка "Install ADB" видна в Settings
3. Нажми — должен пойти лог скачивания, потом "ADB ✓ Installed"
4. Проверь что `%LOCALAPPDATA%\StratagramLauncher\platform-tools\adb.exe` появился
5. Кнопка Setup USB теперь использует этот adb
6. Обнови `docs/changelog.md` и `orchestrator_report.md`
7. Коммит: `feat: auto-install ADB via urllib, no admin rights required`
