"""Stratagem Launcher — Flask application."""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from . import stratagems, keypress
from .config import Config, config as _default_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

WEB_DIR = Path(__file__).parent.parent / "web"


def _loadouts_path() -> Path:
    """Return writable path for loadouts.json.

    In a PyInstaller --onefile bundle sys.frozen is set; the _MEIPASS temp
    dir is read-only so we store the file next to the .exe instead.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "loadouts.json"
    return Path(__file__).parent.parent / "data" / "loadouts.json"


def create_app(cfg: Config = _default_config, loadouts_path: Path | None = None) -> Flask:
    """Application factory."""
    app = Flask(__name__, static_folder=None)
    CORS(app, origins=["http://localhost:*", "http://127.0.0.1:*", "http://192.168.*"])

    # Load stratagems once at startup
    stratagems.load()
    log.info("Loaded %d stratagems", len(stratagems.get_all()))

    # Attach config and loadouts path to app for access in routes
    app.config["SL_CONFIG"] = cfg
    app.config["SL_LOADOUTS_PATH"] = loadouts_path or _loadouts_path()

    # ------------------------------------------------------------------ static

    @app.route("/")
    def index():
        return send_from_directory(WEB_DIR, "index.html")

    @app.route("/<path:filename>")
    def static_files(filename: str):
        return send_from_directory(WEB_DIR, filename)

    # -------------------------------------------------------------------- API

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "timestamp": int(time.time())})

    @app.route("/api/stratagems", methods=["GET"])
    def get_stratagems():
        return jsonify({
            "stratagems": stratagems.get_all(),
            "categories": stratagems.get_categories(),
            "icon_repo": stratagems.get_icon_repo(),
        })

    @app.route("/api/execute", methods=["POST"])
    def execute():
        body = request.get_json(silent=True) or {}
        stratagem_id = body.get("id", "").strip()

        if not stratagem_id:
            return jsonify({"status": "error", "message": "Missing field: id"}), 400

        s = stratagems.get_by_id(stratagem_id)
        if s is None:
            return jsonify({"status": "error", "message": f"Stratagem not found: {stratagem_id}"}), 404

        sl_cfg: Config = app.config["SL_CONFIG"]
        try:
            keypress.execute_stratagem(
                keys=s["keys"],
                key_delay_min_ms=sl_cfg.key_delay_min_ms,
                key_delay_max_ms=sl_cfg.key_delay_max_ms,
                ctrl_delay=sl_cfg.ctrl_hold_delay,
                key_hold=sl_cfg.key_hold,
                auto_click=sl_cfg.auto_click,
            )
        except BlockingIOError:
            return jsonify({"status": "busy", "message": "Another stratagem is being executed"}), 503
        except RuntimeError as e:
            return jsonify({"status": "error", "message": str(e)}), 503

        log.info("Executed: %s %s", s["name"], s["keys"])
        return jsonify({"status": "ok", "stratagem": s["name"], "keys": s["keys"]})

    # ------------------------------------------------------------ manual mode

    @app.route("/api/manual/start", methods=["POST"])
    def manual_start():
        sl_cfg: Config = app.config["SL_CONFIG"]
        body = request.get_json(silent=True) or {}
        timeout = float(body.get("timeout", 3.0))

        try:
            started = keypress.manual_start(
                ctrl_delay=sl_cfg.ctrl_hold_delay,
                timeout=timeout,
            )
        except RuntimeError as e:
            return jsonify({"status": "error", "message": str(e)}), 503

        if not started:
            return jsonify({"status": "busy", "message": "Already executing or manual mode active"}), 503

        log.info("Manual mode started (timeout=%.1fs)", timeout)
        return jsonify({"status": "ok", "manual": True})

    @app.route("/api/manual/key", methods=["POST"])
    def manual_key():
        sl_cfg: Config = app.config["SL_CONFIG"]
        body = request.get_json(silent=True) or {}
        direction = body.get("direction", "").strip()

        if not direction:
            return jsonify({"status": "error", "message": "Missing field: direction"}), 400

        try:
            ok = keypress.manual_key(direction, key_hold=sl_cfg.key_hold)
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400

        if not ok:
            return jsonify({"status": "error", "message": "Manual mode not active"}), 409

        log.info("Manual key: %s", direction)
        return jsonify({"status": "ok", "direction": direction})

    @app.route("/api/manual/stop", methods=["POST"])
    def manual_stop():
        stopped = keypress.manual_stop()
        log.info("Manual mode stopped (was_active=%s)", stopped)
        return jsonify({"status": "ok", "stopped": stopped})

    @app.route("/api/manual/status", methods=["GET"])
    def manual_status():
        return jsonify({"active": keypress.is_manual_active()})

    @app.route("/api/settings", methods=["GET"])
    def get_settings():
        sl_cfg: Config = app.config["SL_CONFIG"]
        return jsonify({
            "key_delay_min_ms": sl_cfg.key_delay_min_ms,
            "key_delay_max_ms": sl_cfg.key_delay_max_ms,
            "key_delay_ms": sl_cfg.key_delay_min_ms,  # deprecated, backward compat
            "ctrl_hold_delay_ms": sl_cfg.ctrl_hold_delay_ms,
            "key_hold_ms": sl_cfg.key_hold_ms,
            "auto_click": sl_cfg.auto_click,
            "version": "1.0.0",
        })

    @app.route("/api/loadouts", methods=["GET"])
    def get_loadouts():
        path: Path = app.config["SL_LOADOUTS_PATH"]
        try:
            with path.open(encoding="utf-8") as f:
                return jsonify(json.load(f))
        except FileNotFoundError:
            return jsonify([])

    @app.route("/api/loadouts", methods=["PUT"])
    def put_loadouts():
        path: Path = app.config["SL_LOADOUTS_PATH"]
        body = request.get_json(silent=True)
        if not isinstance(body, list):
            return jsonify({"status": "error", "message": "Expected JSON array"}), 400
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(body, f)
        log.info("Loadouts saved (%d)", len(body))
        return jsonify({"status": "ok", "count": len(body)})

    @app.route("/api/settings", methods=["POST"])
    def update_settings():
        sl_cfg: Config = app.config["SL_CONFIG"]
        body = request.get_json(silent=True) or {}
        log.info("[SETTINGS] Received: %s", body)

        if "key_delay_min_ms" in body:
            val = int(body["key_delay_min_ms"])
            if not 10 <= val <= 500:
                return jsonify({"status": "error", "message": "key_delay_min_ms must be 10–500"}), 400
            sl_cfg.key_delay_min_ms = val
        if "key_delay_max_ms" in body:
            val = int(body["key_delay_max_ms"])
            if not 10 <= val <= 500:
                return jsonify({"status": "error", "message": "key_delay_max_ms must be 10–500"}), 400
            sl_cfg.key_delay_max_ms = val
        # Backward compat: old key_delay_ms sets both min and max
        if "key_delay_ms" in body and "key_delay_min_ms" not in body:
            val = int(body["key_delay_ms"])
            if not 10 <= val <= 500:
                return jsonify({"status": "error", "message": "key_delay_ms must be 10–500"}), 400
            sl_cfg.key_delay_min_ms = val
            sl_cfg.key_delay_max_ms = val
        # Enforce min <= max
        if sl_cfg.key_delay_min_ms > sl_cfg.key_delay_max_ms:
            sl_cfg.key_delay_max_ms = sl_cfg.key_delay_min_ms

        if "ctrl_hold_delay_ms" in body:
            val = int(body["ctrl_hold_delay_ms"])
            if not 10 <= val <= 500:
                return jsonify({"status": "error", "message": "ctrl_hold_delay_ms must be 10–500"}), 400
            sl_cfg.ctrl_hold_delay_ms = val

        if "key_hold_ms" in body:
            val = int(body["key_hold_ms"])
            if not 0 <= val <= 500:
                return jsonify({"status": "error", "message": "key_hold_ms must be 0–500"}), 400
            sl_cfg.key_hold_ms = val

        if "auto_click" in body:
            sl_cfg.auto_click = bool(body["auto_click"])

        log.info(
            "[SETTINGS] Applied: key_delay=%d–%dms ctrl_hold_delay_ms=%d key_hold_ms=%d auto_click=%s",
            sl_cfg.key_delay_min_ms, sl_cfg.key_delay_max_ms,
            sl_cfg.ctrl_hold_delay_ms, sl_cfg.key_hold_ms, sl_cfg.auto_click,
        )
        return jsonify({
            "status": "ok",
            "key_delay_min_ms": sl_cfg.key_delay_min_ms,
            "key_delay_max_ms": sl_cfg.key_delay_max_ms,
            "key_delay_ms": sl_cfg.key_delay_min_ms,
            "ctrl_hold_delay_ms": sl_cfg.ctrl_hold_delay_ms,
            "key_hold_ms": sl_cfg.key_hold_ms,
            "auto_click": sl_cfg.auto_click,
        })

    return app


def _parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Stratagem Launcher Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (use 0.0.0.0 for WiFi)")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--key-delay-min", type=int, default=50, dest="key_delay_min_ms")
    parser.add_argument("--key-delay-max", type=int, default=80, dest="key_delay_max_ms")
    parser.add_argument("--ctrl-delay", type=int, default=30, dest="ctrl_hold_delay_ms")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    return Config(
        host=args.host,
        port=args.port,
        key_delay_min_ms=args.key_delay_min_ms,
        key_delay_max_ms=args.key_delay_max_ms,
        ctrl_hold_delay_ms=args.ctrl_hold_delay_ms,
        debug=args.debug,
    )


def _print_wifi_info(port: int) -> None:
    """Print local IP addresses and QR code when running in WiFi mode."""
    import socket
    ips: list[str] = []
    try:
        # Get all non-loopback IPv4 addresses
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass

    if not ips:
        log.info("Could not detect local IP. Check your network settings.")
        return

    url = f"http://{ips[0]}:{port}"
    print("\n" + "=" * 48)
    print(f"  Open on your phone: {url}")
    print("=" * 48)

    # Print QR code if qrcode package is available
    try:
        import qrcode  # type: ignore[import]
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        print("  (install qrcode for QR code display: pip install qrcode)")

    if len(ips) > 1:
        print("  Other IPs:", ", ".join(f"http://{ip}:{port}" for ip in ips[1:]))
    print()


if __name__ == "__main__":
    cfg = _parse_args()
    app = create_app(cfg)
    log.info("Starting server on http://%s:%d", cfg.host, cfg.port)
    if cfg.host == "0.0.0.0":
        _print_wifi_info(cfg.port)
    app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)
