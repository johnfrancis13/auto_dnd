import random as random
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from systems.proficiency import ProficiencyType
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
                choice = "highest" if advantage == "adv" else "lowest"
                print(f"Rolled: {r1} and {r2} -> taking {choice}: {max(r1, r2)}")
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
                choice = "highest" if advantage == "adv" else "lowest"
                print(f"Rolled: {r1} and {r2} -> taking {choice}: {min(r1, r2)}")

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
            attack_result.add_modifier(action.attack_roll["bonus"])
        else:
            prof_type = action.proficiency_type or action.attack_roll.get("proficiency_type")
            prof = 0
            if prof_type:
                if isinstance(prof_type, ProficiencyType):
                    has_prof = source.proficiencies.has_proficiency(ProficiencyType.WEAPON, prof_type)
                    prof = source.proficiencies.proficiency_bonus if has_prof else 0
                else:
                    prof_key = str(prof_type).strip().lower()
                    if prof_key in {"spell", "spellcasting", "spell attack", "spell_attack"}:
                        prof = source.proficiencies.proficiency_bonus
                    else:
                        has_prof = source.proficiencies.has_proficiency(
                            ProficiencyType.WEAPON, prof_key
                        )
                        prof = source.proficiencies.proficiency_bonus if has_prof else 0

            ability = action.attack_roll.get("ability")
            ability_options = action.attack_roll.get("ability_options") or []
            ability_mod = self._resolve_ability_modifier(source, ability, ability_options)

            attack_result.add_modifier(ability_mod + action.attack_roll["bonus"] + prof )

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
                    dmg_ability = val.get("ability")
                    dmg_options = val.get("ability_options") or []
                    dmg_mod = self._resolve_ability_modifier(source, dmg_ability, dmg_options)
                    temp_dmg_result.add_modifier(val["bonus"] + dmg_mod)
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

    def _resolve_ability_modifier(self, source, ability, ability_options=None) -> int:
        ability_options = ability_options or []
        resolved_options = []
        for opt in ability_options:
            if not opt:
                continue
            opt_name = str(opt).strip().upper()
            if opt_name in {"SPELL", "SPELLCASTING"}:
                spell_ability = getattr(source.spells, "spellcasting_ability", None)
                if spell_ability:
                    resolved_options.append(spell_ability)
            else:
                resolved_options.append(opt_name)

        if ability:
            ability_name = str(ability).strip().upper()
            if ability_name in {"SPELL", "SPELLCASTING"}:
                ability_name = getattr(source.spells, "spellcasting_ability", None)
            if ability_name:
                resolved_options.append(ability_name)

        if not resolved_options:
            return 0

        return max(source.ability_scores.modifier(opt) for opt in resolved_options)




class CombatTracker:
    def __init__(self, combatants: Optional[Dict[str, object]] = None):
        self.combatants: Dict[str, object] = combatants or {}
        self.initiatives: Dict[str, int] = {}
        self.initiative_order: list[str] = []  # list of combatant IDs
        self.current_turn_index: int = 0
        self.round_number: int = 1
        self.active: bool = False
        if self.combatants:
            self.roll_initiative()

    # -----------------------
    # Combat Management
    # -----------------------

    def set_combatants(self, combatants: Dict[str, object]):
        self.combatants = combatants
        self.roll_initiative()

    def add_combatant(self, combatant, combatant_id: Optional[str] = None):
        cid = combatant_id or getattr(combatant, "name", str(combatant))
        self.combatants[cid] = combatant
        self.initiatives[cid] = self._roll_initiative(combatant)
        self._recalculate_initiative()

    def remove_combatant(self, combatant_id: str):
        if combatant_id in self.combatants:
            self.combatants.pop(combatant_id)
            self.initiatives.pop(combatant_id, None)
            self._recalculate_initiative()

    def _roll_initiative(self, combatant) -> int:
        roll = Dice.roll(sides=20, count=1)
        dex_mod = 0
        if hasattr(combatant, "ability_scores"):
            try:
                dex_mod = combatant.ability_scores.modifier("DEX")
            except Exception:
                dex_mod = 0
        roll.add_modifier(dex_mod)
        return roll.total

    def roll_initiative(self):
        self.initiatives = {}
        for cid, combatant in self.combatants.items():
            self.initiatives[cid] = self._roll_initiative(combatant)
        self._recalculate_initiative()

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
        if not self.initiative_order:
            self.roll_initiative()

    def get_current_combatant_id(self) -> Optional[str]:
        if not self.initiative_order:
            return None
        return self.initiative_order[self.current_turn_index]

    def get_current_combatant(self):
        cid = self.get_current_combatant_id()
        if cid is None:
            return None
        return self.combatants.get(cid)

    def next_turn(self):
        if not self.active or not self.initiative_order:
            return None

        self.current_turn_index += 1

        if self.current_turn_index >= len(self.initiative_order):
            self.current_turn_index = 0
            self.round_number += 1

        current = self.get_current_combatant()
        if current and hasattr(current, "reset_turn_resources"):
            current.reset_turn_resources()
        return self.get_current_combatant_id()


