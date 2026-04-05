from __future__ import annotations

import os
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure repo root and src are on sys.path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Ensure relative data paths resolve from repo root
os.chdir(ROOT)

import systems.character as char
from ai.gm import gm_llm
from data.npcs import NPCRepository
from systems.equipment_choices import (
    build_class_equipment_choices,
    build_background_equipment_choices,
    validate_equipment_choices,
)
from systems.spell_choices import (
    build_spell_choice_groups,
    validate_spell_choices,
    apply_spell_choices,
)
from systems.language_choices import (
    build_language_choice_groups,
    validate_language_choices,
    apply_language_choices,
)
from systems.proficiency_choices import (
    build_class_proficiency_choice_groups,
    validate_proficiency_choices,
    apply_proficiency_choices,
)
from systems.proficiency import ProficiencyType


app = FastAPI(title="Auto DnD UI")
logging.basicConfig(
    level=os.environ.get("AUTO_DND_LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("auto_dnd.ui")


@app.middleware("http")
async def add_no_store_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path or ""
    if path == "/" or path.startswith("/static"):
        response.headers["Cache-Control"] = "no-store"
    return response

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CharacterConfig(BaseModel):
    name: str = "Garian"
    race: str = "Halfling"
    background: str = "Acolyte"
    char_class: str = Field("Cleric", alias="class")
    ability_method: str = "roll"  # standard | roll | point_buy
    ability_score_assignment: Optional[List[str]] = None
    ability_score_values: Optional[List[int]] = None
    short_description: str = "A dark haired traveller with a well-worn staff and calm eyes."


class StartRequest(BaseModel):
    character: CharacterConfig
    model_name: str = "qwen3:8b"
    think: bool = False
    equipment_choices: Optional[Dict[str, List[str]]] = None
    proficiency_choices: Optional[Dict[str, List[str]]] = None
    spell_choices: Optional[Dict[str, List[str]]] = None
    language_choices: Optional[Dict[str, List[str]]] = None


class MessageRequest(BaseModel):
    content: str


class CombatActionRequest(BaseModel):
    action_id: Optional[str] = None
    target_ids: Optional[List[str]] = None
    end_turn: bool = False


class CombatMoveRequest(BaseModel):
    x: int
    y: int


class InventoryToggleRequest(BaseModel):
    item_name: str
    equipped: bool


class SpellToggleRequest(BaseModel):
    spell_name: str
    prepared: bool


class ActionRollRequest(BaseModel):
    action_id: str
    target_id: Optional[str] = None
    target_ids: Optional[List[str]] = None
    target_text: Optional[str] = None
    advantage: Optional[str] = None  # adv | dis
    narrate: bool = False
    player_text: Optional[str] = None


class ResourceUseRequest(BaseModel):
    resource_id: str
    amount: int = 1


class ClientLogRequest(BaseModel):
    level: str = "info"
    message: str
    data: Optional[Dict[str, Any]] = None


class GameSession:
    def __init__(self, config: StartRequest, pc: Optional[char.PC] = None):
        self.config = config
        self.images: List[str] = []
        self.pc = pc or self._build_pc(config.character)
        self._last_combat_log_hash: Optional[str] = None
        self.npc_repo = NPCRepository()
        self.gm = gm_llm(
            model_name=config.model_name,
            pc=self.pc,
            think=config.think,
            npc_factory=self.npc_repo.create,
            npc_names=self.npc_repo.list_names(),
        )
        self.gm.start_adventure()

    def _build_pc(self, cfg: CharacterConfig):
        pc = char.PCFactory().create_basic(
            name=cfg.name,
            race=cfg.race,
            background=cfg.background,
            char_class=cfg.char_class,
            ability_method=cfg.ability_method,
            ability_score_assignment=cfg.ability_score_assignment,
            ability_score_values=cfg.ability_score_values,
            equipment_choices=self.config.equipment_choices or {},
        )
        pc.short_character_description = cfg.short_description
        return pc

    def last_narrative(self) -> str:
        for turn in reversed(self.gm.turns):
            if turn.get("role") == "Dungeon Master":
                return turn.get("content", "")
        return ""

    def _consume_latest_combat_log(self) -> Optional[List[Dict[str, Any]]]:
        for turn in reversed(self.gm.turns):
            if turn.get("role") != "tool" or turn.get("tool_name") != "combat_engine":
                continue
            content = turn.get("content") or ""
            if not content:
                return None
            digest = hashlib.sha1(content.encode("utf-8")).hexdigest()
            if digest == self._last_combat_log_hash:
                return None
            self._last_combat_log_hash = digest
            try:
                parsed = json.loads(content)
            except Exception:
                return None
            return parsed if isinstance(parsed, list) else None
        return None

    def _combat_log_meta(self) -> Optional[Dict[str, Any]]:
        if not self.gm or not self.gm.combat or not self.gm.combat.combat_handler.engine:
            return None
        tracker = self.gm.combat.combat_handler.engine.tracker
        return {
            "round": getattr(tracker, "round_number", None),
            "current_turn": self.gm.combat.combat_handler.current_turn_id(),
        }

    def _serialize_features(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": f.name,
                "source": f.source,
                "type": f.feature_type,
                "description": f.description,
            }
            for f in self.pc.features._features
        ]

    def _serialize_proficiencies(self) -> Dict[str, List[str]]:
        return {
            prof_type.name.lower(): sorted(list(values))
            for prof_type, values in self.pc.proficiencies.proficiencies.items()
        }

    def _serialize_inventory(self) -> List[Dict[str, Any]]:
        items = []
        for item, qty in self.pc.inventory.items.items():
            equipped = item in self.pc.inventory.equipped
            equippable = False
            if hasattr(item, "raw"):
                category = (item.raw.get("equipment_category") or {}).get("index")
                equippable = category in {"weapon", "armor"}
            elif hasattr(item, "type"):
                equippable = str(item.type).lower() in {"weapon", "armor"}
            if hasattr(item, "name"):
                items.append({
                    "name": item.name,
                    "type": getattr(item, "type", None),
                    "subtype": getattr(item, "subtype", None),
                    "rarity": getattr(item, "rarity", None),
                    "description": getattr(item, "description", None),
                    "quantity": qty,
                    "equipped": equipped,
                    "equippable": equippable,
                })
            else:
                items.append({
                    "name": str(item),
                    "type": None,
                    "subtype": None,
                    "rarity": None,
                    "description": None,
                    "quantity": qty,
                    "equipped": False,
                    "equippable": False,
                })
        return items

    def _serialize_actions(self) -> List[Dict[str, Any]]:
        actions = []
        for action in self.pc.actions.available():
            actions.append({
                "id": action.id,
                "name": action.name,
                "type": action.action_type.name.lower(),
                "source": action.source,
                "damage_roll": action.damage_roll,
                "attack_roll": action.attack_roll,
                "save": getattr(action, "save", None),
                "resource_cost": action.resource_cost,
                "proficiency_type": action.proficiency_type.name.lower() if action.proficiency_type else None,
                "range": action.range,
                "targeting": action.targeting,
                "max_targets": action.max_targets,
                "spell_level": getattr(action, "spell_level", 0),
            })
        return actions

    def _serialize_resources(self) -> Dict[str, Any]:
        def pack_resource(res):
            return {
                "id": res.id,
                "name": res.name,
                "category": res.category.name.lower(),
                "current": res.current,
                "maximum": res.maximum,
                "recharge": res.recharge.name.lower(),
                "source": res.source,
            }

        return {
            "custom": [pack_resource(r) for r in self.pc.resources.resources.values()],
            "spell_slots": [pack_resource(r) for r in self.pc.resources.spell_slots.values()],
            "spell_access": [pack_resource(r) for r in self.pc.resources.spells.values()],
        }

    def _serialize_spells(self) -> Dict[str, Any]:
        prepared_limit = None
        class_names = [c.lower() for c in (self.pc.classes.classes or [])]
        if class_names:
            primary_class = class_names[0]
            if primary_class in {"cleric", "druid"}:
                ability = self.pc.spells.spellcasting_ability
                if ability:
                    ability_mod = self.pc.ability_scores.modifier(ability)
                else:
                    ability_mod = 0
                class_level = len(self.pc.classes.classes)
                prepared_limit = max(1, ability_mod + class_level)
        def pack_spell(spell):
            return {
                "name": spell.name,
                "level": spell.level,
                "school": spell.school,
                "range": spell.range,
                "cast_time": spell.cast_time,
                "duration": spell.duration,
                "components": spell.components,
                "ritual": spell.ritual,
                "source": spell.source,
                "description": spell.description,
                "prepared": spell.level == 0 or spell.name in self.pc.spells.prepared_spells,
            }

        return {
            "known": [pack_spell(s) for s in self.pc.spells.known_spells.values()],
            "prepared": [pack_spell(s) for s in self.pc.spells.prepared_spells.values()],
            "spellcasting_ability": self.pc.spells.spellcasting_ability,
            "spell_save_dc": self.pc.spells.spell_save_dc,
            "prepared_limit": prepared_limit,
        }

    def character_summary(self) -> Dict[str, Any]:
        return {
            "identity": {
                "name": self.pc.identity.name,
                "race": self.pc.identity.race,
                "background": self.pc.identity.background,
                "description": self.pc.short_character_description,
                "classes": self.pc.classes.classes,
                "level": len(self.pc.classes.classes),
            },
            "about": {
                "features": self._serialize_features(),
                "proficiencies": self._serialize_proficiencies(),
            },
            "abilities": {
                "ability_scores": self.pc.ability_scores.scores,
                "skill_scores": self.pc.skill_scores,
                "saving_throws": self.pc.saving_throws,
            },
            "inventory": {
                "items": self._serialize_inventory(),
            },
            "actions": {
                "actions": self._serialize_actions(),
                "resources": self._serialize_resources(),
            },
            "spells": self._serialize_spells(),
            "stats": {
                "hp": {
                    "current": self.pc.resources.current_hit_points,
                    "max": self.pc.resources.max_hit_points,
                },
                "ac": self.pc.stats.armor_class(),
            },
        }

    def state_payload(self) -> Dict[str, Any]:
        combat_payload = self.combat_payload()
        return {
            "character": self.character_summary(),
            "game_state": self.gm.game_state.model_dump() if self.gm.game_state else None,
            "story_summary": self.gm.story_summary if hasattr(self.gm, "story_summary") else None,
            "turns": self.gm.turns,
            "images": self.images,
            "combat": combat_payload,
        }

    def combat_payload(self) -> Dict[str, Any]:
        if not self.gm.game_state or self.gm.game_state.mode != "combat":
            return {"active": False}
        targets = []
        targets_detail: List[Dict[str, Any]] = []
        current_turn = None
        initiative_order = []
        move_remaining = None
        move_max = None
        round_number = None
        if self.gm.combat and self.gm.combat.combat_handler.engine:
            targets = self.gm.combat.combat_handler.enemy_ids
            current_turn = self.gm.combat.combat_handler.current_turn_id()
            initiative_order = self.gm.combat.combat_handler.engine.tracker.initiative_order
            round_number = self.gm.combat.combat_handler.engine.tracker.round_number
            engine = self.gm.combat.combat_handler.engine
            for target_id in targets:
                combatant = engine.combatants.get(target_id)
                if not combatant:
                    continue
                hp_current = engine._get_hp(combatant)
                hp_max = None
                if hasattr(combatant, "resources"):
                    hp_max = getattr(combatant.resources, "max_hit_points", None)
                elif hasattr(combatant, "hp"):
                    hp_max = engine._coerce_hp(getattr(combatant, "hp", None))
                ac = None
                if hasattr(combatant, "stats"):
                    try:
                        ac = combatant.stats.armor_class()
                    except Exception:
                        ac = None
                targets_detail.append({
                    "id": target_id,
                    "name": target_id,
                    "hp_current": hp_current,
                    "hp_max": hp_max,
                    "ac": ac,
                })
            if current_turn == self.pc.identity.name:
                move_remaining = self.gm.combat.turn_movement.get(self.pc.identity.name, 0)
                move_max = self.gm.combat._token_speed(self.pc.identity.name)
        return {
            "active": True,
            "targets": targets,
            "targets_detail": targets_detail,
            "current_turn": current_turn,
            "initiative_order": initiative_order,
            "round_number": round_number,
            "player_name": self.pc.identity.name,
            "turn_state": self.gm.combat.player_turn_state if current_turn == self.pc.identity.name else {
                "action": False,
                "bonus": False,
                "reaction": False,
            },
            "map": self.gm.combat.combat_map,
            "move_remaining": move_remaining,
            "move_max": move_max,
        }

    def handle_message(self, content: str) -> Dict[str, Any]:
        self.gm.run_turn(content)
        combat_log = self._consume_latest_combat_log()
        combat_log_meta = self._combat_log_meta() if combat_log else None
        return {
            "narrative": self.last_narrative(),
            "game_state": self.gm.game_state.model_dump() if self.gm.game_state else None,
            "story_summary": self.gm.story_summary if hasattr(self.gm, "story_summary") else None,
            "character": self.character_summary(),
            "combat": self.combat_payload(),
            "combat_log": combat_log,
            "combat_log_meta": combat_log_meta,
        }

    def handle_combat_action(self, action_id: str, target_ids: List[str]) -> Dict[str, Any]:
        error = self.gm.run_combat_action(action_id, target_ids, end_turn=False)
        if error:
            return {"error": error}
        combat_log = self._consume_latest_combat_log()
        combat_log_meta = self._combat_log_meta() if combat_log else None
        return {
            "narrative": self.last_narrative(),
            "game_state": self.gm.game_state.model_dump() if self.gm.game_state else None,
            "story_summary": self.gm.story_summary if hasattr(self.gm, "story_summary") else None,
            "character": self.character_summary(),
            "combat": self.combat_payload(),
            "combat_log": combat_log,
            "combat_log_meta": combat_log_meta,
        }

    def handle_combat_end_turn(self) -> Dict[str, Any]:
        error = self.gm.run_combat_action(None, None, end_turn=True)
        if error:
            return {"error": error}
        combat_log = self._consume_latest_combat_log()
        combat_log_meta = self._combat_log_meta() if combat_log else None
        return {
            "narrative": self.last_narrative(),
            "game_state": self.gm.game_state.model_dump() if self.gm.game_state else None,
            "story_summary": self.gm.story_summary if hasattr(self.gm, "story_summary") else None,
            "character": self.character_summary(),
            "combat": self.combat_payload(),
            "combat_log": combat_log,
            "combat_log_meta": combat_log_meta,
        }

    def handle_toggle_equip(self, item_name: str, equipped: bool) -> Dict[str, Any]:
        item = self.pc.inventory.get(item_name)
        if not item:
            return {"error": f"Item not found: {item_name}"}
        equippable = False
        if hasattr(item, "raw"):
            category = (item.raw.get("equipment_category") or {}).get("index")
            equippable = category in {"weapon", "armor"}
        elif hasattr(item, "type"):
            equippable = str(item.type).lower() in {"weapon", "armor"}
        if not equippable:
            return {"error": f"Item is not equippable: {item_name}"}
        try:
            self.pc.inventory.equip(item, "equip" if equipped else "unequip")
        except Exception as exc:
            return {"error": str(exc)}
        return {
            "character": self.character_summary(),
            "combat": self.combat_payload(),
        }

    def handle_toggle_prepare(self, spell_name: str, prepared: bool) -> Dict[str, Any]:
        spell = self.pc.spells.known_spells.get(spell_name) or self.pc.spells.prepared_spells.get(spell_name)
        if not spell:
            return {"error": f"Spell not found: {spell_name}"}
        if getattr(spell, "level", 1) == 0:
            return {"error": "Cantrips are always prepared."}
        try:
            self.pc.spells.prepare_spell(spell, "add" if prepared else "remove")
        except Exception as exc:
            return {"error": str(exc)}
        return {
            "character": self.character_summary(),
            "combat": self.combat_payload(),
        }

    def handle_action_roll(
        self,
        action_id: str,
        target_id: Optional[str] = None,
        target_ids: Optional[List[str]] = None,
        target_text: Optional[str] = None,
        advantage: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            action = self.pc.actions.get(action_id)
        except Exception:
            action = None
        if not action:
            return {"error": "Invalid action."}
        spell_level = getattr(action, "spell_level", 0) or 0
        if spell_level > 0:
            try:
                self.pc.resources.update_spell_slots(f"Level_{spell_level}", amount=1, use_spell=True)
            except Exception as exc:
                return {"error": str(exc)}
        roll_payload = self._resolve_action_roll(action, target_id, target_ids, target_text, advantage)
        if roll_payload.get("error"):
            return roll_payload
        roll_text = roll_payload.get("summary") or json.dumps(roll_payload, indent=2)
        self.gm.turns.append({
            "role": "tool",
            "tool_name": "action_roll",
            "content": roll_text,
        })
        if self.gm.game_state.mode == "combat":
            self._add_manual_combat_log(roll_payload)
        return {
            "result": roll_payload,
            "character": self.character_summary(),
            "combat": self.combat_payload(),
        }

    def _resolve_action_roll(
        self,
        action,
        target_id: Optional[str],
        target_ids: Optional[List[str]],
        target_text: Optional[str],
        advantage: Optional[str],
    ):
        from engine.game_engine import Dice, DiceHandler, DamageResult
        handler = DiceHandler()

        def resolve_prof_bonus():
            prof_type = action.proficiency_type or (action.attack_roll or {}).get("proficiency_type")
            if not prof_type:
                return 0
            if isinstance(prof_type, str):
                key = prof_type.strip().lower()
                if key in {"spell", "spellcasting", "spell attack", "spell_attack"}:
                    return self.pc.proficiencies.proficiency_bonus
                return self.pc.proficiencies.proficiency_bonus if self.pc.proficiencies.has_proficiency(
                    ProficiencyType.WEAPON, key
                ) else 0
            return 0

        result: Dict[str, Any] = {
            "action_id": action.id,
            "action_name": action.name,
            "target": target_id,
            "targets": target_ids or [],
            "target_text": target_text,
        }

        attack = action.attack_roll or None
        save = getattr(action, "save", None)

        if attack:
            ability = attack.get("ability")
            ability_options = attack.get("ability_options") or []
            ability_mod = handler._resolve_ability_modifier(self.pc, ability, ability_options)
            prof = resolve_prof_bonus()
            bonus = int(attack.get("bonus") or 0)
            roll = handler.roll(
                dice_specs=[(20, 1)],
                modifiers=ability_mod + bonus + prof,
                features=self.pc.features._features,
                advantage=advantage,
            )
            result["attack_roll"] = {
                "total": roll.total,
                "dice": roll.dice,
                "modifiers": roll.modifiers,
                "advantage": roll.advantage,
            }

        if save:
            save_ability = str(save.get("ability") or "").upper()
            save_dc = save.get("dc")
            if isinstance(save_dc, str) and save_dc == "spell_save_dc":
                save_dc = self.pc.spells.spell_save_dc
            result["save"] = {
                "ability": save_ability or None,
                "dc": save_dc,
                "on_success": save.get("on_success"),
            }

        damage_rolls = []
        if action.damage_roll:
            dmg_result = DamageResult()
            for val in action.damage_roll:
                temp = Dice.roll(sides=val["dice_type"], count=val["dice_amount"])
                if self.pc.features._features:
                    for feature in self.pc.features._features:
                        if getattr(feature, "feature_type", None) == "affects_rolls":
                            temp = feature(temp)
                if val.get("precomputed"):
                    temp.add_modifier(val["bonus"])
                else:
                    dmg_ability = val.get("ability")
                    dmg_options = val.get("ability_options") or []
                    dmg_mod = handler._resolve_ability_modifier(self.pc, dmg_ability, dmg_options)
                    temp.add_modifier(val.get("bonus", 0) + dmg_mod)
                dmg_result.add_damage(val["dmg_type"], temp)
                damage_rolls.append({
                    "type": val["dmg_type"],
                    "dice": temp.dice,
                    "total": temp.total,
                })
            result["damage_rolls"] = damage_rolls
            result["damage_total"] = dmg_result.total

        result["summary"] = _format_action_roll_summary(result)
        return result

    def handle_action_roll_and_narrate(
        self,
        action_id: str,
        target_id: Optional[str],
        target_ids: Optional[List[str]],
        target_text: Optional[str],
        advantage: Optional[str],
        player_text: Optional[str],
    ) -> Dict[str, Any]:
        roll_result = self.handle_action_roll(action_id, target_id, target_ids, target_text, advantage)
        if roll_result.get("error"):
            return roll_result
        if self.gm.game_state.mode == "combat":
            return roll_result
        action = self.pc.actions.get(action_id)
        if action:
            base_text = player_text or f"I use {action.name}."
        else:
            base_text = player_text or "I take an action."
        self.gm.run_turn(base_text)
        return {
            **roll_result,
            "narrative": self.last_narrative(),
            "game_state": self.gm.game_state.model_dump() if self.gm.game_state else None,
            "story_summary": self.gm.story_summary if hasattr(self.gm, "story_summary") else None,
        }

    def _add_manual_combat_log(self, roll_payload: Dict[str, Any]):
        combat = getattr(self.gm, "combat", None)
        if not combat or not hasattr(combat, "add_manual_log"):
            return

        attack = roll_payload.get("attack_roll") or {}
        save = roll_payload.get("save") or {}
        breakdown: Dict[str, int] = {}
        for entry in roll_payload.get("damage_rolls") or []:
            dmg_type = str(entry.get("type"))
            breakdown[dmg_type] = breakdown.get(dmg_type, 0) + int(entry.get("total") or 0)

        log = {
            "actor": self.pc.identity.name,
            "action_id": roll_payload.get("action_id"),
            "action_name": roll_payload.get("action_name"),
            "target": roll_payload.get("target"),
            "targets": roll_payload.get("targets") or None,
            "attack_total": attack.get("total"),
            "damage_total": roll_payload.get("damage_total"),
            "damage_breakdown": breakdown or None,
            "save_ability": save.get("ability"),
            "save_dc": save.get("dc"),
            "notes": "Manual roll (no engine resolution).",
        }
        combat.add_manual_log(log)


SESSION: Optional[GameSession] = None
PENDING: Optional[Dict[str, Any]] = None


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    html_path = TEMPLATES_DIR / "index.html"
    return HTMLResponse(
        html_path.read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/state")
def get_state() -> JSONResponse:
    if SESSION is None:
        return JSONResponse({"session": False})
    return JSONResponse({"session": True, **SESSION.state_payload()})


@app.get("/api/pending")
def get_pending() -> JSONResponse:
    if not PENDING:
        return JSONResponse({"pending": False})
    if PENDING.get("proficiency_groups"):
        return JSONResponse({
            "pending": True,
            "requires_proficiency_choices": True,
            "proficiency_choices": PENDING["proficiency_groups"],
        })
    if PENDING.get("language_groups"):
        return JSONResponse({
            "pending": True,
            "requires_language_choices": True,
            "language_choices": PENDING["language_groups"],
        })
    if PENDING.get("spell_groups"):
        return JSONResponse({
            "pending": True,
            "requires_spell_choices": True,
            "spell_choices": PENDING["spell_groups"],
        })
    return JSONResponse({"pending": False})


@app.post("/api/start")
def start_game(payload: StartRequest) -> JSONResponse:
    global SESSION, PENDING
    logger.info(
        "POST /api/start | pending=%s | has_equipment=%s | has_proficiency=%s | has_language=%s | has_spell=%s",
        bool(PENDING),
        bool(payload.equipment_choices),
        bool(payload.proficiency_choices),
        bool(payload.language_choices),
        bool(payload.spell_choices),
    )
    pc = None
    proficiency_choices_applied = False
    language_choices_applied = False

    if PENDING is not None and PENDING.get("language_groups") and not payload.language_choices:
        logger.info("Start blocked: missing language choices (pending).")
        logger.info("Returning language_groups (pending) count=%s", len(PENDING["language_groups"]))
        return JSONResponse({
            "session": False,
            "requires_language_choices": True,
            "language_choices": PENDING["language_groups"],
            "errors": ["Language choices required."],
        })

    if PENDING is not None and PENDING.get("proficiency_groups") and not payload.proficiency_choices:
        logger.info("Start blocked: missing proficiency choices (pending).")
        logger.info("Returning proficiency_groups (pending) count=%s", len(PENDING["proficiency_groups"]))
        return JSONResponse({
            "session": False,
            "requires_proficiency_choices": True,
            "proficiency_choices": PENDING["proficiency_groups"],
            "errors": ["Proficiency choices required."],
        })

    if PENDING is not None and PENDING.get("proficiency_groups") and payload.proficiency_choices:
        pc = PENDING["pc"]
        proficiency_groups = PENDING["proficiency_groups"]
        ok, errors = validate_proficiency_choices(proficiency_groups, payload.proficiency_choices or {})
        if not ok:
            logger.info("Start blocked: invalid proficiency choices | errors=%s", errors)
            return JSONResponse({
                "session": False,
                "requires_proficiency_choices": True,
                "proficiency_choices": proficiency_groups,
                "errors": errors,
            })
        apply_proficiency_choices(pc, payload.proficiency_choices or {}, proficiency_groups)
        PENDING = None
        proficiency_choices_applied = True
        logger.info("Proficiency choices applied (pending).")

    if PENDING is not None and PENDING.get("language_groups") and payload.language_choices:
        pc = PENDING["pc"]
        language_groups = PENDING["language_groups"]
        ok, errors = validate_language_choices(language_groups, payload.language_choices or {})
        if not ok:
            logger.info("Start blocked: invalid language choices | errors=%s", errors)
            return JSONResponse({
                "session": False,
                "requires_language_choices": True,
                "language_choices": language_groups,
                "errors": errors,
            })
        apply_language_choices(pc, payload.language_choices or {}, language_groups)
        PENDING = None
        language_choices_applied = True
        logger.info("Language choices applied (pending).")

    if PENDING is not None and PENDING.get("spell_groups") and not payload.spell_choices:
        logger.info("Start blocked: missing spell choices (pending).")
        logger.info("Returning spell_groups (pending) count=%s", len(PENDING["spell_groups"]))
        return JSONResponse({
            "session": False,
            "requires_spell_choices": True,
            "spell_choices": PENDING["spell_groups"],
            "errors": ["Spell choices required."],
        })

    if PENDING is not None and PENDING.get("spell_groups") and payload.spell_choices:
        pc = PENDING["pc"]
        spell_groups = PENDING["spell_groups"]
        ok, errors = validate_spell_choices(spell_groups, payload.spell_choices or {})
        if not ok:
            logger.info("Start blocked: invalid spell choices | errors=%s", errors)
            return JSONResponse({
                "session": False,
                "requires_spell_choices": True,
                "spell_choices": spell_groups,
                "errors": errors,
            })
        apply_spell_choices(pc, payload.spell_choices or {}, spell_groups)
        SESSION = GameSession(payload, pc=pc)
        PENDING = None
        logger.info("Spell choices applied (pending). Adventure started.")
        return JSONResponse({
            "session": True,
            "narrative": SESSION.last_narrative(),
            **SESSION.state_payload(),
        })

    if pc is None:
        choices = []
        choices.extend(build_class_equipment_choices(payload.character.char_class))
        choices.extend(build_background_equipment_choices(payload.character.background))
        if choices:
            ok, errors = validate_equipment_choices(choices, payload.equipment_choices or {})
            if not ok:
                logger.info("Start blocked: invalid equipment choices | errors=%s", errors)
                logger.info("Equipment choices payload keys: %s", list((payload.equipment_choices or {}).keys()))
                logger.info("Returning equipment choices count=%s", len(choices))
                PENDING = None
                return JSONResponse({
                    "session": False,
                    "requires_choices": True,
                    "choices": choices,
                    "errors": errors,
                })

        pc = char.PCFactory().create_basic(
            name=payload.character.name,
            race=payload.character.race,
            background=payload.character.background,
            char_class=payload.character.char_class,
            ability_method=payload.character.ability_method,
            ability_score_assignment=payload.character.ability_score_assignment,
            ability_score_values=payload.character.ability_score_values,
            equipment_choices=payload.equipment_choices or {},
        )
        pc.short_character_description = payload.character.short_description

    if not proficiency_choices_applied:
        proficiency_groups = build_class_proficiency_choice_groups(payload.character.char_class)
        if proficiency_groups:
            ok, errors = validate_proficiency_choices(proficiency_groups, payload.proficiency_choices or {})
            if not ok:
                logger.info("Start blocked: missing/invalid proficiency choices | errors=%s", errors)
                logger.info("Returning proficiency_groups count=%s", len(proficiency_groups))
                PENDING = {"pc": pc, "proficiency_groups": proficiency_groups}
                return JSONResponse({
                    "session": False,
                    "requires_proficiency_choices": True,
                    "proficiency_choices": proficiency_groups,
                    "errors": errors,
                })
            apply_proficiency_choices(pc, payload.proficiency_choices or {}, proficiency_groups)

    if not language_choices_applied:
        language_groups = build_language_choice_groups(
            payload.character.race,
            payload.character.background,
            payload.character.char_class,
        )
        if language_groups:
            ok, errors = validate_language_choices(language_groups, payload.language_choices or {})
            if not ok:
                logger.info("Start blocked: missing/invalid language choices | errors=%s", errors)
                logger.info("Returning language_groups count=%s", len(language_groups))
                PENDING = {"pc": pc, "language_groups": language_groups}
                return JSONResponse({
                    "session": False,
                    "requires_language_choices": True,
                    "language_choices": language_groups,
                    "errors": errors,
                })
            apply_language_choices(pc, payload.language_choices or {}, language_groups)

    spell_groups = build_spell_choice_groups(pc, payload.character.char_class)
    if spell_groups:
        ok, errors = validate_spell_choices(spell_groups, payload.spell_choices or {})
        if not ok:
            logger.info("Start blocked: missing/invalid spell choices | errors=%s", errors)
            logger.info("Returning spell_groups count=%s", len(spell_groups))
            PENDING = {"pc": pc, "spell_groups": spell_groups}
            return JSONResponse({
                "session": False,
                "requires_spell_choices": True,
                "spell_choices": spell_groups,
                "errors": errors,
            })
        apply_spell_choices(pc, payload.spell_choices or {}, spell_groups)

    SESSION = GameSession(payload, pc=pc)
    PENDING = None
    logger.info("Adventure started.")
    return JSONResponse({
        "session": True,
        "narrative": SESSION.last_narrative(),
        **SESSION.state_payload(),
    })


@app.post("/api/message")
def send_message(payload: MessageRequest) -> JSONResponse:
    if SESSION is None:
        return JSONResponse({"error": "Session not started"}, status_code=400)
    result = SESSION.handle_message(payload.content)
    return JSONResponse(result)


@app.post("/api/combat_action")
def combat_action(payload: CombatActionRequest) -> JSONResponse:
    if SESSION is None:
        return JSONResponse({"error": "Session not started"}, status_code=400)
    if payload.end_turn:
        result = SESSION.handle_combat_end_turn()
        return JSONResponse(result)

    target_ids = payload.target_ids or []
    if payload.action_id is None:
        return JSONResponse({"error": "Missing action_id."}, status_code=400)
    result = SESSION.handle_combat_action(payload.action_id, target_ids)
    return JSONResponse(result)


@app.post("/api/combat_move")
    def combat_move(payload: CombatMoveRequest) -> JSONResponse:
    if SESSION is None:
        return JSONResponse({"error": "Session not started"}, status_code=400)
    error = SESSION.gm.run_combat_move(payload.x, payload.y)
    if error:
        return JSONResponse({"error": error})
    combat_log = SESSION._consume_latest_combat_log()
    combat_log_meta = SESSION._combat_log_meta() if combat_log else None
    return JSONResponse({
        "narrative": SESSION.last_narrative(),
        "game_state": SESSION.gm.game_state.model_dump() if SESSION.gm.game_state else None,
        "story_summary": SESSION.gm.story_summary if hasattr(SESSION.gm, "story_summary") else None,
        "character": SESSION.character_summary(),
        "combat": SESSION.combat_payload(),
        "combat_log": combat_log,
        "combat_log_meta": combat_log_meta,
    })


@app.post("/api/inventory/equip")
def toggle_inventory(payload: InventoryToggleRequest) -> JSONResponse:
    if SESSION is None:
        return JSONResponse({"error": "Session not started"}, status_code=400)
    result = SESSION.handle_toggle_equip(payload.item_name, payload.equipped)
    if result.get("error"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@app.post("/api/spells/prepare")
def toggle_spell(payload: SpellToggleRequest) -> JSONResponse:
    if SESSION is None:
        return JSONResponse({"error": "Session not started"}, status_code=400)
    result = SESSION.handle_toggle_prepare(payload.spell_name, payload.prepared)
    if result.get("error"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@app.post("/api/action/roll")
def roll_action(payload: ActionRollRequest) -> JSONResponse:
    if SESSION is None:
        return JSONResponse({"error": "Session not started"}, status_code=400)
    if payload.narrate:
        result = SESSION.handle_action_roll_and_narrate(
            payload.action_id,
            payload.target_id,
            payload.target_ids,
            payload.target_text,
            payload.advantage,
            payload.player_text,
        )
    else:
        result = SESSION.handle_action_roll(
            payload.action_id,
            payload.target_id,
            payload.target_ids,
            payload.target_text,
            payload.advantage,
        )
    if result.get("error"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@app.post("/api/resource/use")
def use_resource(payload: ResourceUseRequest) -> JSONResponse:
    if SESSION is None:
        return JSONResponse({"error": "Session not started"}, status_code=400)
    try:
        SESSION.pc.resources.spend(payload.resource_id, payload.amount or 1)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return JSONResponse({
        "character": SESSION.character_summary(),
        "combat": SESSION.combat_payload(),
    })


@app.post("/api/log")
def client_log(payload: ClientLogRequest) -> JSONResponse:
    level = (payload.level or "info").lower()
    data = payload.data or {}
    if level == "warning":
        logger.warning("CLIENT | %s | %s", payload.message, data)
    elif level == "error":
        logger.error("CLIENT | %s | %s", payload.message, data)
    else:
        logger.info("CLIENT | %s | %s", payload.message, data)
    return JSONResponse({"ok": True})


@app.post("/api/reset")
def reset_session() -> JSONResponse:
    global SESSION
    SESSION = None
    return JSONResponse({"session": False})
def _format_action_roll_summary(payload: Dict[str, Any]) -> str:
    parts = [f"[ACTION ROLL] {payload.get('action_name')}"]
    if payload.get("targets"):
        parts.append(f"Targets: {', '.join(payload.get('targets') or [])}")
    elif payload.get("target"):
        parts.append(f"Target: {payload.get('target')}")
    elif payload.get("target_text"):
        parts.append(f"Target: {payload.get('target_text')}")
    attack = payload.get("attack_roll")
    if attack:
        adv = attack.get("advantage")
        adv_label = f" {adv}" if adv else ""
        parts.append(
            f"Attack roll:{adv_label} {attack.get('total')} (dice={attack.get('dice')} mods={attack.get('modifiers')})"
        )
    save = payload.get("save")
    if save:
        parts.append(
            f"Save: {save.get('ability')} vs DC {save.get('dc')} (on success: {save.get('on_success')})"
        )
    if payload.get("damage_rolls"):
        dmg_chunks = []
        for roll in payload.get("damage_rolls"):
            dmg_chunks.append(f"{roll.get('total')} {roll.get('type')} (dice={roll.get('dice')})")
        parts.append(f"Damage: {', '.join(dmg_chunks)}")
        parts.append(f"Damage total: {payload.get('damage_total')}")
    return " | ".join([p for p in parts if p])
