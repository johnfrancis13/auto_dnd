from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
import math
import random as random

from systems.features import FeatureManager
from rules.conditions import ConditionManager
from rules.effects import EffectsManager
from systems.spellcasting import Spellcasting
from systems.classes import CharClass
from systems.proficiency import ProficiencyManager, ProficiencyType
from systems.races import Race
from systems.items import Item
from systems.resources import ResourcePool, ResourceCategory
from rules.actions import ActionManager
from systems.classes import ClassProgression
from data.srd_loader import load_srd
from systems.equipment_choices import build_choice_groups, apply_equipment_choices, add_equipment_to_inventory
from systems.items import ItemRepository

ABILITY_NAMES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def ability_modifier(score: int) -> int:
    return math.floor((score - 10) / 2)




# Each of the races applies a certain set of bonuses that we can auto add in

# Main factory to create PCs
class PCFactory:
    @staticmethod
    def create_basic(name, # str
                     race, # str name of valid race
                     background, # str name of valid background
                     char_class, # str name of valid class
                     ability_method="standard", # one of [standard, roll, point_buy]
                     ability_score_assignment=None, # ["STR","DEX","CON","INT","WIS","CHA"]
                     ability_score_values=None, # list of valid point buy numbers [8,10,11,13,15,8]
                     equipment_choices=None # dict of equipment choice selections
                     ):
        pc = PC(name, race, background)
        
        # Generate the values
        if ability_method == "standard":
            ability_score_values = AbilityScoreGenerator.standard_array()
        elif ability_method == "roll":
            ability_score_values = AbilityScoreGenerator.roll_4d6_drop_lowest()
        elif ability_method == "point_buy":
            if not ability_score_values:
                raise ValueError("Must provide point buy distribution")
            ability_score_values = AbilityScoreGenerator.point_buy(ability_score_values)
        else:
            raise ValueError(f"Unknown method: {ability_method}, must be one of [standard, roll, point_buy]")
        
        # If assignment not given, default to sorted assignment
        if ability_score_assignment is None:
            # Default priority: str, dex, con, int, wis, cha - should ideally be unique to each class...
            ability_score_assignment =  ["STR","DEX","CON","INT","WIS","CHA"]
        else: # otherwise, validate correct values are provided
            expected = {"STR", "DEX", "CON", "INT", "WIS", "CHA"}
            if len(ability_score_assignment) != 6:
                raise ValueError(f"Must provide exactly 6 abilities, got {len(ability_score_assignment)}: {ability_score_assignment}")
            if set(ability_score_assignment) != expected:
                raise ValueError(f"Keys must be exactly {expected}, got {ability_score_assignment}")

        pc.ability_scores = AbilityScores(pc, dict(zip(ability_score_assignment, sorted(ability_score_values, reverse=True))))
        
        # Apply race bonuses
        if pc.identity.race:
           Race(pc.identity.race).apply(pc)
        
        # Apply background bonuses
        if pc.identity.background:
            Background(pc.identity.background).apply(pc, equipment_choices=equipment_choices)

        # Apply class, etc.
        if char_class:
            pc.classes.add_class(char_class, pc, equipment_choices=equipment_choices)
        
        # If "Spellcasting" is the name of a feature, we need to add some spells to the character... ideally the person gets to pick them
        
        pc.update_saving_throws()
        pc.update_skills()

        # Ensure the character is a valid 5e character
        PCValidator(pc).validate()

        return pc

