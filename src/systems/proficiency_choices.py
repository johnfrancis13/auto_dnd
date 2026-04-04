from typing import Dict, List, Any, Tuple

from data.srd_loader import load_srd
from systems.proficiency import ProficiencyType


def _srd_skill_name(value: str) -> str:
    value = value.replace("Skill:", "").strip()
    return value.lower().replace(" ", "_")


def _srd_tool_name(value: str) -> str:
    value = value.replace("Tool:", "").strip()
    return value.lower()


def build_class_proficiency_choice_groups(class_name: str) -> List[Dict[str, Any]]:
    classes = load_srd("classes", "5e-SRD-Classes.json") or []
    entry = next((c for c in classes if c.get("name", "").lower() == class_name.lower()), None)
    if not entry:
        return []

    groups: List[Dict[str, Any]] = []
    class_index = entry.get("index") or class_name.lower()

    for idx, choice in enumerate(entry.get("proficiency_choices", []) or []):
        if choice.get("type") != "proficiencies":
            continue
        choose = int(choice.get("choose") or 1)
        desc = choice.get("desc") or ""
        options: List[Dict[str, Any]] = []
        option_counter = 0
        prof_types = set()
        for opt in choice.get("from", {}).get("options", []) or []:
            item = opt.get("item") or {}
            name = item.get("name") or ""
            if name.startswith("Skill:"):
                value = _srd_skill_name(name)
                label = name.replace("Skill:", "").strip()
                prof_type = "skill"
            elif name.startswith("Tool:"):
                value = _srd_tool_name(name)
                label = name.replace("Tool:", "").strip()
                prof_type = "tool"
            elif name.startswith("Language:"):
                value = name.replace("Language:", "").strip()
                label = value
                prof_type = "language"
            else:
                continue
            prof_types.add(prof_type)
            options.append({
                "id": f"proficiencies:class:{class_index}:{idx}:{option_counter}",
                "label": label,
                "prof_type": prof_type,
                "value": value,
            })
            option_counter += 1
        if options:
            if not desc or desc.lower().startswith("choose"):
                if prof_types == {"skill"}:
                    desc = "Choose Skills"
                elif prof_types == {"tool"}:
                    desc = "Choose Tool Proficiencies"
                elif prof_types == {"language"}:
                    desc = "Choose Languages"
                else:
                    desc = "Choose Proficiencies"
            groups.append({
                "id": f"proficiencies:class:{class_index}:{idx}",
                "label": desc,
                "choose": choose,
                "options": options,
            })
    return groups


def validate_proficiency_choices(
    choices: List[Dict[str, Any]],
    selection_map: Dict[str, List[str]],
) -> Tuple[bool, List[str]]:
    errors = []
    for group in choices:
        group_id = group.get("id")
        choose = int(group.get("choose") or 1)
        selected = selection_map.get(group_id, []) if selection_map else []
        if len(selected) != choose:
            errors.append(f"{group_id} requires {choose} selection(s).")
            continue
        valid_ids = {opt.get("id") for opt in group.get("options", [])}
        invalid = [sid for sid in selected if sid not in valid_ids]
        if invalid:
            errors.append(f"{group_id} has invalid selections.")
    return len(errors) == 0, errors


def apply_proficiency_choices(
    character,
    selection_map: Dict[str, List[str]],
    choices: List[Dict[str, Any]],
) -> None:
    if not selection_map:
        return

    additions: Dict[ProficiencyType, set] = {
        ProficiencyType.SKILL: set(),
        ProficiencyType.TOOL: set(),
        ProficiencyType.LANGUAGE: set(),
    }

    for group in choices:
        group_id = group.get("id")
        selected = set(selection_map.get(group_id, []) or [])
        if not selected:
            continue
        for option in group.get("options", []):
            if option.get("id") not in selected:
                continue
            prof_type = option.get("prof_type")
            value = option.get("value")
            if not value:
                continue
            if prof_type == "skill":
                additions[ProficiencyType.SKILL].add(value)
            elif prof_type == "tool":
                additions[ProficiencyType.TOOL].add(value)
            elif prof_type == "language":
                additions[ProficiencyType.LANGUAGE].add(value)

    for prof_type, values in list(additions.items()):
        if not values:
            additions.pop(prof_type)

    if additions:
        character.proficiencies.add_proficiencies(additions)
        character.update_skills()
