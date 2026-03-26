from collections import defaultdict
from proficiency import ProficiencyType
from equipment_choices import build_choice_groups, apply_equipment_choices
from items import ItemRepository
 
from srd_loader import load_srd


def _srd_skill_name(value):
    if not value:
        return None
    value = value.replace("Skill:", "").strip()
    return value.lower().replace(" ", "_")


def _srd_prof_name(value):
    if not value:
        return None
    return value.strip().lower()


def _build_srd_feature_map(features):
    by_index = {}
    for feat in features:
        if not isinstance(feat, dict):
            continue
        index = feat.get("index")
        name = feat.get("name")
        desc = feat.get("desc") or []
        if isinstance(desc, list):
            desc_text = "\n".join(desc)
        else:
            desc_text = desc or ""
        by_index[index] = {
            "name": name,
            "desc": desc_text,
        }
    return by_index


def _build_srd_level_features(levels, feature_index):
    level_dict = defaultdict(dict)
    for lvl in levels:
        level = int(lvl.get("level"))
        for feat_ref in lvl.get("features", []) or []:
            feat = feature_index.get(feat_ref.get("index"))
            if feat:
                level_dict[level][feat["name"]] = feat["desc"]
    return dict(level_dict)


def _build_srd_spell_slots(levels):
    progression = {}
    for lvl in levels:
        level = int(lvl.get("level"))
        spellcasting = lvl.get("spellcasting")
        if not spellcasting:
            continue
        cantrips = spellcasting.get("cantrips_known")
        slots = {}
        for key, value in spellcasting.items():
            if not key.startswith("spell_slots_level_"):
                continue
            slot_level = int(key.replace("spell_slots_level_", ""))
            slots[slot_level] = value
        progression[level] = {
            "cantrips": cantrips or 0,
            "slots": slots,
        }
    return progression


