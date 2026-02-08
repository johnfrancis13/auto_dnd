class NPC:
    def __init__(self, name, race, background):
        self.identity = Identity(name, race, background)
        self.ability_scores = AbilityScores()
        self.resources = ResourcePool()
        self.inventory = Inventory()
        self.features = FeatureManager()
        self.spells = Spellcasting()
        self.conditions = ConditionManager()


def create_npc(name:str,
               cr:int,
               race:str):
    
    return NPC_new

# Same as above, but connected to random generators
def create_random_npc(name:str,
                      cr:int,
                      race:str):
    
    return NPC_new