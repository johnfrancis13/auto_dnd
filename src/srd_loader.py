import json
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
SRD_DIR = ROOT / "data" / "srd"
SRD_REPO = ROOT / "5e-database" / "5e-database-main" / "src"


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


def _merge_payload(base: Any, override: Any) -> Any:
    if base is None:
        return override
    if override is None:
        return base
    if isinstance(base, list) and isinstance(override, list):
        return _merge_lists(base, override)
    if isinstance(base, dict) and isinstance(override, dict):
        return _merge_dict(base, override)
    return override


def load_srd(name: str, filename: str) -> Any:
    """
    Load a merged SRD payload.
    Priority:
      1) data/srd/<name>.json (prebuilt)
      2) 5e-database/src/2014 + 2024 merged in-memory
    """
    prebuilt = SRD_DIR / f"{name}.json"
    payload = _read_json(prebuilt)
    if payload is not None:
        return payload

    base_path = SRD_REPO / "2014" / filename
    override_path = SRD_REPO / "2024" / filename
    base_payload = _read_json(base_path)
    override_payload = _read_json(override_path)

    if base_payload is None and override_payload is None:
        raise FileNotFoundError(
            f"SRD file not found: {filename} in data/srd or 5e-database."
        )

    return _merge_payload(base_payload, override_payload)