# Main PC class
class PC:
    def __init__(self, name, race, background):
        self.identity = Identity(name, race, background)
        self.ability_scores = AbilityScores(self)
        self.classes = ClassProgression(self)
        self.proficiencies = ProficiencyManager(self)
        self.resources = ResourcePool(self)
        self.inventory = Inventory(self)
        self.features = FeatureManager(self)
        self.spells = Spellcasting(self)
        self.conditions = ConditionManager(self)
        self.effects = EffectsManager(self)

        self.stats = ComputedStats(self)
        self.actions = ActionManager(self)
        self.short_character_description=None
        self.senses = set()


        # Generate skill scores
        self.skill_scores = dict()
        self.update_skills()

        self.saving_throws = dict()
        self.update_saving_throws()

    def __repr__(self):
        return f"PC({self.identity.name!r} is a level {len(self.classes.classes)} {self.identity.race!r} {self.classes.classes[0]} who is currently sitting at {self.resources.current_hit_points} hit points, with the following attributes: {self.ability_scores.scores})"
    
    def update_skills(self):
        skills = {
            "athletics": "STR",
            "acrobatics": "DEX",
            "sleight_of_hand": "DEX",
            "stealth": "DEX",
            "arcana": "INT",
            "history": "INT",
            "investigation": "INT",
            "nature": "INT",
            "religion": "INT",
            "animal_handling": "WIS",
            "insight": "WIS",
            "medicine": "WIS",
            "perception": "WIS",
            "survival": "WIS",
            "deception": "CHA",
            "intimidation": "CHA",
            "performance": "CHA",
            "persuasion": "CHA",
        }
        
        # Apply the ability score + proficiency bonus
        for skill in skills:
            if skill in self.proficiencies.proficiencies[ProficiencyType.SKILL]:
                self.skill_scores[skill] = self.ability_scores.modifier(skills[skill]) + self.proficiencies.proficiency_bonus
            else:
                self.skill_scores[skill] = self.ability_scores.modifier(skills[skill])
    
    def update_saving_throws(self):
        saving_throws = ["STR","DEX","CON","INT","WIS","CHA"]
        
        # Apply the ability score + proficiency bonus
        for abiility in saving_throws:
            if abiility in self.proficiencies.proficiencies[ProficiencyType.SAVE]:
                self.saving_throws[abiility] = self.ability_scores.modifier(abiility) + self.proficiencies.proficiency_bonus
            else:
                self.saving_throws[abiility] = self.ability_scores.modifier(abiility)





# Who you are
class Identity:
    def __init__(self, name, race, background):
        self.name = name
        self.race = race
        self.background = background
    


class AbilityScoreGenerator:
    @staticmethod
    def standard_array():
        # Returns a list of six scores
        return [15, 14, 13, 12, 10, 8]

    @staticmethod
    def point_buy(distribution):
        """
        distribution: dict of ability -> value
        Enforce point-buy rules here if needed.
        """
        if (len(distribution)!=6):
            raise ValueError("Point buy list must contain exactly 6 integers")
        
        # if any list values are less than 8 or more than 15 raise an error
        if (any(val>15 for val in distribution) or any(val<8 for val in distribution)):
            raise ValueError("No values in point buy distribution may be less than 8 or greater than 15")
        map_dict = {8:0,
                    9:1,
                    10:2,
                    11:3,
                    12:4,
                    13:5,
                    14:7,
                    15:9}
        
        if sum([map_dict[val] for val in distribution])>27:
            raise ValueError("Sum of point buy is greater than 27")
        
         # Returns a list of six scores
        return distribution

    @staticmethod
    def roll_4d6_drop_lowest():
        result = []
        for _ in range(6):
            rolls = sorted([random.randint(1, 6) for _ in range(4)])
            result.append(sum(rolls[1:]))
         # Returns a list of six scores
        return result


class AbilityScores:
    def __init__(self,
                 owner,
                 scores= {
                     "STR": 10,
                     "DEX": 10,
                     "CON": 10,
                     "INT": 10,
                     "WIS": 10,
                     "CHA": 10,
                 }):
        self.owner = owner
        self.scores = scores
        self.ability_names = ["STR","DEX","CON","INT","WIS","CHA"]

    # Retrieves the bonus for the names base ability
    def modifier(self, stat):
        return (self.scores[stat] - 10) // 2
    
    # increases the stored scores using a provided dictionary
    def apply_bonuses(self, bonus_dict):
        for key in bonus_dict:
            if key in self.ability_names:
                self.scores[key] = self.scores[key] + bonus_dict[key]
                print(key,"updated by", bonus_dict[key])


