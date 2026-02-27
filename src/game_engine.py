import random as random
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from proficiency import ProficiencyType
from enum import Enum, auto



# Types of proficiencies one could have
class DamageType(Enum):
    SLASHING = auto()
    PIERCING = auto()
    BLUDGEONING = auto()
    MAGICAL_SLASHING = auto()
    MAGICAL_PIERCING = auto()
    MAGICAL_BLUDGEONING = auto()
    RADIANT = auto()
    NECROTIC = auto()
    FIRE = auto()
    COLD = auto()
    THUNDER = auto()
    LIGHTNING = auto()
    FORCE = auto()
    ACID = auto()
    POISON = auto()
    PSYCHIC = auto()

@dataclass
class RollResult:
    dice: List[int]
    base_total: int
    modifiers: int = 0
    advantage: Optional[str] = None
    is_critical: bool = False
    metadata: Dict = field(default_factory=dict)
    def __repr__(self) -> str:
        return (
            f"RollResult("
            f"total={self.total}, "
            f"dice={self.dice}, "
            f"dice_total={self.base_total}, "
            f"modifiers={self.modifiers}, "
            f"advantage={self.advantage}, "
            f"is_critical={self.is_critical}, "
            f"metadata={self.metadata}"
            f")")

    @property
    def total(self) -> int:
        return self.base_total + self.modifiers

    def add_modifier(self, value: int):
        self.modifiers += value

    def add_metadata(self, key, value):
        self.metadata[key] = value

    def add_roll(self,roll_result):
        self.dice.extend(roll_result.dice)
        self.base_total += roll_result.base_total

@dataclass
class AttackResult:
    attack_roll: RollResult
    hit: bool = False
    is_critical: bool = False
    damage: Optional[Dict[str, RollResult]] = None

@dataclass
class DamageResult:
    damage: Dict["DamageType", List["RollResult"]] = field(default_factory=dict)

    @property
    def total(self) -> int:
        """Return the total of all rolls for all damage types."""
        return sum(
            subroll.total
            for rolls in self.damage.values()
            for subroll in rolls
        )

    def breakdown(self) -> Dict["DamageType", int]:
        """Return a subtotal for each damage type."""
        return {
            dt: sum(subroll.total for subroll in rolls)
            for dt, rolls in self.damage.items()
        }

    def add_damage(self, dmg_type: "DamageType", roll_result: "RollResult"):
        """Add a roll result to a specific damage type."""
        if dmg_type not in self.damage:
            self.damage[dmg_type] = []
        self.damage[dmg_type].append(roll_result)



class Dice:
    @staticmethod
    def roll(sides=20, count=1,advantage=None):
        if advantage is None:
            results = [random.randint(1, sides) for _ in range(count)]
            print(f"Individual rolls: {results}")
            print(f"Total: {sum(results)}")
            if (len(results)==1 and results[0]==20):
                crit=True
            else:
                crit=False
            return RollResult(
                dice=results,
                base_total=sum(results),
                is_critical=crit)
            
        if advantage=="adv":
            if (count!=1 or sides!=20):
                raise ValueError("advantage must be for a one d20 roll")
            else:
                r1 = random.randint(1, sides)
                r2 = random.randint(1, sides)
                print(f"Rolled: {r1} and {r2} -> taking {'highest' if advantage=="adv" else 'lowest'}: {max(r1, r2)}")
                if max(r1, r2)==20:
                    crit=True
                else:
                    crit=False
                return  RollResult(
                    dice=[r1,r2],
                    base_total=max(r1, r2),
                    advantage="adv",
                    is_critical=crit)
            
        elif advantage=="dis":
            if (count!=1 or sides!=20):
                raise ValueError("advantage must be for a one d20 roll")
            else:
                r1 = random.randint(1, sides)
                r2 = random.randint(1, sides)
                print(f"Rolled: {r1} and {r2} -> taking {'highest' if advantage=="adv" else 'lowest'}: {min(r1, r2)}")

                if min(r1, r2)==20:
                    crit=True
                else:
                    crit=False

                return RollResult(
                    dice=[r1,r2],
                    base_total=min(r1, r2),
                    advantage="dis",
                    is_critical=crit) 
            
        else:
            raise ValueError("advantage must be one of adv or dis")


