import pandas as pd
from actions import Action
from features import Feature

# 
class Item:
    def __init__(self, data):
        self.name = data["name"]
        self.description = data.get("description", "")
        self.type = data.get("type", None)
        self.subtype = data.get("subType", None)
        self.rarity = data.get("Rarity","Common")
        self.attunement = data.get("Attunement", False)
        self.cost = data.get("cost",0)
        self.weight = data.get("weight",0)


def load_items():
    df = pd.read_csv("../data/all_items.csv")

    ITEMS = {
        data["name"]: Item(data)
        for id, data in  df.to_dict(orient="index").items()
        }
    return ITEMS


# Basically actions should be attached to items, i need a function to create actions from the item description if an action should in fact be created