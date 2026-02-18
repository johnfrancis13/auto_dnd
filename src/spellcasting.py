import json
from collections import defaultdict
from helper_functions import normalize_fg, clean_item_description, extract_link_text


class Spell:
    def __init__(self, data):
        self.name = data["name"].replace(" (Copy)", "").strip()
        self.description = clean_item_description(data.get("description", ""))
        self.level = int(data["level"])
        self.duration = data["duration"]
        self.school = data["school"]
        self.components = data["components"]
        #self.dmg_type = data["DamageType"]
        self.cast_time = data["castingtime"]
        self.range = data["range"]
        self.ritual =  data.get("ritual", None) 
        self.source = data.get("source", None) 
        self.links = extract_link_text(data)
        #self.save = data["Save"]

class Spellcasting:
    def __init__(self):
        self.known_spells = []
        self.prepared_spells = []
        self.spellcasting_ability = None

    def add_spell(self, spell: Spell):
        self.known_spells[spell.name] = spell


class SpellRepository:
    def __init__(self, path="../data/spell.json"):
        with open(path, "r", encoding="utf-8") as f:
            raw_data = normalize_fg(json.load(f))

        # Create objects
        self.all_spells = [Spell(item) for item in raw_data]

        # Primary index (fast lookup by name)
        self.by_name = {item.name: item for item in self.all_spells}

        # Secondary indexes (fast filtering)
        self.by_level = defaultdict(list)
        self.by_source = defaultdict(list)

        for item in self.all_spells:
            # by level
            self.by_level[item.level].append(item)

            # by individual source
            if item.source:
                sources = [s.strip() for s in item.source.split(",")]
                for s in sources:
                    self.by_source[s].append(item)
            # ---- Retrieval Methods ----

    def get(self, name):
        return self.by_name.get(name)

    def get_many(self, names):
        return [self.by_name[n] for n in names if n in self.by_name]

    def filter_by_level(self, spell_level):
        return self.by_level.get(spell_level, [])

    def filter_by_source(self, source):
        return self.by_source.get(source, [])

    def search(self, keyword):
        keyword = keyword.lower()
        return [
            item for item in self.all_spells
            if keyword in item.name.lower()
        ]
