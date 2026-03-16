"""Tests for server/app.py — Flask test client, all endpoints + error cases."""

import pytest
from unittest.mock import patch

from server.app import create_app
from server.config import Config


@pytest.fixture
def app():
    cfg = Config(key_delay_ms=0, ctrl_hold_delay_ms=0)
    application = create_app(cfg)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


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
            client.post("/api/execute", json={"id": "reinforce"})
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        assert kwargs["keys"] == ["up", "down", "right", "left", "up"]


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
