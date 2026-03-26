from __future__ import annotations

import os
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

import character as char
from gm import gm_llm
from npcs import NPCRepository
from equipment_choices import (
    build_class_equipment_choices,
    build_background_equipment_choices,
    validate_equipment_choices,
)


app = FastAPI(title="Auto DnD UI")

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
    short_description: str = "A compact halfling cleric with a travel-worn staff and calm eyes."


class StartRequest(BaseModel):
    character: CharacterConfig
    model_name: str = "qwen3:8b"
    think: bool = False
    equipment_choices: Optional[Dict[str, List[str]]] = None


class MessageRequest(BaseModel):
    content: str


class CombatActionRequest(BaseModel):
    action_id: Optional[str] = None
    target_ids: Optional[List[str]] = None
    end_turn: bool = False


class CombatMoveRequest(BaseModel):
    x: int
    y: int


class GameSession:
    def __init__(self, config: StartRequest):
        self.config = config
        self.images: List[str] = []
        self.pc = self._build_pc(config.character)
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
            if hasattr(item, "name"):
                items.append({
                    "name": item.name,
                    "type": getattr(item, "type", None),
                    "subtype": getattr(item, "subtype", None),
                    "rarity": getattr(item, "rarity", None),
                    "quantity": qty,
                })
            else:
                items.append({
                    "name": str(item),
                    "type": None,
                    "subtype": None,
                    "rarity": None,
                    "quantity": qty,
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
                "resource_cost": action.resource_cost,
                "proficiency_type": action.proficiency_type.name.lower() if action.proficiency_type else None,
                "range": action.range,
                "targeting": action.targeting,
                "max_targets": action.max_targets,
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
            }

        return {
            "known": [pack_spell(s) for s in self.pc.spells.known_spells.values()],
            "prepared": [pack_spell(s) for s in self.pc.spells.prepared_spells.values()],
            "spellcasting_ability": self.pc.spells.spellcasting_ability,
            "spell_save_dc": self.pc.spells.spell_save_dc,
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
        current_turn = None
        initiative_order = []
        move_remaining = None
        move_max = None
        if self.gm.combat and self.gm.combat.combat_handler.engine:
            targets = self.gm.combat.combat_handler.enemy_ids
            current_turn = self.gm.combat.combat_handler.current_turn_id()
            initiative_order = self.gm.combat.combat_handler.engine.tracker.initiative_order
            if current_turn == self.pc.identity.name:
                move_remaining = self.gm.combat.turn_movement.get(self.pc.identity.name, 0)
                move_max = self.gm.combat._token_speed(self.pc.identity.name)
        return {
            "active": True,
            "targets": targets,
            "current_turn": current_turn,
            "initiative_order": initiative_order,
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
        return {
            "narrative": self.last_narrative(),
            "game_state": self.gm.game_state.model_dump() if self.gm.game_state else None,
            "story_summary": self.gm.story_summary if hasattr(self.gm, "story_summary") else None,
            "character": self.character_summary(),
            "combat": self.combat_payload(),
        }

    def handle_combat_action(self, action_id: str, target_ids: List[str]) -> Dict[str, Any]:
        error = self.gm.run_combat_action(action_id, target_ids, end_turn=False)
        if error:
            return {"error": error}
        return {
            "narrative": self.last_narrative(),
            "game_state": self.gm.game_state.model_dump() if self.gm.game_state else None,
            "story_summary": self.gm.story_summary if hasattr(self.gm, "story_summary") else None,
            "character": self.character_summary(),
            "combat": self.combat_payload(),
        }

    def handle_combat_end_turn(self) -> Dict[str, Any]:
        error = self.gm.run_combat_action(None, None, end_turn=True)
        if error:
            return {"error": error}
        return {
            "narrative": self.last_narrative(),
            "game_state": self.gm.game_state.model_dump() if self.gm.game_state else None,
            "story_summary": self.gm.story_summary if hasattr(self.gm, "story_summary") else None,
            "character": self.character_summary(),
            "combat": self.combat_payload(),
        }


SESSION: Optional[GameSession] = None


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    html_path = TEMPLATES_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/state")
def get_state() -> JSONResponse:
    if SESSION is None:
        return JSONResponse({"session": False})
    return JSONResponse({"session": True, **SESSION.state_payload()})


@app.post("/api/start")
def start_game(payload: StartRequest) -> JSONResponse:
    global SESSION
    choices = []
    choices.extend(build_class_equipment_choices(payload.character.char_class))
    choices.extend(build_background_equipment_choices(payload.character.background))
    if choices:
        ok, errors = validate_equipment_choices(choices, payload.equipment_choices or {})
        if not ok:
            SESSION = None
            return JSONResponse({
                "session": False,
                "requires_choices": True,
                "choices": choices,
                "errors": errors,
            })
    SESSION = GameSession(payload)
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
    return JSONResponse({
        "narrative": SESSION.last_narrative(),
        "game_state": SESSION.gm.game_state.model_dump() if SESSION.gm.game_state else None,
        "story_summary": SESSION.gm.story_summary if hasattr(SESSION.gm, "story_summary") else None,
        "character": SESSION.character_summary(),
        "combat": SESSION.combat_payload(),
    })


@app.post("/api/reset")
def reset_session() -> JSONResponse:
    global SESSION
    SESSION = None
    return JSONResponse({"session": False})
