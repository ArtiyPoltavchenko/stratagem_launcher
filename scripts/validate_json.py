"""Quick validation script: verifies stratagems.json is well-formed and complete."""

import json
import sys
from pathlib import Path

VALID_KEYS = {"up", "down", "left", "right"}
REQUIRED_FIELDS = {"id", "name", "category", "keys", "icon"}


def validate(path: Path) -> bool:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    categories = set(data["categories"].keys())
    stratagems = data["stratagems"]
    ids: set[str] = set()
    errors: list[str] = []

    for s in stratagems:
        missing = REQUIRED_FIELDS - s.keys()
        if missing:
            errors.append(f"{s.get('id', '?')}: missing fields {missing}")
            continue

        if s["id"] in ids:
            errors.append(f"duplicate id: {s['id']}")
        ids.add(s["id"])

        if s["category"] not in categories:
            errors.append(f"{s['id']}: unknown category '{s['category']}'")

        bad_keys = [k for k in s["keys"] if k not in VALID_KEYS]
        if bad_keys:
            errors.append(f"{s['id']}: invalid keys {bad_keys}")

        if not s["keys"]:
            errors.append(f"{s['id']}: empty key sequence")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return False

    print(f"OK: {len(stratagems)} stratagems, {len(categories)} categories — all valid")
    return True


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    json_path = root / "data" / "stratagems.json"
    sys.exit(0 if validate(json_path) else 1)
