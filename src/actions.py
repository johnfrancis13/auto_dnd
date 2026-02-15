from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Optional
from game_engine import Dice, DiceHandler
from proficiency import ProficiencyType

class ActionType(Enum):
    ACTION = auto()
    BONUS_ACTION = auto()
    REACTION = auto()
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
    resource_cost: Optional[dict] = None

class ActionManager:
    def __init__(self):
        self._actions = {}

    def add(self, action: Action):
        self._actions[action.id] = action

    def remove(self, action_id: str):
        self._actions.pop(action_id, None)

    def get(self, action_id: str) -> Action:
        return self._actions[action_id]

    def available(self):
        return list(self._actions.values())

    def execute(self, action_id, pc, target=None):
        action = self.get(action_id)
        if action.execute:
            return action.execute(pc, target)
    
    def attack_roll(self, action_id, pc, target=None):
        action = self.get(action_id)
        if action.attack_roll:
            return {"attack_roll":action.attack_roll(pc, target),
                    "damage":action.damage_roll(pc, target)}
    
    def request_save(self, action_id, pc, target=None):
        action = self.get(action_id)
        if action.request_save:
            return {"save_request":action.request_save(pc, target),
                    "damage":action.damage_roll(pc, target)}



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