import json
from collections import defaultdict
from srd_loader import load_srd


class Spell:
    def __init__(self, data):
        self.name = data["name"].replace(" (Copy)", "").strip()
        desc = data.get("desc") or []
        higher = data.get("higher_level") or []
        self.description = "\n".join(desc + higher).strip()
        self.level = int(data.get("level", 0))
        self.duration = data.get("duration")
        school = data.get("school")
        if isinstance(school, dict):
            self.school = school.get("name")
        else:
            self.school = school
        self.components = data.get("components") or []
        self.cast_time = data.get("casting_time")
        self.range = data.get("range")
        self.ritual = data.get("ritual")
        self.source = data.get("source") or data.get("document__title")
        self.links = []

class Spellcasting:
    def __init__(self, owner):
        self.owner = owner
        self.known_spells = dict()
        self.prepared_spells = dict()
        self.spellcasting_ability = None
        self.spell_save_dc = None

    def manage_spells(self, spell: Spell,action="add"):
        if action=="add":
            self.known_spells[spell.name] = spell
        elif action=="remove":
            self.known_spells.pop(spell.name, None)
        else:
            raise ValueError("action must be one of remove or add")


    def prepare_spell(self, spell: Spell, action="add"):
        if action=="add":
            self.prepared_spells[spell.name] = spell
        elif action=="remove":
            self.prepared_spells.pop(spell.name, None)
        else:
            raise ValueError("action must be one of remove or add")



class SpellRepository:
    def __init__(self, path=None):
        if path is None:
            raw_data = load_srd("spells", "5e-SRD-Spells.json")
        else:
            from pathlib import Path
            with Path(path).open("r", encoding="utf-8") as f:
                raw_data = json.load(f)

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
