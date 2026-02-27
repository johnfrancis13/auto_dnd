from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Optional
from game_engine import Dice, DiceHandler
from proficiency import ProficiencyType

class ActionType(Enum):
    ACTION = auto()
    BONUS = auto()
    REACTION = auto()
    LAIR = auto()
    LEGENDARY = auto()
    FREE = auto()
    SPECIAL = auto()


@dataclass
class Action:
    id: str
    name: str
    action_type: ActionType
    source: Optional[str] = None  # "Race", "Monk", "Longsword", etc.
    execute: Optional[Callable] = None #
    request_save: Optional[Callable] = None # create a request with the users spell save dc
    attack_roll: Optional[Callable] = None # add any modifiers
    damage_roll: Optional[dict] = None # each damage type needs its own dice
    effects: Optional[dict] = None # each effect should be listed separately
    proficiency_type: Optional[ProficiencyType] = None
    resource_cost: Optional[dict] = None

class ActionManager:
    def __init__(self, owner):
        self.owner = owner
        self._actions = {}

    def add(self, action: Action):
        self._actions[action.id] = action

    def remove(self, action_id: str):
        self._actions.pop(action_id, None)

    def get(self, action_id: str) -> Action:
        return self._actions[action_id]

    def available(self):
        return list(self._actions.values())

    def execute(self, action_id, source, target=None):
        action = self.get(action_id)
        if action.execute:
            return action.execute(source, target)
    
    def attack_roll(self, action_id, source, target=None,adv=None):
        action = self.get(action_id)
        if action.attack_roll:
            attack_result = DiceHandler().roll_attack(action,source,target,advantage=adv) # roll attack, determine if success, roll damage
            return attack_result
    
    def request_save(self, action_id, source, target=None):
        action = self.get(action_id)
        if action.request_save:
            return {"save_request":action.request_save(source, target),
                    "damage":action.damage_roll(source, target)}
        
    def roll_ability_check(self, ability,advantage=None):
        return DiceHandler().roll(dice_specs = [(20,1)],
                                  modifiers=self.owner.ability_scores.modifier(ability), 
                                  features=self.owner.features._features,
                                  advantage=advantage)
    
    def roll_skill_check(self, skill,advantage=None):
        return DiceHandler().roll(dice_specs = [(20,1)],
                                  modifiers=self.owner.skill_scores[skill], 
                                  features=self.owner.features._features,
                                  advantage=advantage)
    
    def roll_saving_throw(self, ability,advantage=None):
        return DiceHandler().roll(dice_specs = [(20,1)],
                                  modifiers=self.owner.saving_throws[ability], 
                                  features=self.owner.features._features,
                                  advantage=advantage)




longsword_attack = Action(
    id="longsword_attack",
    name="Longsword Slash",
    action_type=ActionType.ACTION,
    attack_roll= {"ability":"STR",
                 "bonus":0 ,
                 "proficiency_type":"simple melee"},
    damage_roll=[{"dmg_type" : "slashing",
                  "dice_type": 8,
                  "dice_amount":1,
                  "ability":"STR",
                 "bonus":0}]
)

#DiceHandler.roll_attack( action,source, target, advantage=None))