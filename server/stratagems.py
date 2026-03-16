"""Load and query stratagems from data/stratagems.json."""

import json
from pathlib import Path
from typing import Optional

_DATA_PATH = Path(__file__).parent.parent / "data" / "stratagems.json"

_data: dict = {}
_by_id: dict[str, dict] = {}

VALID_KEYS = {"up", "down", "left", "right"}
REQUIRED_FIELDS = {"id", "name", "category", "keys", "icon"}


class StratagemsLoadError(Exception):
    pass


def load(path: Path = _DATA_PATH) -> None:
    """Load and validate stratagems from JSON file. Raises StratagemsLoadError on failure."""
    global _data, _by_id

    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise StratagemsLoadError(f"Failed to load stratagems: {e}") from e

    categories = set(data.get("categories", {}).keys())
    stratagems = data.get("stratagems", [])
    errors: list[str] = []
    seen_ids: set[str] = set()

    for s in stratagems:
        missing = REQUIRED_FIELDS - s.keys()
        if missing:
            errors.append(f"{s.get('id', '?')}: missing fields {missing}")
            continue

        if s["id"] in seen_ids:
            errors.append(f"duplicate id: {s['id']}")
        seen_ids.add(s["id"])

        if s["category"] not in categories:
            errors.append(f"{s['id']}: unknown category '{s['category']}'")

        bad_keys = [k for k in s["keys"] if k not in VALID_KEYS]
        if bad_keys:
            errors.append(f"{s['id']}: invalid keys {bad_keys}")

        if not s["keys"]:
            errors.append(f"{s['id']}: empty key sequence")

    if errors:
        raise StratagemsLoadError("Validation errors:\n" + "\n".join(errors))

    _data = data
    _by_id = {s["id"]: s for s in stratagems}


def get_all() -> list[dict]:
    """Return all stratagems."""
    return list(_by_id.values())


def get_by_id(stratagem_id: str) -> Optional[dict]:
    """Return stratagem by id, or None if not found."""
    return _by_id.get(stratagem_id)


def get_categories() -> dict:
    """Return categories dict from JSON."""
    return _data.get("categories", {})
