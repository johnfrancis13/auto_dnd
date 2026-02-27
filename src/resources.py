from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Callable, Dict

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

    def get(self, resource_name):
        return next((obj for obj in self.resources if obj.name == resource_name), None)
    
    def add_resource(self, resource: Resource):
        self.resources[resource.id] = resource

    def get(self, resource_id: str) -> Resource | None:
        return self.resources.get(resource_id)

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
        if set_current:
            self.spells[spell_level].current += amount

    def update_spell_slots(self, spell_level,  amount=1, use_spell=False, set_max=False):
        if set_max:
            self.spell_slots[spell_level].maximum = amount
        if use_spell:
            self.spell_slots[spell_level].current += -1*(amount)
            if self.spell_slots[spell_level].current<0:
                self.spell_slots[spell_level].current = 0
                raise ValueError(f"Not enough {spell_level} spell slots remianing to cast a spell.")

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
