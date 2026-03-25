import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
SRD_DIR = ROOT / "data" / "srd"
OUT_FILE = ROOT / "src" / "generated_features.py"


SYSTEM_PROMPT = """You are generating Python Feature class scaffolding for a D&D SRD engine.
Return ONLY valid JSON with these fields:
{
  "hp_bonus_on_attach": <int>,
  "hp_bonus_per_level": <int>,
  "notes": "<short note or empty>",
  "needs_review": <true|false>
}

Assumptions:
- Proficiencies, languages, senses, and ability bonuses are already applied automatically elsewhere.
- Only describe EXTRA mechanics not covered by those automatic applications.
- If you are unsure or the feature is descriptive only, set needs_review=true and use 0 bonuses.
"""


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _class_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", name).title().replace(" ", "")
    if not cleaned:
        cleaned = "Feature"
    if cleaned[0].isdigit():
        cleaned = f"Feature{cleaned}"
    return cleaned


def _call_ollama(prompt: str, model: str) -> Dict:
    try:
        from ollama import chat
        response = chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            format="json",
            options={"temperature": 0.1},
        )
        content = response["message"]["content"]
    except Exception:
        cmd = ["ollama", "run", model]
        full_prompt = SYSTEM_PROMPT + "\n\n" + prompt
        result = subprocess.run(cmd, input=full_prompt, text=True, capture_output=True, check=True)
        content = result.stdout.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "hp_bonus_on_attach": 0,
            "hp_bonus_per_level": 0,
            "notes": "LLM output was not valid JSON.",
            "needs_review": True,
        }


def _build_feature_list() -> List[Dict]:
    traits = _load(SRD_DIR / "traits.json")
    feats = _load(SRD_DIR / "feats.json")
    class_features = _load(SRD_DIR / "features.json")

    def tag(items, source):
        for item in items:
            item["_source_type"] = source
        return items

    merged = tag(traits, "trait") + tag(feats, "feat") + tag(class_features, "class")
    by_name = {}
    for item in merged:
        name = item.get("name")
        if not name:
            continue
        key = name.lower()
        if key not in by_name:
            by_name[key] = item
    return list(by_name.values())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    features = _build_feature_list()
    if args.limit:
        features = features[: args.limit]

    class_defs = []
    registry_lines = []

    class_defs.append("from features import Feature, apply_srd_feature_data")
    class_defs.append("")

    for feat in features:
        name = feat.get("name", "")
        desc = feat.get("desc") or []
        if isinstance(desc, list):
            desc_text = "\n".join(desc)
        else:
            desc_text = str(desc)

        prompt = f"""Feature name: {name}
Source type: {feat.get('_source_type')}
Description:
{desc_text}
"""
        llm = _call_ollama(prompt, args.model)
        class_name = _class_name(name)
        hp_on_attach = int(llm.get("hp_bonus_on_attach", 0) or 0)
        hp_per_level = int(llm.get("hp_bonus_per_level", 0) or 0)
        needs_review = bool(llm.get("needs_review", False))
        notes = llm.get("notes", "").strip()

        class_defs.append(f"class {class_name}(Feature):")
        class_defs.append(f"    def __init__(self):")
        class_defs.append(f"        super().__init__(\"{name}\", source=\"{feat.get('_source_type')}\")")
        class_defs.append("")
        class_defs.append(f"    def on_attach(self, character):")
        class_defs.append(f"        apply_srd_feature_data(character, \"{name}\")")
        if hp_on_attach:
            class_defs.append(f"        character.resources.update_health({hp_on_attach})")
        if needs_review or notes:
            note_text = notes or "Needs review."
            class_defs.append(f"        # TODO: {note_text}")
        class_defs.append("")
        if hp_per_level:
            class_defs.append(f"    def on_level_up(self, character, new_level: int):")
            class_defs.append(f"        character.resources.update_health({hp_per_level})")
            class_defs.append("")

        registry_lines.append(f"    \"{name}\": {class_name},")

    class_defs.append("GENERATED_FEATURES_REGISTRY = {")
    class_defs.extend(registry_lines)
    class_defs.append("}")

    OUT_FILE.write_text("\n".join(class_defs), encoding="utf-8")
    print(f"Wrote {len(features)} feature classes to {OUT_FILE}")


if __name__ == "__main__":
    main()