class DiceHandler:
    """
    Handles rolling dice with multiple dice specs, modifiers, and additional features.
    Advantage/disadvantage is handled inside the Dice class, so no extra logic needed here.
    """

    def __init__(self):
        pass

    def roll(self, dice_specs, modifiers=0, features=None, advantage=None):
        """
        dice_specs: list of tuples [(sides, count), ...]
        modifiers: int (flat bonuses)
        features: list of callables (rolls, total) -> new rolls, new total
        advantage: passed through to Dice.roll() if needed

        Returns: dict with rolls and final total
        """

        counter = 0
        for sides, count in dice_specs:
            # Call Dice.roll() with count, sides, and advantage
            if counter==0:
                result = Dice.roll(sides=sides, count=count, advantage=advantage)
            else:
                result.add_roll(Dice.roll(sides=sides, count=count, advantage=advantage))
            counter +=1


        
        # Apply any features - these should only affect the dice?
        if features:
            for feature in features:
                if getattr(feature, "feature_type", None) == "affects_rolls":
                    result = feature.on_d20_roll(result)
        # Apply modifiers
        result.add_modifier(modifiers)        
        
        # Print debug info
        print(f"Final rolls: {result.dice}")
        print(f"Total after modifiers/features: {result.total}")

        return result
    

    def roll_attack(self, action,source,target,  advantage=None):
        """
        action: Attack action object
        target: Any creature/object with an AC value
        features: list of callables (rolls, total) -> new rolls, new total
        advantage: passed through to Dice.roll() if needed

        Returns: dict with rolls and final total
        """

        attack_result = Dice.roll(sides=20, count=1, advantage=advantage)


        # Apply any features - these should only affect the dice?
        if source.features._features:
            for feature in source.features._features:
                if getattr(feature, "feature_type", None) == "affects_rolls":
                    attack_result = feature(attack_result)

        # Apply modifiers
        if action.attack_roll.get("precomputed"):
            attack_result.add_modifier(action.attack_roll["bonus"] )
        else:
            if source.proficiencies.has_proficiency( ProficiencyType.WEAPON,action.proficiency_type):
                prof = source.proficiencies.proficiency_bonus
            else:
                prof = 0
            attack_result.add_modifier(source.ability_scores.modifier(action.attack_roll["ability"]) + action.attack_roll["bonus"] + prof )

        if attack_result.total>= target.stats.armor_class():
            dmg_result = DamageResult()
            for val in action.damage_roll:
                temp_dmg_result = Dice.roll(sides=val["dice_type"], count=val["dice_amount"])
                 # Apply any features - these should only affect the dice?
                if source.features._features:
                    for feature in source.features._features:
                        if getattr(feature, "feature_type", None) == "affects_rolls":
                            temp_dmg_result = feature(temp_dmg_result) 
                if val.get("precomputed"):
                    temp_dmg_result.add_modifier(val["bonus"])
                else:
                    temp_dmg_result.add_modifier(val["bonus"] + source.ability_scores.modifier(val["ability"]))
                dmg_result.add_damage(val["dmg_type"],temp_dmg_result)

            return AttackResult(attack_roll=attack_result,
                                hit=True,
                                is_critical=attack_result.is_critical,
                                damage=dmg_result)
        else:
            return AttackResult(attack_roll=attack_result,
                                hit=False,
                                is_critical=attack_result.is_critical,
                                damage=None)




class CombatTracker:
    def __init__(self):
        self.combatants: set[str] = set()
        self.initiative_order: list[str] = []  # list of combatant IDs
        self.current_turn_index: int = 0
        self.round_number: int = 1
        self.active: bool = False
        self.initiatives = self.get_initiatives()
        self._recalculate_initiative()
    # -----------------------
    # Combat Management
    # -----------------------

    def add_combatant(self, combatant):
        self.combatants.add(combatant)
        self._recalculate_initiative()

    def remove_combatant(self, combatant):
        if combatant in self.combatants:
            self.combatants.remove(combatant)
            self._recalculate_initiative()

    def get_initiatives(self):
        initiatives = dict()
        for combatant in self.combatants:
            initiatives[combatant.name] = combatant.roll_initiative()

    def _recalculate_initiative(self):
        self.initiative_order = sorted(
            self.initiatives.keys(),
            key=lambda cid: self.initiatives[cid],
            reverse=True
        )

    # -----------------------
    # Turn Handling
    # -----------------------

    def start_combat(self):
        self.active = True
        self.round_number = 1
        self.current_turn_index = 0
        self._recalculate_initiative()

    def get_current_combatant(self):
        if not self.initiative_order:
            return None
        cid = self.initiative_order[self.current_turn_index]
        return self.combatants[cid]

    def next_turn(self):
        if not self.active:
            return

        self.current_turn_index += 1

        if self.current_turn_index >= len(self.initiative_order):
            self.current_turn_index = 0
            self.round_number += 1

        current = self.get_current_combatant()
        if current:
            current.reset_turn_resources()

# @dataclass
# class DiceRequest:
#     roll_type: str               # attack, damage, save, check
#     dice: str                    # "1d20", "2d6"
#     modifier: int
#     advantage: Optional[str] = None  # advantage / disadvantage
#     description: str = ""


