from character import AbilityScores, Inventory
from resources import ResourcePool, Resource, ResourceCategory, RechargeType
from actions import Action, ActionManager, ActionType
from spellcasting import Spellcasting, SpellRepository
from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict, Union
from conditions import ConditionManager
from features import FeatureManager
from pathlib import Path
import json
import re
from srd_loader import load_srd


# Class to create an NPC
# class NPCFactory:
#     @staticmethod
#     def create_basic(name, # str
#                      race, # str name of valid race
#                      background, # str name of valid background
#                      char_class, # str name of valid class
#                      ability_method="standard", # one of [standard, roll, point_buy]
#                      ability_score_assignment=None, # ["STR","DEX","CON","INT","WIS","CHA"]
#                      ability_score_values=None # list of valid point buy numbers [8,10,11,13,15,8]
#                      ):
#         pc = PC(name, race, background)
        
#         # Generate the values
#         if ability_method == "standard":
#             ability_score_values = AbilityScoreGenerator.standard_array()
#         elif ability_method == "roll":
#             ability_score_values = AbilityScoreGenerator.roll_4d6_drop_lowest()
#         elif ability_method == "point_buy":
#             if not ability_score_values:
#                 raise ValueError("Must provide point buy distribution")
#             ability_score_values = AbilityScoreGenerator.point_buy(ability_score_values)
#         else:
#             raise ValueError(f"Unknown method: {ability_method}, must be one of [standard, roll, point_buy]")
        
#         # If assignment not given, default to sorted assignment
#         if ability_score_assignment is None:
#             # Default priority: str, dex, con, int, wis, cha - should ideally be unique to each class...
#             ability_score_assignment =  ["STR","DEX","CON","INT","WIS","CHA"]
#         else: # otherwise, validate correct values are provided
#             expected = {"STR", "DEX", "CON", "INT", "WIS", "CHA"}
#             if len(ability_score_assignment) != 6:
#                 raise ValueError(f"Must provide exactly 6 abilities, got {len(ability_score_assignment)}: {ability_score_assignment}")
#             if set(ability_score_assignment) != expected:
#                 raise ValueError(f"Keys must be exactly {expected}, got {ability_score_assignment}")

#         pc.ability_scores = AbilityScores(dict(zip(ability_score_assignment, sorted(ability_score_values, reverse=True))))
        
#         # Apply race bonuses
#         if pc.identity.race:
#            Race(pc.identity.race).apply(pc)
        
#         # Apply background bonuses
#         if pc.identity.background:
#             Background(pc.identity.background).apply(pc)

#         # Apply class, etc.
#         if char_class:
#             pc.classes.add_class(char_class, pc)
        
#         # Ensure the character is a valid 5e character
#         NPCValidator(pc).validate()

#         return pc

def parse_attack(text: str):
    attack_roll = {
        "ability": None,
        "bonus": 0,
        "proficiency_type": None,
        "precomputed": True
    }

    damage_roll = []
    attack_range = None

    # #  Attack type
    # attack_type_match = re.search(r"(Melee|Ranged) (Weapon|Spell) Attack:", text)
    # if attack_type_match:
    #     kind, category = attack_type_match.groups()
    #     attack_roll["proficiency_type"] = f"{kind.lower()} {category.lower()}"

    # Hit bonus
    hit_match = re.search(r"\+(\d+) to hit", text)
    if hit_match:
        attack_roll["bonus"] = int(hit_match.group(1))

    reach_match = re.search(r"reach\s+(\d+)\s*ft", text, re.IGNORECASE)
    if reach_match:
        attack_range = int(reach_match.group(1))

    range_match = re.search(r"range\s+(\d+)\s*/\s*\d+\s*ft", text, re.IGNORECASE)
    if range_match:
        attack_range = int(range_match.group(1))

    #  Damage dice and type
    dmg_match = re.search(
        r"\((\d+)d(\d+)(\s*[+-]\s*\d+)?\)\s+(\w+)\s+damage",
        text
    )

    if dmg_match:
        dice_amount = int(dmg_match.group(1))
        dice_type = int(dmg_match.group(2))
        bonus = dmg_match.group(3)
        dmg_type = dmg_match.group(4)
        bonus_value = 0
        if bonus:
            bonus_value = int(bonus.replace(" ", ""))

        damage_roll.append({
            "dmg_type": dmg_type,
            "dice_type": dice_type,
            "dice_amount": dice_amount,
            "ability": None,
            "bonus": bonus_value,
            "precomputed": True
        })

    return attack_roll, damage_roll, attack_range


