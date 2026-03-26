from game_engine import Dice
from proficiency import ProficiencyType
import resources
import actions
from typing import Optional, Callable, Dict, Tuple
import random
from srd_loader import load_srd


_TRAIT_INDEX = None
_FEAT_INDEX = None
_CLASS_FEATURE_INDEX = None
_TRAIT_DATA = None
_FEAT_DATA = None
_CLASS_FEATURE_DATA = None


def _load_trait_index():
    global _TRAIT_INDEX
    if _TRAIT_INDEX is not None:
        return _TRAIT_INDEX
    traits = load_srd("traits", "5e-SRD-Traits.json")
    index = {}
    for trait in traits:
        name = trait.get("name")
        if not name:
            continue
        desc_text = _normalize_desc(trait)
        index[name.lower()] = desc_text
    _TRAIT_INDEX = index
    return _TRAIT_INDEX


def _load_feat_index():
    global _FEAT_INDEX
    if _FEAT_INDEX is not None:
        return _FEAT_INDEX
    feats = load_srd("feats", "5e-SRD-Feats.json")
    index = {}
    for feat in feats:
        name = feat.get("name")
        if not name:
            continue
        desc_text = _normalize_desc(feat)
        index[name.lower()] = desc_text
    _FEAT_INDEX = index
    return _FEAT_INDEX


def _load_class_feature_index():
    global _CLASS_FEATURE_INDEX
    if _CLASS_FEATURE_INDEX is not None:
        return _CLASS_FEATURE_INDEX
    features = load_srd("features", "5e-SRD-Features.json")
    index = {}
    for feat in features:
        name = feat.get("name")
        if not name:
            continue
        desc_text = _normalize_desc(feat)
        index[name.lower()] = desc_text
    _CLASS_FEATURE_INDEX = index
    return _CLASS_FEATURE_INDEX


def _normalize_desc(data: Dict) -> str:
    desc = data.get("desc")
    if desc is None:
        desc = data.get("description")
    if isinstance(desc, list):
        return "\n".join(desc).strip()
    if desc is None:
        return ""
    return str(desc).strip()


def _load_trait_data():
    global _TRAIT_DATA
    if _TRAIT_DATA is not None:
        return _TRAIT_DATA
    traits = load_srd("traits", "5e-SRD-Traits.json")
    data = {}
    for trait in traits:
        name = trait.get("name")
        if name:
            data[name.lower()] = trait
    _TRAIT_DATA = data
    return _TRAIT_DATA


def _load_feat_data():
    global _FEAT_DATA
    if _FEAT_DATA is not None:
        return _FEAT_DATA
    feats = load_srd("feats", "5e-SRD-Feats.json")
    data = {}
    for feat in feats:
        name = feat.get("name")
        if name:
            data[name.lower()] = feat
    _FEAT_DATA = data
    return _FEAT_DATA


def _load_class_feature_data():
    global _CLASS_FEATURE_DATA
    if _CLASS_FEATURE_DATA is not None:
        return _CLASS_FEATURE_DATA
    feats = load_srd("features", "5e-SRD-Features.json")
    data = {}
    for feat in feats:
        name = feat.get("name")
        if name:
            data[name.lower()] = feat
    _CLASS_FEATURE_DATA = data
    return _CLASS_FEATURE_DATA


def _trait_description(name: str) -> Optional[str]:
    if not name:
        return None
    index = _load_trait_index()
    return index.get(name.lower())


def _feat_description(name: str) -> Optional[str]:
    if not name:
        return None
    index = _load_feat_index()
    return index.get(name.lower())


def _class_feature_description(name: str) -> Optional[str]:
    if not name:
        return None
    index = _load_class_feature_index()
    return index.get(name.lower())


def _feature_data(name: str) -> Optional[Dict]:
    if not name:
        return None
    key = name.lower()
    return (
        _load_trait_data().get(key)
        or _load_feat_data().get(key)
        or _load_class_feature_data().get(key)
    )


