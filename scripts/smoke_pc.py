from pathlib import Path

# Ensure repo root on path
ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from character import PCFactory, PCValidator


def main():
    pc = PCFactory.create_basic(
        name="Garian",
        race="Halfling",
        background="Acolyte",
        char_class="Cleric",
        ability_method="standard",
    )

    PCValidator(pc).validate()

    print("PC created:")
    print(pc)
    print("Ability scores:", pc.ability_scores.scores)
    print("Skills:", pc.skill_scores)
    print("Saves:", pc.saving_throws)
    print("Proficiencies:", {k.name: list(v) for k, v in pc.proficiencies.proficiencies.items()})
    print("Features:", [f.name for f in pc.features._features])


if __name__ == "__main__":
    main()