@dataclass
class CombatActionLog:
    actor: str
    action_id: str
    action_name: str
    target: Optional[str] = None
    hit: Optional[bool] = None
    critical: bool = False
    attack_total: Optional[int] = None
    attack_roll_detail: Optional[Dict[str, Any]] = None
    damage_total: int = 0
    damage_breakdown: Optional[Dict[str, int]] = None
    damage_rolls_detail: Optional[List[Dict[str, Any]]] = None
    target_hp_before: Optional[int] = None
    target_hp_after: Optional[int] = None
    save_ability: Optional[str] = None
    save_total: Optional[int] = None
    save_dc: Optional[int] = None
    save_success: Optional[bool] = None
    save_roll_detail: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class CombatEngine:
    def __init__(self, combatants: Dict[str, object]):
        self.combatants = combatants
        self.tracker = CombatTracker(combatants)

    def start(self):
        self.tracker.start_combat()

    def current_turn_id(self) -> Optional[str]:
        return self.tracker.get_current_combatant_id()

    def _coerce_hp(self, value) -> Optional[int]:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            import re
            match = re.search(r"\d+", value)
            return int(match.group(0)) if match else None
        return None

    def _get_hp(self, combatant) -> Optional[int]:
        if hasattr(combatant, "resources"):
            return combatant.resources.current_hit_points
        if hasattr(combatant, "hp"):
            return self._coerce_hp(combatant.hp)
        return None

    def _set_hp(self, combatant, value: int):
        if hasattr(combatant, "resources"):
            combatant.resources.current_hit_points = value
            if combatant.resources.max_hit_points < value:
                combatant.resources.max_hit_points = value
        elif hasattr(combatant, "hp"):
            combatant.hp = value

    def _ensure_hp_initialized(self, combatant):
        if not hasattr(combatant, "resources"):
            return
        if combatant.resources.max_hit_points != 0:
            return
        base_hp = None
        if hasattr(combatant, "hp"):
            base_hp = self._coerce_hp(combatant.hp)
        if base_hp is not None:
            combatant.resources.max_hit_points = base_hp
            combatant.resources.current_hit_points = base_hp

    def apply_damage(self, target, amount: int) -> Optional[int]:
        self._ensure_hp_initialized(target)
        hp_before = self._get_hp(target)
        if hp_before is None:
            return None
        new_hp = max(0, hp_before - amount)
        self._set_hp(target, new_hp)
        return new_hp

    def is_defeated(self, combatant) -> bool:
        hp = self._get_hp(combatant)
        return hp is not None and hp <= 0

    def resolve_attack_action(
        self,
        attacker_id: str,
        action_id: str,
        target_id: str,
        advantage: Optional[str] = None,
        slot_level: Optional[int] = None,
        caster_level: Optional[int] = None,
    ) -> CombatActionLog:
        attacker = self.combatants.get(attacker_id)
        target = self.combatants.get(target_id)
        if attacker is None or target is None:
            return CombatActionLog(
                actor=attacker_id,
                action_id=action_id,
                action_name=action_id,
                target=target_id,
                notes="Invalid attacker or target.",
            )

        try:
            action = attacker.actions.get(action_id)
        except KeyError:
            action = None
        log = CombatActionLog(
            actor=attacker_id,
            action_id=action_id,
            action_name=action.name if action else action_id,
            target=target_id,
        )

        if action is None or not action.attack_roll:
            log.notes = "Action not supported by combat engine."
            return log

        target_hp_before = self._get_hp(target)
        log.target_hp_before = target_hp_before

        scaled_action = self._with_scaled_damage(action, attacker, slot_level, caster_level)
        attack_result = DiceHandler().roll_attack(scaled_action, attacker, target, advantage=advantage)

        if attack_result is None:
            log.notes = "Action did not produce an attack result."
            return log

        log.hit = attack_result.hit
        log.critical = attack_result.is_critical
        log.attack_total = attack_result.attack_roll.total
        log.attack_roll_detail = self._roll_result_detail(attack_result.attack_roll)

        if attack_result.damage:
            log.damage_total = attack_result.damage.total
            log.damage_breakdown = {
                str(dmg_type): subtotal
                for dmg_type, subtotal in attack_result.damage.breakdown().items()
            }
            log.damage_rolls_detail = self._build_damage_rolls_detail(scaled_action, attack_result.damage)
            self.apply_damage(target, log.damage_total)
            log.target_hp_after = self._get_hp(target)
        else:
            log.damage_total = 0
            log.target_hp_after = target_hp_before

        return log

    def resolve_save_action(
        self,
        attacker_id: str,
        action_id: str,
        target_id: str,
        slot_level: Optional[int] = None,
        caster_level: Optional[int] = None,
    ) -> CombatActionLog:
        attacker = self.combatants.get(attacker_id)
        target = self.combatants.get(target_id)
        if attacker is None or target is None:
            return CombatActionLog(
                actor=attacker_id,
                action_id=action_id,
                action_name=action_id,
                target=target_id,
                notes="Invalid attacker or target.",
            )

        try:
            action = attacker.actions.get(action_id)
        except KeyError:
            action = None

        log = CombatActionLog(
            actor=attacker_id,
            action_id=action_id,
            action_name=action.name if action else action_id,
            target=target_id,
        )

        if action is None or not getattr(action, "save", None):
            log.notes = "Save action not supported by combat engine."
            return log

        save = action.save or {}
        save_ability = str(save.get("ability") or "").upper() or None
        save_dc = save.get("dc")
        if isinstance(save_dc, str) and save_dc == "spell_save_dc":
            save_dc = self._get_spell_save_dc(attacker)
        if not isinstance(save_dc, int):
            save_dc = None

        log.save_ability = save_ability
        log.save_dc = save_dc

        save_mod = self._get_save_modifier(target, save_ability)
        save_roll = DiceHandler().roll(dice_specs=[(20, 1)], modifiers=save_mod)
        log.save_total = save_roll.total
        log.save_roll_detail = self._roll_result_detail(save_roll)

        save_success = save_dc is not None and save_roll.total >= save_dc
        log.save_success = save_success

        target_hp_before = self._get_hp(target)
        log.target_hp_before = target_hp_before

        scaled_action = self._with_scaled_damage(action, attacker, slot_level, caster_level)
        if scaled_action.damage_roll:
            dmg_result = DamageResult()
            for val in scaled_action.damage_roll:
                temp_dmg_result = Dice.roll(sides=val["dice_type"], count=val["dice_amount"])
                if attacker.features._features:
                    for feature in attacker.features._features:
                        if getattr(feature, "feature_type", None) == "affects_rolls":
                            temp_dmg_result = feature(temp_dmg_result)
                if val.get("precomputed"):
                    temp_dmg_result.add_modifier(val["bonus"])
                else:
                    dmg_ability = val.get("ability")
                    dmg_options = val.get("ability_options") or []
                    dmg_mod = DiceHandler()._resolve_ability_modifier(attacker, dmg_ability, dmg_options)
                    temp_dmg_result.add_modifier(val["bonus"] + dmg_mod)
                dmg_result.add_damage(val["dmg_type"], temp_dmg_result)

            total_damage = dmg_result.total
            on_success = str(save.get("on_success") or "").lower()
            if save_success and on_success in {"half", "half damage"}:
                total_damage = total_damage // 2
            elif save_success and on_success in {"none", "no", "negate"}:
                total_damage = 0

            log.damage_total = total_damage
            log.damage_breakdown = {
                str(dmg_type): subtotal
                for dmg_type, subtotal in dmg_result.breakdown().items()
            }
            log.damage_rolls_detail = self._build_damage_rolls_detail(scaled_action, dmg_result)
            if total_damage:
                self.apply_damage(target, total_damage)
            log.target_hp_after = self._get_hp(target)
        else:
            log.damage_total = 0
            log.target_hp_after = target_hp_before

        return log

    def resolve_spell_action(
        self,
        attacker_id: str,
        action_id: str,
        target_id: str,
        advantage: Optional[str] = None,
        slot_level: Optional[int] = None,
        caster_level: Optional[int] = None,
    ) -> CombatActionLog:
        attacker = self.combatants.get(attacker_id)
        if attacker is None:
            return CombatActionLog(
                actor=attacker_id,
                action_id=action_id,
                action_name=action_id,
                target=target_id,
                notes="Invalid attacker.",
            )
        try:
            action = attacker.actions.get(action_id)
        except KeyError:
            action = None

        if action is None:
            return CombatActionLog(
                actor=attacker_id,
                action_id=action_id,
                action_name=action_id,
                target=target_id,
                notes="Action not found.",
            )

        if action.save:
            return self.resolve_save_action(
                attacker_id,
                action_id,
                target_id,
                slot_level=slot_level,
                caster_level=caster_level,
            )
        return self.resolve_attack_action(
            attacker_id,
            action_id,
            target_id,
            advantage=advantage,
            slot_level=slot_level,
            caster_level=caster_level,
        )

    def _get_save_modifier(self, target, ability: Optional[str]) -> int:
        if not ability:
            return 0
        ability = str(ability).upper()
        if hasattr(target, "saving_throws") and ability in target.saving_throws:
            return target.saving_throws[ability]
        if hasattr(target, "ability_scores"):
            try:
                return target.ability_scores.modifier(ability)
            except Exception:
                return 0
        return 0

    def _get_spell_save_dc(self, source) -> Optional[int]:
        if hasattr(source, "spells") and getattr(source.spells, "spell_save_dc", None):
            return source.spells.spell_save_dc
        ability = None
        if hasattr(source, "spells"):
            ability = getattr(source.spells, "spellcasting_ability", None)
        if ability and hasattr(source, "ability_scores"):
            try:
                ability_mod = source.ability_scores.modifier(ability)
            except Exception:
                ability_mod = 0
        else:
            ability_mod = 0
        prof = getattr(getattr(source, "proficiencies", None), "proficiency_bonus", 0)
        return 8 + prof + ability_mod

    def _roll_result_detail(self, roll: RollResult) -> Dict[str, Any]:
        return {
            "dice": roll.dice,
            "modifiers": roll.modifiers,
            "total": roll.total,
            "advantage": roll.advantage,
            "critical": roll.is_critical,
        }

    def _lookup_damage_rolls(self, dmg_result: DamageResult, dmg_type) -> List[RollResult]:
        if dmg_type in dmg_result.damage:
            return dmg_result.damage[dmg_type]
        desired = str(dmg_type).lower()
        for key, rolls in dmg_result.damage.items():
            if str(key).lower() == desired:
                return rolls
        return []

    def _build_damage_rolls_detail(self, action, dmg_result: DamageResult) -> Optional[List[Dict[str, Any]]]:
        specs = getattr(action, "damage_roll", None) or []
        if not specs or not dmg_result:
            return None
        indices: Dict[str, int] = {}
        details: List[Dict[str, Any]] = []
        for spec in specs:
            dmg_type = spec.get("dmg_type")
            rolls = self._lookup_damage_rolls(dmg_result, dmg_type)
            key = str(dmg_type).lower()
            idx = indices.get(key, 0)
            roll = rolls[idx] if idx < len(rolls) else None
            indices[key] = idx + 1
            if not roll:
                continue
            details.append({
                "type": str(dmg_type),
                "dice_type": spec.get("dice_type"),
                "dice_amount": spec.get("dice_amount"),
                "dice": roll.dice,
                "modifiers": roll.modifiers,
                "total": roll.total,
            })
        return details or None

    def _with_scaled_damage(
        self,
        action,
        caster,
        slot_level: Optional[int],
        caster_level: Optional[int],
    ):
        if not getattr(action, "damage_roll", None):
            return action

        scaling = getattr(action, "scaling", None)
        if not scaling:
            return action

        mode = scaling.get("mode")
        table = scaling.get("table") or {}
        if not table:
            return action

        effective_level = None
        if mode == "slot_level":
            effective_level = slot_level or getattr(action, "spell_level", None)
        elif mode == "character_level":
            if caster_level is None and hasattr(caster, "classes"):
                try:
                    caster_level = caster.classes.pc_level()
                except Exception:
                    caster_level = None
            effective_level = caster_level

        if effective_level is None:
            return action

        try:
            keys = sorted(int(k) for k in table.keys())
        except ValueError:
            return action

        chosen = None
        for key in keys:
            if key <= effective_level:
                chosen = key
        if chosen is None:
            chosen = keys[0]

        dice_str = table.get(str(chosen))
        if not dice_str or "d" not in dice_str:
            return action

        parts = dice_str.lower().split("d", 1)
        try:
            dice_amount = int(parts[0]) if parts[0] else 1
            dice_type = int(parts[1])
        except ValueError:
            return action

        action_copy = action.__class__(**action.__dict__)
        new_damage_roll = []
        for val in action.damage_roll:
            new_val = dict(val)
            new_val["dice_amount"] = dice_amount
            new_val["dice_type"] = dice_type
            new_damage_roll.append(new_val)
        action_copy.damage_roll = new_damage_roll
        return action_copy


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
