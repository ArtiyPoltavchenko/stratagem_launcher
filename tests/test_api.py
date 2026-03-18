"""Tests for server/app.py — Flask test client, all endpoints + error cases."""

import pytest
from pathlib import Path
from unittest.mock import patch

from server.app import create_app
from server.config import Config


@pytest.fixture
def app():
    cfg = Config(key_delay_min_ms=0, key_delay_max_ms=0, ctrl_hold_delay_ms=0)
    application = create_app(cfg)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def loadouts_app(tmp_path):
    """App variant with loadouts stored in a temp directory."""
    cfg = Config(key_delay_min_ms=0, key_delay_max_ms=0, ctrl_hold_delay_ms=0)
    application = create_app(cfg, loadouts_path=tmp_path / "loadouts.json")
    application.config["TESTING"] = True
    return application


@pytest.fixture
def loadouts_client(loadouts_app):
    return loadouts_app.test_client()


class TestHealth:
    def test_returns_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "ok"
        assert "timestamp" in data


class TestGetStratagems:
    def test_returns_200(self, client):
        r = client.get("/api/stratagems")
        assert r.status_code == 200

    def test_has_stratagems_list(self, client):
        data = client.get("/api/stratagems").get_json()
        assert isinstance(data["stratagems"], list)
        assert len(data["stratagems"]) > 0

    def test_has_categories(self, client):
        data = client.get("/api/stratagems").get_json()
        assert "categories" in data
        assert "orbital" in data["categories"]


