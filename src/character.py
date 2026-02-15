from dataclasses import dataclass, field
from typing import Dict, List
import math
import random as random

import pandas as pd

from features import FeatureManager
from conditions import ConditionManager
from effects import EffectsManager
from spellcasting import Spellcasting
from classes import CharClass
from proficiency import ProficiencyManager, ProficiencyType
from races import Race
from items import Item
from resources import ResourcePool
from actions import ActionManager
import ast

ABILITY_NAMES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]


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
                     ability_score_values=None # list of valid point buy numbers [8,10,11,13,15,8]
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

        pc.ability_scores = AbilityScores(dict(zip(ability_score_assignment, sorted(ability_score_values, reverse=True))))
        
        # Apply race bonuses
        if pc.identity.race:
           Race(pc.identity.race).apply(pc)
        
        # Apply background bonuses
        if pc.identity.background:
            Background(pc.identity.background).apply(pc)

        # Apply class, etc.
        if char_class:
            pc.classes.add_class(char_class, pc)
        
        # Ensure the character is a valid 5e character
        PCValidator(pc).validate()

        return pc

# Main PC class
class PC:
    def __init__(self, name, race, background):
        self.identity = Identity(name, race, background)
        self.ability_scores = AbilityScores()
        self.classes = ClassProgression()
        self.proficiencies = ProficiencyManager()
        self.resources = ResourcePool()
        self.inventory = Inventory()
        self.features = FeatureManager()
        self.spells = Spellcasting()
        self.conditions = ConditionManager()
        self.effects = EffectsManager()

        self.stats = ComputedStats(self)
        self.actions = ActionManager()


        # Generate skill scores
        self.skills = self.update_skills()


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
        self.skill_scores = dict()
        for skill in skills:
            if skill in self.proficiencies.proficiencies[ProficiencyType.SKILL]:
                self.skills_scores[skill] = self.ability_scores.modifier(skills[skill]) + self.proficiencies.proficiency_bonus
            else:
                self.skills_scores[skill] = self.ability_scores.modifier(skills[skill])





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
                 scores= {
                     "STR": 10,
                     "DEX": 10,
                     "CON": 10,
                     "INT": 10,
                     "WIS": 10,
                     "CHA": 10,
                 }):
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



class ClassProgression:
    def __init__(self):
        self.classes = []  # e.g. [Fighter, Fighter, Fighter, Rogue]

    def add_class(self, char_class, pc):
        # Create the class fist to make sure char_class is valid
        new_class = CharClass(char_class)
        # add the new class
        self.classes.append(char_class)

        # get the level of the new class being added
        class_level_to_add = sum([1 for val in self.classes if val==char_class])

        # Add in the relevant info for the new class to the pc
        # new_class.apply(class_level_to_add, pc)





class Inventory:
    def __init__(self):
        self.items = {}  # {Item: quantity}

    def add_item(self, item, quantity=1):
        self.items[item] = self.items.get(item, 0) + quantity

    def remove_item(self, item, quantity=1):
        if item not in self.items:
            raise ValueError("Item not in inventory")

        self.items[item] -= quantity
        if self.items[item] <= 0:
            del self.items[item]



class Background:
    def __init__(self, id):
        df = pd.read_csv("../data/woc_backgrounds.csv")
        self.id = id
        if id not in df["name"].values:
            raise ValueError(f"{id} not a valid background.")
        self.racial_data=df[df["name"]==id].iloc[0].to_dict()


    def apply(self, character):
        pass
        # character.ability_scores.apply_bonuses(self.ability_bonuses)

        # for feature in self.features:
        #     character.features.add(feature)



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

    # def armor_class(self):
    #     pass
    #     ctx = ArmorClassContext(self.pc)

    #     # # Armor & shields
    #     # self.pc.inventory.modify_armor_class(ctx)

    #     # # Class & racial features
    #     # self.pc.features.modify_armor_class(ctx)

    #     # # Conditions (haste, restrained, etc.)
    #     # self.pc.conditions.modify_armor_class(ctx)

    #     # dex_mod = self.pc.ability_scores.modifier("dex")
    #     if ctx.dex_cap is not None:
    #         dex_mod = min(dex_mod, ctx.dex_cap)

    #     return ctx.base + dex_mod + ctx.bonus
    
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

        
