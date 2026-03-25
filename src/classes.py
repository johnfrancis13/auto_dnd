import json
from pathlib import Path
from collections import defaultdict
from helper_functions import normalize_fg
from proficiency import ProficiencyType
from resources import ResourceCategory, Resource, RechargeType
from srd_loader import load_srd

import re

def parse_class_table(table_data):
    progression = {}

    # Extract header names
    raw_headers = table_data[0]["td"]

    headers = []
    for cell in raw_headers:
        if isinstance(cell, dict):
            headers.append(cell.get("b", "").strip())
        else:
            headers.append(str(cell).strip())

    # Normalize header names to safe keys
    def normalize(header):
        return header.lower().replace(" ", "_")

    normalized_headers = [normalize(h) for h in headers]

    # Process rows
    for row in table_data[1:]:
        cells = row["td"]

        row_data = {}

        for header, value in zip(normalized_headers, cells):
            if header == "level":
                level = int(re.match(r"(\d+)", value).group(1))
                continue

            if value == "-" or value == "":
                row_data[header] = None
                continue

            # Special handling
            if header == "proficiency_bonus":
                row_data[header] = int(value.replace("+", ""))
            elif header == "features":
                row_data[header] = [f.strip() for f in value.split(",")]
            else:
                row_data[header] = value

        progression[level] = row_data

    return progression


def parse_spell_slots_table(table_data):
    progression = {}

    header = table_data[0]["td"]
    # header looks like: Level, Cantrips, 1st, 2nd, ... 9th

    for row in table_data[1:]:
        cells = row["td"]

        # Extract level number
        level_str = cells[0]
        level = int(re.match(r"(\d+)", level_str).group(1))

        # Cantrips known
        cantrips = int(cells[1])

        slots = {}

        # Remaining columns are spell levels 1–9
        for spell_level, value in enumerate(cells[2:], start=1):
            if value != "-" and value != "":
                slots[spell_level] = int(value)

        progression[level] = {
            "cantrips": cantrips,
            "slots": slots
        }

    return progression


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


def extract_feature_text(text_block):
    """Flatten the formattedtext structure into a readable string."""
    parts = []

    if not text_block:
        return ""

    # Handle paragraph content
    p = text_block.get("p")
    if isinstance(p, str):
        parts.append(p)
    elif isinstance(p, list):
        for item in p:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                # handle {'i': 'text'} or {'b': 'text'}
                parts.extend(item.values())

    # Handle list items
    lst = text_block.get("list", {}).get("li")
    if isinstance(lst, list):
        parts.extend(lst)

    return "\n".join(parts)


def build_feature_dict(features):
    level_dict = defaultdict(dict)

    for feature in features.values():
        level = int(feature.get("level"))
        name = feature.get("name")
        text_block = feature.get("text", {})

        description = extract_feature_text(text_block)

        level_dict[level][name] = description

    return dict(level_dict)

