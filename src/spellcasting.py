import pandas as pd

class Spellcasting:
    def __init__(self):
        self.known_spells = []
        self.prepared_spells = []
        self.spellcasting_ability = None

class Spell:
    def __init__(self, data):
        self.name = data["name"]
        self.description = data["description"]
        self.level = data["Level"]
        self.school = data["School"]
        self.components = data["Components"]
        self.dmg_type = data["DamageType"]
        self.cast_time = data["CastingTime"]
        self.range = data["Range"]
        self.save = data["Save"]


def load_spells():
    df = pd.read_csv("../data/woc_spells.csv")

    SPELLS = {
        data["name"]: Spell(data)
        for spell_id, data in  df.to_dict(orient="index").items()
        }
    return SPELLS