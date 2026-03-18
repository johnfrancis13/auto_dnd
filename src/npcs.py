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

def unwrap(value):
    if isinstance(value, dict):
        if '#text' in value:
            text = value['#text']
            if value.get('@type') == 'number':
                return int(text)
            return text
        # recursively unwrap nested dicts
        return {k: unwrap(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [unwrap(v) for v in value]
    return value
    
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
        r"\((\d+)d(\d+)\)\s+(\w+)\s+damage",
        text
    )

    if dmg_match:
        dice_amount = int(dmg_match.group(1))
        dice_type = int(dmg_match.group(2))
        dmg_type = dmg_match.group(3)

        damage_roll.append({
            "dmg_type": dmg_type,
            "dice_type": dice_type,
            "dice_amount": dice_amount,
            "ability": None,
            "bonus": 0,
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


def _clean_npc_name(value: Optional[Union[dict, str]]) -> str:
    if isinstance(value, dict):
        name = value.get("#text", "")
    else:
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
def create_npc(json_data):
    

    npc_dict = unwrap(json_data)

    
    ability_scores = {
        name[:3].upper(): int(ability["score"])
        for name, ability in npc_dict["abilities"].items()
    }

    # Set up the NPC class
    NPC_new = NPC(
        abilities=ability_scores,
        name=_clean_npc_name(npc_dict.get("name")),
        description=npc_dict["text"]["p"],
        size=npc_dict.get("size", {}),
        type=npc_dict.get("type", {}),
        alignment=npc_dict.get("alignment", {}),
        #traits = [npc_dict["traits"][b] for b in npc_dict["traits"]],
        traits = list((npc_dict.get("traits") or {}).values()),
        senses=npc_dict.get("senses", {}),
        skills=npc_dict.get("skills", {}),
        ac=npc_dict.get("ac", {}),
        hp=npc_dict.get("hp", {}),
        hd=npc_dict.get("hd", {}),
        cr=npc_dict.get("cr", {}),
        damagethreshold=npc_dict.get("damagethreshold", {}),
        xp=npc_dict.get("xp", {}),
        speed=npc_dict.get("speed", {}),
        languages=npc_dict.get("languages", {}),
    )

    base_hp = _extract_hp_value(npc_dict.get("hp"))
    if base_hp is not None:
        NPC_new.resources.max_hit_points = base_hp
        NPC_new.resources.current_hit_points = base_hp

    # Create the actions
    action_classes =['actions', 'bonusactions','lairactions','legendaryactions', 'reactions']
    action_types =[ActionType.ACTION,ActionType.BONUS,ActionType.LAIR,ActionType.LEGENDARY, ActionType.REACTION]
    
    for val in range(len(action_classes)):
        if npc_dict[action_classes[val]] is not None:
            for key in  npc_dict[action_classes[val]]:

                attack_roll, damage_roll, attack_range = parse_attack(npc_dict[action_classes[val]][key]["desc"])
                NPC_new.actions.add(
                    Action( id= npc_dict[action_classes[val]][key]["name"],
                            name= npc_dict[action_classes[val]][key]["name"],
                            action_type= action_types[val],
                            attack_roll=attack_roll,
                            damage_roll=damage_roll,
                            range=attack_range,
                            targeting={"shape": "single"})
                    )
                
    # Create the spells
    spell_repo = SpellRepository()
    spell_classes =['innatespells', 'spells']
    
    for val in range(len(spell_classes)):
        if npc_dict[spell_classes[val]] is not None:
            for key in  npc_dict[spell_classes[val]]:
                temp_spell = spell_repo.get(npc_dict[spell_classes[val]][key]["name"])
                if temp_spell is not None:
                    NPC_new.spells.add_spell(
                        temp_spell
                    )
            


    # create resources from each spell slot if they exist
    if npc_dict.get("spellslots"):
        for lvl in npc_dict["spellslots"]:
            NPC_new.resources.add_resource( Resource(id= lvl ,
                                             name= lvl ,
                                             category= ResourceCategory.SPELL_SLOT,
                                             current= npc_dict["spellslots"][lvl],
                                             maximum= npc_dict["spellslots"][lvl],
                                             recharge= RechargeType.LONG_REST ))

    return NPC_new


class NPCRepository:
    def __init__(self, path: Optional[Union[str, Path]] = None):
        if path is None:
            path = Path(__file__).resolve().parents[1] / "data" / "npc.json"
        self.path = Path(path)
        self._raw = []
        self._index: Dict[str, dict] = {}
        self._lower_index: Dict[str, str] = {}
        self._load()

    def _load(self):
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
    


