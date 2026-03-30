from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Dict, Any, Tuple

import json
import re

from srd_loader import load_srd

# Types of resources one could have
class ResourceCategory(Enum):
    SPELL_SLOT = auto()
    CLASS_RESOURCE = auto()
    FEATURE_USE = auto()
    ITEM_CHARGE = auto()
    LIMITED_USE = auto()
    CUSTOM = auto()

class RechargeType(Enum):
    SHORT_REST = auto()
    LONG_REST = auto()
    DAILY = auto()
    TURN = auto()
    NONE = auto()


@dataclass
class Resource:
    id: str                     # unique key (e.g. "ki_points")
    name: str                   # display name
    category: ResourceCategory
    current: int
    maximum: int
    recharge: RechargeType  # RechargeType.LONG_REST etc.
    max_calc: Optional[Callable[["Character"], int]] = None
    scaling_stat: Optional[str] = None  # "wisdom", "proficiency_bonus", etc.
    source: Optional[str] = None  # "Monk", "Magic Item", "Feat"

    def max_value(self, character):
        if self.max_calc is None:
            return self.maximum
        value = self.max_calc(character)
        self.maximum = value
        return value


class ResourcePool:
    def __init__(self, owner):
        self.owner = owner
        self.max_hit_points = 0
        self.current_hit_points = 0
        self.hit_die: Dict[int, int] = {}
        self.death_saves = {"success": 0, "failure": 0}

        spell_types = ["cantrips"]+["Level_"+str(a+1) for a in range(9)]

        # Create a holder for the amount of spells a character can know
        self.spells ={a:Resource(id=a+"_spells",
                                 name=a+" Spells",
                                   category=ResourceCategory.CLASS_RESOURCE,
                                     current=0,
                                     maximum=0,
                                     recharge=RechargeType.NONE,
                                     source="class"
                                     )  for a in spell_types}
        
        # Create a holder for the amount of spell slots a character has access to
        self.spell_slots ={a:Resource(id=a+"_spell_slots",
                                 name=a+" Spell Slots",
                                   category=ResourceCategory.SPELL_SLOT,
                                     current=0,
                                     maximum=0,
                                     recharge=RechargeType.LONG_REST, # for Warlock switch to short rest
                                     source="class"
                                     )  for a in spell_types}
        # 🔥 unified system
        self.resources: Dict[str, Resource] = {}

    def add_resource(self, resource: Resource):
        if resource.max_calc is not None:
            try:
                resource.current = resource.max_value(self.owner)
            except Exception:
                pass
        self.resources[resource.id] = resource

    def get(self, resource_id: str) -> Optional[Resource]:
        return self.resources.get(resource_id)

    def apply_class_resources(self, class_index: str, class_level: int) -> None:
        class_index = (class_index or "").strip().lower()
        if not class_index or class_level <= 0:
            return
        levels = load_srd("levels", "5e-SRD-Levels.json") or []
        entry = next(
            (
                lvl for lvl in levels
                if (lvl.get("class") or {}).get("index") == class_index
                and int(lvl.get("level") or 0) == int(class_level)
            ),
            None,
        )
        if not entry:
            return
        class_specific = entry.get("class_specific") or {}
        if not class_specific:
            return
        mapping = _load_resource_mappings().get("class_specific", {})
        if not mapping:
            return
        class_name = (entry.get("class") or {}).get("name")
        for key, definition in mapping.items():
            if key not in class_specific:
                continue
            value = class_specific.get(key)
            if value is None:
                continue
            try:
                amount = int(value)
            except (TypeError, ValueError):
                continue
            resource = _resource_from_mapping(definition, amount, source=class_name)
            if not resource:
                continue
            existing = self.resources.get(resource.id)
            if existing:
                existing.maximum = resource.maximum
                existing.recharge = resource.recharge
                existing.category = resource.category
                existing.name = resource.name
                existing.source = resource.source
                if existing.current > existing.maximum:
                    existing.current = existing.maximum
            else:
                self.add_resource(resource)

    def apply_text_resource(
        self,
        name: str,
        text: str,
        source: Optional[str] = None,
        category: ResourceCategory = ResourceCategory.FEATURE_USE,
    ) -> Optional[Resource]:
        if not name or not text:
            return None
        resource = _heuristic_resource_from_text(
            name=name,
            text=text,
            source=source,
            category=category,
            owner=self.owner,
        )
        if not resource:
            return None
        existing = self.resources.get(resource.id)
        if existing:
            return existing
        self.add_resource(resource)
        return resource

    def spend(self, resource_id: str, amount: int = 1):
        resource = self.get(resource_id)
        if not resource:
            raise ValueError(f"Resource '{resource_id}' not found")

        if resource.current < amount:
            raise ValueError(f"Not enough {resource.name}")

        resource.current -= amount

    def restore(self, resource_id: str, amount: int = 1):
        resource = self.get(resource_id)
        if not resource:
            raise ValueError(f"Resource '{resource_id}' not found")

        resource.current = min(resource.maximum, resource.current + amount)

    def apply_rest(self, rest_type: RechargeType):
        for resource in self.resources.values():
            if resource.recharge == rest_type:
                resource.current = resource.maximum

    def update_health(self, amount:int):
        self.max_hit_points += amount
        self.current_hit_points += amount

    def update_hit_die(self, dice:int, amount:int):
        self.hit_die[dice] =  self.hit_die.get(dice, 0) + amount

    def update_spell_access(self, spell_level,  amount=1, set_current=False, set_max=False):
        if set_max:
            self.spells[spell_level].maximum = amount
            if self.spells[spell_level].current < amount:
                self.spells[spell_level].current = amount
        if set_current:
            self.spells[spell_level].current += amount

    def update_spell_slots(self, spell_level,  amount=1, use_spell=False, set_max=False):
        if set_max:
            self.spell_slots[spell_level].maximum = amount
            if self.spell_slots[spell_level].current < amount:
                self.spell_slots[spell_level].current = amount
        if use_spell:
            self.spell_slots[spell_level].current += -1*(amount)
            if self.spell_slots[spell_level].current<0:
                self.spell_slots[spell_level].current = 0
                raise ValueError(f"Not enough {spell_level} spell slots remianing to cast a spell.")


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RESOURCE_MAP_PATH = DATA_DIR / "resources.json"