class Inventory:
    def __init__(self, owner):
        self.owner = owner
        self.items = {}  # {Item: quantity}
        self.equipped = set()

    def equip(self, item, equip_or_unequip="equip"):
        # ensure item is in inventory
        if item in self.items:
            if equip_or_unequip=="equip":
                self.equipped.add(item)
                # need a function that runs here to ensure equipped item effects are applied properly
                self._maybe_add_item_action(item)
            elif equip_or_unequip=="unequip":
                if item in self.equipped:
                    self.equipped.remove(item)
                # need a function that runs here to ensure equipped item effects are applied properly
                self._maybe_remove_item_action(item)
            else:
                raise ValueError(f"equip_or_unequip must be one of equip or unequip, not {equip_or_unequip}")

        else:
            raise ValueError("Cannot equip or unequip an item that is not in inventory.")

    def get(self, item_name):
        for obj in self.items:
            if hasattr(obj, "name") and obj.name == item_name:
                return obj
            if str(obj) == item_name:
                return obj
        return None
        
    def add_item(self, item, quantity=1):
        self.items[item] = self.items.get(item, 0) + quantity
        if not getattr(self.owner, "resources", None):
            return
        raw = getattr(item, "raw", None) or {}
        desc = raw.get("desc")
        if isinstance(desc, list):
            desc = " ".join(desc)
        if desc:
            category = ResourceCategory.ITEM_CHARGE
            self.owner.resources.apply_text_resource(
                name=getattr(item, "name", None) or str(item),
                text=desc,
                source=getattr(item, "name", None),
                category=category,
            )

    def remove_item(self, item, quantity=1):
        if item not in self.items:
            raise ValueError("Item not in inventory")

        self.items[item] -= quantity
        if self.items[item] <= 0:
            del self.items[item]
            if item in self.equipped:
                self.equipped.remove(item)
                self._maybe_remove_item_action(item)

    def _maybe_add_item_action(self, item):
        if not getattr(self.owner, "actions", None):
            return
        try:
            from rules.action_factory import weapon_action_from_item, weapon_action_from_name
        except Exception:
            return

        action = None
        if hasattr(item, "raw"):
            action = weapon_action_from_item(item.raw)
        if action is None:
            name = getattr(item, "name", None) or str(item)
            action = weapon_action_from_name(name)

        if action and action.id not in self.owner.actions._actions:
            self.owner.actions.add(action)

    def _maybe_remove_item_action(self, item):
        if not getattr(self.owner, "actions", None):
            return
        try:
            from rules.action_factory import weapon_action_from_item, weapon_action_from_name
        except Exception:
            return

        action = None
        if hasattr(item, "raw"):
            action = weapon_action_from_item(item.raw)
        if action is None:
            name = getattr(item, "name", None) or str(item)
            action = weapon_action_from_name(name)

        if action:
            self.owner.actions.remove(action.id)



class Background:
    def __init__(self, id):
        self.id = id
        backgrounds = load_srd("backgrounds", "5e-SRD-Backgrounds.json")
        self.background_data = next(
            (b for b in backgrounds if b.get("name", "").lower() == id.lower()),
            None,
        )
        if not self.background_data:
            raise ValueError(f"{id} not a valid background.")


    def apply(self, character, equipment_choices=None):
        profs = {
            ProficiencyType.SKILL: set(),
            ProficiencyType.TOOL: set(),
            ProficiencyType.LANGUAGE: set(),
        }

        starting = self.background_data.get("starting_proficiencies") or []
        profs_list = self.background_data.get("proficiencies") or []
        combined = starting + profs_list
        for prof in combined:
            name = prof.get("name") if isinstance(prof, dict) else str(prof)
            if name.startswith("Skill:"):
                profs[ProficiencyType.SKILL].add(name.replace("Skill:", "").strip().lower())
            elif name.startswith("Tool:"):
                profs[ProficiencyType.TOOL].add(name.replace("Tool:", "").strip().lower())
            elif name.startswith("Language:"):
                profs[ProficiencyType.LANGUAGE].add(name.replace("Language:", "").strip())

        for lang in self.background_data.get("languages") or []:
            if isinstance(lang, dict):
                name = lang.get("name")
            else:
                name = str(lang)
            if name:
                profs[ProficiencyType.LANGUAGE].add(name)

        for prof_type, values in list(profs.items()):
            if not values:
                profs.pop(prof_type)

        if profs:
            character.proficiencies.add_proficiencies(profs)

        feat = self.background_data.get("feat")
        if isinstance(feat, dict) and feat.get("name"):
            character.features.add_feature(feat["name"], character)

        equipment_repo = ItemRepository()
        for entry in self.background_data.get("starting_equipment", []) or []:
            item = entry.get("equipment") or {}
            name = item.get("name")
            qty = entry.get("quantity", 1)
            if not name:
                continue
            add_equipment_to_inventory(character, equipment_repo, name, qty)

        option_blocks = []
        option_blocks.extend(self.background_data.get("starting_equipment_options") or [])
        option_blocks.extend(self.background_data.get("equipment_options") or [])
        choice_groups = build_choice_groups(
            option_blocks,
            f"background:{self.background_data.get('index') or self.id.lower()}",
        )
        apply_equipment_choices(character, equipment_choices or {}, choice_groups)



class ArmorClassContext:
    def __init__(self, pc):
        self.pc = pc
        self.base = 10
        self.dex_cap = None
        self.bonus = 0

    def set_base(self, value):
        self.base = value

    def add_bonus(self, value):
        self.bonus += value

class ComputedStats:
    def __init__(self, pc):
        self.pc = pc
    #     self._ac_cache = self.armor_class()

    def armor_class(self):
        return 10
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
    
    # def total_level(self):
    #     # Simple sum of all classes in ClassProgression

    #     return  len(self.pc.classes.classes)
    
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


# A class to check if a pc is a valid 5e character
class PCValidator:
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

        
