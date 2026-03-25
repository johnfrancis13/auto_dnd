import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRD_DIR = ROOT / "data" / "srd"


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require(entry, fields, label):
    missing = [f for f in fields if f not in entry]
    if missing:
        return f"{label}: missing {missing}"
    return None


def validate_spells():
    spells = _load(SRD_DIR / "spells.json")
    errors = []
    for spell in spells:
        err = _require(spell, ["name", "level", "school", "range"], "spell")
        if err:
            errors.append(err)
    return errors


def validate_monsters():
    monsters = _load(SRD_DIR / "monsters.json")
    errors = []
    for monster in monsters:
        err = _require(monster, ["name", "hit_points", "armor_class"], "monster")
        if err:
            errors.append(err)
    return errors


def validate_classes():
    classes = _load(SRD_DIR / "classes.json")
    errors = []
    for cls in classes:
        err = _require(cls, ["name", "hit_die", "proficiencies"], "class")
        if err:
            errors.append(err)
    return errors


def validate_races():
    races = _load(SRD_DIR / "races.json")
    errors = []
    for race in races:
        err = _require(race, ["name", "size", "speed"], "race")
        if err:
            errors.append(err)
    return errors


def main():
    if not SRD_DIR.exists():
        raise FileNotFoundError("data/srd does not exist. Run build first.")

    checks = [
        ("spells", validate_spells),
        ("monsters", validate_monsters),
        ("classes", validate_classes),
        ("races", validate_races),
    ]

    total = 0
    for name, fn in checks:
        errors = fn()
        total += len(errors)
        if errors:
            print(f"{name}: {len(errors)} issue(s)")
            for err in errors[:10]:
                print(f"  - {err}")
        else:
            print(f"{name}: ok")

    if total:
        raise SystemExit(f"Validation failed with {total} error(s).")

    print("All SRD checks passed.")


if __name__ == "__main__":
    main()
