import json
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "5e-database" / "5e-database-main" / "src"
OUT_DIR = ROOT / "data" / "srd"


FILES = {
    "spells": "5e-SRD-Spells.json",
    "equipment": "5e-SRD-Equipment.json",
    "magic_items": "5e-SRD-Magic-Items.json",
    "monsters": "5e-SRD-Monsters.json",
    "classes": "5e-SRD-Classes.json",
    "levels": "5e-SRD-Levels.json",
    "features": "5e-SRD-Features.json",
    "races": "5e-SRD-Races.json",
    "subraces": "5e-SRD-Subraces.json",
    "species": "5e-SRD-Species.json",
    "subspecies": "5e-SRD-Subspecies.json",
    "backgrounds": "5e-SRD-Backgrounds.json",
    "skills": "5e-SRD-Skills.json",
    "proficiencies": "5e-SRD-Proficiencies.json",
    "languages": "5e-SRD-Languages.json",
    "conditions": "5e-SRD-Conditions.json",
    "damage_types": "5e-SRD-Damage-Types.json",
    "traits": "5e-SRD-Traits.json",
    "alignments": "5e-SRD-Alignments.json",
    "weapon_properties": "5e-SRD-Weapon-Properties.json",
    "magic_schools": "5e-SRD-Magic-Schools.json",
    "feats": "5e-SRD-Feats.json",
    "equipment_categories": "5e-SRD-Equipment-Categories.json",
}


def _read_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _item_key(item: Dict[str, Any]) -> str:
    key = item.get("index") or item.get("name")
    if not key:
        return json.dumps(item, sort_keys=True)
    return str(key).strip().lower()


def _merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key not in merged:
            merged[key] = value
            continue
        if isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _merge_lists(base: List[Any], override: List[Any]) -> List[Any]:
    if not base:
        return list(override)
    if not override:
        return list(base)
    if not all(isinstance(x, dict) for x in base + override):
        return list(override)
    by_key: Dict[str, Dict[str, Any]] = {}
    for item in base:
        by_key[_item_key(item)] = item
    for item in override:
        key = _item_key(item)
        if key in by_key:
            by_key[key] = _merge_dict(by_key[key], item)
        else:
            by_key[key] = item
    return list(by_key.values())


def merge_payload(base: Any, override: Any) -> Any:
    if base is None:
        return override
    if override is None:
        return base
    if isinstance(base, list) and isinstance(override, list):
        return _merge_lists(base, override)
    if isinstance(base, dict) and isinstance(override, dict):
        return _merge_dict(base, override)
    return override


def main() -> None:
    if not SRC_ROOT.exists():
        raise FileNotFoundError(
            f"Expected 5e-database at {SRC_ROOT}. Update SRC_ROOT if moved."
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for key, filename in FILES.items():
        base_path = SRC_ROOT / "2014" / filename
        override_path = SRC_ROOT / "2024" / filename
        base_payload = _read_json(base_path)
        override_payload = _read_json(override_path)

        if base_payload is None and override_payload is None:
            continue

        merged = merge_payload(base_payload, override_payload)

        out_path = OUT_DIR / f"{key}.json"
        with out_path.open("w", encoding="utf-8") as handle:
            json.dump(merged, handle, indent=2, ensure_ascii=False)

        base_count = len(base_payload) if isinstance(base_payload, list) else "n/a"
        override_count = len(override_payload) if isinstance(override_payload, list) else "n/a"
        merged_count = len(merged) if isinstance(merged, list) else "n/a"
        print(f"{key}: {base_count} + {override_count} -> {merged_count}")


if __name__ == "__main__":
    main()