class CharClass:
    def __init__(self, class_data):
        self.name = class_data["name"].replace(" (Copy)", "").strip()
        self.index = class_data.get("index") or self.name.lower()
        self.hit_die = int(class_data["hit_die"])
        self.starting_hp = self.hit_die
        self.levelup_hp = (self.hit_die // 2) + 1
        self.proficiencies = class_data.get("proficiencies", [])
        self.saving_throws = class_data.get("saving_throws", [])
        self.proficiency_choices = class_data.get("proficiency_choices", [])
        self.starting_equipment = [
            {
                "name": item.get("equipment", {}).get("name"),
                "quantity": item.get("quantity", 1),
            }
            for item in class_data.get("starting_equipment", []) or []
            if item.get("equipment")
        ]
        self.starting_equipment_options = class_data.get("starting_equipment_options", []) or []

        levels = class_data.get("_levels", [])
        features = class_data.get("_features", [])
        feature_index = _build_srd_feature_map(features)
        self.class_features = _build_srd_level_features(levels, feature_index)
        self.levelup_spell_slots = _build_srd_spell_slots(levels)
        self.spell_caster = True if self.levelup_spell_slots else False
        
    def apply(self, level_to_add,character, equipment_choices=None):
        if level_to_add==1:
            self.first_level_setup(character, equipment_choices=equipment_choices) # have not implemented multiclassing yet
        elif 1 < level_to_add <= 20:
            self.level_up(character,level_to_add)
        else:
            raise ValueError("level_to_add must be an integer greater than 0 and no more than 20")
        # need something different for the others
    def first_level_setup(self, character, equipment_choices=None):
        con_modifier = character.ability_scores.modifier("CON")
        starting_hp = int(self.starting_hp) + con_modifier
        character.resources.update_health(starting_hp)

        character.resources.update_hit_die(self.hit_die, 1)

        class_profs = dict()
        if self.proficiencies:
            armor = [p["name"] for p in self.proficiencies if "Armor" in p["name"]]
            weapons = [p["name"] for p in self.proficiencies if "Weapons" in p["name"]]
            tools = [p["name"] for p in self.proficiencies if "Tools" in p["name"]]
            if armor:
                class_profs[ProficiencyType.ARMOR] = set(_srd_prof_name(a) for a in armor)
            if weapons:
                weapon_set = set(_srd_prof_name(w) for w in weapons)
                if any("simple weapons" in w for w in weapon_set):
                    weapon_set.update({"simple melee", "simple ranged"})
                if any("martial weapons" in w for w in weapon_set):
                    weapon_set.update({"martial melee", "martial ranged"})
                class_profs[ProficiencyType.WEAPON] = weapon_set
            if tools:
                class_profs[ProficiencyType.TOOL] = set(_srd_prof_name(t) for t in tools)

        if self.saving_throws:
            class_profs[ProficiencyType.SAVE] = set(
                s["name"].upper() for s in self.saving_throws
            )

        skill_choices = []
        choose = 0
        for choice in self.proficiency_choices:
            if choice.get("type") != "proficiencies":
                continue
            choose = max(choose, choice.get("choose", 0))
            options = choice.get("from", {}).get("options", [])
            for option in options:
                item = option.get("item") or {}
                if item.get("name", "").startswith("Skill:"):
                    skill_choices.append(_srd_skill_name(item.get("name")))
        if skill_choices:
            class_profs[ProficiencyType.SKILL] = set(skill_choices[:choose or len(skill_choices)])

        if class_profs:
            character.proficiencies.add_proficiencies(class_profs)

        equipment_repo = ItemRepository()
        for item in self.starting_equipment:
            name = item.get("name")
            quantity = item.get("quantity", 1)
            if not name:
                continue
            obj = equipment_repo.get(name) or name
            character.inventory.add_item(obj, quantity)

        choice_groups = build_choice_groups(self.starting_equipment_options, f"class:{self.index}")
        apply_equipment_choices(character, equipment_choices or {}, choice_groups)

        level_1_features = self.class_features.get(1, {})
        for feat in level_1_features:
            character.features.add_feature(feat, character, description=level_1_features[feat])

        if self.levelup_spell_slots is not None and 1 in self.levelup_spell_slots:
            character.resources.update_spell_slots(
                "cantrips", self.levelup_spell_slots[1]["cantrips"], set_max=True
            )
            if 1 in self.levelup_spell_slots[1]["slots"]:
                character.resources.update_spell_slots(
                    "Level_1", self.levelup_spell_slots[1]["slots"][1], set_max=True
                )

        # Set spellcasting ability + save DC if applicable
        if getattr(character, "spells", None) is not None:
            class_entry = load_srd("classes", "5e-SRD-Classes.json")
            entry = next(
                (c for c in class_entry or [] if c.get("name", "").lower() == self.name.lower()),
                None,
            )
            if entry and entry.get("spellcasting"):
                ability = (entry.get("spellcasting") or {}).get("spellcasting_ability") or {}
                ability_name = ability.get("name")
                if ability_name:
                    character.spells.spellcasting_ability = ability_name
                    ability_mod = character.ability_scores.modifier(ability_name)
                    character.spells.spell_save_dc = (
                        8 + character.proficiencies.proficiency_bonus + ability_mod
                    )
        return
            

    def level_up(self, character,level):

        # Add hp
        character.resources.update_health(int(self.levelup_hp))
        
        # Add features
        new_level_features =  self.class_features.get(level, {})
        for feat in new_level_features:
            character.features.add_feature(feat, character, description=new_level_features[feat])

        # Update resources
        # Add resources
        if self.levelup_spell_slots is not None and level in self.levelup_spell_slots:
            character.resources.update_spell_slots(
                "cantrips",self.levelup_spell_slots[level]["cantrips"],set_max=True)
            for lvl in self.levelup_spell_slots[level]["slots"]:
                character.resources.update_spell_slots(
                f"Level_{lvl}",self.levelup_spell_slots[level]["slots"][lvl],set_max=True)

        character.features.on_level_up(character, level)

        
class CharClassRepository:
    def __init__(self):
        classes = load_srd("classes", "5e-SRD-Classes.json")
        levels = load_srd("levels", "5e-SRD-Levels.json")
        features = load_srd("features", "5e-SRD-Features.json")

        levels_by_class = defaultdict(list)
        for lvl in levels:
            class_ref = (lvl.get("class") or {}).get("index")
            if class_ref:
                levels_by_class[class_ref].append(lvl)

        raw_data = []
        for class_entry in classes:
            entry = dict(class_entry)
            class_index = class_entry.get("index")
            entry["_levels"] = levels_by_class.get(class_index, [])
            entry["_features"] = features
            raw_data.append(entry)

        # Create objects
        self.all_charclasses = [CharClass(item) for item in raw_data]

        # Primary index (fast lookup by name)
        self.by_name = {item.name: item for item in self.all_charclasses}

        # Secondary indexes (fast filtering)
        self.by_spell_caster = defaultdict(list)


        for item in self.all_charclasses:
            # by level
            self.by_spell_caster[item.spell_caster].append(item)


    def get(self, name):
        return self.by_name.get(name)

    def get_many(self, names):
        return [self.by_name[n] for n in names if n in self.by_name]

    def filter_by_spell_caster(self, caster):
        return self.by_spell_caster.get(caster, [])

    def search(self, keyword):
        keyword = keyword.lower()
        return [
            item for item in self.all_charclasses
            if keyword in item.name.lower()
        ]


class ClassProgression:
    def __init__(self, owner):
        self.owner = owner
        self.classes = []  # e.g. [Fighter, Fighter, Fighter, Rogue]

    def add_class(self, char_class, pc, equipment_choices=None):
        # Create the class fist to make sure char_class is valid
        new_class = CharClassRepository().get(char_class)
        # add the new class
        self.classes.append(new_class.name)

        # get the level of the new class being added
        class_level_to_add = sum([1 for val in self.classes if val==new_class.name])

        # Add in the relevant info for the new class to the pc
        new_class.apply(class_level_to_add, pc, equipment_choices=equipment_choices)

    def pc_level(self):
        return len(self.classes)
    
    def class_level(self,char_class):
        return sum([1 for val in self.classes if val==char_class])


