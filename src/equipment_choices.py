from typing import Dict, List, Optional, Any, Tuple

from srd_loader import load_srd
from items import ItemRepository


def _load_equipment_categories() -> Dict[str, List[Dict[str, Any]]]:
    categories = load_srd("equipment_categories", "5e-SRD-Equipment-Categories.json") or []
    by_index: Dict[str, List[Dict[str, Any]]] = {}
    for cat in categories:
        index = cat.get("index")
        equipment = cat.get("equipment") or []
        if index:
            by_index[index] = equipment
    return by_index


def _make_item(name: str, quantity: int = 1, kind: str = "equipment") -> Dict[str, Any]:
    return {"name": name, "quantity": quantity, "kind": kind}


def _item_label(item: Dict[str, Any]) -> str:
    qty = item.get("quantity", 1)
    name = item.get("name", "")
    if item.get("kind") == "money":
        return f"{qty} {name}"
    if qty and qty != 1:
        return f"{qty} {name}"
    return name


def _option_label(items: List[Dict[str, Any]]) -> str:
    return ", ".join(_item_label(item) for item in items if item.get("name"))


def _items_from_option(option: Dict[str, Any]) -> List[Dict[str, Any]]:
    option_type = option.get("option_type")
    if option_type == "counted_reference":
        ref = option.get("of") or {}
        name = ref.get("name")
        count = option.get("count", 1)
        if name:
            return [_make_item(name, count)]
    if option_type == "reference":
        ref = option.get("item") or option.get("of") or {}
        name = ref.get("name")
        if name:
            return [_make_item(name, 1)]
    if option_type == "money":
        unit = option.get("unit") or "gp"
        count = option.get("count", 0)
        return [_make_item(unit, count, kind="money")]
    if option_type == "multiple":
        items: List[Dict[str, Any]] = []
        for sub in option.get("items", []) or []:
            items.extend(_items_from_option(sub))
        return items
    return []


def build_choice_groups(
    option_blocks: List[Dict[str, Any]],
    group_prefix: str,
) -> List[Dict[str, Any]]:
    categories = _load_equipment_categories()
    groups: List[Dict[str, Any]] = []

    for idx, block in enumerate(option_blocks or []):
        choose = int(block.get("choose") or 1)
        desc = block.get("desc")
        from_block = block.get("from") or {}
        option_set_type = from_block.get("option_set_type")
        options: List[Dict[str, Any]] = []

        if option_set_type == "options_array":
            for opt_idx, opt in enumerate(from_block.get("options") or []):
                items = _items_from_option(opt)
                if not items:
                    continue
                option_id = f"{group_prefix}:{idx}:{opt_idx}"
                options.append({
                    "id": option_id,
                    "label": _option_label(items),
                    "items": items,
                })
        elif option_set_type == "equipment_category":
            category = from_block.get("equipment_category") or {}
            cat_index = category.get("index")
            cat_name = category.get("name")
            equipment = categories.get(cat_index, [])
            for opt_idx, item in enumerate(equipment):
                name = item.get("name")
                if not name:
                    continue
                option_id = f"{group_prefix}:{idx}:{opt_idx}"
                options.append({
                    "id": option_id,
                    "label": name,
                    "items": [_make_item(name, 1)],
                })
            if not desc and cat_name:
                desc = f"Choose {cat_name}"

        if not options:
            continue

        group_id = f"{group_prefix}:{idx}"
        groups.append({
            "id": group_id,
            "label": desc or "Choose starting equipment",
            "choose": choose,
            "options": options,
        })

    return groups


def build_class_equipment_choices(class_name: str) -> List[Dict[str, Any]]:
    classes = load_srd("classes", "5e-SRD-Classes.json") or []
    entry = next((c for c in classes if c.get("name", "").lower() == class_name.lower()), None)
    if not entry:
        return []
    index = entry.get("index") or class_name.lower()
    return build_choice_groups(entry.get("starting_equipment_options") or [], f"class:{index}")


def build_background_equipment_choices(background_name: str) -> List[Dict[str, Any]]:
    backgrounds = load_srd("backgrounds", "5e-SRD-Backgrounds.json") or []
    entry = next((b for b in backgrounds if b.get("name", "").lower() == background_name.lower()), None)
    if not entry:
        return []
    index = entry.get("index") or background_name.lower()
    option_blocks = []
    option_blocks.extend(entry.get("starting_equipment_options") or [])
    option_blocks.extend(entry.get("equipment_options") or [])
    return build_choice_groups(option_blocks, f"background:{index}")


def validate_equipment_choices(
    choices: List[Dict[str, Any]],
    selection_map: Dict[str, List[str]],
) -> Tuple[bool, List[str]]:
    errors = []
    for group in choices:
        group_id = group.get("id")
        choose = int(group.get("choose") or 1)
        selected = selection_map.get(group_id, []) if selection_map else []
        if len(selected) != choose:
            errors.append(f"{group_id} requires {choose} selection(s).")
            continue
        valid_ids = {opt.get("id") for opt in group.get("options", [])}
        invalid = [sid for sid in selected if sid not in valid_ids]
        if invalid:
            errors.append(f"{group_id} has invalid selections.")
    return len(errors) == 0, errors


def apply_equipment_choices(
    character,
    selection_map: Dict[str, List[str]],
    choices: List[Dict[str, Any]],
) -> None:
    if not selection_map:
        return

    item_repo = ItemRepository()

    for group in choices:
        group_id = group.get("id")
        selected = set(selection_map.get(group_id, []) or [])
        if not selected:
            continue
        for option in group.get("options", []):
            if option.get("id") not in selected:
                continue
            for item in option.get("items", []) or []:
                name = item.get("name")
                quantity = int(item.get("quantity", 1) or 1)
                kind = item.get("kind")
                if kind == "money":
                    character.inventory.add_item(f"{quantity} {name}", 1)
                    continue
                obj = item_repo.get(name) or name
                character.inventory.add_item(obj, quantity)
