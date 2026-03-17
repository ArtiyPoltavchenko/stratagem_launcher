"""Stratagem Launcher — Desktop Server Manager (tkinter GUI).

Run from project root:
    python desktop/server_manager.py

Or build a standalone .exe:
    scripts\\build_exe.bat
"""

from __future__ import annotations

import ctypes
import logging
import os
import queue
import socket
import subprocess
import sys
import threading
from tkinter import messagebox, scrolledtext
import tkinter as tk


# ---------------------------------------------------------------- venv check
# Runs early so the error message is readable before any import fails.
# Skipped when running as a PyInstaller bundle (sys.frozen is set).

_in_venv = hasattr(sys, "real_prefix") or (
    hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
)
if not _in_venv and not getattr(sys, "frozen", False):
    _venv_python = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".venv_win", "Scripts", "python.exe",
    )
    if os.path.exists(_venv_python):
        print("[!] Not running in a virtual environment.")
        print("    Please activate the venv first:")
        print()
        print("        .venv_win\\Scripts\\activate")
        print("        python desktop\\server_manager.py")
        sys.exit(1)
    # venv not found — dependencies might be installed globally, continue


# ------------------------------------------------------------------ paths

def resource_path(relative_path: str) -> str:
    """Resolve path to bundled resource — works in dev and PyInstaller onefile."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# Ensure project root is on sys.path so the 'server' package is importable
# when this script is run directly (python desktop/server_manager.py).
_project_root = resource_path(".")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from server.app import create_app          # noqa: E402  (after sys.path fixup)
from server.config import Config           # noqa: E402

try:
    from werkzeug.serving import make_server as _make_server
except ImportError:  # pragma: no cover
    _make_server = None  # type: ignore[assignment]


# ---------------------------------------------------------------- constants

WINDOW_TITLE = "Stratagem Launcher — Server Manager"
WINDOW_MIN_W = 800
WINDOW_MIN_H = 500
WINDOW_INIT  = "1160x840"

COLOR_RUN   = "#4caf50"
COLOR_STOP  = "#f44336"
COLOR_BG    = "#141414"
COLOR_PANEL = "#1e1e1e"
COLOR_CARD  = "#252525"
COLOR_FG    = "#e0e0e0"
COLOR_DIM   = "#888"
COLOR_YEL   = "#f5c518"
COLOR_BTN   = "#2a2a2a"

# Font definitions — ~1.5× larger than original
F_BASE  = ("Segoe UI", 13)
F_BOLD  = ("Segoe UI", 13, "bold")
F_SM    = ("Segoe UI", 11)
F_LG    = ("Segoe UI", 14, "bold")
F_PANEL = ("Segoe UI", 11, "bold")   # LabelFrame titles
F_MONO  = ("Consolas", 11)
F_DOT   = ("Segoe UI", 20)


# ---------------------------------------------------------------- IP helper

def get_lan_ip() -> str:
    """Get actual LAN IP by connecting to external address (no traffic sent)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # determines route without sending data
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""


# ---------------------------------------------------------------- log handler

class TkLogHandler(logging.Handler):
    """Thread-safe logging handler that forwards records to a Queue."""

    def __init__(self, log_queue: queue.Queue) -> None:
        super().__init__()
        self.log_queue = log_queue
        self.setFormatter(
            logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
        )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.log_queue.put_nowait(self.format(record))
        except Exception:
            self.handleError(record)


# ---------------------------------------------------------------- server thread

class ServerThread(threading.Thread):
    """Runs the Flask app via werkzeug make_server() in a daemon thread."""

    def __init__(self, cfg: Config) -> None:
        super().__init__(daemon=True, name="flask-server")
        self.cfg = cfg
        self._srv = None
        self.error: str | None = None

    def run(self) -> None:
        if _make_server is None:
            logging.getLogger(__name__).error(
                "werkzeug not installed — cannot start server."
            )
            return
        try:
            app = create_app(self.cfg)
            self._srv = _make_server(self.cfg.host, self.cfg.port, app)
            logging.getLogger(__name__).info(
                "Server started on http://%s:%d", self.cfg.host, self.cfg.port
            )
            self._srv.serve_forever()
        except Exception as exc:
            self.error = str(exc)
            logging.getLogger(__name__).error("Server error: %s", exc)

    def shutdown(self) -> None:
        if self._srv is not None:
            self._srv.shutdown()


