import json
from actions import Action
from features import Feature
from helper_functions import normalize_fg, clean_item_description, extract_link_text
from collections import defaultdict
import re

class Item:
    def __init__(self, data):
        self.name = data["name"].replace(" (Copy)", "").strip()
        self.description = clean_item_description(data.get("description", ""))
        self.type = data.get("type", None)
        self.subtype = data.get("subType", None)
        self.rarity = data.get("Rarity","Common")
        self.attunement = "attunement" in (self.rarity or "").lower()
        self.cost = data.get("cost",0)
        self.weight = data.get("weight",0)
        self.links = extract_link_text(data)


class ItemRepository:
    def __init__(self, path="../data/item.json"):
        with open(path, "r", encoding="utf-8") as f:
            raw_data = normalize_fg(json.load(f))

        # Create objects
        self.all_items = [Item(item) for item in raw_data]

        # Primary index (fast lookup by name)
        self.by_name = {item.name: item for item in self.all_items}

        # Secondary indexes (fast filtering)
        self.by_type = defaultdict(list)
        self.by_subtype = defaultdict(list)

        for item in self.all_items:
            self.by_type[item.type].append(item)
            self.by_subtype[item.subtype].append(item)

    # ---- Retrieval Methods ----

    def get(self, name):
        return self.by_name.get(name)

    def get_many(self, names):
        return [self.by_name[n] for n in names if n in self.by_name]

    def filter_by_type(self, item_type):
        return self.by_type.get(item_type, [])

    def filter_by_subtype(self, subtype):
        return self.by_subtype.get(subtype, [])

    def search(self, keyword):
        keyword = keyword.lower()
        return [
            item for item in self.all_items
            if keyword in item.name.lower()
        ]

# items_repo = ItemRepository()
# items_repo.get("Longsword")
# items_repo.filter_by_type("Adventuring Gear")
# items_repo.get_many(["Longsword", "Shield"])
# items_repo.search("potion")
# Basically actions should be attached to items, i need a function to create actions from the item description if an action should in fact be created