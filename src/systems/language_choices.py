from typing import Dict, List, Any, Tuple, Set

from data.srd_loader import load_srd
from systems.proficiency import ProficiencyType


def _load_languages() -> List[Dict[str, Any]]:
    return load_srd("languages", "5e-SRD-Languages.json") or []


def _language_names_from_list(entries: List[Any]) -> Set[str]:
    names: Set[str] = set()
    for entry in entries or []:
        if isinstance(entry, dict):
            name = entry.get("name")
        else:
            name = str(entry)
        if name:
            names.add(name)
    return names


def _language_options_from_block(block: Dict[str, Any]) -> List[str]:
    if not block:
        return []
    from_block = block.get("from") or {}
    option_set_type = from_block.get("option_set_type")
    options: List[str] = []

    if option_set_type == "resource_list":
        for lang in _load_languages():
            name = lang.get("name")
            if name:
                options.append(name)
        return options

    if option_set_type == "options_array":
        for opt in from_block.get("options") or []:
            if opt.get("option_type") != "reference":
                continue
            item = opt.get("item") or {}
            name = item.get("name")
            if name:
                options.append(name)
        return options

    return options


def _build_group(
    group_prefix: str,
    label: str,
    choose: int,
    options: List[str],
    known_languages: Set[str],
) -> Dict[str, Any]:
    filtered = [name for name in options if name not in known_languages]
    option_list = filtered or options
    group_id = f"{group_prefix}"
    option_payload = []
    for idx, name in enumerate(option_list):
        option_payload.append({
            "id": f"{group_id}:{idx}",
            "label": name,
            "language": name,
        })
    return {
        "id": group_id,
        "label": label,
        "choose": int(choose or 1),
        "options": option_payload,
    }


def _language_options_from_proficiency_choices(entry: Dict[str, Any]) -> Tuple[int, List[str]]:
    choose = 0
    options: List[str] = []
    for choice in entry.get("proficiency_choices", []) or []:
        if choice.get("type") != "proficiencies":
            continue
        choose = max(choose, int(choice.get("choose") or 0))
        for opt in choice.get("from", {}).get("options", []) or []:
            item = opt.get("item") or {}
            name = item.get("name") or ""
            if name.startswith("Language:"):
                options.append(name.replace("Language:", "").strip())
    return choose, options


def build_language_choice_groups(race_name: str, background_name: str, class_name: str) -> List[Dict[str, Any]]:
    groups: List[Dict[str, Any]] = []
    known_languages: Set[str] = set()

    races = load_srd("races", "5e-SRD-Races.json") or []
    backgrounds = load_srd("backgrounds", "5e-SRD-Backgrounds.json") or []
    classes = load_srd("classes", "5e-SRD-Classes.json") or []

    race_entry = next((r for r in races if r.get("name", "").lower() == race_name.lower()), None)
    background_entry = next(
        (b for b in backgrounds if b.get("name", "").lower() == background_name.lower()),
        None,
    )
    class_entry = next((c for c in classes if c.get("name", "").lower() == class_name.lower()), None)

    if race_entry:
        known_languages |= _language_names_from_list(race_entry.get("languages") or [])
    if background_entry:
        known_languages |= _language_names_from_list(background_entry.get("languages") or [])
        for prof in background_entry.get("proficiencies", []) or []:
            name = prof.get("name") if isinstance(prof, dict) else str(prof)
            if name and name.startswith("Language:"):
                known_languages.add(name.replace("Language:", "").strip())
    if class_entry:
        for prof in class_entry.get("proficiencies", []) or []:
            name = prof.get("name") if isinstance(prof, dict) else str(prof)
            if name and name.startswith("Language:"):
                known_languages.add(name.replace("Language:", "").strip())

    if race_entry and race_entry.get("language_options"):
        block = race_entry.get("language_options") or {}
        options = _language_options_from_block(block)
        if options:
            groups.append(
                _build_group(
                    f"languages:race:{race_entry.get('index') or race_name.lower()}",
                    "Choose Race Languages",
                    block.get("choose") or 1,
                    options,
                    known_languages,
                )
            )

    if background_entry and background_entry.get("language_options"):
        block = background_entry.get("language_options") or {}
        options = _language_options_from_block(block)
        if options:
            groups.append(
                _build_group(
                    f"languages:background:{background_entry.get('index') or background_name.lower()}",
                    "Choose Background Languages",
                    block.get("choose") or 1,
                    options,
                    known_languages,
                )
            )

    if class_entry:
        choose, options = _language_options_from_proficiency_choices(class_entry)
        if choose and options:
            groups.append(
                _build_group(
                    f"languages:class:{class_entry.get('index') or class_name.lower()}",
                    "Choose Class Languages",
                    choose,
                    options,
                    known_languages,
                )
            )

    return groups


def validate_language_choices(
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


def apply_language_choices(
    character,
    selection_map: Dict[str, List[str]],
    choices: List[Dict[str, Any]],
) -> None:
    if not selection_map:
        return
    for group in choices:
        group_id = group.get("id")
        selected = set(selection_map.get(group_id, []) or [])
        if not selected:
            continue
        languages = set()
        for option in group.get("options", []):
            if option.get("id") not in selected:
                continue
            language = option.get("language") or option.get("label")
            if language:
                languages.add(language)
        if languages:
            character.proficiencies.add_proficiencies({
                ProficiencyType.LANGUAGE: languages,
            })
