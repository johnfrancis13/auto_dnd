from typing import Dict, List, Optional, Any, Tuple

from srd_loader import load_srd
from spellcasting import SpellRepository, Spell


PREPARED_CASTERS = {"cleric", "druid"}
WIZARD_SPELLBOOK_COUNT = 6


def _class_entry(class_name: str) -> Optional[Dict[str, Any]]:
    classes = load_srd("classes", "5e-SRD-Classes.json") or []
    return next((c for c in classes if c.get("name", "").lower() == class_name.lower()), None)


def _class_level_entry(class_name: str, level: int = 1) -> Optional[Dict[str, Any]]:
    levels = load_srd("levels", "5e-SRD-Levels.json") or []
    for entry in levels:
        if (entry.get("class") or {}).get("name", "").lower() == class_name.lower() and entry.get("level") == level:
            return entry
    return None


def _class_spell_list(class_name: str) -> List[Spell]:
    repo = SpellRepository()
    raw_spells = load_srd("spells", "5e-SRD-Spells.json") or []
    class_spell_names = {
        entry.get("name")
        for entry in raw_spells
        if any(
            cls.get("name", "").lower() == class_name.lower()
            for cls in entry.get("classes", []) or []
        )
    }
    return [spell for spell in repo.all_spells if spell.name in class_spell_names]


def _spell_options(spells: List[Spell], prefix: str) -> List[Dict[str, Any]]:
    options = []
    for idx, spell in enumerate(spells):
        options.append({
            "id": f"{prefix}:{idx}",
            "label": spell.name,
            "spell": spell.name,
            "description": spell.description,
        })
    return options


def build_spell_choice_groups(pc, class_name: str) -> List[Dict[str, Any]]:
    class_entry = _class_entry(class_name)
    level_entry = _class_level_entry(class_name, level=1)
    if not class_entry or not level_entry:
        return []

    spellcasting = class_entry.get("spellcasting")
    if not spellcasting:
        return []

    spellcasting_level = spellcasting.get("level", 1)
    if spellcasting_level and spellcasting_level > 1:
        return []

    spellcasting_ability = (spellcasting.get("spellcasting_ability") or {}).get("name")
    if spellcasting_ability:
        pc.spells.spellcasting_ability = spellcasting_ability
        ability_mod = pc.ability_scores.modifier(spellcasting_ability)
        pc.spells.spell_save_dc = 8 + pc.proficiencies.proficiency_bonus + ability_mod

    spell_list = _class_spell_list(class_name)
    cantrips = [s for s in spell_list if s.level == 0]
    level_one = [s for s in spell_list if s.level == 1]

    groups: List[Dict[str, Any]] = []
    class_index = class_entry.get("index") or class_name.lower()
    spellcasting_info = level_entry.get("spellcasting") or {}
    cantrips_known = int(spellcasting_info.get("cantrips_known") or 0)
    spells_known = spellcasting_info.get("spells_known")

    if cantrips_known and cantrips:
        groups.append({
            "id": f"spells:{class_index}:cantrips",
            "label": "Choose Cantrips",
            "choose": cantrips_known,
            "type": "cantrip",
            "options": _spell_options(cantrips, f"spells:{class_index}:cantrips"),
        })

    if spells_known:
        groups.append({
            "id": f"spells:{class_index}:known",
            "label": "Choose Spells Known",
            "choose": int(spells_known),
            "type": "known",
            "options": _spell_options(level_one, f"spells:{class_index}:known"),
        })
        return groups

    class_key = class_name.lower()
    if class_key in PREPARED_CASTERS:
        ability = (spellcasting.get("spellcasting_ability") or {}).get("name")
        ability_mod = pc.ability_scores.modifier(ability) if ability else 0
        prepared_count = max(1, ability_mod + 1)
        groups.append({
            "id": f"spells:{class_index}:prepared",
            "label": "Prepare Spells",
            "choose": prepared_count,
            "type": "prepared",
            "auto_known": True,
            "options": _spell_options(level_one, f"spells:{class_index}:prepared"),
        })
    elif class_key == "wizard":
        groups.append({
            "id": f"spells:{class_index}:spellbook",
            "label": "Choose Spellbook Spells",
            "choose": WIZARD_SPELLBOOK_COUNT,
            "type": "known",
            "options": _spell_options(level_one, f"spells:{class_index}:spellbook"),
        })

    return groups


def validate_spell_choices(
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


def apply_spell_choices(
    pc,
    selection_map: Dict[str, List[str]],
    choices: List[Dict[str, Any]],
) -> None:
    if not selection_map:
        return
    repo = SpellRepository()
    lookup = {spell.name: spell for spell in repo.all_spells}

    for group in choices:
        group_id = group.get("id")
        group_type = group.get("type")
        selected = set(selection_map.get(group_id, []) or [])
        if group.get("auto_known"):
            for option in group.get("options", []) or []:
                spell_name = option.get("spell")
                spell_obj = lookup.get(spell_name)
                if spell_obj:
                    pc.spells.manage_spells(spell_obj, action="add")
        if not selected:
            continue
        for option in group.get("options", []):
            if option.get("id") not in selected:
                continue
            spell_name = option.get("spell")
            if not spell_name:
                continue
            spell_obj = lookup.get(spell_name)
            if not spell_obj:
                continue
            if group_type == "prepared":
                pc.spells.prepare_spell(spell_obj, action="add")
            else:
                pc.spells.manage_spells(spell_obj, action="add")
