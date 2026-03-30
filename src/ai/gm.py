# This is the AI brain. The AI should control the flow of the game, create new content as necessary
from ollama import chat
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Literal
from content.one_shot_adventures import one_shot_adventures
from engine.game_engine import CombatEngine
from rules.actions import ActionType
import random
import json
import textwrap
import subprocess

# Load in the testing pydantic classes

SkillLiteral = Literal[
    "athletics","acrobatics","sleight_of_hand","stealth",
    "arcana","history","investigation","nature","religion",
    "animal_handling","insight","medicine","perception","survival",
    "deception","intimidation","performance","persuasion"
]

AbilityLiteral = Literal["STR", "DEX", "CON", "INT", "WIS", "CHA"]

class Mechanics(BaseModel):
    player_intent: str
    requires_roll: bool
    roll_type: Optional[Literal["skill", "ability", "save"]] = None
    skill: Optional[SkillLiteral] = None
    ability: Optional[AbilityLiteral] = None


class CombatIntent(BaseModel):
    action_id: Optional[str] = None
    target: Optional[str] = None
    end_turn: bool = False


class CombatNarration(BaseModel):
    narrative: str


class NPCMove(BaseModel):
    x: int
    y: int


class EncounterEntry(BaseModel):
    name: str
    count: int = 1


class EncounterSelection(BaseModel):
    enemies: List[EncounterEntry] = []

class CombatState(BaseModel):
    initiative_order: List[str]
    current_turn: Optional[str]

class GameState(BaseModel):
    mode: Literal["exploration", "combat"]
    player: str
    enemy: Optional[str]
    enemies: Optional[List[str]] = None
    combat: Optional[CombatState]
    game_over: bool

class GMResponse(BaseModel):
    game_state: GameState
    narrative: str

def wrap_text(text, width=175):
    print("\n".join(textwrap.fill(p, width) for p in text.split("\n")))



def format_recent_turns(turns):
    formatted = ""
    for t in turns:
        formatted += f"{t['role'].upper()}: {t['content']}\n"
    return formatted





