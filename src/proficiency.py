from enum import Enum, auto
def proficiency_bonus(level: int) -> int:
    return 2 + ((level - 1) // 4)

# Types of proficiencies one could have
class ProficiencyType(Enum):
    ARMOR = auto()
    WEAPON = auto()
    TOOL = auto()
    SKILL = auto()
    ABILITY = auto()
    LANGUAGE = auto()
    SAVE = auto()
    

# Manager class to deal with proficiency
class ProficiencyManager:
    def __init__(self, owner):
        self.owner = owner
        self.proficiencies = {
            ProficiencyType.ARMOR: set(),
            ProficiencyType.WEAPON: set(),
            ProficiencyType.TOOL: set(),
            ProficiencyType.SKILL: set(),
            ProficiencyType.ABILITY: set(),
            ProficiencyType.LANGUAGE: set(),
            ProficiencyType.SAVE: set(),
        }
        self.proficiency_bonus = 1
    
    def update_proficiency_bonus(self, level: int) -> int:
        self.proficiency_bonus = 2 + (level - 1) // 4
        return self.proficiency_bonus
    
    def add_proficiencies(self, source_proficiencies):
        for prof_type, values in source_proficiencies.items():
            self.proficiencies[prof_type].update(values)

    def has_proficiency(self, prof_type, value):
        return value in self.proficiencies[prof_type]
