one_shot_adventures = adventures = [

{
    "title": "The Lighthouse That Forgot the Sea",
    "duration_min": 45,
    "world": {
        "problem": "An inland lighthouse shines nightly despite no coastline.",
        "cause": "Reality distortion anchored to an old mariner's oath.",
        "pressure": "Travelers vanish into the light."
    },
    "actors": {
        "keeper_echo": {
            "motivation": "Fulfill sworn duty eternally.",
            "rules": [
                "Speaks as if ships still sail nearby.",
                "Resists accepting the sea is gone."
            ]
        },
        "townsfolk": {
            "motivation": "Stop disappearances.",
            "risk": "May destroy lighthouse impulsively."
        }
    },
    "scenes": [
        {"name": "Town Square", "tags": ["missing posters", "fear"]},
        {"name": "Hilltop Lighthouse", "tags": ["impossible horizon", "strange gravity"]},
        {"name": "Lantern Room", "tags": ["blinding light", "memory fragments"]}
    ],
    "complications": [
        "PC sees visions of distant ocean.",
        "Light intensifies unpredictably.",
        "Townsfolk approach with torches."
    ],
    "outcomes": [
        "Oath resolved peacefully.",
        "Light destroyed violently.",
        "Distortion spreads.",
        "Keeper freed."
    ],
    "npc_options": ["Ghost", "Specter", "Will-o'-Wisp"],
    "reward": {
        "gold": 75,
        "item": "Lantern Shard (1 use: reveal invisible for 1 min)",
        "reputation": "Trusted mediator."
    },
    "escalation": [
        "Light grows brighter nightly.",
        "More vanishings.",
        "Reality warps around hill."
    ]
},

{
    "title": "The Orchard That Ripens Overnight",
    "duration_min": 45,
    "world": {
        "problem": "Fruit appears overnight but causes vivid dreams.",
        "cause": "Fey crossing beneath orchard.",
        "pressure": "Villagers growing dependent."
    },
    "actors": {
        "fey_emissary": {
            "motivation": "Cultivate emotional energy.",
            "rules": [
                "Never lies directly.",
                "Offers bargains disguised as gifts."
            ]
        },
        "orchard_owner": {
            "motivation": "Protect livelihood.",
            "risk": "Already ate fruit repeatedly."
        }
    },
    "scenes": [
        {"name": "Dreaming Orchard", "tags": ["glowing fruit", "whispers"]},
        {"name": "Root Hollow", "tags": ["thin veil", "fey sigils"]},
        {"name": "Twilight Crossing", "tags": ["mutable terrain"]}
    ],
    "complications": [
        "PC experiences dream vision.",
        "Fruit rapidly overripens.",
        "Villagers defend orchard."
    ],
    "outcomes": [
        "Fey pact negotiated.",
        "Crossing sealed.",
        "Orchard transformed.",
        "Village addicted."
    ],
    "npc_options": ["Dryad", "Sprite", "Satyr", "Blink Dog"],
    "reward": {
        "gold": 75,
        "item": "Fey Apple Seed (plant once for safe shelter overnight)",
        "reputation": "Known to the fey."
    },
    "escalation": [
        "Dreams intensify.",
        "Sleepwalking incidents.",
        "Permanent crossing forms."
    ]
},

{
    "title": "The Silent Bell Tower",
    "duration_min": 40,
    "world": {
        "problem": "Town bell no longer rings; time feels distorted.",
        "cause": "Time spirit bound in mechanism.",
        "pressure": "Market chaos; missed rituals."
    },
    "actors": {
        "bound_spirit": {
            "motivation": "Escape endless cycle.",
            "rules": [
                "Speaks in past and future tense.",
                "Alters small time details."
            ]
        },
        "priest": {
            "motivation": "Maintain tradition."
        }
    },
    "scenes": [
        {"name": "Bell Tower Base", "tags": ["confused townsfolk"]},
        {"name": "Clockwork Interior", "tags": ["moving gears", "temporal echoes"]},
        {"name": "Bell Chamber", "tags": ["frozen dust", "time loops"]}
    ],
    "complications": [
        "Short time rewind.",
        "Aged object suddenly crumbles.",
        "Bell rings prematurely."
    ],
    "outcomes": [
        "Spirit freed.",
        "Spirit rebound differently.",
        "Tower dismantled.",
        "Time stabilized partially."
    ],
    "npc_options": ["Shadow", "Specter", "Wraith"],
    "reward": {
        "gold": 75,
        "item": "Moment Token (1 use: reroll a failed check)",
        "reputation": "Respected problem-solver."
    },
    "escalation": [
        "Time skips minutes.",
        "Objects age rapidly.",
        "Day repeats fragment."
    ]
},


{
    "title": "The Map That Draws Itself",
    "duration_min": 45,
    "world": {
        "problem": "A map updates with unexplored locations nightly.",
        "cause": "Sentient cartographic spirit.",
        "pressure": "Map predicting disasters."
    },
    "actors": {
        "map_spirit": {
            "motivation": "Be completed.",
            "rules": ["Adds locations when ignored."]
        }
    },
    "scenes": [
        {"name": "Study Room", "tags": ["animated ink"]},
        {"name": "Newly Drawn Alley", "tags": ["architecture mismatch"]},
        {"name": "Blank Space", "tags": ["reality thin"]}
    ],
    "complications": ["Ink spreads.", "Location shifts."],
    "outcomes": ["Map completed.", "Map burned.", "Map bonded to PC."],
    "npc_options": ["Animated Armor", "Flying Sword", "Rug of Smothering"],
    "reward": {
        "gold": 75,
        "item": "Self-Updating Map (marks nearest settlement once/day)",
        "reputation": "Local curiosity."
    },
    "escalation": ["More areas drawn.", "Warnings appear.", "Entire district redrawn."]
},

{
    "title": "The House That Rearranges",
    "duration_min": 45,
    "world": {
        "problem": "Interior rooms shift unpredictably.",
        "cause": "Lonely mimic-colony organism.",
        "pressure": "Residents trapped inside."
    },
    "actors": {
        "house_entity": {
            "motivation": "Keep occupants forever.",
            "rules": ["Rearranges when ignored."]
        }
    },
    "scenes": [
        {"name": "Entry Hall", "tags": ["familiar but wrong"]},
        {"name": "Moving Corridor", "tags": ["sliding walls"]},
        {"name": "Heart Room", "tags": ["organic beams"]}
    ],
    "complications": ["Room seals.", "Furniture moves."],
    "outcomes": ["Entity befriended.", "House escapes town.", "Entity dispersed."],
    "npc_options": ["Mimic", "Rug of Smothering", "Animated Armor"],
    "reward": {
        "gold": 75,
        "item": "Key of Familiar Doors (once: open known door within 60 ft)",
        "reputation": "Trusted rescuer."
    },
    "escalation": ["Rooms duplicate.", "Exits vanish.", "Structure expands."]
},

{
    "title": "The River That Flows Uphill",
    "duration_min": 45,
    "world": {
        "problem": "River reverses flow weekly.",
        "cause": "Elemental imbalance upstream.",
        "pressure": "Mill economy failing."
    },
    "actors": {
        "water_spirit": {
            "motivation": "Correct imbalance.",
            "rules": ["Responds to respectful offerings."]
        }
    },
    "scenes": [
        {"name": "Riverbank", "tags": ["floating debris upstream"]},
        {"name": "Abandoned Mill", "tags": ["waterwheel stalled"]},
        {"name": "Source Pool", "tags": ["elemental rift"]}
    ],
    "complications": ["Sudden surge.", "Villagers argue."],
    "outcomes": ["Balance restored.", "Permanent reversal.", "Spirit angered."],
    "npc_options": ["Water Elemental", "Steam Mephit", "Merfolk"],
    "reward": {
        "gold": 75,
        "item": "Vial of Reversed Water (1 use: reverse gravity on small object briefly)",
        "reputation": "River-friend."
    },
    "escalation": ["Flooding.", "Drought downstream.", "Rift widens."]
},

{
    "title": "The Whispering Statue Garden",
    "duration_min": 40,
    "world": {
        "problem": "Statues whisper secrets at night.",
        "cause": "Bound souls in marble.",
        "pressure": "Secrets spreading chaos."
    },
    "actors": {
        "stone_curator": {
            "motivation": "Preserve collection.",
            "rules": ["Denies wrongdoing."]
        }
    },
    "scenes": [
        {"name": "Garden Path", "tags": ["soft whispers"]},
        {"name": "Workshop", "tags": ["unfinished sculpture"]},
        {"name": "Hidden Vault", "tags": ["soul-binding tools"]}
    ],
    "complications": ["Statue cracks.", "Secret revealed."],
    "outcomes": ["Souls freed.", "Garden destroyed.", "Curator exposed."],
    "npc_options": ["Gargoyle", "Animated Armor", "Rug of Smothering"],
    "reward": {
        "gold": 75,
        "item": "Stone Whisper (1 use: ask a statue one question)",
        "reputation": "Seeker of truth."
    },
    "escalation": ["Whispers louder.", "Statues animate briefly.", "Public panic."]
},

{
    "title": "The Festival That Won’t End",
    "duration_min": 45,
    "world": {
        "problem": "Village stuck in looping festival day.",
        "cause": "Joy spirit feeding on repetition.",
        "pressure": "Villagers unaware of loop."
    },
    "actors": {
        "joy_spirit": {
            "motivation": "Sustain celebration.",
            "rules": ["Resets day if confronted violently."]
        }
    },
    "scenes": [
        {"name": "Festival Grounds", "tags": ["repeating events"]},
        {"name": "Quiet Alley", "tags": ["memories flicker"]},
        {"name": "Center Stage", "tags": ["time anchor"]}
    ],
    "complications": ["Memory bleed.", "Time stutter."],
    "outcomes": ["Loop ended.", "Loop refined.", "PC trapped temporarily."],
    "npc_options": ["Satyr", "Sprite", "Blink Dog"],
    "reward": {
        "gold": 75,
        "item": "Ribbon of Recall (1 use: remember prior failed interaction)",
        "reputation": "Festival friend."
    },
    "escalation": ["Glitches visible.", "Day shortens.", "Loop destabilizes."]
},

{
    "title": "The Library With No Exit",
    "duration_min": 45,
    "world": {
        "problem": "Visitors vanish in endless archive.",
        "cause": "Knowledge-hungry extradimensional space.",
        "pressure": "Scholars missing."
    },
    "actors": {
        "archive_entity": {
            "motivation": "Acquire stories.",
            "rules": ["Trades safe exit for secrets."]
        }
    },
    "scenes": [
        {"name": "Grand Stacks", "tags": ["infinite shelves"]},
        {"name": "Reading Alcove", "tags": ["books rewrite themselves"]},
        {"name": "Catalog Chamber", "tags": ["living index"]}
    ],
    "complications": ["Exit disappears.", "Book traps reader."],
    "outcomes": ["Entity bargained with.", "Library collapsed.", "PC marked as author."],
    "npc_options": ["Specter", "Ghost", "Mimic"],
    "reward": {
        "gold": 75,
        "item": "Bookmark of Return (1 use: retrace last hour path instantly)",
        "reputation": "Friend of scholars."
    },
    "escalation": ["Shelves shift.", "Language changes.", "Reality thins."]
},

{
    "title": "The Mirror That Reflects Tomorrow",
    "duration_min": 45,
    "world": {
        "problem": "Mirror shows future events inaccurately.",
        "cause": "Fragmented prophecy spirit.",
        "pressure": "Town acting on flawed visions."
    },
    "actors": {
        "mirror_spirit": {
            "motivation": "Be understood correctly.",
            "rules": ["Shows symbolic truths."]
        }
    },
    "scenes": [
        {"name": "Mayor's Hall", "tags": ["crowded anxiety"]},
        {"name": "Mirror Chamber", "tags": ["distorted reflections"]},
        {"name": "Vision Space", "tags": ["symbolic landscape"]}
    ],
    "complications": ["False vision spreads.", "Reflection acts independently."],
    "outcomes": ["Spirit clarified.", "Mirror shattered.", "Visions embraced."],
    "npc_options": ["Doppelganger", "Shadow", "Specter"],
    "reward": {
        "gold": 75,
        "item": "Shard of Foresight (1 use: glimpse likely outcome of action)",
        "reputation": "Voice of reason."
    },
    "escalation": ["Visions worsen.", "Public unrest.", "Prophecy manifests wrongly."]
},

{
    "title": "The Bridge That Demands Stories",
    "duration_min": 40,
    "world": {
        "problem": "Bridge refuses passage without tales.",
        "cause": "Ancient narrative guardian.",
        "pressure": "Trade halted."
    },
    "actors": {
        "bridge_entity": {
            "motivation": "Collect meaningful stories.",
            "rules": ["Rejects lies instantly."]
        }
    },
    "scenes": [
        {"name": "Bridge Span", "tags": ["echoing voice"]},
        {"name": "River Below", "tags": ["deep current"]},
        {"name": "Memory Echo", "tags": ["story made real briefly"]}
    ],
    "complications": ["Story manifests.", "Listener interrupts."],
    "outcomes": ["Guardian satisfied.", "Guardian tricked.", "Bridge collapses."],
    "npc_options": ["Ogre", "Troll", "Bandit"],
    "reward": {
        "gold": 75,
        "item": "Token of Telling (1 use: compel honest answer to a question)",
        "reputation": "Silver-tongued traveler."
    },
    "escalation": ["Demands deepen.", "Stories turn hostile.", "Bridge seals fully."]
},
{
    "title": "The Clockmaker’s Secret",
    "duration_min": 45,
    "world": {
        "problem": "A town’s clock tower chimes randomly, causing confusion.",
        "cause": "Clockmaker embedded a hidden mechanism to hide a secret.",
        "pressure": "Time-sensitive festival approaching."
    },
    "actors": {
        "clockmaker": {"motivation": "Hide past transgression.", "rules": ["Misleads politely.", "Guards workshop."]},
        "townsfolk": {"motivation": "Keep festival on time.", "risk": "Intervene impulsively."}
    },
    "scenes": [
        {"name": "Workshop", "tags": ["gears", "blueprints"]},
        {"name": "Clock Tower", "tags": ["hidden hatch", "spinning cogs"]},
        {"name": "Festival Square", "tags": ["confused crowd", "temporal glitches"]}
    ],
    "complications": ["Clock chimes out of sequence.", "Blueprint missing.", "Clockmaker evades."],
    "outcomes": ["Secret revealed.", "Clock repaired.", "Tower sealed."],
    "npc_options": ["Animated Armor", "Flying Sword", "Thug"],
    "reward": {"gold": 75, "item": "Pocket Cog (1 use: slow small moving mechanism briefly)", "reputation": "Respected problem-solver."},
    "escalation": ["Chimes desynchronize.", "Crowd panics.", "Festival disrupted."]
},

{
    "title": "The Lighthouse of Echoes",
    "duration_min": 50,
    "world": {
        "problem": "A coastal lighthouse transmits strange whispers.",
        "cause": "Residual psychic energy from shipwreck survivors.",
        "pressure": "Mariners report hallucinations; accidents rising."
    },
    "actors": {
        "ghosts": {"motivation": "Relive past events.", "rules": ["Interact subtly; no direct harm."]},
        "coastguard": {"motivation": "Protect sailors.", "risk": "Block access."}
    },
    "scenes": [
        {"name": "Beach", "tags": ["wreckage", "broken masts"]},
        {"name": "Lighthouse Base", "tags": ["strange sounds", "weathered stones"]},
        {"name": "Lantern Room", "tags": ["psychic resonance", "flickering light"]},
    ],
    "complications": ["Whispers mislead PC.", "Fog rolls in.", "Coastguard interrupts."],
    "outcomes": ["Spirits guided to peace.", "Energy dissipates.", "Whispers amplified."],
    "npc_options": ["Ghost", "Specter", "Will-o'-Wisp"],
    "reward": {"gold": 75, "item": "Shell of Calm (1 use: quiet mental interference for 1 minute)", "reputation": "Mariners trust you."},
    "escalation": ["Whispers intensify.", "Sailors endangered.", "Light malfunctions."]
},

{
    "title": "The Clockwork Menagerie",
    "duration_min": 45,
    "world": {
        "problem": "Mechanical animals in a noble’s garden have gone missing.",
        "cause": "Automaton caretaker malfunction.",
        "pressure": "Garden in disarray; social embarrassment imminent."
    },
    "actors": {
        "caretaker": {"motivation": "Repair systems.", "rules": ["Denies negligence.", "Redirects blame."]},
        "noble": {"motivation": "Maintain appearances.", "risk": "Fire PC for failure."}
    },
    "scenes": [
        {"name": "Garden Entrance", "tags": ["damaged automata", "broken hedges"]},
        {"name": "Workshop", "tags": ["spare parts", "schematics"]},
        {"name": "Fountain", "tags": ["water-activated gears", "lost automaton"]}
    ],
    "complications": ["Parts scattered.", "Automaton behaves oddly.", "Caretaker misleads."] ,
    "outcomes": ["Menagerie repaired.", "Automata escape.", "Noble satisfied or displeased."],
    "npc_options": ["Animated Armor", "Flying Sword", "Rug of Smothering"],
    "reward": {"gold": 75, "item": "Clockwork Key (1 use: temporarily control small automaton)", "reputation": "Respected tinker."},
    "escalation": ["Automata malfunction.", "Garden damages escalate.", "Noble pressures PC."]
},

{
    "title": "The Deserted Carnival",
    "duration_min": 45,
    "world": {
        "problem": "A carnival appears abandoned but lights and music persist.",
        "cause": "Residual magical glamour anchored to a forgotten pact.",
        "pressure": "Nearby town children lured in nightly."
    },
    "actors": {
        "carnival_spirit": {"motivation": "Maintain festivity.", "rules": ["Cannot lie; playful misdirection only."]},
        "town_guard": {"motivation": "Rescue children.", "risk": "Blocks paths aggressively."}
    },
    "scenes": [
        {"name": "Entrance Gate", "tags": ["glittering lights", "phantom music"]},
        {"name": "Carousel", "tags": ["moving animals", "illusion"]},
        {"name": "Big Tent", "tags": ["distorted size", "echoing laughter"]},
    ],
    "complications": ["Music hypnotizes.", "Tent shifts.", "Guard misfires."] ,
    "outcomes": ["Glamour removed.", "Children rescued.", "Spirit placated."],
    "npc_options": ["Owlbear", "Doppelganger", "Sprite"],
    "reward": {"gold": 75, "item": "Carnival Coin (1 use: charm one creature briefly)", "reputation": "Hero to children."},
    "escalation": ["Illusions intensify.", "Children lost.", "Town panic."]
},

{
    "title": "The Ship That Never Docked",
    "duration_min": 50,
    "world": {
        "problem": "A ghost ship circles the harbor nightly.",
        "cause": "Captain’s soul tethered to incomplete voyage.",
        "pressure": "Sailors refuse to work; trade stops."
    },
    "actors": {
        "ghost_captain": {"motivation": "Complete journey.", "rules": ["Only communicates cryptically."]},
        "harbormaster": {"motivation": "Resume trade.", "risk": "Refuses PC cooperation."}
    },
    "scenes": [
        {"name": "Dock", "tags": ["fog", "water reflections"]},
        {"name": "Captain’s Cabin", "tags": ["floating charts", "spectral logs"]},
        {"name": "Deck", "tags": ["windy deck", "phantom rigging"]},
    ],
    "complications": ["Ship drifts unpredictably.", "Crew reacts emotionally.", "Fog reduces visibility."],
    "outcomes": ["Captain freed.", "Ship dissipates.", "Tether remains partially."],
    "npc_options": ["Ghost", "Specter", "Wraith", "Skeleton"],
    "reward": {"gold": 75, "item": "Nautical Compass (1 use: detect ghostly presence)", "reputation": "Sailors trust you."},
    "escalation": ["Ship drifts into harbor.", "Mariners panic.", "Trade delayed further."]
},

{
    "title": "The Tower of Forgotten Letters",
    "duration_min": 45,
    "world": {
        "problem": "Old letters appear, detailing events that never happened.",
        "cause": "Poltergeist binds memory to parchment.",
        "pressure": "Nobles misled by false claims."
    },
    "actors": {
        "poltergeist": {"motivation": "Record its story.", "rules": ["Cannot harm physically.", "Alters letters unpredictably."]},
        "noble": {"motivation": "Recover true history.", "risk": "Demands immediate solutions."}
    },
    "scenes": [
        {"name": "Archive Room", "tags": ["piles of letters", "ink flies"]},
        {"name": "Study", "tags": ["misleading documents"]},
        {"name": "Tower Top", "tags": ["letter windstorm"]},
    ],
    "complications": ["Letters rearrange.", "Pages vanish.", "Poltergeist appears visibly."],
    "outcomes": ["Poltergeist placated.", "History corrected.", "Tower sealed."],
    "npc_options": ["Ghost", "Specter", "Shadow"],
    "reward": {"gold": 75, "item": "Ink of Truth (1 use: detect written lies once)", "reputation": "Trusted historian."},
    "escalation": ["Letters proliferate.", "False claims spread.", "Poltergeist agitation rises."]
},

{
    "title": "The Floating Market",
    "duration_min": 50,
    "world": {
        "problem": "Market stalls drift across a lake unpredictably.",
        "cause": "Elemental currents unbalanced.",
        "pressure": "Merchants lose goods; town economy suffers."
    },
    "actors": {
        "water_elemental": {"motivation": "Restore currents.", "rules": ["React to offerings; resists force."]},
        "merchants": {"motivation": "Protect inventory.", "risk": "Block or sabotage PC actions."}
    },
    "scenes": [
        {"name": "Dockside", "tags": ["floating planks", "waves"]},
        {"name": "Central Pier", "tags": ["colliding stalls"]},
        {"name": "Market Heart", "tags": ["elemental currents", "floating goods"]},
    ],
    "complications": ["Goods tumble.", "Current shifts.", "Elemental tests PC."] ,
    "outcomes": ["Currents stabilized.", "Market floats freely.", "Partial goods lost."],
    "npc_options": ["Water Elemental", "Merfolk", "Sahuagin"],
    "reward": {"gold": 75, "item": "Water Token (1 use: calm moving water briefly)", "reputation": "Trusted by merchants."},
    "escalation": ["Currents strengthen.", "Goods lost.", "Merchant panic."]
},

{
    "title": "The Library of Living Shadows",
    "duration_min": 45,
    "world": {
        "problem": "Shadows detach and wander the library.",
        "cause": "Magical experiment gone awry.",
        "pressure": "Visitors trapped; books destroyed."
    },
    "actors": {
        "library_guardian": {"motivation": "Recover shadows.", "rules": ["Does not harm PC."]},
        "scholars": {"motivation": "Preserve knowledge.", "risk": "Interfere recklessly."}
    },
    "scenes": [
        {"name": "Entrance Hall", "tags": ["shadows move independently"]},
        {"name": "Stacks", "tags": ["animated books", "obscured paths"]},
        {"name": "Archivist Office", "tags": ["shadow swarm"]},
    ],
    "complications": ["Shadows hide books.", "PC gets lost.", "Shadows merge."],
    "outcomes": ["Shadows returned.", "Experiment contained.", "Library partially ruined."],
    "npc_options": ["Shadow", "Specter", "Ghost"],
    "reward": {"gold": 75, "item": "Shadow Thread (1 use: control shadow briefly)", "reputation": "Keeper of knowledge."},
    "escalation": ["Shadows grow.", "Books lost.", "Visitors panic."]
},

{
    "title": "The Lantern Festival in Peril",
    "duration_min": 45,
    "world": {
        "problem": "Festival lanterns refuse to float; magic falters.",
        "cause": "Sky spirit distracted by earthly conflict.",
        "pressure": "Festival may fail; town morale drops."
    },
    "actors": {
        "sky_spirit": {"motivation": "Attend own realm.", "rules": ["Distracted; reacts if approached."]},
        "festival_organizer": {"motivation": "Launch lanterns.", "risk": "Forces unsafe shortcuts."}
    },
    "scenes": [
        {"name": "Festival Grounds", "tags": ["lantern racks", "crowd"]},
        {"name": "Riverside", "tags": ["floating lanterns", "water reflections"]},
        {"name": "Spirit Gate", "tags": ["visible aura", "ethereal tether"]},
    ],
    "complications": ["Lanterns fall.", "Spirit moves away.", "Crowd panics."],
    "outcomes": ["Spirit appeased.", "Lanterns float.", "Festival partial success."],
    "npc_options": ["Invisible Stalker", "Air Elemental", "Will-o'-Wisp"],
    "reward": {"gold": 75, "item": "Lantern Charm (1 use: levitate small object 1 min)", "reputation": "Festival hero."},
    "escalation": ["Lanterns fail.", "Spirit leaves.", "Crowd frustrated."]
},

{
    "title": "The Abandoned Observatory",
    "duration_min": 50,
    "world": {
        "problem": "Stars shift unpredictably; telescopes malfunction.",
        "cause": "Ancient starbound artifact misaligned.",
        "pressure": "Navigation errors affecting trade."
    },
    "actors": {
        "astronomer_ghost": {"motivation": "Restore observation.", "rules": ["Only gives cryptic guidance."]},
        "traders": {"motivation": "Ensure routes.", "risk": "Ignore PC advice."}
    },
    "scenes": [
        {"name": "Observatory Tower", "tags": ["broken telescope", "rotating lenses"]},
        {"name": "Star Deck", "tags": ["erratic readings", "astral patterns"]},
        {"name": "Artifact Chamber", "tags": ["floating orbs", "celestial alignment"]},
    ],
    "complications": ["Artifact shifts.", "Astral energy flares.", "Ghost misleads."],
    "outcomes": ["Alignment restored.", "Artifact neutralized.", "Ghost remains."],
    "npc_options": ["Will-o'-Wisp", "Specter", "Gargoyle"],
    "reward": {"gold": 75, "item": "Star Shard (1 use: glimpse direction at night)", "reputation": "Trusted navigator."},
    "escalation": ["Stars shift.", "Telescopes break.", "Traders panic."]
},

{
    "title": "The Market of Forgotten Things",
    "duration_min": 45,
    "world": {
        "problem": "Items with unusual properties appear and vanish at market.",
        "cause": "Temporal pocket overlaps.",
        "pressure": "Traders confused; trade disrupted."
    },
    "actors": {
        "temporal_keeper": {"motivation": "Recover items.", "rules": ["Appears at random times.", "Does not harm PC."]},
        "traders": {"motivation": "Secure goods.", "risk": "Attempt to seize items improperly."}
    },
    "scenes": [
        {"name": "Market Entrance", "tags": ["floating wares"]},
        {"name": "Stall Rows", "tags": ["items appear/disappear"]},
        {"name": "Hidden Pocket", "tags": ["temporal anomaly"]},
    ],
    "complications": ["Goods vanish mid-trade.", "Stalls shift.", "Temporal anomaly spreads."],
    "outcomes": ["Items retrieved.", "Anomaly sealed.", "Pocket remains unstable."],
    "npc_options": ["Dust Mephit", "Ice Mephit", "Magma Mephit", "Steam Mephit"],
    "reward": {"gold": 75, "item": "Time Coin (1 use: retrieve object lost in last minute)", "reputation": "Curator of lost things."},
    "escalation": ["Items vanish more frequently.", "Market chaos.", "Pocket grows."]
},

{
    "title": "The Catacombs of Whispers",
    "duration_min": 50,
    "world": {
        "problem": "Underground tomb whispers secrets from past rulers.",
        "cause": "Residual memory imprinted in walls.",
        "pressure": "Historians risk misinterpreting."
    },
    "actors": {
        "tomb_echo": {"motivation": "Preserve memory.", "rules": ["Repeats fragments; misleads if ignored."]},
        "historians": {"motivation": "Document history.", "risk": "Disturb structures."}
    },
    "scenes": [
        {"name": "Entry Passage", "tags": ["faint whispers", "narrow corridor"]},
        {"name": "Hall of Kings", "tags": ["statues whisper", "collapsed areas"]},
        {"name": "Memory Vault", "tags": ["fragments of events", "illusion"]},
    ],
    "complications": ["Echoes mislead.", "Structures unstable.", "Fragments animate."],
    "outcomes": ["Memories preserved.", "Echo fades.", "Artifacts lost."],
    "npc_options": ["Skeleton", "Zombie", "Ghoul", "Wight", "Specter"],
    "reward": {"gold": 75, "item": "Whisper Gem (1 use: hear one past event clearly)", "reputation": "Trusted historian."},
    "escalation": ["Whispers intensify.", "Corridors collapse.", "Artifacts damaged."]
},

{
    "title": "The Garden of Mirrors",
    "duration_min": 45,
    "world": {
        "problem": "Reflections act independently.",
        "cause": "Magic trapped in glass panes.",
        "pressure": "Visitors disoriented; garden dangerous."
    },
    "actors": {
        "mirror_spirit": {"motivation": "Express trapped magic.", "rules": ["Shadows PC; cannot directly attack."]},
        "gardener": {"motivation": "Restore garden.", "risk": "Moves panes recklessly."}
    },
    "scenes": [
        {"name": "Entrance Arch", "tags": ["distorted reflections"]},
        {"name": "Central Fountain", "tags": ["mirrored water", "walking reflections"]},
        {"name": "Maze of Mirrors", "tags": ["paths shift", "illusion triggers"]},
    ],
    "complications": ["Reflections mislead.", "Maze shifts.", "Water mirror floods."],
    "outcomes": ["Magic freed.", "Garden stabilized.", "Some mirrors remain enchanted."],
    "npc_options": ["Doppelganger", "Shadow", "Specter"],
    "reward": {"gold": 75, "item": "Mirror Shard (1 use: see reflection of distant area)", "reputation": "Master of perception."},
    "escalation": ["Reflections act independently.", "Paths rearrange.", "Visitors panic."]
}

]
