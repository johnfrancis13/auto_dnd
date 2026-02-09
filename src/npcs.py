# Class to create an NPC
class NPCFactory:
    @staticmethod
    def create_basic(name, # str
                     race, # str name of valid race
                     background, # str name of valid background
                     char_class, # str name of valid class
                     ability_method="standard", # one of [standard, roll, point_buy]
                     ability_score_assignment=None, # ["STR","DEX","CON","INT","WIS","CHA"]
                     ability_score_values=None # list of valid point buy numbers [8,10,11,13,15,8]
                     ):
        pc = PC(name, race, background)
        
        # Generate the values
        if ability_method == "standard":
            ability_score_values = AbilityScoreGenerator.standard_array()
        elif ability_method == "roll":
            ability_score_values = AbilityScoreGenerator.roll_4d6_drop_lowest()
        elif ability_method == "point_buy":
            if not ability_score_values:
                raise ValueError("Must provide point buy distribution")
            ability_score_values = AbilityScoreGenerator.point_buy(ability_score_values)
        else:
            raise ValueError(f"Unknown method: {ability_method}, must be one of [standard, roll, point_buy]")
        
        # If assignment not given, default to sorted assignment
        if ability_score_assignment is None:
            # Default priority: str, dex, con, int, wis, cha - should ideally be unique to each class...
            ability_score_assignment =  ["STR","DEX","CON","INT","WIS","CHA"]
        else: # otherwise, validate correct values are provided
            expected = {"STR", "DEX", "CON", "INT", "WIS", "CHA"}
            if len(ability_score_assignment) != 6:
                raise ValueError(f"Must provide exactly 6 abilities, got {len(ability_score_assignment)}: {ability_score_assignment}")
            if set(ability_score_assignment) != expected:
                raise ValueError(f"Keys must be exactly {expected}, got {ability_score_assignment}")

        pc.ability_scores = AbilityScores(dict(zip(ability_score_assignment, sorted(ability_score_values, reverse=True))))
        
        # Apply race bonuses
        if pc.identity.race:
           Race(pc.identity.race).apply(pc)
        
        # Apply background bonuses
        if pc.identity.background:
            Background(pc.identity.background).apply(pc)

        # Apply class, etc.
        if char_class:
            pc.classes.add_class(char_class, pc)
        
        # Ensure the character is a valid 5e character
        NPCValidator(pc).validate()

        return pc

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


# A class to check if a pc is a valid 5e character
class NPCValidator:
    def __init__(self, pc):
        self.pc = pc

    def validate(self):
        errors = []

        # 1. Abilities: must all be between 1-20 
        for abbr, score in self.pc.ability_scores.scores.items():
            if not (1 <= score <= 20):
                errors.append(f"Ability {abbr} has invalid score {score}")

        # 2. Race: must exist
        if not self.pc.identity.race:
            errors.append("No race assigned")

        # 3. Background: must exist
        if not self.pc.identity.background:
            errors.append("No background assigned")

        # 4. Classes: must have at least one level
        if  (len(self.pc.classes.classes)<1 or len(self.pc.classes.classes)>20):  
            errors.append("Character must have at least one class, and no more than 20 class levels.")

        # # 5. Proficiencies: check if any are missing
        # if not self.proficiencies.valid():
        #     errors.append("Proficiencies not properly assigned")

        # # 6. Features: at least the minimum required for class and race
        # if not self.features.valid():
        #     errors.append("Features missing or inconsistent")

        # # 7. Spells: if spellcasting class, must have spell slots
        # if hasattr(self.spells, "validate") and not self.spells.validate():
        #     errors.append("Spells not valid for spellcasting class")

        if errors:
            raise ValueError("Character validation failed:\n" + "\n".join(errors))
        return True