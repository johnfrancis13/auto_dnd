import pandas as pd
from proficiency import ProficiencyType
import ast
# Look up values from db
class Race:
    def __init__(self, id):
        df = pd.read_csv("../data/woc_races_clean.csv")
        self.id = id
        if id not in df["name"].values:
            raise ValueError(f"{id} not a valid race.")
        self.racial_data=df[df["name"]==id].iloc[0].to_dict()


    def apply(self, character):
        character.ability_scores.apply_bonuses(self.racial_data)

        languages =   {ProficiencyType.LANGUAGE: set(ast.literal_eval(self.racial_data["languages"]))}
        character.proficiencies.add_proficiencies(languages)


        racial_traits = ast.literal_eval(self.racial_data["unique_traits"])
        for feat in racial_traits:
            character.features.add_feature(feat["name"], character)


        self.description = self.racial_data["description"]
        
    def get_speed(self):
        return(self.racial_data["walking_speed"])
    
    def get_size(self):
        return(self.racial_data["size"])

    def get_creature_type(self):
        return(self.racial_data["creature_type"])

    def has_darkvision(self):
        return(self.racial_data["darkvision"])