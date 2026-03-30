from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from rules.actions import Action, ActionType, SpellAction
from data.srd_loader import load_srd


def _parse_dice(dice: str) -> Optional[Tuple[int, int]]:
    if not dice or "d" not in dice:
        return None
    parts = dice.lower().split("d", 1)
    try:
        count = int(parts[0]) if parts[0] else 1
        sides = int(parts[1])
    except ValueError:
        return None
    return count, sides


def _weapon_proficiency_type(item: Dict[str, Any]) -> Optional[str]:
    category = item.get("category_range") or ""
    category = str(category).strip().lower()
    return category or None


def _weapon_ability(item: Dict[str, Any]) -> Tuple[str, List[str]]:
    weapon_range = str(item.get("weapon_range") or "").strip().lower()
    properties = item.get("properties") or []
    property_indexes = {
        (p.get("index") if isinstance(p, dict) else str(p)).strip().lower()
        for p in properties
        if p
    }

    ability = "STR" if weapon_range == "melee" else "DEX"
    ability_options: List[str] = []

    if "finesse" in property_indexes:
        ability_options = ["STR", "DEX"]
        ability = "STR"

    return ability, ability_options


def weapon_action_from_item(item: Dict[str, Any]) -> Optional[Action]:
    if not isinstance(item, dict):
        return None
    if (item.get("equipment_category") or {}).get("index") != "weapon":
        return None

    damage = item.get("damage") or {}
    damage_dice = damage.get("damage_dice")
    parsed = _parse_dice(damage_dice)
    if not parsed:
        return None
    dice_amount, dice_type = parsed

    dmg_type = (damage.get("damage_type") or {}).get("index") or "bludgeoning"

    ability, ability_options = _weapon_ability(item)
    prof_type = _weapon_proficiency_type(item)

    range_block = item.get("throw_range") or item.get("range") or {}
    range_normal = range_block.get("normal")

    index = item.get("index") or item.get("name", "").strip().lower().replace(" ", "-")
    name = item.get("name") or index

    return Action(
        id=f"weapon:{index}",
        name=f"{name} Attack",
        action_type=ActionType.ACTION,
        source=name,
        attack_roll={
            "ability": ability,
            "ability_options": ability_options,
            "bonus": 0,
            "proficiency_type": prof_type,
        },
        damage_roll=[
            {
                "dmg_type": dmg_type,
                "dice_type": dice_type,
                "dice_amount": dice_amount,
                "ability": ability,
                "ability_options": ability_options,
                "bonus": 0,
            }
        ],
        range=range_normal,
        targeting={"shape": "single"},
        max_targets=1,
    )


def build_weapon_actions(equipment_data: List[Dict[str, Any]]) -> Dict[str, Action]:
    actions: Dict[str, Action] = {}
    for item in equipment_data or []:
        action = weapon_action_from_item(item)
        if action:
            actions[action.id] = action
    return actions


def load_weapon_actions_from_srd() -> Dict[str, Action]:
    equipment = load_srd("equipment", "5e-SRD-Equipment.json")
    return build_weapon_actions(equipment or [])


_WEAPON_INDEX_BY_NAME: Optional[Dict[str, Dict[str, Any]]] = None


def _weapon_index_by_name() -> Dict[str, Dict[str, Any]]:
    global _WEAPON_INDEX_BY_NAME
    if _WEAPON_INDEX_BY_NAME is not None:
        return _WEAPON_INDEX_BY_NAME
    equipment = load_srd("equipment", "5e-SRD-Equipment.json") or []
    index: Dict[str, Dict[str, Any]] = {}
    for item in equipment:
        name = (item.get("name") or "").strip().lower()
        if name:
            index[name] = item
    _WEAPON_INDEX_BY_NAME = index
    return _WEAPON_INDEX_BY_NAME


def weapon_action_from_name(name: str) -> Optional[Action]:
    if not name:
        return None
    item = _weapon_index_by_name().get(name.strip().lower())
    if not item:
        return None
    return weapon_action_from_item(item)


def _parse_range(range_text: Optional[str]) -> Optional[int]:
    if not range_text:
        return None
    if isinstance(range_text, (int, float)):
        return int(range_text)
    text = str(range_text).lower()
    if "feet" in text:
        try:
            return int(text.split("feet")[0].strip())
        except ValueError:
            return None
    return None


