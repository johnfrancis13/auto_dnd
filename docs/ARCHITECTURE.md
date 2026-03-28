# Architecture: Game Engine + AI DM

This repo has two big moving parts that work together:

1. `game_engine.py` provides the deterministic rules and combat resolution.
2. `gm.py` provides the AI Dungeon Master that calls the rules engine and narrates the outcome.

Below is a concrete map of how those pieces interact, plus the action pipeline and UI roll flow.

**High-level flow**
1. The UI (FastAPI) creates a `GameSession` (`ui/server.py`).
2. A player character (PC) is built via `PCFactory` (`src/character.py`).
3. The AI DM (`gm_llm` in `src/gm.py`) starts the adventure and owns the game loop.
4. Each player message is routed through the AI DM:
   - Exploration: the DM decides whether a roll is required, triggers the roll, and narrates.
   - Combat: the DM routes actions to the combat engine, then narrates the results.

**Where the rules live**
- `src/game_engine.py`
  - `Dice` and `DiceHandler` handle dice rolls and modifiers.
  - `CombatTracker` manages initiative, rounds, and turn order.
  - `CombatEngine` resolves attacks and applies damage to combatants.
  - `resolve_save_action()` and `resolve_spell_action()` handle save-based and spell actions.
  - `AttackResult`, `DamageResult`, and `CombatActionLog` are the structured outputs the DM uses to narrate.

- `src/actions.py`
  - `Action` and `ActionManager` define and execute actions (attacks, skill checks, saves).
  - `SpellAction` extends `Action` for spell metadata (level, school).
  - Actions are data-first (attack/save/damage specs) to enable JSON parsing.

**Where the AI DM lives**
- `src/gm.py`
  - `gm_llm` is the AI DM entry point. It owns the turn history, story summary, and `GameState`.
  - The DM uses multiple prompts to split responsibilities:
    - Rules extraction: determines if a roll is needed and which stat/skill to use.
    - Combat parsing: maps player intent to a specific action and target.
    - Combat narration: turns structured combat logs into flavorful text.
    - Encounter selection and NPC movement: selects NPCs and tactical moves.
  - All of those prompts are constrained with Pydantic schemas, so the model returns structured JSON.
  - Manual rolls are appended to `turns` as `tool` messages (`tool_name: action_roll`).
  - `CombatOrchestrator` stores manual combat logs (`manual_logs`) which are merged into combat narration.

**Exploration loop (non-combat)**
1. `gm_llm.run_turn()` is called with the player’s input.
2. The “rules engine” prompt produces a `Mechanics` JSON payload with:
   - whether a roll is required
   - what kind of roll (skill/ability/save)
3. If a roll is required, the DM calls `ActionManager.roll_*` on the PC.
4. The DM then calls the narrator prompt, passing:
   - current `GameState`
   - a rolling `story_summary`
   - recent turns (player + DM + tool results)
5. The narrator returns a `GMResponse` with an updated `GameState` and narrative text.
6. Optional: UI can call `/api/action/roll` with `narrate=true` to roll and immediately narrate.

**Combat loop**
1. Combat is orchestrated by `CombatOrchestrator` (in `gm.py`), which owns:
   - action economy state (action/bonus/reaction)
   - a simple grid map and movement rules
2. `GmCombatHandler` wraps the `CombatEngine` and:
   - builds NPC combatants
   - starts the encounter and initiative
   - resolves actions against targets
3. Player actions flow like this:
   - UI sends the action ID and target(s)
   - `CombatOrchestrator` validates range/shape
   - `CombatEngine.resolve_attack_action()` applies dice + damage
   - a `CombatActionLog` is produced
4. NPC turns are chosen by the DM (action selection + optional movement).
5. The combat narrator prompt converts the structured combat log into the DM’s descriptive output.
6. Manual roll results (from the UI) are merged into the combat log payload before narration.

**Action data pipeline (weapons + spells)**
- `src/action_factory.py` turns SRD JSON into `Action` / `SpellAction`:
  - `weapon_action_from_item()` and `load_weapon_actions_from_srd()`
  - `spell_action_from_spell()` and `load_spell_actions_from_srd()`
- `Action.attack_roll` supports `ability_options` (e.g., finesse STR/DEX) and spellcasting.
- `Action.save` is data-driven for save spells: `{ability, dc, on_success}`.
- Scaling (cantrips / slot levels) is stored in `Action.scaling` and resolved by `CombatEngine`.

**Game state and data sources**
- `GameState` (Pydantic in `gm.py`) tracks mode (`exploration` vs `combat`), enemies, initiative, and `game_over`.
- `src/character.py` constructs PCs and their stats, proficiencies, inventory, and actions.
- `src/npcs.py` provides NPC definitions used in encounters.
- `data/` stores the raw rules content (classes, items, NPCs, spells, races, backgrounds, monsters).

**UI integration**
- `ui/server.py` exposes endpoints used by the front end:
  - `/api/start` builds a PC and starts a session.
  - `/api/message` sends player input to the DM.
  - `/api/combat_action` and `/api/combat_move` manage combat turns and movement.
  - `/api/inventory/equip` toggles equipped state (weapons/armor only).
  - `/api/spells/prepare` toggles prepared state (cantrips are always prepared).
  - `/api/action/roll` rolls action dice; with `narrate=true` it immediately calls the DM in exploration.
- The UI always displays the DM’s latest narrative, the current `GameState`, and the player’s updated sheet.

**UI action roll UX**
- Actions display roll breakdowns (attack / save / damage) plus a Roll button.
- Roll controls include advantage/disadvantage and multi-target selection in combat.
- Exploration rolls include a free-form target input and a “Roll + Narrate” button.
- Roll results are shown as quick badges next to actions and are pushed into GM context.