def _extract_hp_value(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        return int(match.group(0)) if match else None
    return None


def _clean_npc_name(value: Optional[str]) -> str:
    name = value or ""
    return name.replace(" (Copy)", "").strip()

@dataclass
class NPC:
    abilities: Any
    name: str
    description: str
    size: str
    type: str
    alignment: str
    traits: list
    senses: str
    skills: str
    ac: int
    hp: int
    hd: str
    cr: str
    damagethreshold: int
    xp: int
    speed: str
    languages: str
    stats: "ComputedStats" = field(init=False)

    def __post_init__(self):
        self.stats = ComputedStats(self)
        self.actions = ActionManager(self)
        self.spells = Spellcasting(self)
        self.resources = ResourcePool(self)
        self.ability_scores = AbilityScores(self,scores=self.abilities)
        self.inventory = Inventory(self)
        self.conditions = ConditionManager(self)
        self.features = FeatureManager(self)


# Create NPC from json data, need a separate function to create a random npc
def _format_speed(speed):
    if isinstance(speed, str):
        return speed
    if isinstance(speed, dict):
        parts = []
        for key, value in speed.items():
            parts.append(f"{key} {value}")
        return ", ".join(parts)
    return ""


def _extract_ac(value):
    if isinstance(value, int):
        return value
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first.get("value") or first.get("armor_class") or 10
    if isinstance(value, dict):
        return value.get("value") or value.get("armor_class") or 10
    return 10


def _join_desc(desc):
    if isinstance(desc, list):
        return " ".join(desc)
    return desc or ""


def create_npc(npc_dict):
    ability_scores = {
        "STR": npc_dict.get("strength"),
        "DEX": npc_dict.get("dexterity"),
        "CON": npc_dict.get("constitution"),
        "INT": npc_dict.get("intelligence"),
        "WIS": npc_dict.get("wisdom"),
        "CHA": npc_dict.get("charisma"),
    }

    NPC_new = NPC(
        abilities=ability_scores,
        name=npc_dict.get("name", ""),
        description=_join_desc(npc_dict.get("desc", "")),
        size=npc_dict.get("size", ""),
        type=npc_dict.get("type", ""),
        alignment=npc_dict.get("alignment", ""),
        traits=npc_dict.get("special_abilities", []) or [],
        senses=npc_dict.get("senses", {}),
        skills=npc_dict.get("skills", {}),
        ac=_extract_ac(npc_dict.get("armor_class")),
        hp=npc_dict.get("hit_points"),
        hd=npc_dict.get("hit_dice", ""),
        cr=npc_dict.get("challenge_rating", ""),
        damagethreshold=npc_dict.get("damage_threshold", 0),
        xp=npc_dict.get("xp", 0),
        speed=_format_speed(npc_dict.get("speed", "")),
        languages=npc_dict.get("languages", ""),
    )

    base_hp = _extract_hp_value(npc_dict.get("hit_points"))
    if base_hp is not None:
        NPC_new.resources.max_hit_points = base_hp
        NPC_new.resources.current_hit_points = base_hp

    action_groups = [
        ("actions", ActionType.ACTION),
        ("bonus_actions", ActionType.BONUS),
        ("reactions", ActionType.REACTION),
        ("legendary_actions", ActionType.LEGENDARY),
    ]

    for key, action_type in action_groups:
        for action in npc_dict.get(key, []) or []:
            desc = _join_desc(action.get("desc", ""))
            attack_roll, damage_roll, attack_range = parse_attack(desc)

            if action.get("attack_bonus") is not None:
                attack_roll["bonus"] = action.get("attack_bonus")

            if action.get("damage"):
                damage_roll = []
                for dmg in action["damage"]:
                    dmg_type = dmg.get("damage_type", {}).get("name")
                    dmg_dice = dmg.get("damage_dice")
                    if dmg_type and dmg_dice:
                        dice_match = re.match(r"(\d+)d(\d+)(\s*[+-]\s*\d+)?", dmg_dice)
                        if dice_match:
                            dice_amount = int(dice_match.group(1))
                            dice_type = int(dice_match.group(2))
                            bonus = dice_match.group(3)
                            bonus_val = int(bonus.replace(" ", "")) if bonus else 0
                            damage_roll.append({
                                "dmg_type": dmg_type.lower(),
                                "dice_type": dice_type,
                                "dice_amount": dice_amount,
                                "ability": None,
                                "bonus": bonus_val,
                                "precomputed": True,
                            })

            NPC_new.actions.add(
                Action(
                    id=action.get("name", ""),
                    name=action.get("name", ""),
                    action_type=action_type,
                    attack_roll=attack_roll,
                    damage_roll=damage_roll,
                    range=attack_range,
                    targeting={"shape": "single"},
                )
            )

    return NPC_new


class NPCRepository:
    def __init__(self, path: Optional[Union[str, Path]] = None):
        self.path = Path(path) if path else None
        self._raw = []
        self._index: Dict[str, dict] = {}
        self._lower_index: Dict[str, str] = {}
        self._load()

    def _load(self):
        if self.path is None:
            self._raw = load_srd("monsters", "5e-SRD-Monsters.json")
        else:
            if not self.path.exists():
                raise FileNotFoundError(f"NPC data file not found: {self.path}")
            with self.path.open("r", encoding="utf-8") as handle:
                self._raw = json.load(handle)
        for entry in self._raw:
            name = _clean_npc_name(entry.get("name"))
            if not name:
                continue
            if name not in self._index:
                self._index[name] = entry
                self._lower_index[name.lower()] = name

    def list_names(self) -> List[str]:
        return sorted(self._index.keys())

    def get_raw(self, name: str) -> Optional[dict]:
        if name in self._index:
            return self._index[name]
        key = self._lower_index.get(name.strip().lower())
        if key:
            return self._index[key]
        return None

    def create(self, name: str) -> NPC:
        raw = self.get_raw(name)
        if raw is None:
            raise KeyError(f"NPC '{name}' not found in repository.")
        return create_npc(raw)


class ComputedStats:
    def __init__(self, pc):
        self.pc = pc
    #     self._ac_cache = self.armor_class()

    def armor_class(self):
        return self.pc.ac
        ctx = ArmorClassContext(self.pc)

        # # Armor & shields
        # self.pc.inventory.modify_armor_class(ctx)

        # # Class & racial features
        # self.pc.features.modify_armor_class(ctx)

        # # Conditions (haste, restrained, etc.)
        # self.pc.conditions.modify_armor_class(ctx)

        # dex_mod = self.pc.ability_scores.modifier("dex")
        if ctx.dex_cap is not None:
            dex_mod = min(dex_mod, ctx.dex_cap)

        return ctx.base + dex_mod + ctx.bonus
    
    # def initiative(self):
    #     # Baseline based on ability, modified by any features, items, spells, etc.

    #     return total_level
    
    # def speed(self):
    #     # Baseline based on race, modified by any features, items, spells, etc.
    #     speed = self.pc.race.get_speed()

    #     speed += self.pc.features.modify_speed()
    #     speed += self.pc.inventory.modify_speed()
    #     speed += self.pc.inventory.modify_speed()

    #     return speed
    # def size(self):
    #     # Baseline based on race, modified by any features, items, spells, etc.
    #     size = self.pc.race.get_size()

    #     size = self.pc.features.modify_speed()
    #     size = self.pc.inventory.modify_speed()
    #     size = self.pc.inventory.modify_speed()

    #     return size
    # def creature_type(self):
    #     # Baseline based on race, modified by any features, items, spells, etc.
    #     creature_type = self.pc.race.get_creature_type()

    #     creature_type = self.pc.features.modify_creature_type()
    #     creature_type = self.pc.inventory.modify_creature_type()
    #     creature_type = self.pc.inventory.modify_creature_type()

    #     return creature_type
    
    # def passive_perception(self):
    #     # Baseline based on ability, modified by any features, items, spells, etc.
        

    #     return total_level
    
    # def spell_save_dc(self):
    #     # Baseline based on class, ability, modified by any features, items, spells, etc.

    #     return total_level

# # Same as above, but connected to random generators
# def create_random_npc(name:str,
#                       cr:int,
#                       race:str):
    
#     return NPC_new


# A class to check if a pc is a valid 5e character
class NPCValidator:
    def __init__(self, pc):
        self.pc = pc

    def validate(self):
        errors = []

        # 1. Abilities: must all be between 1-20 
        for abbr, score in self.pc.ability_scores.scores.items():
            if not (1 <= score <= 20):
                errors.append(f"Ability {abbr} has invalid score {score}")

        # 2. Race: must exist
        if not self.pc.identity.race:
            errors.append("No race assigned")

        # 3. Background: must exist
        if not self.pc.identity.background:
            errors.append("No background assigned")

        # 4. Classes: must have at least one level
        if  (len(self.pc.classes.classes)<1 or len(self.pc.classes.classes)>20):  
            errors.append("Character must have at least one class, and no more than 20 class levels.")

        # # 5. Proficiencies: check if any are missing
        # if not self.proficiencies.valid():
        #     errors.append("Proficiencies not properly assigned")

        # # 6. Features: at least the minimum required for class and race
        # if not self.features.valid():
        #     errors.append("Features missing or inconsistent")

        # # 7. Spells: if spellcasting class, must have spell slots
        # if hasattr(self.spells, "validate") and not self.spells.validate():
        #     errors.append("Spells not valid for spellcasting class")

        if errors:
            raise ValueError("Character validation failed:\n" + "\n".join(errors))
        return True
    




