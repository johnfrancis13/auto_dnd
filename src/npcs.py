from character import AbilityScores, Inventory
from resources import ResourcePool, Resource, ResourceCategory, RechargeType
from actions import Action, ActionManager, ActionType
from spellcasting import Spellcasting, SpellRepository
from dataclasses import dataclass, field
from typing import List, Any
from conditions import ConditionManager
from features import FeatureManager
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

    # #  Attack type
    # attack_type_match = re.search(r"(Melee|Ranged) (Weapon|Spell) Attack:", text)
    # if attack_type_match:
    #     kind, category = attack_type_match.groups()
    #     attack_roll["proficiency_type"] = f"{kind.lower()} {category.lower()}"

    # Hit bonus
    hit_match = re.search(r"\+(\d+) to hit", text)
    if hit_match:
        attack_roll["bonus"] = int(hit_match.group(1))

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

    return attack_roll, damage_roll

@dataclass
class NPC:
    ability_scores: Any
    name: str
    description: str
    size: str
    type: str
    alignment: str
    traits: list
    resources: Any
    actions: Any
    spells: Any
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
    inventory: Inventory = field(default_factory=Inventory)
    conditions: ConditionManager = field(default_factory=ConditionManager)
    features: FeatureManager = field(default_factory=FeatureManager)
    stats: "ComputedStats" = field(init=False)

    def __post_init__(self):
        self.stats = ComputedStats(self)


def create_npc(json_data):
    

    npc_dict = unwrap(json_data)

    
    ability_scores = {
        name[:3].upper(): int(ability["score"])
        for name, ability in npc_dict["abilities"].items()
    }

    # Create the actions
    actions_manager = ActionManager()
    action_classes =['actions', 'bonusactions','lairactions','legendaryactions', 'reactions']
    action_types =[ActionType.ACTION,ActionType.BONUS,ActionType.LAIR,ActionType.LEGENDARY, ActionType.REACTION]
    
    for val in range(len(action_classes)):
        if npc_dict[action_classes[val]] is not None:
            for key in  npc_dict[action_classes[val]]:

                attack_roll, damage_roll = parse_attack(npc_dict[action_classes[val]][key]["desc"])
                actions_manager.add(
                    Action( id= npc_dict[action_classes[val]][key]["name"],
                            name= npc_dict[action_classes[val]][key]["name"],
                            action_type= action_types[val],
                            attack_roll=attack_roll,
                            damage_roll=damage_roll)
                    )
                
    # Create the spells
    spellcasting = Spellcasting()
    spell_repo = SpellRepository()
    spell_classes =['innatespells', 'spells']
    
    for val in range(len(spell_classes)):
        if npc_dict[spell_classes[val]] is not None:
            for key in  npc_dict[spell_classes[val]]:
                temp_spell = spell_repo.get(npc_dict[spell_classes[val]][key]["name"])
                if temp_spell is not None:
                    spellcasting.add_spell(
                        temp_spell
                    )
            


    # create resources from each spell slot if they exist
    resource_pool = ResourcePool()
    for lvl in npc_dict["spellslots"]:
        resource_pool.add_resource( Resource(id= lvl ,
                                         name= lvl ,
                                         category= ResourceCategory.SPELL_SLOT,
                                         current= npc_dict["spellslots"][lvl],
                                         maximum= npc_dict["spellslots"][lvl],
                                         recharge= RechargeType.LONG_REST ))


    NPC_new = NPC(
        ability_scores=AbilityScores(scores=ability_scores),
        name=npc_dict["name"].replace(" (Copy)", "").strip(),
        description=npc_dict["text"]["p"],
        size=npc_dict["size"],
        type=npc_dict["type"],
        alignment=npc_dict["alignment"],
        traits = [npc_dict["traits"][b] for b in npc_dict["traits"]],
        resources=resource_pool,
        actions = actions_manager,
        spells= spellcasting,
        senses=npc_dict["senses"],
        skills=npc_dict["skills"],
        ac=npc_dict["ac"],
        hp=npc_dict["hp"],
        hd=npc_dict["hd"],
        cr=npc_dict["cr"],
        damagethreshold=npc_dict["damagethreshold"],
        xp=npc_dict["xp"],
        speed=npc_dict["speed"],
        languages=npc_dict["languages"],
    )


    return NPC_new


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
    