def _feature_source_and_type(name: str, data: Optional[Dict]) -> Tuple[Optional[str], Optional[str]]:
    if not name or not data:
        return None, None
    key = name.lower()
    if key in _load_trait_data():
        return _trait_source(data), "trait"
    if key in _load_feat_data():
        return "Feat", "feat"
    if key in _load_class_feature_data():
        return _class_feature_source(data), "class"
    return None, None


def _trait_source(data: Dict) -> Optional[str]:
    names = []
    for field in ("races", "subraces", "species", "subspecies"):
        for entry in data.get(field, []) or []:
            if isinstance(entry, dict):
                name = entry.get("name")
            else:
                name = str(entry)
            if name:
                names.append(name)
    if not names:
        return "Race Trait"
    if len(names) == 1:
        return names[0]
    return f"{names[0]} +{len(names) - 1}"


def _class_feature_source(data: Dict) -> Optional[str]:
    subclass = data.get("subclass") or {}
    class_info = data.get("class") or {}
    subclass_name = subclass.get("name")
    class_name = class_info.get("name")
    if subclass_name and class_name:
        return f"{class_name} ({subclass_name})"
    return subclass_name or class_name or "Class Feature"


def _extract_ability_bonuses(data: Dict) -> Dict[str, int]:
    bonuses = {}

    def add_bonus(ability, amount):
        if ability:
            bonuses[ability] = bonuses.get(ability, 0) + int(amount)

    for entry in data.get("ability_score_increases", []) or []:
        ability = (entry.get("ability_score") or {}).get("name")
        add_bonus(ability, entry.get("bonus", 0))

    for entry in data.get("ability_score_increase", []) or []:
        ability = (entry.get("ability_score") or {}).get("name")
        add_bonus(ability, entry.get("bonus", 0))

    for entry in data.get("ability_bonuses", []) or []:
        ability = (entry.get("ability_score") or {}).get("name")
        add_bonus(ability, entry.get("bonus", 0))

    return bonuses


def _extract_proficiencies(data: Dict) -> Dict[ProficiencyType, set]:
    profs = {ProficiencyType.SKILL: set(), ProficiencyType.TOOL: set(), ProficiencyType.LANGUAGE: set()}
    for prof in data.get("proficiencies", []) or []:
        name = prof.get("name") if isinstance(prof, dict) else str(prof)
        if name.startswith("Skill:"):
            profs[ProficiencyType.SKILL].add(name.replace("Skill:", "").strip().lower())
        elif name.startswith("Tool:"):
            profs[ProficiencyType.TOOL].add(name.replace("Tool:", "").strip().lower())
        elif name.startswith("Language:"):
            profs[ProficiencyType.LANGUAGE].add(name.replace("Language:", "").strip())

    # Some feats include languages separately
    for lang in data.get("languages", []) or []:
        if isinstance(lang, dict):
            profs[ProficiencyType.LANGUAGE].add(lang.get("name"))
        elif isinstance(lang, str):
            profs[ProficiencyType.LANGUAGE].add(lang)

    # Remove empty entries
    return {k: v for k, v in profs.items() if v}


def _extract_senses(data: Dict) -> set:
    senses = set()
    raw = data.get("senses")
    if isinstance(raw, list):
        for sense in raw:
            if isinstance(sense, dict):
                name = sense.get("name")
            else:
                name = str(sense)
            if name:
                senses.add(name)
    elif isinstance(raw, dict):
        for key, value in raw.items():
            senses.add(f"{key} {value}".strip())
    return senses


def _apply_feature_data(character, data: Optional[Dict]):
    if not data:
        return

    bonuses = _extract_ability_bonuses(data)
    if bonuses:
        character.ability_scores.apply_bonuses(bonuses)

    profs = _extract_proficiencies(data)
    if profs:
        character.proficiencies.add_proficiencies(profs)

    senses = _extract_senses(data)
    if senses:
        if not hasattr(character, "senses"):
            character.senses = set()
        character.senses.update(senses)


def apply_srd_feature_data(character, feature_name: str):
    """Public helper for generated Feature classes."""
    _apply_feature_data(character, _feature_data(feature_name))

