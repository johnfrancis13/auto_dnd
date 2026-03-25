import json
from collections import defaultdict
from helper_functions import clean_item_description, extract_link_text
from srd_loader import load_srd

class Item:
    def __init__(self, data):
        self.name = data["name"].replace(" (Copy)", "").strip()
        if "equipment_category" in data:
            desc = data.get("desc") or []
            self.description = "\n".join(desc).strip()
            category = data.get("equipment_category")
            if isinstance(category, dict):
                self.type = category.get("name")
            else:
                self.type = category
            self.subtype = (
                data.get("weapon_category")
                or data.get("armor_category")
                or data.get("gear_category")
            )
            rarity = data.get("rarity")
            if isinstance(rarity, dict):
                rarity = rarity.get("name")
            self.rarity = rarity or "Common"
            self.attunement = bool(data.get("requires_attunement")) or "attunement" in (
                self.rarity or ""
            ).lower()
            cost = data.get("cost") or {}
            if isinstance(cost, dict):
                qty = cost.get("quantity")
                unit = cost.get("unit")
                self.cost = f"{qty} {unit}".strip() if qty is not None else None
            else:
                self.cost = cost
            self.weight = data.get("weight", 0)
            self.links = []
        else:
            self.description = clean_item_description(data.get("description", ""))
            self.type = data.get("type", None)
            self.subtype = data.get("subType", None)
            self.rarity = data.get("Rarity","Common")
            self.attunement = "attunement" in (self.rarity or "").lower()
            self.cost = data.get("cost",0)
            self.weight = data.get("weight",0)
            self.links = extract_link_text(data)


class ItemRepository:
    def __init__(self, path=None):
        if path is None:
            equipment = load_srd("equipment", "5e-SRD-Equipment.json")
            magic_items = load_srd("magic_items", "5e-SRD-Magic-Items.json")
            raw_data = list(equipment or []) + list(magic_items or [])
        else:
            from pathlib import Path
            with Path(path).open("r", encoding="utf-8") as f:
                raw_data = json.load(f)

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
