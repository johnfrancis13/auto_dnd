from systems.proficiency import ProficiencyType
from data.srd_loader import load_srd


def _merge_by_key(base, override):
    by_key = {r.get("index", "").lower(): r for r in base if isinstance(r, dict)}
    for item in override:
        if not isinstance(item, dict):
            continue
        key = item.get("index", "").lower()
        if key and key in by_key:
            merged = dict(by_key[key])
            merged.update(item)
            by_key[key] = merged
        elif key:
            by_key[key] = item
    return list(by_key.values())


def _find_race(races, name):
    target = name.strip().lower()
    for race in races:
        if race.get("name", "").strip().lower() == target:
            return race
    return None


class Race:
    def __init__(self, id):
        races = load_srd("races", "5e-SRD-Races.json")
        species = load_srd("species", "5e-SRD-Species.json")
        merged = _merge_by_key(races or [], species or [])

        self.id = id
        self.racial_data = _find_race(merged, id)
        if not self.racial_data:
            raise ValueError(f"{id} not a valid race.")

    def apply(self, character):
        bonuses = {}

        for bonus in self.racial_data.get("ability_bonuses", []) or []:
            ability = (bonus.get("ability_score") or {}).get("name")
            if ability:
                bonuses[ability] = bonuses.get(ability, 0) + int(bonus.get("bonus", 0))

        for bonus in self.racial_data.get("ability_score_increases", []) or []:
            ability = (bonus.get("ability_score") or {}).get("name")
            if ability:
                bonuses[ability] = bonuses.get(ability, 0) + int(bonus.get("bonus", 0))

        if bonuses:
            character.ability_scores.apply_bonuses(bonuses)

        languages = self.racial_data.get("languages") or []
        language_names = set()
        for lang in languages:
            if isinstance(lang, dict):
                language_names.add(lang.get("name"))
            elif isinstance(lang, str):
                language_names.add(lang)
        if language_names:
            character.proficiencies.add_proficiencies({
                ProficiencyType.LANGUAGE: set(filter(None, language_names))
            })

        traits = self.racial_data.get("traits") or []
        for feat in traits:
            if isinstance(feat, dict):
                name = feat.get("name")
            else:
                name = str(feat)
            if name:
                character.features.add_feature(name, character)

        self.description = self.racial_data.get("description", "")

    def get_speed(self):
        speed = self.racial_data.get("speed")
        if isinstance(speed, dict):
            return speed.get("walk", 0)
        return speed

    def get_size(self):
        return self.racial_data.get("size")

    def get_creature_type(self):
        return self.racial_data.get("type")

    def has_darkvision(self):
        for trait in self.racial_data.get("traits", []) or []:
            name = trait.get("name") if isinstance(trait, dict) else str(trait)
            if "darkvision" in name.lower():
                return True
        return False
