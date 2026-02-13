from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Optional

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
    execute: Optional[Callable] = None
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