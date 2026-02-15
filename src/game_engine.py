import random as random
from abc import ABC, abstractmethod
from typing import Optional, Dict
from dataclasses import dataclass
from proficiency import ProficiencyType
        
class Dice:
    @staticmethod
    def roll(sides=20, count=1,advantage=None):
        if advantage is None:
            results = [random.randint(1, sides) for _ in range(count)]
            print(f"Individual rolls: {results}")
            total = sum(results)
            print(f"Total: {total}")
            return {"total":total,
                        "dice":results}
        if advantage=="adv":
            if (count!=1 or sides!=20):
                raise ValueError("advantage must be for a one d20 roll")
            else:
                r1 = random.randint(1, sides)
                r2 = random.randint(1, sides)
                print(f"Rolled: {r1} and {r2} -> taking {'highest' if advantage=="adv" else 'lowest'}: {max(r1, r2)}")
                return {"total":max(r1, r2),
                        "dice":[r1,r2]}
        elif advantage=="dis":
            if (count!=1 or sides!=20):
                raise ValueError("advantage must be for a one d20 roll")
            else:
                r1 = random.randint(1, sides)
                r2 = random.randint(1, sides)
                print(f"Rolled: {r1} and {r2} -> taking {'highest' if advantage=="adv" else 'lowest'}: {min(r1, r2)}")
                return {"total":min(r1, r2),
                        "dice":[r1,r2]}
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
        all_rolls = []

        for sides, count in dice_specs:
            # Call Dice.roll() with count, sides, and advantage
            result = Dice.roll(sides=sides, count=count, advantage=advantage)
            all_rolls.extend(result["dice"])

        total = sum(all_rolls)

        
        # Apply any features - these should only affect the dice?
        if features:
            for feature in features:
                all_rolls, total = feature(all_rolls, total)

        # Apply modifiers
        total += modifiers        
        
        # Print debug info
        if len(all_rolls) > 1 or advantage:
            print(f"Final rolls: {all_rolls}")
        print(f"Total after modifiers/features: {total}")

        return {"total": total, "dice": all_rolls}
    

    def roll_attack(self, action,source,target,  advantage=None):
        """
        action: Attack action object
        target: Any creature/object with an AC value
        features: list of callables (rolls, total) -> new rolls, new total
        advantage: passed through to Dice.roll() if needed

        Returns: dict with rolls and final total
        """
        all_rolls = []
        
        result = Dice.roll(sides=20, count=1, advantage=advantage)
        all_rolls.extend(result["dice"])

        total = sum(all_rolls)

        # Apply any features - these should only affect the dice?
        if source.features:
            for feature in source.features:
                all_rolls, total = feature(all_rolls, total)

        # Apply modifiers
        if source.proficency.has_proficiency( ProficiencyType.WEAPON,action.attack_roll["porficiency_type"]):
            prof = source.proficency.proficiency_bonus
        else:
            prof = 0
        total += source.ability_scores.modifier(action.attack_roll["ability"]) + action.attack_roll["bonus"] + prof     
        
        if total>= target.stats.armor_class():
            dmg_dict = dict()
            for val in action.damage:
                result = Dice.roll(sides=val["dice_type"], count=val["dice_amt"])
                all_rolls = [result["dice"]]
                total = sum(all_rolls)
                 # Apply any features - these should only affect the dice?
                if source.features:
                    for feature in source.features:
                        all_rolls, total = feature(all_rolls, total)
                final = total + val["bonus"] + source.ability_scores.modifier(val["ability"]) 
                dmg_dict[val["dmg_type"]] = final

            return{"result":"success",
                   "total": total, 
                   "dice": all_rolls,
                   "damage":dmg_dict}
        else:
            return{"result":"failure",
                   "total": total, 
                   "dice": all_rolls,
                   "damage":None}




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