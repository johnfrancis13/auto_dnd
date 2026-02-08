import pandas as pd

class CharClass:
    def __init__(self, char_class):
        df = pd.read_csv("../data/woc_classes.csv")
        if char_class not in df["name"].values:
            raise ValueError(f"{char_class} not a valid class.")
        
        self.class_data=df[df["name"]==char_class].iloc[0].to_dict()
    
    def apply(self, character,level):
        level_info = self.class_data[level]

        character.ability_scores.apply_bonuses(level_info.ability_bonuses)

        for feature in level_info.features:
            character.features.add(feature)
        