# class Action(ABC):
#     name: str

#     @abstractmethod
#     def request_roll(self, user, target) -> DiceRequest:
#         pass

#     @abstractmethod
#     def apply_roll(self, user, target, roll_total: int):
#         pass

# @dataclass
# class Weapon:
#     name: str
#     damage_die: str          # e.g. "1d8"
#     damage_type: str         # slashing, piercing
#     properties: list        # finesse, heavy, etc.
#     ability: str             # STR or DEX
#     proficient_group: str   # martial, simple

# class AttackContext:
#     def __init__(self, attacker, target, weapon):
#         self.attacker = attacker
#         self.target = target
#         self.weapon = weapon

#         self.attack_bonus = 0
#         self.damage_bonus = 0
#         self.advantage = False
#         self.disadvantage = False

# class AttackResolver:
#     @staticmethod
#     def resolve(attacker, target, weapon):
#         ctx = AttackContext(attacker, target, weapon)

#         AbilityRules.apply(ctx)
#         ProficiencyRules.apply(ctx)
#         EquipmentRules.apply(ctx)
#         FeatureRules.apply(ctx)
#         ConditionRules.apply(ctx)

#         roll = Dice.roll_d20(ctx)
#         total = roll + ctx.attack_bonus

#         if total >= target.armor_class:
#             DamageResolver.resolve(ctx)



# class WeaponAttackAction(Action):
#     def __init__(self, weapon):
#         self.weapon = weapon
#         self.name = f"Attack with {weapon.name}"
#         self._pending_damage = False

#     def request_roll(self, user, target):
#         if not self._pending_damage:
#             ability_mod = user.ability_mods[self.weapon.ability]
#             proficient = self.weapon.proficient_group in user.proficiencies
#             mod = ability_mod + (user.proficiency_bonus if proficient else 0)

#             return DiceRequest(
#                 roll_type="attack",
#                 dice="1d20",
#                 modifier=mod,
#                 description=f"Attack roll vs AC {target.armor_class}"
#             )

#         # damage roll
#         return DiceRequest(
#             roll_type="damage",
#             dice=self.weapon.damage_die,
#             modifier=user.ability_mods[self.weapon.ability],
#             description=f"{self.weapon.damage_type} damage"
#         )

#     def apply_roll(self, user, target, roll_total: int):
#         if not self._pending_damage:
#             if roll_total >= target.armor_class:
#                 self._pending_damage = True
#                 return {"hit": True, "next": "roll_damage"}
#             return {"hit": False}

#         target.take_damage(roll_total)
#         self._pending_damage = False
#         return {"damage": roll_total}

# class Equipment:
#     def __init__(self):
#         self.weapon: Optional[Weapon] = None

#     def actions(self):
#         actions = []
#         if self.weapon:
#             actions.append(WeaponAttackAction(self.weapon))
#         return actions

# @dataclass
# class Spell:
#     name: str
#     level: int
#     school: str
#     casting_time: str
#     save_ability: Optional[str] = None
#     attack_spell: bool = False
#     damage: Optional[str] = None

# class Spellcasting:
#     def __init__(self, ability: str):
#         self.ability = ability
#         self.spell_slots = {1: 0, 2: 0, 3: 0}
#         self.spells_known: list[Spell] = []
#         self.prepared_spells: list[Spell] = []

#     def spell_attack_bonus(self, character):
#         return (
#             character.ability_mods[self.ability]
#             + character.proficiency_bonus
#         )

#     def spell_save_dc(self, character):
#         return 8 + self.spell_attack_bonus(character)

#     def actions(self):
#         return [
#             CastSpellAction(spell)
#             for spell in self.prepared_spells
#         ]

# class CastSpellAction(Action):
#     def __init__(self, spell):
#         self.spell = spell
#         self.name = f"Cast {spell.name}"

#     def request_roll(self, user, target):
#         if self.spell.attack_spell:
#             return DiceRequest(
#                 roll_type="spell_attack",
#                 dice="1d20",
#                 modifier=user.spellcasting.spell_attack_bonus(user),
#                 description="Spell attack roll"
#             )

#         return DiceRequest(
#             roll_type="saving_throw",
#             dice="1d20",
#             modifier=0,
#             description=f"Target makes a {self.spell.save_ability} save"
#         )

#     def apply_roll(self, user, target, roll_total):
#         return {"roll": roll_total}



# @dataclass
# class GameState:
#     location: str
#     time: str

#     party: Dict[str, PC]
#     npcs: Dict[str, PC]

#     world_flags: Dict[str, bool]
#     quest_state: Dict[str, str]

#     relationships: Dict[str, Dict[str, int]]

#     recent_events: List[str]