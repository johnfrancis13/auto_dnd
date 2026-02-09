import pandas as pd

class Item:
    def __init__(self, data):
        self.name = data["name"]
        self.description = data.get("description", "")
        self.type = data.get("Type")
        self.subtype = data.get("SubType")
        self.rarity = data.get("Rarity","Common")
        self.attunement = data.get("Attunement", False)
        self.properties = data.get("Properties", [])
        self.cost = data.get("Cost",0)
        self.weight = data.get("Weight",0)


def load_items():
    df = pd.read_csv("../data/woc_items.csv")

    ITEMS = {
        data["name"]: Item(data)
        for id, data in  df.to_dict(orient="index").items()
        }
    return ITEMS