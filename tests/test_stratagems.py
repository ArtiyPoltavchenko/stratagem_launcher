"""Tests for server/stratagems.py."""

import json
import pytest
from pathlib import Path

from server import stratagems
from server.stratagems import StratagemsLoadError


DATA_PATH = Path(__file__).parent.parent / "data" / "stratagems.json"


@pytest.fixture(autouse=True)
def reload_stratagems():
    """Reload real stratagems before each test."""
    stratagems.load(DATA_PATH)


class TestLoad:
    def test_loads_without_error(self):
        stratagems.load(DATA_PATH)

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(StratagemsLoadError, match="Failed to load"):
            stratagems.load(tmp_path / "nonexistent.json")

    def test_raises_on_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(StratagemsLoadError, match="Failed to load"):
            stratagems.load(bad)

    def test_raises_on_duplicate_ids(self, tmp_path):
        data = {
            "categories": {"orbital": {"name": "Orbital", "color": "#fff"}},
            "stratagems": [
                {"id": "x", "name": "X", "category": "orbital", "keys": ["up"], "icon": "x.svg"},
                {"id": "x", "name": "X2", "category": "orbital", "keys": ["down"], "icon": "x.svg"},
            ],
        }
        p = tmp_path / "s.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(StratagemsLoadError, match="duplicate id"):
            stratagems.load(p)

    def test_raises_on_invalid_keys(self, tmp_path):
        data = {
            "categories": {"orbital": {"name": "Orbital", "color": "#fff"}},
            "stratagems": [
                {"id": "x", "name": "X", "category": "orbital", "keys": ["invalid"], "icon": "x.svg"},
            ],
        }
        p = tmp_path / "s.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(StratagemsLoadError, match="invalid keys"):
            stratagems.load(p)

    def test_raises_on_unknown_category(self, tmp_path):
        data = {
            "categories": {},
            "stratagems": [
                {"id": "x", "name": "X", "category": "unknown", "keys": ["up"], "icon": "x.svg"},
            ],
        }
        p = tmp_path / "s.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(StratagemsLoadError, match="unknown category"):
            stratagems.load(p)


class TestQuery:
    def test_get_all_returns_list(self):
        result = stratagems.get_all()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_all_count(self):
        result = stratagems.get_all()
        assert len(result) > 0  # count may grow as stratagems.json is updated

    def test_all_have_required_fields(self):
        for s in stratagems.get_all():
            assert "id" in s
            assert "name" in s
            assert "category" in s
            assert "keys" in s
            assert "icon" in s

    def test_get_by_id_known(self):
        s = stratagems.get_by_id("orbital_precision_strike")
        assert s is not None
        assert s["name"] == "Orbital Precision Strike"
        assert s["keys"] == ["right", "right", "up"]

    def test_get_by_id_unknown(self):
        assert stratagems.get_by_id("nonexistent_stratagem") is None

    def test_get_categories_returns_dict(self):
        cats = stratagems.get_categories()
        assert isinstance(cats, dict)
        assert "orbital" in cats
        assert "eagle" in cats

    def test_no_duplicate_ids(self):
        ids = [s["id"] for s in stratagems.get_all()]
        assert len(ids) == len(set(ids))

    def test_all_keys_valid(self):
        valid = {"up", "down", "left", "right"}
        for s in stratagems.get_all():
            for k in s["keys"]:
                assert k in valid, f"{s['id']} has invalid key: {k}"
