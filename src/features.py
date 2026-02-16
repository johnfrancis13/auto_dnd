from game_engine import Dice
from proficiency import ProficiencyType
import resources
import actions
from typing import Optional, Callable, Dict
import random

class FeatureManager:
    def __init__(self):
        self._features = []

    def add_feature(self, feature, engine):
        # First check if in Feature registry
        if feature["name"] not in FEATURE_REGISTRY:
            print("Feature does not exist or has not yet been implemented in the feature registry")
            return None # make this an error later
            #raise ValueError("Feature does not exist or has not yet been implemented in the feature registry")

        
        feature_class = FEATURE_REGISTRY[feature["name"]]
        if feature_class not in self._features:
            self._features.append(feature_class)
            feature_class().on_attach(engine) # add permanent character level changes

    def remove_feature(self, feature, engine):
        if feature in self._features:
            feature.on_detach(engine)
            self._features.remove(feature) # remove permanent character level changes

    def dispatch(self, engine, hook_name, *args, **kwargs):
        """
        Generic hook dispatcher.
        """
        result = None

        for feature in self._features:
            hook = getattr(feature, hook_name, None)
            if callable(hook):
                value = hook(engine, *args, **kwargs)
                if value is not None:
                    result = value

        return result


class Feature:
    def __init__(self, name, source=None,feature_type=None):
        self.name = name
        self.source = source  # race, class, item, feat
        self.feature_type = feature_type

    # =========================
    # Lifecycle
    # =========================

    def on_attach(self, engine):
        """Called when feature is added to a character engine."""
        pass

    def on_detach(self, engine):
        """Called when feature is removed."""
        pass

    # =========================
    # Passive Modifiers
    # =========================

    def modify_stat(self, engine, stat_name, value):
        return value

    def modify_speed(self, engine, speed):
        return speed

    def modify_ac(self, engine, ac):
        return ac

    def grant_proficiencies(self, engine):
        return []

    # =========================
    # Roll Hooks
    # =========================

    def on_d20_roll(self, rolls, total):
        pass

    def on_attack_roll(self, rolls, total):
        pass

    def on_damage_roll(self, rolls, total):
        pass

    def on_ability_check(self, rolls, total):
        pass

    def on_saving_throw(self, rolls, total):
        pass

    def on_initiative(self, rolls, total):
        pass

    # =========================
    # Combat Events
    # =========================

    def on_turn_start(self, engine):
        pass

    def on_turn_end(self, engine):
        pass

    def on_combat_start(self, engine):
        pass

    def on_combat_end(self, engine):
        pass

    def on_take_damage(self, engine, damage_context):
        return damage_context

    def on_deal_damage(self, engine, damage_context):
        return damage_context

    # =========================
    # Activation
    # =========================

    def can_activate(self, engine):
        """Override if feature is activatable."""
        return False

    def activate(self, engine, **kwargs):
        """Override for active abilities."""
        pass



    
# Features that affect dice rolls need to take rolls, total as input and output new rolls and new totals
class HalflingLuck(Feature):
    def __init__(self):
        super().__init__("Halfling Luck", source="race",feature_type="affects_rolls")

    def on_d20_roll(self,roll_result):
        # reroll any 1s 
        roll_result.dice = [r if r > 1 else random.randint(2, 20) for r in roll_result.dice]
        roll_result.total()
        return roll_result
    
class FelineAgility(Feature):
    def __init__(self):
        super().__init__("Feline Agility", source="race")

    def on_attach(self, engine):
        engine.resources.add_resource(resources.Resource(
            id="feline_agility",
            name="Feline Agility",
            category=resources.ResourceCategory.FEATURE_USE,
            current=1,
            maximum=1,
            recharge=resources.RechargeType.TURN,
            source="Tabaxi"
            ))

    def activate(self, engine, **kwargs):
        if engine.resources.spend("feline_agility"):
            engine.add_condition("double_speed_until_end_of_turn")

class Claws(Feature):
    def __init__(self):
        super().__init__("Claws", source="race")
    def on_attach(self, character):
        character.climb_speed = 20
        character.actions.add(actions.Action(id="claw_attack",
                                              name="Claw Attack",
                                               action_type=actions.ActionType.ACTION ,
                                              source = "Tabaxi",
                                               attack_roll= {"ability":"DEX",
                                                             "bonus":0 ,
                                                             "proficiency_type":"simple melee"},
                                               damage_roll=[{"dmg_type" : "slashing",
                                                             "dice_type": 4,
                                                             "dice_amount":1,
                                                             "ability":"DEX",
                                                             "bonus":0}]))


class Talent(Feature):
    def __init__(self):
        super().__init__("Talent", source="race")
    def on_attach(self, character):
        skill_additions = {ProficiencyType.SKILL: set(["Perception","Stealth"])}
        character.proficiencies.add_proficiencies(skill_additions)


FEATURE_REGISTRY = {
    "Feline Agility": FelineAgility,
    "Claws": Claws,
    "Talent": Talent,
    "Halfling Luck": HalflingLuck,
}