class TestExecute:
    def test_success(self, client):
        with patch("server.keypress.execute_stratagem", return_value=True):
            r = client.post("/api/execute", json={"id": "orbital_precision_strike"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "ok"
        assert data["stratagem"] == "Orbital Precision Strike"
        assert data["keys"] == ["right", "right", "up"]

    def test_missing_id_returns_400(self, client):
        r = client.post("/api/execute", json={})
        assert r.status_code == 400
        assert r.get_json()["status"] == "error"

    def test_unknown_id_returns_404(self, client):
        r = client.post("/api/execute", json={"id": "nonexistent_stratagem"})
        assert r.status_code == 404
        data = r.get_json()
        assert data["status"] == "error"
        assert "not found" in data["message"]

    def test_busy_returns_503(self, client):
        with patch("server.keypress.execute_stratagem", side_effect=BlockingIOError("busy")):
            r = client.post("/api/execute", json={"id": "orbital_precision_strike"})
        assert r.status_code == 503
        assert r.get_json()["status"] == "busy"

    def test_pynput_unavailable_returns_503(self, client):
        with patch("server.keypress.execute_stratagem", side_effect=RuntimeError("pynput not available")):
            r = client.post("/api/execute", json={"id": "orbital_precision_strike"})
        assert r.status_code == 503

    def test_empty_body_returns_400(self, client):
        r = client.post("/api/execute", content_type="application/json", data="")
        assert r.status_code == 400

    def test_correct_keys_passed_to_keypress(self, client):
        with patch("server.keypress.execute_stratagem", return_value=True) as mock_exec:
            client.post("/api/execute", json={"id": "orbital_precision_strike"})
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        assert kwargs["keys"] == ["right", "right", "up"]


class TestSettings:
    def test_get_returns_defaults(self, client):
        r = client.get("/api/settings")
        assert r.status_code == 200
        data = r.get_json()
        assert "key_delay_ms" in data
        assert "ctrl_hold_delay_ms" in data
        assert "version" in data

    def test_update_key_delay(self, client):
        r = client.post("/api/settings", json={"key_delay_ms": 80})
        assert r.status_code == 200
        assert r.get_json()["key_delay_ms"] == 80

    def test_update_ctrl_delay(self, client):
        r = client.post("/api/settings", json={"ctrl_hold_delay_ms": 50})
        assert r.status_code == 200
        assert r.get_json()["ctrl_hold_delay_ms"] == 50

    def test_invalid_delay_too_low(self, client):
        r = client.post("/api/settings", json={"key_delay_ms": 5})
        assert r.status_code == 400

    def test_invalid_delay_too_high(self, client):
        r = client.post("/api/settings", json={"key_delay_ms": 9999})
        assert r.status_code == 400

    def test_update_persists_in_get(self, client):
        client.post("/api/settings", json={"key_delay_ms": 123})
        data = client.get("/api/settings").get_json()
        assert data["key_delay_ms"] == 123

    def test_get_includes_key_hold_ms(self, client):
        data = client.get("/api/settings").get_json()
        assert "key_hold_ms" in data

    def test_update_key_hold(self, client):
        r = client.post("/api/settings", json={"key_hold_ms": 60})
        assert r.status_code == 200
        assert r.get_json()["key_hold_ms"] == 60

    def test_key_hold_persists_in_get(self, client):
        client.post("/api/settings", json={"key_hold_ms": 55})
        data = client.get("/api/settings").get_json()
        assert data["key_hold_ms"] == 55

    def test_invalid_key_hold_too_high(self, client):
        r = client.post("/api/settings", json={"key_hold_ms": 9999})
        assert r.status_code == 400

    def test_update_auto_click(self, client):
        r = client.post("/api/settings", json={"auto_click": True})
        assert r.status_code == 200
        assert r.get_json()["auto_click"] is True

    def test_auto_click_persists_in_get(self, client):
        client.post("/api/settings", json={"auto_click": True})
        data = client.get("/api/settings").get_json()
        assert data["auto_click"] is True

    def test_settings_post_logs(self, client, caplog):
        """POST /api/settings emits log lines with the received values."""
        import logging
        with caplog.at_level(logging.INFO, logger="server.app"):
            client.post("/api/settings", json={"key_delay_ms": 75})
        messages = " ".join(r.message for r in caplog.records)
        assert "75" in messages


class TestManualAPI:
    def test_start_ok(self, client):
        with patch("server.keypress.manual_start", return_value=True):
            r = client.post("/api/manual/start")
        assert r.status_code == 200
        assert r.get_json()["status"] == "ok"
        assert r.get_json()["manual"] is True

    def test_start_busy(self, client):
        with patch("server.keypress.manual_start", return_value=False):
            r = client.post("/api/manual/start")
        assert r.status_code == 503
        assert r.get_json()["status"] == "busy"

    def test_start_unavailable(self, client):
        with patch("server.keypress.manual_start", side_effect=RuntimeError("no pynput")):
            r = client.post("/api/manual/start")
        assert r.status_code == 503

    def test_key_ok(self, client):
        with patch("server.keypress.manual_key", return_value=True):
            r = client.post("/api/manual/key", json={"direction": "up"})
        assert r.status_code == 200
        assert r.get_json()["direction"] == "up"

    def test_key_missing_direction(self, client):
        r = client.post("/api/manual/key", json={})
        assert r.status_code == 400

    def test_key_invalid_direction(self, client):
        with patch("server.keypress.manual_key", side_effect=ValueError("bad")):
            r = client.post("/api/manual/key", json={"direction": "diagonal"})
        assert r.status_code == 400

    def test_key_not_active(self, client):
        with patch("server.keypress.manual_key", return_value=False):
            r = client.post("/api/manual/key", json={"direction": "up"})
        assert r.status_code == 409

    def test_stop_ok(self, client):
        with patch("server.keypress.manual_stop", return_value=True):
            r = client.post("/api/manual/stop")
        assert r.status_code == 200
        assert r.get_json()["stopped"] is True

    def test_stop_idempotent(self, client):
        with patch("server.keypress.manual_stop", return_value=False):
            r = client.post("/api/manual/stop")
        assert r.status_code == 200
        assert r.get_json()["stopped"] is False

    def test_status_inactive(self, client):
        with patch("server.keypress.is_manual_active", return_value=False):
            r = client.get("/api/manual/status")
        assert r.status_code == 200
        assert r.get_json()["active"] is False

    def test_status_active(self, client):
        with patch("server.keypress.is_manual_active", return_value=True):
            r = client.get("/api/manual/status")
        assert r.get_json()["active"] is True


class TestLoadouts:
    def test_get_empty(self, loadouts_client):
        r = loadouts_client.get("/api/loadouts")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_put_and_get(self, loadouts_client):
        payload = [{"id": "l_1", "name": "My Loadout", "stratagems": ["orbital_precision_strike"]}]
        r = loadouts_client.put("/api/loadouts", json=payload)
        assert r.status_code == 200
        assert r.get_json()["status"] == "ok"
        assert r.get_json()["count"] == 1

        r2 = loadouts_client.get("/api/loadouts")
        assert r2.status_code == 200
        data = r2.get_json()
        assert len(data) == 1
        assert data[0]["id"] == "l_1"
        assert data[0]["name"] == "My Loadout"

    def test_put_replaces(self, loadouts_client):
        loadouts_client.put("/api/loadouts", json=[{"id": "l_1", "name": "A", "stratagems": []}])
        loadouts_client.put("/api/loadouts", json=[{"id": "l_2", "name": "B", "stratagems": []}])
        r = loadouts_client.get("/api/loadouts")
        data = r.get_json()
        assert len(data) == 1
        assert data[0]["id"] == "l_2"

    def test_put_empty_clears(self, loadouts_client):
        loadouts_client.put("/api/loadouts", json=[{"id": "l_1", "name": "A", "stratagems": []}])
        loadouts_client.put("/api/loadouts", json=[])
        r = loadouts_client.get("/api/loadouts")
        assert r.get_json() == []

    def test_put_invalid_body(self, loadouts_client):
        r = loadouts_client.put("/api/loadouts", json={"not": "a list"})
        assert r.status_code == 400