# ---------------------------------------------------------------- GUI app

class ServerManagerApp:
    """Main tkinter GUI for managing the Flask server."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.minsize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.root.configure(bg=COLOR_BG)

        self._server_thread: ServerThread | None = None
        self._log_queue: queue.Queue = queue.Queue()
        # qr_canvas and qr_url_label are set in _build_ui()

        # Shared mutable config — slider updates it live while server runs
        self._cfg = Config()

        self._mode_var = tk.StringVar(value="wifi")   # "wifi" | "local" | "usb"
        self._port_var = tk.StringVar(value="5000")
        self._delay_var = tk.IntVar(value=50)

        self._build_ui()
        self._attach_log_handler()
        self._set_running(False)
        self._refresh_qr()
        self._poll_log()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----------------------------------------------------------- UI build

    def _build_ui(self) -> None:
        # ── Status bar ────────────────────────────────────────────────────
        status_bar = tk.Frame(self.root, bg=COLOR_PANEL, pady=10)
        status_bar.pack(fill="x", side="top")

        tk.Label(
            status_bar, text="Server Status:", bg=COLOR_PANEL, fg=COLOR_DIM,
            font=F_BASE,
        ).pack(side="left", padx=(16, 8))
        self._status_dot = tk.Label(
            status_bar, text="●", bg=COLOR_PANEL, font=F_DOT,
        )
        self._status_dot.pack(side="left")
        self._status_lbl = tk.Label(
            status_bar, text="STOPPED", bg=COLOR_PANEL, font=F_LG,
        )
        self._status_lbl.pack(side="left", padx=(6, 0))

        # ── Main content: draggable PanedWindow ────────────────────────────
        paned = tk.PanedWindow(
            self.root, orient=tk.HORIZONTAL, sashwidth=6,
            bg="#444", sashrelief=tk.RAISED,
        )
        paned.pack(fill="both", expand=True, padx=8, pady=(6, 8))

        left = tk.Frame(paned, bg=COLOR_BG)
        paned.add(left, minsize=400, stretch="never")

        right = tk.Frame(paned, bg=COLOR_BG)
        paned.add(right, minsize=300, stretch="always")

        # ── LEFT panel: bottom-up packing so QR fills remaining space ──────

        # Control buttons — bottom
        ctrl = tk.Frame(left, bg=COLOR_BG)
        ctrl.pack(side="bottom", fill="x", padx=4, pady=(0, 6))

        self._start_btn = self._make_btn(ctrl, "▶  Start",   self._start,   bg="#2b4a2b")
        self._start_btn.pack(side="left", padx=(0, 8))

        self._stop_btn = self._make_btn(ctrl, "■  Stop",    self._stop,    bg="#4a2b2b")
        self._stop_btn.pack(side="left", padx=(0, 8))

        self._restart_btn = self._make_btn(ctrl, "↻  Restart", self._restart, bg=COLOR_CARD)
        self._restart_btn.pack(side="left")

        # Settings panel — above buttons (also bottom)
        sett = self._make_panel(left, " Settings ")
        sett.pack(side="bottom", fill="x", padx=4, pady=(0, 10))

        mode_row = tk.Frame(sett, bg=COLOR_PANEL)
        mode_row.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(
            mode_row, text="Mode:", bg=COLOR_PANEL, fg=COLOR_DIM, font=F_BASE,
        ).pack(side="left", padx=(0, 10))
        for label, value in [
            ("WiFi (0.0.0.0)", "wifi"),
            ("Localhost", "local"),
            ("USB (ADB)", "usb"),
        ]:
            tk.Radiobutton(
                mode_row, text=label, variable=self._mode_var, value=value,
                bg=COLOR_PANEL, fg=COLOR_FG, selectcolor=COLOR_BG,
                activebackground=COLOR_PANEL, font=F_BASE,
                command=self._on_mode_change,
            ).pack(side="left", padx=(0, 10))

        self._usb_hint = tk.Label(
            sett,
            text="→ Run  scripts\\setup_usb.bat  then connect USB cable",
            bg=COLOR_PANEL, fg=COLOR_YEL, font=F_SM,
        )
        # shown only in USB mode; hidden initially

        delay_row = tk.Frame(sett, bg=COLOR_PANEL)
        delay_row.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(
            delay_row, text="Key delay:", bg=COLOR_PANEL, fg=COLOR_DIM, font=F_BASE,
        ).pack(side="left", padx=(0, 8))
        self._delay_lbl = tk.Label(
            delay_row, text="50 ms", bg=COLOR_PANEL, fg=COLOR_YEL,
            font=F_BOLD, width=7, anchor="e",
        )
        self._delay_lbl.pack(side="right")
        tk.Scale(
            delay_row, from_=20, to=200, orient="horizontal",
            variable=self._delay_var, showvalue=False,
            bg=COLOR_PANEL, fg=COLOR_FG, troughcolor=COLOR_BG,
            highlightthickness=0, command=self._on_delay_change,
        ).pack(side="left", fill="x", expand=True)

        # Connection panel — top
        conn = self._make_panel(left, " Connection ")
        conn.pack(side="top", fill="x", padx=4, pady=(4, 0))

        self._wifi_url_var = tk.StringVar(value="—")
        self._local_url_var = tk.StringVar(value="http://127.0.0.1:5000")

        self._url_row(conn, "WiFi:", self._wifi_url_var, self._copy_wifi)
        self._url_row(conn, "Local:", self._local_url_var, self._copy_local)

        port_row = tk.Frame(conn, bg=COLOR_PANEL)
        port_row.pack(fill="x", padx=12, pady=(4, 8))
        tk.Label(
            port_row, text="Port:", bg=COLOR_PANEL, fg=COLOR_DIM,
            font=F_BASE, width=6, anchor="w",
        ).pack(side="left")
        tk.Entry(
            port_row, textvariable=self._port_var, width=7,
            bg=COLOR_BG, fg=COLOR_FG, insertbackground=COLOR_FG,
            relief="flat", font=F_BASE,
        ).pack(side="left")
        self._port_var.trace_add("write", lambda *_: self.root.after(200, self._refresh_qr))

        # QR area — fills remaining space between Connection (top) and Settings (bottom)
        qr_frame = tk.Frame(left, bg=COLOR_PANEL, bd=1, relief="solid")
        qr_frame.pack(fill="both", expand=True, padx=4, pady=8)

        tk.Label(
            qr_frame, text="Open on phone:", bg=COLOR_PANEL, fg=COLOR_DIM, font=F_SM,
        ).pack(pady=(8, 2))

        self.qr_canvas = tk.Canvas(
            qr_frame, width=200, height=200, bg="#FFFFFF", highlightthickness=0,
        )
        self.qr_canvas.pack(fill="both", expand=True, padx=10, pady=5)
        self.qr_canvas.bind("<Configure>", lambda e: self._refresh_qr())

        self.qr_url_label = tk.Label(
            qr_frame, text="", bg=COLOR_PANEL, fg=COLOR_YEL, font=F_SM,
        )
        self.qr_url_label.pack(pady=(0, 8))

        # ── Log viewer — fills entire right pane ───────────────────────────
        log_frame = self._make_panel(right, " Log ")
        log_frame.pack(fill="both", expand=True, padx=4, pady=4)

        self._log_text = scrolledtext.ScrolledText(
            log_frame, state="disabled",
            bg="#0e0e0e", fg="#bbbbbb",
            font=F_MONO, relief="flat",
            wrap="word", insertbackground=COLOR_FG,
        )
        self._log_text.pack(fill="both", expand=True, padx=6, pady=(6, 0))

        clear_row = tk.Frame(log_frame, bg=COLOR_PANEL)
        clear_row.pack(fill="x", padx=6, pady=6)
        self._make_btn(clear_row, "Clear", self._clear_log, bg=COLOR_CARD).pack(side="right")

    # ── widget factory helpers ──────────────────────────────────────────────

    def _make_panel(self, parent, title: str) -> tk.LabelFrame:
        return tk.LabelFrame(
            parent, text=title, bg=COLOR_PANEL, fg=COLOR_YEL,
            font=F_PANEL, labelanchor="nw", bd=1, relief="solid",
        )

    def _make_btn(self, parent, text: str, cmd, bg: str = COLOR_BTN) -> tk.Button:
        return tk.Button(
            parent, text=text, command=cmd, bg=bg, fg=COLOR_FG,
            relief="flat", font=F_BOLD,
            padx=14, pady=8, cursor="hand2",
            activebackground=COLOR_CARD, activeforeground=COLOR_FG,
        )

    def _url_row(self, parent, label: str, var: tk.StringVar, copy_cmd) -> None:
        row = tk.Frame(parent, bg=COLOR_PANEL)
        row.pack(fill="x", padx=12, pady=(10, 2))
        tk.Label(
            row, text=label, bg=COLOR_PANEL, fg=COLOR_DIM,
            font=F_BASE, width=6, anchor="w",
        ).pack(side="left")
        tk.Label(
            row, textvariable=var, bg=COLOR_PANEL, fg=COLOR_YEL,
            font=F_BOLD, anchor="w",
        ).pack(side="left", fill="x", expand=True)
        self._make_btn(row, "Copy", copy_cmd, bg=COLOR_CARD).pack(
            side="right", padx=(6, 0),
        )

    # ── URL / QR helpers ───────────────────────────────────────────────────

    def _get_host(self) -> str:
        return "0.0.0.0" if self._mode_var.get() == "wifi" else "127.0.0.1"

    def _get_port(self) -> int:
        try:
            return int(self._port_var.get())
        except ValueError:
            return 5000

    def _on_mode_change(self) -> None:
        mode = self._mode_var.get()
        if mode == "usb":
            self._usb_hint.pack(fill="x", padx=12, pady=(0, 10))
            messagebox.showinfo(
                "USB Setup",
                "1. Connect phone via USB\n"
                "2. Enable USB Debugging on phone\n"
                "3. Click OK to run ADB setup",
            )
            logging.getLogger(__name__).info("[USB] Running ADB port forwarding...")
            try:
                subprocess.Popen(
                    ["cmd", "/c", resource_path("scripts\\setup_usb.bat")],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            except Exception as exc:
                logging.getLogger(__name__).error("[USB] Failed to run setup_usb.bat: %s", exc)
        else:
            self._usb_hint.pack_forget()
        self._refresh_qr()

    def _refresh_qr(self) -> None:
        """Draw QR code directly on tkinter Canvas — no PIL needed."""
        print(f"DEBUG QR: canvas size={self.qr_canvas.winfo_width()}x{self.qr_canvas.winfo_height()}")
        port = self._get_port()
        mode = self._mode_var.get()
        lan  = get_lan_ip()

        # Always update connection URL label vars
        if mode == "wifi" and lan:
            wifi_url = f"http://{lan}:{port}"
            self._wifi_url_var.set(wifi_url)
        else:
            wifi_url = ""
            self._wifi_url_var.set("—")

        # Local URL — use 127.0.0.1 explicitly (Windows 11: localhost → ::1 IPv6)
        self._local_url_var.set(f"http://127.0.0.1:{port}")

        # Non-WiFi modes: no QR needed
        if mode in ("local", "usb"):
            self.qr_canvas.delete("all")
            self.qr_url_label.configure(text=f"http://127.0.0.1:{port}")
            return

        if not wifi_url:
            self.qr_canvas.delete("all")
            self.qr_url_label.configure(text="(No LAN IP — check network)")
            return

        # WiFi mode — generate and draw QR matrix on Canvas
        self.qr_url_label.configure(text=wifi_url)

        try:
            import qrcode  # type: ignore[import]
        except ImportError:
            self.qr_canvas.delete("all")
            return

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=1,
            border=2,
        )
        qr.add_data(wifi_url)
        qr.make(fit=True)
        matrix = qr.get_matrix()   # list[list[bool]] — True = dark module

        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0

        canvas_size = min(self.qr_canvas.winfo_width(), self.qr_canvas.winfo_height())
        if canvas_size < 10:
            canvas_size = 200   # fallback before first Tk layout pass

        box = max(1, canvas_size // max(rows, cols, 1))
        print(f"DEBUG QR: matrix {rows}x{cols}, box={box}")
        total_w = cols * box
        total_h = rows * box
        ox = (canvas_size - total_w) // 2
        oy = (canvas_size - total_h) // 2

        self.qr_canvas.delete("all")
        self.qr_canvas.create_rectangle(0, 0, canvas_size, canvas_size,
                                         fill="#FFFFFF", outline="")
        for r, row in enumerate(matrix):
            for c, cell in enumerate(row):
                if cell:
                    x1 = ox + c * box
                    y1 = oy + r * box
                    self.qr_canvas.create_rectangle(
                        x1, y1, x1 + box, y1 + box,
                        fill="#000000", outline="",
                    )

    def _on_delay_change(self, val: str) -> None:
        ms = int(val)
        self._delay_lbl.configure(text=f"{ms} ms")
        self._cfg.key_delay_ms = ms  # live-update shared config

    def _copy_wifi(self) -> None:
        url = self._wifi_url_var.get()
        if url != "—":
            self.root.clipboard_clear()
            self.root.clipboard_append(url)

    def _copy_local(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(self._local_url_var.get())

    # ── server control ─────────────────────────────────────────────────────

    def _set_running(self, running: bool) -> None:
        color = COLOR_RUN if running else COLOR_STOP
        label = "RUNNING" if running else "STOPPED"
        self._status_dot.configure(fg=color)
        self._status_lbl.configure(text=label, fg=color)
        self._start_btn.configure(state="disabled" if running else "normal")
        self._stop_btn.configure(state="normal" if running else "disabled")
        self._restart_btn.configure(state="normal" if running else "disabled")

    def _start(self) -> None:
        if self._server_thread and self._server_thread.is_alive():
            return
        self._cfg = Config(
            host=self._get_host(),
            port=self._get_port(),
            key_delay_ms=self._delay_var.get(),
        )
        self._refresh_qr()
        self._server_thread = ServerThread(self._cfg)
        self._server_thread.start()
        self._set_running(True)
        host = self._cfg.host
        port = self._cfg.port
        self._log(f"Server started on http://{host}:{port}")

    def _stop(self, callback=None) -> None:
        """Shut down the server in a background thread to avoid blocking tkinter."""
        thread = self._server_thread
        self._server_thread = None
        self._set_running(False)   # update UI immediately
        self._log("Server stopped")

        def _do() -> None:
            if thread is not None:
                thread.shutdown()
                thread.join(timeout=5)
            if callback is not None:
                self.root.after(0, callback)

        threading.Thread(target=_do, daemon=True, name="stop-server").start()

    def _restart(self) -> None:
        def _after_stop() -> None:
            self.root.after(300, self._start)   # brief pause for OS to release port
        self._stop(callback=_after_stop)

    def _on_close(self) -> None:
        self._stop(callback=self.root.destroy)

    # ── log ────────────────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        """Emit a message directly to the log panel (GUI thread only)."""
        logging.getLogger(__name__).info(msg)

    def _attach_log_handler(self) -> None:
        handler = TkLogHandler(self._log_queue)
        handler.setLevel(logging.INFO)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)
        logging.getLogger("werkzeug").setLevel(logging.INFO)

    def _poll_log(self) -> None:
        """Drain the log queue and insert into ScrolledText. Reschedules itself."""
        try:
            while True:
                msg = self._log_queue.get_nowait()
                self._log_text.configure(state="normal")
                self._log_text.insert("end", msg + "\n")
                self._log_text.configure(state="disabled")
                self._log_text.see("end")
        except queue.Empty:
            pass
        self.root.after(100, self._poll_log)

    def _clear_log(self) -> None:
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")


# ---------------------------------------------------------------- entry point

def main() -> None:
    # Windows DPI awareness — must be called BEFORE Tk() initialization
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)   # Per-Monitor V2 (Win 10 1703+)
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()    # System DPI (fallback)
            except (AttributeError, OSError):
                pass

    root = tk.Tk()
    root.geometry(WINDOW_INIT)
    ServerManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
