# auto_dnd

auto_dnd is a work-in-progress tabletop D&D 5e sandbox with an AI Dungeon Master. The long-term goal is a full web app that can run a complete session: character creation, exploration, and combat, with the DM calling tools for rules and outcomes.

**What this repo contains**
- `src/` - Core game rules, data models, and the AI DM logic.
- `ui/` - FastAPI web server plus HTML/CSS/JS front-end for the interactive session.
- `data/` - Source data files (classes, items, NPCs, spells, races, backgrounds, monsters).
- `*.ipynb` - Experiment notebooks used during early prototyping.

**Data sources**
- The game uses a unified SRD dataset in `data/srd/`, built from the 5e-bits SRD JSON (2014 + 2024).
- If both versions contain the same entry, the 2024 data wins and missing fields fall back to 2014.
- Legacy data has been moved to `data/legacy/`.

**Architecture**
- See `docs/ARCHITECTURE.md` for how the `game_engine` and AI DM interact, and where combat/exploration logic lives.

**To run the UI**
```bash
python -m uvicorn ui.server:app --reload
```
