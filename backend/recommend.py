"""Small deterministic recommendation rules, seeded from the AAC catalog."""
import json
from pathlib import Path

_SEED = json.loads((Path(__file__).resolve().parent / "seed.json").read_text(encoding="utf-8"))


def recommend(message: str, language: str = "en") -> list[dict]:
    key = " ".join(message.casefold().split())
    rules = _SEED.get("suggestions", {})
    item_by_id = {item["id"]: item for item in _SEED["items"]}
    ids = rules.get(key)
    if ids is None:
        matched = next((prefix for prefix in rules if key.endswith(" " + prefix)), None)
        ids = rules.get(matched, [])
    return [{**item_by_id[item_id], "label": item_by_id[item_id].get(language, item_by_id[item_id]["en"])}
            for item_id in ids if item_id in item_by_id]