class FeatureManager:
    def __init__(self, owner):
        self.owner = owner
        self._features = []

    def add_feature(self, feature, engine,description=None):
        # First check if in mechanics registry
        if feature not in MECHANICS_REGISTRY:
            print("Feature does not exist or has not yet been implemented in the feature registry")
            # create a descriptive feature for now
            if description is None:
                description = _trait_description(feature)
            if description is None:
                description = _feat_description(feature)
            if description is None:
                description = _class_feature_description(feature)
            data = _feature_data(feature)
            source, feature_type = _feature_source_and_type(feature, data)
            feature_class = Feature(
                name=feature,
                source=source,
                feature_type=feature_type,
                description=description,
            )
            _apply_feature_data(engine, data)
            #return None # make this an error later
            #raise ValueError("Feature does not exist or has not yet been implemented in the feature registry")
        else:
            feature_class = MECHANICS_REGISTRY[feature]()

        
        if feature_class not in self._features:
            self._features.append(feature_class)
            feature_class.on_attach(engine) # add permanent character level changes

    def on_level_up(self, engine, new_level: int):
        for feature in self._features:
            hook = getattr(feature, "on_level_up", None)
            if callable(hook):
                hook(engine, new_level)

    def get(self, feature_name):
        return next((obj for obj in self._features if obj.name == feature_name), None)

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
    def __init__(self, name, source=None,feature_type=None, description=None):
        self.name = name
        self.source = source  # race, class, item, feat
        self.feature_type = feature_type
        self.description = description

    # =========================
    # Lifecycle
    # =========================

    def on_attach(self, engine):
        """Called when feature is added to a character engine."""
        pass

    def on_detach(self, engine):
        """Called when feature is removed."""
        pass

    def on_level_up(self, engine, new_level: int):
        """Called when a character gains a level."""
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

    def on_d20_roll(self, roll_result):
        pass

    def on_attack_roll(self, roll_result):
        pass

    def on_damage_roll(self, roll_result):
        pass

    def on_ability_check(self, roll_result):
        pass

    def on_saving_throw(self, roll_result):
        pass

    def on_initiative(self, roll_result):
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


###################################################################################################
# Build feature subclass only when necessary, otherwise it is just a data holder (description only)
###################################################################################################
    
# Features that affect dice rolls need to take rolls, total as input and output new rolls and new totals
class HalflingLuck(Feature):
    def __init__(self):
        super().__init__("Halfling Luck", source="race",feature_type="affects_rolls")

    def on_d20_roll(self,roll_result):
        # reroll any 1s 
        roll_result.dice = [r if r > 1 else random.randint(2, 20) for r in roll_result.dice]
        roll_result.base_total = sum(roll_result.dice )
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
                                                             "bonus":0}],
                                              range=5,
                                              targeting={"shape": "single"}))


class Talent(Feature):
    def __init__(self):
        super().__init__("Talent", source="race")
    def on_attach(self, character):
        skill_additions = {ProficiencyType.SKILL: set(["Perception","Stealth"])}
        character.proficiencies.add_proficiencies(skill_additions)


class DwarvenToughness(Feature):
    def __init__(self):
        super().__init__("Dwarven Toughness", source="race")

    def on_attach(self, character):
        character.resources.update_health(1)

    def on_level_up(self, character, new_level: int):
        character.resources.update_health(1)


MECHANICS_REGISTRY = {
    "Feline Agility": FelineAgility,
    "Claws": Claws,
    "Talent": Talent,
    "Luck": HalflingLuck,
    "Halfling Luck": HalflingLuck,
    "Dwarven Toughness": DwarvenToughness,
}

# Optional generated registry (LLM scaffolding)
try:
    from generated_features import GENERATED_FEATURES_REGISTRY
except Exception:
    GENERATED_FEATURES_REGISTRY = {}

# Generated features should not override hand-written mechanics.
for key, value in GENERATED_FEATURES_REGISTRY.items():
    if key not in MECHANICS_REGISTRY:
        MECHANICS_REGISTRY[key] = value