def _load_resource_mappings() -> Dict[str, Any]:
    if not RESOURCE_MAP_PATH.exists():
        return {}
    try:
        with RESOURCE_MAP_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def _enum_from_string(enum_cls, value, default):
    if value is None:
        return default
    if isinstance(value, enum_cls):
        return value
    text = str(value).strip().upper()
    try:
        return enum_cls[text]
    except KeyError:
        return default


def _resource_from_mapping(definition: Dict[str, Any], amount: int, source: Optional[str] = None) -> Optional[Resource]:
    if not definition:
        return None
    resource_id = definition.get("id")
    name = definition.get("name")
    if not resource_id and name:
        resource_id = name.lower().replace(" ", "_")
    if not resource_id:
        return None
    category = _enum_from_string(ResourceCategory, definition.get("category"), ResourceCategory.CUSTOM)
    recharge = _enum_from_string(RechargeType, definition.get("recharge"), RechargeType.NONE)
    display_name = name or resource_id.replace("_", " ").title()
    resource_source = definition.get("source") or source
    return Resource(
        id=resource_id,
        name=display_name,
        category=category,
        current=amount,
        maximum=amount,
        recharge=recharge,
        source=resource_source,
    )


def _resource_id_from_name(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return cleaned.strip("_")


def _extract_recharge(text: str) -> RechargeType:
    lowered = text.lower()
    if "short or long rest" in lowered:
        return RechargeType.SHORT_REST
    if "short rest" in lowered:
        return RechargeType.SHORT_REST
    if "long rest" in lowered:
        return RechargeType.LONG_REST
    if "at dawn" in lowered or "each day" in lowered or "per day" in lowered:
        return RechargeType.DAILY
    return RechargeType.NONE


def _extract_count(text: str) -> Optional[int]:
    lowered = text.lower()
    match = re.search(r"\b(\d+)\s+charges?\b", lowered)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d+)\s+times?\b", lowered)
    if match:
        return int(match.group(1))
    if re.search(r"\bthrice\b", lowered):
        return 3
    if re.search(r"\btwice\b", lowered):
        return 2
    if re.search(r"\bonce\b", lowered):
        return 1
    return None


def _extract_scaling_calc(text: str) -> Optional[Callable[[Any], int]]:
    lowered = text.lower()
    if "proficiency bonus" in lowered:
        return lambda c: getattr(c.proficiencies, "proficiency_bonus", 0)
    ability_map = {
        "strength": "STR",
        "dexterity": "DEX",
        "constitution": "CON",
        "intelligence": "INT",
        "wisdom": "WIS",
        "charisma": "CHA",
    }
    for label, stat in ability_map.items():
        if f"{label} modifier" in lowered:
            return lambda c, s=stat: c.ability_scores.modifier(s)
    return None


def _heuristic_resource_from_text(
    name: str,
    text: str,
    source: Optional[str],
    category: ResourceCategory,
    owner: Any,
) -> Optional[Resource]:
    if not text:
        return None
    count = _extract_count(text)
    max_calc = None
    if count is None:
        max_calc = _extract_scaling_calc(text)
        if max_calc is None:
            return None
        try:
            count = int(max_calc(owner))
        except Exception:
            count = 0
    recharge = _extract_recharge(text)
    resource_id = _resource_id_from_name(name)
    return Resource(
        id=resource_id,
        name=name,
        category=category,
        current=count,
        maximum=count,
        recharge=recharge,
        max_calc=max_calc,
        source=source,
    )

# Example resources
# Resource(
#         id="rage",
#         name="Rage",
#         category=ResourceCategory.CLASS_RESOURCE,
#         current=3,
#         maximum=3,
#         recharge=RechargeType.LONG_REST,
#         source="Barbarian"
#     )

# Resource(
#         id="ki_points",
#         name="Ki Points",
#         category=ResourceCategory.CLASS_RESOURCE,
#         current=5,
#         maximum=5,
#         recharge=RechargeType.SHORT_REST,
#         max_calc=lambda character: character.monk_level,
#         source="Monk"
#     )

# BARDIC_INSPIRATION = Resource(
#     id="bardic_inspiration",
#     name="Bardic Inspiration",
#     category=ResourceCategory.CLASS_RESOURCE,
#     recharge=RechargeType.LONG_REST,
#     mamax_calcx_func=lambda c: max(1, c.cha_mod),
# )

# WAND_CHARGES = Resource(
#     id="wand_fireballs",
#     name="Wand of Fireballs Charges",
#     category=ResourceCategory.ITEM_CHARGE,
#     recharge=RechargeType.DAILY,
#     max_calc=lambda c: 7,
#     source="Wand of Fireballs"
# )