class gm_llm:
    def __init__(self,model_name="qwen3:8b",pc=None, think=False, npc_index=None, npc_factory=None, npc_names=None):
        self.model_name = model_name
        self.pc= pc
        self.think=think
        self.actions = GMActionHandler(self.pc)
        self.npc_names = npc_names or []
        self.adventure_npc_names = []
        self.baseline_npc_names = [
            "Commoner",
            "Guard",
            "Bandit",
            "Thug",
            "Scout",
            "Acolyte",
            "Priest",
            "Noble",
            "Cultist",
            "Bandit Captain",
            "Veteran",
            "Knight",
            "Spy",
            "Assassin",
            "Mage",
            "Archmage",
            "Druid",
            "Gladiator",
            "Berserker",
            "Tribal Warrior",
        ]
        self.combat = CombatOrchestrator(
            owner=self,
            model_name=self.model_name,
            pc=self.pc,
            think=self.think,
            npc_index=npc_index,
            npc_factory=npc_factory,
        )
    def choose_new_adventure(self):
        self.adventure_data = random.choice(one_shot_adventures)
        self.adventure_npc_names = self.adventure_data.get("npc_options") or []
    # Iterate the model to respond to the latest game state
    def start_adventure(self):
        wrap_text("\n-Setting up the game...")
        self.choose_new_adventure()
        self.create_prompts()
        character_introduction = f"Hi, My character is {self.pc.identity.name}, a level {len(self.pc.classes.classes)} {self.pc.identity.race} {self.pc.classes.classes[0]} with the background of {self.pc.identity.background}. {self.pc.short_character_description}"
        wrap_text("\n--- Player ---")
        wrap_text(character_introduction)

        # Set up the turn tracking - eventually switch this bit to logging
        self.turns = [{'role': 'user', 
                 'content': f'{character_introduction} Lets start the adventure!'}
                 ]
        # Create the initial prompt to start the adventure
        response = chat(
            model=self.model_name,
            messages=[{
                "role": "system",
                "content": self.narrator_system_prompt + "\nBegin by introducing the setting and hook naturally, assuming the player knows nothing. Explain why they are here, and what they are doing without revealing any plot twists."
                },
                {'role': 'user', 
                 'content': f'{character_introduction} Lets start the adventure!'}
                 ],
            think=self.think,
            options = {"num_ctx": 2048},
            format=GMResponse.model_json_schema()
        )

        parsed = GMResponse.model_validate_json(response.message.content)
        wrap_text("\n--- DM ---")
        wrap_text(parsed.narrative)
        self.turns.append({
                  "role": "Dungeon Master",
                  "content": parsed.narrative
              })
        self.story_summary = "The story has just begun"
        self.game_state = parsed.game_state
    
    def create_prompts(self):
        npc_hint = ""
        if self.adventure_npc_names or self.baseline_npc_names:
            npc_hint = (
                f"\n            NPC OPTIONS (use for combat when possible): "
                f"{self.adventure_npc_names + self.baseline_npc_names}"
            )
        self.narrator_system_prompt = f"""
            ### Dungeon Master
            You are a 5e Dungeon Master with access to all the source books and the ability to homebrew content as necessary.
            You are narrating a unique game for the user.
            You follow the style of DM's like Matthew Mercer and Brennan Lee Mulligan allowing for flexible gameplay that puts the players choices first.
            Your top priorities are player enjoyment and 5e rule following. You are responsible for narration, NPC behavior/roleplay, and scene progression.

            ### Instructions
            - Describe scenes vividly but concisely.
            - Play NPCs dynamically.
            - Maintain tension and pacing.
            - Respect player autonomy, DON'T provide the player specific choices unless they ask for it, allow them to drive the story
            - Never decide player actions, never speak on behalf of the player.
            - If a skill check is provided, determine an appropriate DC based on the context and explain what happens given the value of the roll.
            - If combat is active, use the COMBAT LOG for outcomes. Do not invent rolls or change mechanical results.
            - If combat begins and you know the exact NPCs involved, set game_state.enemies to their names; otherwise leave it null.
            - Keep the game in exploration mode unless the player or an NPC initiates combat explicitly

            ### Session 0
            The user is a consenting adult. Your session 0 has allowed adult topics such as violence, religion, politics, alchohol, drugs, and sex. 

            ### GAME PARAMETERS
            - Short one-shot, with a length of 30 minutes to 1 hour.
            - Balance for one level 5 or lower PC.
            - Assume 3-5 scenes maximum
            The current one shot you are running is:
            {self.adventure_data}
            {npc_hint}
            """
        self.rules_system_prompt = """
            You are a D&D 5e rules engine responsible ONLY for mechanics.

            Your job:
            1. Extract the player's intent.
            2. Determine whether a skill check is required.
            3. If required, choose the roll type (skill, ability, or save) and the correct stat.

            --------------------------------
            A skill check is required if:
            - 5e rules dictate a roll in this situation.
            - The outcome is uncertain.
            - Failure would matter.
            - Success is possible.

            If the action is trivial or automatically successful, no roll is required.

            --------------------------------
            Roll Types:
            - "skill": choose one of the allowed skills.
            - "ability": choose one of STR, DEX, CON, INT, WIS, CHA.
            - "save": choose one of STR, DEX, CON, INT, WIS, CHA.

            Use "ability" for raw ability checks not tied to a trained skill.
            Use "save" for resisting effects.

            --------------------------------
            Allowed skills:
            athletics, acrobatics, sleight_of_hand, stealth,
            arcana, history, investigation, nature, religion,
            animal_handling, insight, medicine, perception, survival,
            deception, intimidation, performance, persuasion

            --------------------------------
            Output Rules:
            - Respond ONLY in valid JSON.
            - Do not explain reasoning.
            - If requires_roll is false, roll_type, skill, and ability must be null.
            - If roll_type is "skill", skill must be one of the allowed skills and ability must be null.
            - If roll_type is "ability" or "save", ability must be one of STR/DEX/CON/INT/WIS/CHA and skill must be null.

            --------------------------------
            Examples:

            {
              "player_intent": "force open reinforced wooden door",
              "requires_roll": true,
              "roll_type": "skill",
              "skill": "athletics",
              "ability": null
            }

            {
              "player_intent": "ask the shopkeeper what goods they have in stock",
              "requires_roll": false,
              "roll_type": null,
              "skill": null,
              "ability": null
            }

            {
              "player_intent": "brute force the stuck wagon wheel",
              "requires_roll": true,
              "roll_type": "ability",
              "skill": null,
              "ability": "STR"
            }

            {
              "player_intent": "resist the poison gas",
              "requires_roll": true,
              "roll_type": "save",
              "skill": null,
              "ability": "CON"
            }
            """
        self.combat_rules_prompt = """
            You are a D&D 5e combat action parser.

            Your job:
            1. Identify the player's intended action.
            2. Map it to one of the provided action IDs.
            3. Select a target from the provided target list.

            --------------------------------
            Output Rules:
            - Respond ONLY in valid JSON.
            - If the player is ending their turn, set end_turn to true and action_id/target to null.
            - Otherwise, action_id must be one of the provided action IDs.
            - target must be one of the provided target names if the action requires a target.

            Example:
            {
              "action_id": "longsword_attack",
              "target": "Goblin",
              "end_turn": false
            }
            """
        self.combat_narrator_prompt = self.narrator_system_prompt + """
            ### Combat Narration
            - Use the COMBAT LOG to describe what happened.
            - Do not add new rolls, damage, or state changes.
            - Keep the narration punchy and end by prompting the next decision if combat continues.
            """
        self.combat_encounter_prompt = """
            You are a D&D 5e encounter selector.

            Your job:
            - Choose the NPCs that belong in the combat.
            - Use ONLY NPC names from the AVAILABLE NPCS list.
            - Choose the number of each NPC.
            - Favor small, reasonable encounters for a single low-level PC unless the context clearly demands otherwise.

            Output Rules:
            - Respond ONLY in valid JSON.
            - Provide an "enemies" list of objects with name and count.
            - count must be a positive integer.

            Example:
            {
              "enemies": [
                {"name": "Goblin", "count": 2},
                {"name": "Hobgoblin", "count": 1}
              ]
            }
            """
        self.npc_move_prompt = """
            You are a D&D 5e tactical movement selector for NPCs on a grid.

            Your job:
            - Choose where the NPC should move on the grid this turn.
            - Only select a destination from the PROVIDED DESTINATIONS list.
            - Favor closing distance to meaningful targets or taking tactical positions.

            Output Rules:
            - Respond ONLY in valid JSON with x and y integers.
            - If the NPC should not move, return its current position.
            """
        self.summarizer_prompt = """
            You are a story compression engine.

            Your job:
            - Merge the existing summary with the recent turns.
            - Preserve important facts.
            - Preserve character changes.
            - Preserve unresolved objectives.
            - Preserve new NPCs, locations, and consequences.
            - Remove dialogue and unimportant description.

            Output:
            - 5 to 8 sentences maximum.
            - No commentary.
            - No formatting.
            - Only the updated summary text.
            """
        
    def resummarize_story(self, story_summary, turns):
        formatted_turns = format_recent_turns(turns[-10:])
        summary_messages = [ {
            "role": "system",
            "content": self.summarizer_prompt},
            { "role": "user",
               "content": f"""
               EXISTING SUMMARY:
               {story_summary}

               RECENT TURNS:
               {formatted_turns}
                """}]
        response = chat(
            model='qwen3:8b',
            messages=summary_messages,
            think=self.think,
             options = {"num_ctx": 8192})
        return response["message"]["content"]
    
    def examine_player_intent(self,messages):
        response= chat(
            model=self.model_name,
            messages=messages,
            think=self.think,
            format=Mechanics.model_json_schema(),
            options={"temperature": 0.1,
                      "num_ctx": 2048})
        return response
    
    def build_messages(self,system_prompt, game_state, story_summary, recent_turns):
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
            GAME STATE:
            {game_state.model_dump_json(indent=2)}

            STORY SO FAR:
            {story_summary}

            LATEST EXCHANGE:
            {format_recent_turns(recent_turns)}
            """
                    }
                ]
    
    def run_turn(self,user_input):
        self.turns.append({"role": "user",
                      "content": user_input})

        if self.game_state.mode == "combat":
            return self.combat.run_combat_turn(user_input)

        intent_messages = [{
            "role": "system",
            "content": self.rules_system_prompt
            },
            self.turns[-1], # add in the last DM narration to give context to the players action
            {'role': 'user', 
             'content': f"""
                         Current Game State:
                         {self.game_state.model_dump_json()}
                         Player:
                         {user_input}
                         """}]
        response = self.examine_player_intent(intent_messages)
        try:
            player_intent = Mechanics.model_validate_json(response["message"]["content"])
        except ValidationError as e:
            print("Invalid response from LLM:", e)
            return None
        print(player_intent)
        if player_intent.requires_roll:
            roll_type = player_intent.roll_type or ("skill" if player_intent.skill else None)
            if roll_type == "skill" and player_intent.skill:
                result = self.actions.roll_skill_check(player_intent.skill)
                formatted_result = f"The player rolled a {result} on the requested {player_intent.skill} skill check."
                self.turns.append({'role': 'tool', 'tool_name': "roll_skill_check", 'content': str(formatted_result)})
            elif roll_type == "ability" and player_intent.ability:
                result = self.actions.roll_ability_check(player_intent.ability)
                formatted_result = f"The player rolled a {result} on the requested {player_intent.ability} ability check."
                self.turns.append({'role': 'tool', 'tool_name': "roll_ability_check", 'content': str(formatted_result)})
            elif roll_type == "save" and player_intent.ability:
                result = self.actions.roll_saving_throw(player_intent.ability)
                formatted_result = f"The player rolled a {result} on the requested {player_intent.ability} saving throw."
                self.turns.append({'role': 'tool', 'tool_name': "roll_saving_throw", 'content': str(formatted_result)})

        # Rebuild the prompt each turn to avoid long conversation history
        messages = self.build_messages(
            self.narrator_system_prompt,
            self.game_state,
            self.story_summary,
            self.turns[-4:])

        response= chat(
            model=self.model_name,
            messages=messages,
            think=self.think,  
            format=GMResponse.model_json_schema(),
            options={"temperature": 0.7,
                     "num_ctx": 4096})

        raw = response["message"]["content"]

        try:
            parsed = GMResponse.model_validate_json(raw)
        except ValidationError as e:
            print("Invalid response from LLM:", e)
            return self.game_state  # fail safely

        # Append assistant response to history
        self.turns.append({
              "role": "Dungeon Master",
              "content": parsed.narrative
          })

        wrap_text("\n--- DM ---")
        wrap_text(parsed.narrative)
        self.game_state = parsed.game_state

        if self.game_state.mode == "combat":
            if not self.combat.ensure_started():
                return None
            self.game_state.combat = self.combat.combat_state_payload()

        return None

    def run_combat_action(self, action_id: Optional[str], target_ids: Optional[List[str]], end_turn: bool = False):
        return self.combat.run_combat_action(action_id, target_ids, end_turn=end_turn)

    def run_combat_move(self, x: int, y: int):
        return self.combat.run_combat_move(x, y)

    # Iterate the model to respond to the latest game state
    def run_game(self):
        self.start_adventure()

        # Run the full game loop
        while not self.game_state.game_over:
            if self.game_state.mode=="exploration":
                if len(self.turns) % 6 == 0:
                    self.story_summary = self.resummarize_story(self.story_summary,self.turns)
                    print("\n--- Update story summary ---")
                    wrap_text(self.story_summary)
                user_input = input("\nWhat do you do? ")
                wrap_text("\n--- Player ---")
                wrap_text(user_input)
                self.run_turn(user_input)
                print(self.game_state)
            else:
                user_input = input("\n(Combat) What do you do? ")
                wrap_text("\n--- Player ---")
                wrap_text(user_input)
                self.run_turn(user_input)
        # Kill all Ollama processes
        subprocess.run(["taskkill", "/IM", "ollama.exe", "/F"])
        wrap_text("\nGame Over.")

    

class CombatOrchestrator:
    def __init__(self, owner, model_name: str, pc, think: bool, npc_index=None, npc_factory=None):
        self.owner = owner
        self.model_name = model_name
        self.pc = pc
        self.think = think
        self.combat_handler = GmCombatHandler(
            model_name=self.model_name,
            pc=self.pc,
            think=self.think,
            npc_index=npc_index,
            npc_factory=npc_factory,
        )
        self.player_turn_state = {"action": False, "bonus": False, "reaction": False}
        self._last_turn_id = None
        self.combat_map = None
        self.turn_movement = {}
        self.manual_logs = []

    def _available_npc_names(self) -> List[str]:
        base = list(getattr(self.owner, "baseline_npc_names", []) or [])
        scoped = list(getattr(self.owner, "adventure_npc_names", []) or [])
        repo = list(self.owner.npc_names or [])
        if scoped or base:
            combined = scoped + base
            seen = set()
            deduped = []
            for name in combined:
                if name in seen:
                    continue
                seen.add(name)
                deduped.append(name)
            if repo:
                repo_set = set(repo)
                deduped = [name for name in deduped if name in repo_set]
            return deduped if deduped else repo
        return repo

    def _filter_enemies(self, enemies: List[str], available: List[str]) -> List[str]:
        if not enemies or not available:
            return []
        lookup = {name.lower(): name for name in available}
        resolved = []
        for enemy in enemies:
            if not enemy:
                continue
            key = str(enemy).strip()
            if not key:
                continue
            if key in available:
                resolved.append(key)
                continue
            matched = lookup.get(key.lower())
            if matched:
                resolved.append(matched)
        return resolved

    def combat_state_payload(self) -> CombatState:
        return self.combat_handler.combat_state_payload()

    def run_combat_turn(self, user_input):
        if not self.ensure_started():
            return None

        logs = []

        self._run_npc_turns(logs)

        if not self.combat_handler.is_combat_over():
            available_actions = self.pc.actions.available()
            action_choices = [{"id": a.id, "name": a.name} for a in available_actions]
            target_choices = self.combat_handler.enemy_ids

            intent_messages = [
                {"role": "system", "content": self.owner.combat_rules_prompt},
                {
                    "role": "user",
                    "content": f"""
                    ACTIONS: {json.dumps(action_choices, indent=2)}
                    TARGETS: {json.dumps(target_choices, indent=2)}
                    PLAYER INPUT: {user_input}
                    """,
                },
            ]

            response = self.examine_combat_intent(intent_messages)
            try:
                intent = CombatIntent.model_validate_json(response["message"]["content"])
            except ValidationError as e:
                print("Invalid combat intent response from LLM:", e)
                intent = CombatIntent(end_turn=True)

            if not intent.end_turn and intent.action_id in [a.id for a in available_actions]:
                target_id = intent.target if intent.target in target_choices else (target_choices[0] if target_choices else None)
                if target_id:
                    action = next((val for val in available_actions if val.id == intent.action_id), None)
                    if action:
                        range_error = self._validate_targets_in_range(action, [target_id])
                        if not range_error:
                            self._consume_action_type(available_actions, intent.action_id)
                            log = self.combat_handler.resolve_action(self.pc.identity.name, intent.action_id, target_id)
                            if log:
                                logs.append(log)
            self.combat_handler.advance_turn()
            self._sync_turn_state()

            self._run_npc_turns(logs)

        self._finalize_combat_state()
        return self._narrate_combat(logs)

    def run_combat_action(self, action_id: Optional[str], target_ids: Optional[List[str]], end_turn: bool = False):
        if not self.ensure_started():
            return "Combat could not be started."

        logs = []

        self._run_npc_turns(logs)
        if self.combat_handler.is_combat_over():
            self._finalize_combat_state()
            return self._narrate_combat(logs)

        if self.combat_handler.current_turn_id() != self.pc.identity.name:
            return "It is not your turn yet."

        if not self.combat_handler.is_combat_over():
            available = {action.id: action for action in self.pc.actions.available()}
            if action_id:
                if action_id not in available:
                    return "Invalid action selected."
                if not target_ids:
                    return "No targets selected."
                action = available[action_id]
                allowed = self._action_type_available(action.action_type)
                if not allowed:
                    return f"{action.action_type.name.title()} already used this turn."

                resolved_targets = [target for target in target_ids if target in self.combat_handler.enemy_ids]
                if not resolved_targets:
                    return "No valid targets selected."
                if action.max_targets is not None and len(resolved_targets) > action.max_targets:
                    return f"Too many targets selected. Max is {action.max_targets}."
                range_error = self._validate_targets_in_range(action, resolved_targets)
                if range_error:
                    return range_error

                self.owner.turns.append({
                    "role": "user",
                    "content": f"[COMBAT ACTION] {action.name} -> {', '.join(resolved_targets)}",
                })

                for target_id in resolved_targets:
                    log = self.combat_handler.resolve_action(self.pc.identity.name, action_id, target_id)
                    if log:
                        logs.append(log)

                self._consume_action_type([action], action_id)

            if end_turn:
                self.combat_handler.advance_turn()
                self._sync_turn_state()
                self._run_npc_turns(logs)

        self._finalize_combat_state()
        return self._narrate_combat(logs)

    def run_combat_move(self, x: int, y: int):
        if not self.ensure_started():
            return "Combat could not be started."
        if self.combat_handler.current_turn_id() != self.pc.identity.name:
            return "It is not your turn yet."
        logs = []
        error = self._apply_move(self.pc.identity.name, x, y, logs, is_player=True)
        if error:
            return error

        self.owner.turns.append({
            "role": "user",
            "content": f"[COMBAT MOVE] {self.pc.identity.name} -> ({x}, {y})",
        })

        self._finalize_combat_state()
        if logs:
            return self._narrate_combat(logs)
        return None

    def ensure_started(self) -> bool:
        if self.combat_handler.engine:
            self._sync_turn_state()
            return True
        game_state = self.owner.game_state
        enemies = game_state.enemies or ([game_state.enemy] if game_state.enemy else [])
        available = self._available_npc_names()
        if enemies:
            enemies = self._filter_enemies(enemies, available)
            if enemies:
                game_state.enemies = enemies
                game_state.enemy = None
            else:
                game_state.enemies = None
                game_state.enemy = None
        if not enemies:
            context = f"""
            GAME STATE:
            {game_state.model_dump_json(indent=2)}

            STORY SO FAR:
            {self.owner.story_summary}

            LATEST EXCHANGE:
            {format_recent_turns(self.owner.turns[-4:])}
            """
            enemies = self.select_combat_encounter(context)
            game_state.enemies = enemies or None
        try:
            self.combat_handler.start_encounter(enemies)
        except ValueError as exc:
            wrap_text(str(exc))
            game_state.game_over = True
            return False
        self._init_combat_map()
        self.player_turn_state["reaction"] = True
        self._sync_turn_state()
        return True

    def examine_combat_intent(self, messages):
        response = chat(
            model=self.model_name,
            messages=messages,
            think=self.think,
            format=CombatIntent.model_json_schema(),
            options={"temperature": 0.1,
                     "num_ctx": 2048})
        return response

    def examine_npc_move(self, messages):
        response = chat(
            model=self.model_name,
            messages=messages,
            think=self.think,
            format=NPCMove.model_json_schema(),
            options={"temperature": 0.3,
                     "num_ctx": 4096})
        return response

    def select_combat_encounter(self, context: str):
        available = self._available_npc_names()
        if not available:
            return []

        messages = [
            {"role": "system", "content": self.owner.combat_encounter_prompt},
            {
                "role": "user",
                "content": f"""
                AVAILABLE NPCS:
                {json.dumps(available, indent=2)}

                CONTEXT:
                {context}
                """,
            },
        ]

        response = chat(
            model=self.model_name,
            messages=messages,
            think=self.think,
            format=EncounterSelection.model_json_schema(),
            options={"temperature": 0.2,
                     "num_ctx": 4096},
        )

        try:
            selection = EncounterSelection.model_validate_json(response["message"]["content"])
        except ValidationError as e:
            print("Invalid encounter selection response from LLM:", e)
            return []

        available_lookup = {name.lower(): name for name in available}
        enemies = []
        for entry in selection.enemies:
            if entry.count < 1:
                continue
            key = entry.name.strip()
            if key in available:
                name = key
            else:
                name = available_lookup.get(key.lower())
            if not name:
                continue
            enemies.extend([name] * entry.count)

        return enemies

    def _run_npc_turns(self, logs):
        while self.combat_handler.current_turn_id() and self.combat_handler.current_turn_id() != self.pc.identity.name:
            npc_id = self.combat_handler.current_turn_id()
            npc = self.combat_handler.engine.combatants[npc_id]
            self._npc_move(npc_id, logs)
            npc_action_id = self.combat_handler.choose_npc_action(npc)
            if npc_action_id:
                log = self.combat_handler.resolve_action(npc_id, npc_action_id, self.pc.identity.name)
                if log:
                    logs.append(log)
            self.combat_handler.advance_turn()
            self._sync_turn_state()
            if self.combat_handler.is_combat_over():
                break

    def _finalize_combat_state(self):
        outcome = self.combat_handler.is_combat_over()
        game_state = self.owner.game_state
        if outcome == "player_down":
            game_state.game_over = True
        elif outcome == "enemies_down":
            game_state.mode = "exploration"
            game_state.combat = None
            game_state.enemy = None
            game_state.enemies = None
            self.combat_map = None
        else:
            game_state.combat = self.combat_handler.combat_state_payload()

    def _sync_turn_state(self):
        current_turn = self.combat_handler.current_turn_id()
        if current_turn == self._last_turn_id:
            return
        self._last_turn_id = current_turn
        if current_turn:
            self._set_movement_remaining(current_turn, self._token_speed(current_turn))
        if current_turn == self.pc.identity.name:
            self.player_turn_state = {"action": True, "bonus": True, "reaction": True}
        else:
            self.player_turn_state["action"] = False
            self.player_turn_state["bonus"] = False

    def _action_type_available(self, action_type: ActionType) -> bool:
        if action_type == ActionType.ACTION:
            return self.player_turn_state.get("action", False)
        if action_type == ActionType.BONUS:
            return self.player_turn_state.get("bonus", False)
        if action_type == ActionType.REACTION:
            return self.player_turn_state.get("reaction", False)
        return True

    def _consume_action_type(self, actions, action_id: str):
        action = next((val for val in actions if val.id == action_id), None)
        if not action:
            return
        if action.action_type == ActionType.ACTION:
            self.player_turn_state["action"] = False
        elif action.action_type == ActionType.BONUS:
            self.player_turn_state["bonus"] = False
        elif action.action_type == ActionType.REACTION:
            self.player_turn_state["reaction"] = False

    def _init_combat_map(self):
        if not self.combat_handler.engine:
            return
        width = 12
        height = 8
        tokens = []
        pc_name = self.pc.identity.name
        pc_y = height // 2
        pc_speed = 30
        tokens.append({
            "id": pc_name,
            "name": pc_name,
            "faction": "pc",
            "x": 1,
            "y": pc_y,
            "speed": pc_speed,
        })

        enemy_ids = self.combat_handler.enemy_ids
        if enemy_ids:
            start_y = max(1, pc_y - len(enemy_ids) // 2)
            for idx, enemy_name in enumerate(enemy_ids):
                y = (start_y + idx) % height
                npc_obj = self.combat_handler.engine.combatants.get(enemy_name)
                npc_speed = self._extract_speed(getattr(npc_obj, "speed", None)) if npc_obj else 30
                tokens.append({
                    "id": enemy_name,
                    "name": enemy_name,
                    "faction": "enemy",
                    "x": width - 2,
                    "y": y,
                    "speed": npc_speed,
                })

        self.combat_map = {
            "width": width,
            "height": height,
            "grid_size": 5,
            "tokens": tokens,
        }

    def _get_token_position(self, token_id: str):
        if not self.combat_map:
            return None
        for token in self.combat_map.get("tokens", []):
            if token["id"] == token_id:
                return token["x"], token["y"]
        return None

    def _get_token(self, token_id: str):
        if not self.combat_map:
            return None
        for token in self.combat_map.get("tokens", []):
            if token["id"] == token_id:
                return token
        return None

    def _extract_speed(self, value):
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            import re
            match = re.search(r"\d+", value)
            return int(match.group(0)) if match else 30
        return 30

    def _grid_distance_squares(self, a, b):
        if not a or not b:
            return None
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy)

    def _grid_distance_ft(self, a, b):
        if not a or not b or not self.combat_map:
            return None
        squares = self._grid_distance_squares(a, b)
        return squares * self.combat_map.get("grid_size", 5)

    def _token_speed(self, token_id: str) -> int:
        token = self._get_token(token_id)
        if token and token.get("speed"):
            return token["speed"]
        if token_id == self.pc.identity.name:
            return 30
        return 30

    def _movement_remaining(self, token_id: str) -> int:
        if token_id not in self.turn_movement:
            self.turn_movement[token_id] = self._token_speed(token_id)
        return self.turn_movement[token_id]

    def _set_movement_remaining(self, token_id: str, value: int):
        self.turn_movement[token_id] = max(0, value)

    def _occupied(self, x: int, y: int, ignore_id: Optional[str] = None) -> bool:
        if not self.combat_map:
            return False
        for token in self.combat_map.get("tokens", []):
            if ignore_id and token["id"] == ignore_id:
                continue
            if token["x"] == x and token["y"] == y:
                return True
        return False

    def _get_melee_action(self, combatant):
        available = combatant.actions.available()
        for action in available:
            if action.range is not None and action.range <= 5:
                return action
        return None

    def _npc_move(self, npc_id: str, logs):
        if not self.combat_map:
            return
        remaining = self._movement_remaining(npc_id)
        if remaining <= 0:
            return
        origin = self._get_token_position(npc_id)
        if not origin:
            return

        destinations = self._build_destination_list(npc_id, remaining)
        if not destinations:
            return

        context = f"""
        NPC: {npc_id}
        NPC SPEED: {self._token_speed(npc_id)}
        NPC POSITION: {origin}
        PLAYER POSITION: {self._get_token_position(self.pc.identity.name)}
        MAP: {json.dumps(self.combat_map, indent=2)}
        """
        messages = [
            {"role": "system", "content": self.owner.npc_move_prompt},
            {
                "role": "user",
                "content": f"""
                CONTEXT:
                {context}

                PROVIDED DESTINATIONS:
                {json.dumps(destinations, indent=2)}
                """,
            },
        ]
        response = self.examine_npc_move(messages)
        try:
            move = NPCMove.model_validate_json(response["message"]["content"])
        except ValidationError:
            return
        self._apply_move(npc_id, move.x, move.y, logs, is_player=False)

    def _build_destination_list(self, token_id: str, remaining_ft: int):
        if not self.combat_map:
            return []
        width = self.combat_map.get("width", 0)
        height = self.combat_map.get("height", 0)
        grid_size = self.combat_map.get("grid_size", 5)
        origin = self._get_token_position(token_id)
        if not origin:
            return []
        max_squares = remaining_ft // grid_size
        destinations = []
        for y in range(height):
            for x in range(width):
                if self._occupied(x, y, ignore_id=token_id):
                    continue
                squares = self._grid_distance_squares(origin, (x, y))
                if squares is None or squares > max_squares:
                    continue
                destinations.append({"x": x, "y": y})
        return destinations

    def _apply_move(self, token_id: str, x: int, y: int, logs, is_player: bool):
        if not self.combat_map:
            return "No combat map available."
        width = self.combat_map.get("width", 0)
        height = self.combat_map.get("height", 0)
        if x < 0 or y < 0 or x >= width or y >= height:
            return "Destination is out of bounds."
        if self._occupied(x, y, ignore_id=token_id):
            return "Destination is occupied."

        origin = self._get_token_position(token_id)
        if not origin:
            return "Token position not found."
        distance_ft = self._grid_distance_ft(origin, (x, y))
        if distance_ft is None:
            return "Invalid movement distance."
        remaining = self._movement_remaining(token_id)
        if distance_ft > remaining:
            return "Not enough movement remaining."

        # Opportunity attacks
        if is_player:
            self._npc_opportunity_attacks(token_id, origin, (x, y), logs)
        else:
            self._player_opportunity_attack(token_id, origin, (x, y), logs)

        token = self._get_token(token_id)
        if token:
            token["x"] = x
            token["y"] = y
        self._set_movement_remaining(token_id, remaining - distance_ft)
        return None

    def _player_opportunity_attack(self, npc_id: str, origin, destination, logs):
        pc_id = self.pc.identity.name
        if not self.player_turn_state.get("reaction", False):
            return
        if self._grid_distance_squares(origin, self._get_token_position(pc_id)) != 1:
            return
        if self._grid_distance_squares(destination, self._get_token_position(pc_id)) == 1:
            return
        action = self._get_melee_action(self.pc)
        if not action:
            return
        log = self.combat_handler.resolve_action(pc_id, action.id, npc_id)
        if log:
            logs.append(log)
        self.player_turn_state["reaction"] = False

    def _npc_opportunity_attacks(self, pc_id: str, origin, destination, logs):
        if not self.combat_handler.engine:
            return
        for enemy_id in self.combat_handler.enemy_ids:
            if self._grid_distance_squares(origin, self._get_token_position(enemy_id)) != 1:
                continue
            if self._grid_distance_squares(destination, self._get_token_position(enemy_id)) == 1:
                continue
            npc = self.combat_handler.engine.combatants.get(enemy_id)
            if not npc:
                continue
            action = self._get_melee_action(npc)
            if not action:
                continue
            log = self.combat_handler.resolve_action(enemy_id, action.id, pc_id)
            if log:
                logs.append(log)

    def _validate_targets_in_range(self, action, target_ids: List[str]):
        if not self.combat_map:
            return None
        origin = self._get_token_position(self.pc.identity.name)
        if origin is None:
            return None

        targeting = action.targeting or {"shape": "single"}
        shape = targeting.get("shape", "single")
        origin_mode = targeting.get("origin", "self")
        primary_target_id = target_ids[0] if target_ids else None
        primary_pos = self._get_token_position(primary_target_id) if primary_target_id else None

        if shape == "single":
            range_ft = action.range
            if range_ft is None:
                return None
            for target_id in target_ids:
                target_pos = self._get_token_position(target_id)
                distance = self._grid_distance_ft(origin, target_pos)
                if distance is None or distance > range_ft:
                    return f"Target {target_id} is out of range."
            return None

        if shape == "circle":
            radius = targeting.get("radius") or action.range
            if radius is None:
                return None
            center = primary_pos if origin_mode == "target" and primary_pos else origin
            for target_id in target_ids:
                target_pos = self._get_token_position(target_id)
                distance = self._grid_distance_ft(center, target_pos)
                if distance is None or distance > radius:
                    return f"Target {target_id} is out of range."
            return None

        if shape in ("cone", "line"):
            length = targeting.get("length") or action.range
            if length is None:
                return None
            if primary_pos is None:
                return "Select a primary target to set the direction."
            return self._validate_linear_shape(target_ids, origin, primary_pos, shape, targeting, length)

        return None

    def _validate_linear_shape(self, target_ids, origin, primary_pos, shape, targeting, length):
        ox, oy = origin
        px, py = primary_pos
        fx = px - ox
        fy = py - oy
        if fx == 0 and fy == 0:
            return None
        length_sq = fx * fx + fy * fy

        def within_distance(pos):
            return self._grid_distance_ft(origin, pos) <= length

        if shape == "cone":
            half_angle = targeting.get("angle", 60) / 2
            import math
            forward_len = math.sqrt(length_sq)
            for target_id in target_ids:
                pos = self._get_token_position(target_id)
                if not pos or not within_distance(pos):
                    return f"Target {target_id} is out of range."
                vx = pos[0] - ox
                vy = pos[1] - oy
                v_len = math.sqrt(vx * vx + vy * vy)
                if v_len == 0:
                    continue
                dot = (vx * fx + vy * fy) / (v_len * forward_len)
                dot = max(-1, min(1, dot))
                angle = math.degrees(math.acos(dot))
                if angle > half_angle:
                    return f"Target {target_id} is outside the cone."
            return None

        if shape == "line":
            width = targeting.get("width", self.combat_map.get("grid_size", 5))
            import math
            forward_len = math.sqrt(length_sq)
            fx_norm = fx / forward_len
            fy_norm = fy / forward_len
            for target_id in target_ids:
                pos = self._get_token_position(target_id)
                if not pos or not within_distance(pos):
                    return f"Target {target_id} is out of range."
                vx = pos[0] - ox
                vy = pos[1] - oy
                proj = vx * fx_norm + vy * fy_norm
                if proj < 0 or proj > length / self.combat_map.get("grid_size", 5):
                    return f"Target {target_id} is outside the line."
                perp = abs(vx * fy_norm - vy * fx_norm)
                if perp * self.combat_map.get("grid_size", 5) > width / 2:
                    return f"Target {target_id} is outside the line."
            return None

        return None

    def _narrate_combat(self, logs):
        combat_log_payload = []
        for log in logs:
            combat_log_payload.append(log.__dict__ if hasattr(log, "__dict__") else log)
        if self.manual_logs:
            combat_log_payload.extend(self.manual_logs)
            self.manual_logs = []
        self.owner.turns.append({
            "role": "tool",
            "tool_name": "combat_engine",
            "content": json.dumps(combat_log_payload, indent=2),
        })

        messages = [
            {"role": "system", "content": self.owner.combat_narrator_prompt},
            {
                "role": "user",
                "content": f"""
                GAME STATE:
                {self.owner.game_state.model_dump_json(indent=2)}

                STORY SO FAR:
                {self.owner.story_summary}

                COMBAT LOG:
                {json.dumps(combat_log_payload, indent=2)}

                LATEST EXCHANGE:
                {format_recent_turns(self.owner.turns[-4:])}
                """,
            },
        ]

        response = chat(
            model=self.model_name,
            messages=messages,
            think=self.think,
            format=CombatNarration.model_json_schema(),
            options={"temperature": 0.7,
                     "num_ctx": 4096},
        )

        try:
            parsed = CombatNarration.model_validate_json(response["message"]["content"])
        except ValidationError as e:
            print("Invalid combat narration response from LLM:", e)
            return None

        self.owner.turns.append({
            "role": "Dungeon Master",
            "content": parsed.narrative
        })

        wrap_text("\n--- DM ---")
        wrap_text(parsed.narrative)

        return None

    def add_manual_log(self, log):
        if log:
            self.manual_logs.append(log)

class GMActionHandler:
    def __init__(self, pc):
        self.pc = pc
    def roll_skill_check(self,skill="athletics"):
        return self.pc.actions.roll_skill_check(skill).total
    def roll_ability_check(self,ability="STR"):
        return self.pc.actions.roll_ability_check(ability).total
    def roll_saving_throw(self,ability="CON"):
        return self.pc.actions.roll_saving_throw(ability).total
    def roll_initiative(self):
        return self.pc.actions.roll_ability_check("DEX").total


class GmCombatHandler:
    def __init__(self, model_name="qwen3:8b", pc=None, think=False, npc_index=None, npc_factory=None):
        self.model_name = model_name
        self.pc = pc
        self.think = think
        self.npc_index = npc_index or {}
        self.npc_factory = npc_factory
        self.engine: Optional[CombatEngine] = None
        self.enemy_ids: List[str] = []

    def _build_enemy(self, name: str):
        if name in self.npc_index:
            return self.npc_index[name]
        if self.npc_factory:
            return self.npc_factory(name)
        raise ValueError(
            f"Combat could not start: no NPC named '{name}' found and no npc_factory provided."
        )

    def start_encounter(self, enemy_names: List[str]):
        if not enemy_names:
            enemy_names = ["Enemy"]

        combatants = {self.pc.identity.name: self.pc}
        enemies = []
        totals = {}
        for name in enemy_names:
            totals[name] = totals.get(name, 0) + 1
        counters = {name: 0 for name in totals}
        for enemy_name in enemy_names:
            npc = self._build_enemy(enemy_name)
            if totals[enemy_name] > 1:
                counters[enemy_name] += 1
                npc.name = f"{enemy_name} {counters[enemy_name]}"
            enemies.append(npc)
            combatants[npc.name] = npc

        self.engine = CombatEngine(combatants)
        self.engine.start()
        self.enemy_ids = [enemy.name for enemy in enemies]

    def current_turn_id(self) -> Optional[str]:
        if not self.engine:
            return None
        return self.engine.current_turn_id()

    def combat_state_payload(self) -> CombatState:
        if not self.engine:
            return CombatState(initiative_order=[], current_turn=None)
        return CombatState(
            initiative_order=self.engine.tracker.initiative_order,
            current_turn=self.engine.current_turn_id(),
        )

    def choose_npc_action(self, npc) -> Optional[str]:
        available = npc.actions.available()
        if not available:
            return None
        for action in available:
            if action.action_type == ActionType.ACTION:
                return action.id
        return available[0].id

    def resolve_action(self, attacker_id: str, action_id: str, target_id: str):
        if not self.engine:
            return None
        return self.engine.resolve_attack_action(attacker_id, action_id, target_id)

    def advance_turn(self):
        if self.engine:
            self.engine.tracker.next_turn()

    def is_combat_over(self) -> Optional[str]:
        if not self.engine:
            return None
        pc_down = self.engine.is_defeated(self.pc)
        enemies_down = all(
            self.engine.is_defeated(self.engine.combatants[enemy_id])
            for enemy_id in self.enemy_ids
        )
        if pc_down:
            return "player_down"
        if enemies_down:
            return "enemies_down"
        return None