class CharClass:
    def __init__(self, class_data):
        self.name = class_data["name"].replace(" (Copy)", "").strip()
        self._format = "fg"

        if "hit_die" in class_data:
            self._format = "srd"
            self.hit_die = int(class_data["hit_die"])
            self.starting_hp = self.hit_die
            self.levelup_hp = (self.hit_die // 2) + 1
            self.proficiencies = class_data.get("proficiencies", [])
            self.saving_throws = class_data.get("saving_throws", [])
            self.proficiency_choices = class_data.get("proficiency_choices", [])
            self.starting_equipment = [
                item.get("equipment", {}).get("name")
                for item in class_data.get("starting_equipment", []) or []
                if item.get("equipment")
            ]

            levels = class_data.get("_levels", [])
            features = class_data.get("_features", [])
            feature_index = _build_srd_feature_map(features)
            self.class_features = _build_srd_level_features(levels, feature_index)
            self.levelup_spell_slots = _build_srd_spell_slots(levels)
            self.spell_caster = True if self.levelup_spell_slots else False
        else:
            self.starting_hp = class_data["hp"]["hitpointsat1stlevel"]["text"]
            self.hit_dice = class_data["hp"]["hitdice"]["text"]
            self.levelup_hp = class_data["hp"]["hitpointsathigherlevels"]["text"]
            self.proficiencies = class_data["proficiencies"]

            self.starting_equipment = class_data["text"]["list"]["li"]

            # Get spell slots and features per level
            if isinstance(class_data["text"]["table"], list):
                self.levelup_feature_dict = parse_class_table(class_data["text"]["table"][0]["tr"])
                self.levelup_spell_slots = parse_spell_slots_table(class_data["text"]["table"][1]["tr"])
            else:
                self.levelup_feature_dict = parse_class_table(class_data["text"]["table"]["tr"])
                self.levelup_spell_slots = None

            self.class_features = build_feature_dict(class_data["features"])
            self.spell_caster = True if self.levelup_spell_slots else False
        
    def apply(self, level_to_add,character):
        if level_to_add==1:
            self.first_level_setup(character) # have not implemented multiclassing yet
        elif 1 < level_to_add <= 20:
            self.level_up(character,level_to_add)
        else:
            raise ValueError("level_to_add must be an integer greater than 0 and no more than 20")
        # need something different for the others
    def first_level_setup(self, character):
        if self._format == "srd":
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

            for item in self.starting_equipment:
                if item:
                    character.inventory.add_item(item)

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
            return

        # Legacy FG flow
        flat_val = int(re.search(r'\d+', self.starting_hp).group())
        con_modifier = character.ability_scores.modifier("CON")
        starting_hp = flat_val+con_modifier
        character.resources.update_health( starting_hp)
        print(f"Starting HP set to {starting_hp}")

        # Assign hit dice
        dice_part = self.hit_dice.split()[0]
        num, sides = dice_part.split('d')
        character.resources.update_hit_die(int(sides),int(num))
        print(f"Hit die updated")

        # Add proficiencies
        class_profs = dict()
        if self.proficiencies["armor"]["text"]!="None":
            class_profs[ ProficiencyType.ARMOR] = set([item.strip() for item in self.proficiencies["armor"]["text"].split(",")])
        if self.proficiencies["savingthrows"]["text"]!="None":
            class_profs[ ProficiencyType.SAVE] = set([item.strip()[:3].upper() for item in self.proficiencies["savingthrows"]["text"].split(",")])
        if self.proficiencies["skills"]["text"]!="None":
            if "Choose two from" in self.proficiencies["skills"]["text"]:
                class_profs[ ProficiencyType.SKILL] = set([item.strip() for item in self.proficiencies["skills"]["text"].split(",")][-2:])
            else:
                class_profs[ ProficiencyType.SKILL] = set([item.strip() for item in self.proficiencies["skills"]["text"].split(",")])
        if self.proficiencies["tools"]["text"]!="None":
            class_profs[ ProficiencyType.TOOL] = set([item.strip() for item in self.proficiencies["tools"]["text"].split(",")])
        if self.proficiencies["weapons"]["text"]!="None":
            class_profs[ ProficiencyType.WEAPON] = set([item.strip() for item in self.proficiencies["weapons"]["text"].split(",")])

        character.proficiencies.add_proficiencies(class_profs)
        print(f"Proficiences added: {class_profs}")

        # Add equipment
        for item in self.starting_equipment:
            character.inventory.add_item(item)

        print(f"Items added: {self.starting_equipment}")

        # Add features
        level_1_features =  self.class_features[1]
        for feat in level_1_features:
            # convert to an actual feature first... need to parse the text into a feature class object
            character.features.add_feature(feat,character,description = level_1_features[feat])

        # Add resoources
        if self.levelup_spell_slots is not None:
            character.resources.update_spell_slots(
                "cantrips",self.levelup_spell_slots[1]["cantrips"],set_max=True)
            character.resources.update_spell_slots(
                "Level_1",self.levelup_spell_slots[1]["slots"][1],set_max=True)
            # If warlock, need to update all the recharge types to Short_rest
            #RechargeType.SHORT_REST if self.name=="Warlock" else RechargeType.LONG_REST,

            #   Also need to add in the total number of spells of each type they should have  character.resources.update_spell_access
            

    def level_up(self, character,level):

        # Add hp
        if self._format == "srd":
            character.resources.update_health(int(self.levelup_hp))
        else:
            character.resources.update_health(self.levelup_hp )
        
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
    def __init__(self, path=None):
        if path is None:
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
        else:
            path = Path(path)
            with open(path, "r", encoding="utf-8") as f:
                raw_data = normalize_fg(json.load(f))

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

    def add_class(self, char_class, pc):
        # Create the class fist to make sure char_class is valid
        new_class = CharClassRepository().get(char_class)
        # add the new class
        self.classes.append(new_class.name)

        # get the level of the new class being added
        class_level_to_add = sum([1 for val in self.classes if val==new_class.name])

        # Add in the relevant info for the new class to the pc
        new_class.apply(class_level_to_add, pc)

    def pc_level(self):
        return len(self.classes)
    
    def class_level(self,char_class):
        return sum([1 for val in self.classes if val==char_class])