def _parse_damage_dice_from_table(table: Dict[str, str]) -> Optional[Tuple[int, int]]:
    if not table:
        return None
    try:
        keys = sorted(int(k) for k in table.keys())
    except ValueError:
        return None
    if not keys:
        return None
    return _parse_dice(table[str(keys[0])])


def spell_action_from_spell(spell: Dict[str, Any]) -> Optional[SpellAction]:
    if not isinstance(spell, dict):
        return None

    damage = spell.get("damage") or {}
    damage_type = (damage.get("damage_type") or {}).get("index")
    dmg_table_slot = damage.get("damage_at_slot_level") or {}
    dmg_table_level = damage.get("damage_at_character_level") or {}

    dice = None
    scaling = None
    if dmg_table_slot:
        dice = _parse_damage_dice_from_table(dmg_table_slot)
        scaling = {"mode": "slot_level", "table": dmg_table_slot}
    elif dmg_table_level:
        dice = _parse_damage_dice_from_table(dmg_table_level)
        scaling = {"mode": "character_level", "table": dmg_table_level}
    elif damage.get("damage_dice"):
        dice = _parse_dice(damage.get("damage_dice"))

    if not dice or not damage_type:
        return None

    dice_amount, dice_type = dice

    attack_type = spell.get("attack_type")
    dc_block = spell.get("dc") or {}
    dc_type = (dc_block.get("dc_type") or {}).get("name")
    dc_success = dc_block.get("dc_success")

    is_attack_spell = bool(attack_type)
    is_save_spell = bool(dc_type)
    if not (is_attack_spell or is_save_spell):
        return None

    name = spell.get("name") or spell.get("index")
    index = spell.get("index") or name.lower().replace(" ", "-")

    action = SpellAction(
        id=f"spell:{index}",
        name=f"Cast {name}",
        action_type=ActionType.ACTION,
        source=name,
        spell_level=int(spell.get("level", 0)),
        school=(spell.get("school") or {}).get("name"),
        range=_parse_range(spell.get("range")),
        targeting={"shape": "single"},
        max_targets=1,
        scaling=scaling,
        damage_roll=[
            {
                "dmg_type": damage_type,
                "dice_type": dice_type,
                "dice_amount": dice_amount,
                "ability": "SPELLCASTING",
                "bonus": 0,
            }
        ],
    )

    if is_attack_spell:
        action.attack_roll = {
            "ability": "SPELLCASTING",
            "bonus": 0,
            "proficiency_type": "spell",
        }
    if is_save_spell:
        action.save = {
            "ability": str(dc_type).upper(),
            "dc": "spell_save_dc",
            "on_success": dc_success or "none",
        }

    return action


def build_spell_actions(spell_data: List[Dict[str, Any]]) -> Dict[str, SpellAction]:
    actions: Dict[str, SpellAction] = {}
    for spell in spell_data or []:
        action = spell_action_from_spell(spell)
        if action:
            actions[action.id] = action
    return actions


def load_spell_actions_from_srd() -> Dict[str, SpellAction]:
    spells = load_srd("spells", "5e-SRD-Spells.json")
    return build_spell_actions(spells or [])


_SPELL_INDEX_BY_NAME: Optional[Dict[str, Dict[str, Any]]] = None


def _spell_index_by_name() -> Dict[str, Dict[str, Any]]:
    global _SPELL_INDEX_BY_NAME
    if _SPELL_INDEX_BY_NAME is not None:
        return _SPELL_INDEX_BY_NAME
    spells = load_srd("spells", "5e-SRD-Spells.json") or []
    index: Dict[str, Dict[str, Any]] = {}
    for spell in spells:
        name = (spell.get("name") or "").strip().lower()
        if name:
            index[name] = spell
    _SPELL_INDEX_BY_NAME = index
    return _SPELL_INDEX_BY_NAME


def spell_action_from_name(name: str) -> Optional[SpellAction]:
    if not name:
        return None
    spell = _spell_index_by_name().get(name.strip().lower())
    if not spell:
        return None
    return spell_action_from_spell(spell)
