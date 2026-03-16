"""Stratagem Launcher — Flask application."""

import argparse
import logging
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


def create_app(cfg: Config = _default_config) -> Flask:
    """Application factory."""
    app = Flask(__name__, static_folder=None)
    CORS(app, origins=["http://localhost:*", "http://127.0.0.1:*", "http://192.168.*"])

    # Load stratagems once at startup
    stratagems.load()
    log.info("Loaded %d stratagems", len(stratagems.get_all()))

    # Attach config to app for access in routes
    app.config["SL_CONFIG"] = cfg

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
                key_delay=sl_cfg.key_delay,
                ctrl_delay=sl_cfg.ctrl_hold_delay,
            )
        except BlockingIOError:
            return jsonify({"status": "busy", "message": "Another stratagem is being executed"}), 503
        except RuntimeError as e:
            return jsonify({"status": "error", "message": str(e)}), 503

        log.info("Executed: %s %s", s["name"], s["keys"])
        return jsonify({"status": "ok", "stratagem": s["name"], "keys": s["keys"]})

    @app.route("/api/settings", methods=["GET"])
    def get_settings():
        sl_cfg: Config = app.config["SL_CONFIG"]
        return jsonify({
            "key_delay_ms": sl_cfg.key_delay_ms,
            "ctrl_hold_delay_ms": sl_cfg.ctrl_hold_delay_ms,
            "version": "1.0.0",
        })

    @app.route("/api/settings", methods=["POST"])
    def update_settings():
        sl_cfg: Config = app.config["SL_CONFIG"]
        body = request.get_json(silent=True) or {}

        if "key_delay_ms" in body:
            val = int(body["key_delay_ms"])
            if not 10 <= val <= 500:
                return jsonify({"status": "error", "message": "key_delay_ms must be 10–500"}), 400
            sl_cfg.key_delay_ms = val

        if "ctrl_hold_delay_ms" in body:
            val = int(body["ctrl_hold_delay_ms"])
            if not 10 <= val <= 500:
                return jsonify({"status": "error", "message": "ctrl_hold_delay_ms must be 10–500"}), 400
            sl_cfg.ctrl_hold_delay_ms = val

        return jsonify({
            "status": "ok",
            "key_delay_ms": sl_cfg.key_delay_ms,
            "ctrl_hold_delay_ms": sl_cfg.ctrl_hold_delay_ms,
        })

    return app


def _parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Stratagem Launcher Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (use 0.0.0.0 for WiFi)")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--key-delay", type=int, default=50, dest="key_delay_ms")
    parser.add_argument("--ctrl-delay", type=int, default=30, dest="ctrl_hold_delay_ms")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    return Config(
        host=args.host,
        port=args.port,
        key_delay_ms=args.key_delay_ms,
        ctrl_hold_delay_ms=args.ctrl_hold_delay_ms,
        debug=args.debug,
    )


if __name__ == "__main__":
    cfg = _parse_args()
    app = create_app(cfg)
    log.info("Starting server on http://%s:%d", cfg.host, cfg.port)
    app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)
