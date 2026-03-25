# Architecture: Game Engine + AI DM

This repo has two big moving parts that work together:

1. `game_engine.py` provides the deterministic rules and combat resolution.
2. `gm.py` provides the AI Dungeon Master that calls the rules engine and narrates the outcome.

Below is a concrete map of how those pieces interact.

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
  - `AttackResult`, `DamageResult`, and `CombatActionLog` are the structured outputs the DM uses to narrate.

- `src/actions.py`
  - `Action` and `ActionManager` define and execute actions (attacks, skill checks, saves).
  - Actions are used by both PCs and NPCs. Combat resolution ultimately flows through `ActionManager` into `CombatEngine`.

**Where the AI DM lives**
- `src/gm.py`
  - `gm_llm` is the AI DM entry point. It owns the turn history, story summary, and `GameState`.
  - The DM uses multiple prompts to split responsibilities:
    - Rules extraction: determines if a roll is needed and which stat/skill to use.
    - Combat parsing: maps player intent to a specific action and target.
    - Combat narration: turns structured combat logs into flavorful text.
    - Encounter selection and NPC movement: selects NPCs and tactical moves.
  - All of those prompts are constrained with Pydantic schemas, so the model returns structured JSON.

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

**Game state and data sources**
- `GameState` (Pydantic in `gm.py`) tracks mode (`exploration` vs `combat`), enemies, initiative, and game_over.
- `src/character.py` constructs PCs and their stats, proficiencies, and actions.
- `src/npcs.py` provides NPC definitions used in encounters.
- `data/` stores the raw rules content (classes, items, NPCs, spells, races, backgrounds, monsters).

**UI integration**
- `ui/server.py` exposes endpoints used by the front end:
  - `/api/start` builds a PC and starts a session.
  - `/api/message` sends player input to the DM.
  - `/api/combat_action` and `/api/combat_move` manage combat turns and movement.
- The UI always displays the DM’s latest narrative, the current `GameState`, and the player’s updated sheet.

If you want a deeper dive into a specific subsystem (character creation, spells, NPC data, or map rules), tell me which one and I can document it next.
