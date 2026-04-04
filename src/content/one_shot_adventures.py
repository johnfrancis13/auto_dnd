one_shot_adventures = adventures = [

{
    "title": "The Lighthouse That Forgot the Sea",
    "duration_min": 45,
    "hook": "The town council hires you after three travelers vanish in a beam of light from an inland lighthouse.",
    "premise": "An oath-bound mariner echo keeps a lighthouse burning though the coast is long gone.",
    "stakes": "More people disappear and the distortion spreads across the hill.",
    "scenes": [
        {"name": "Town Square", "tags": ["missing posters", "fear"]},
        {"name": "Hilltop Lighthouse", "tags": ["impossible horizon", "strange gravity"]},
        {"name": "Lantern Room", "tags": ["blinding light", "memory fragments"]}
    ],
    "npcs": [
        {"name": "Keeper Echo", "role": "oath-bound spirit", "motivation": "keep the light burning", "mannerisms": "speaks as if ships still sail"},
        {"name": "Worried Townsfolk", "role": "mob", "motivation": "end disappearances quickly", "mannerisms": "impatient and afraid"}
    ],
    "complications": [
        "The PC sees visions of a distant ocean.",
        "The light intensifies unpredictably.",
        "Townsfolk arrive with torches and pitchforks."
    ],
    "outcomes": [
        "The oath is resolved peacefully.",
        "The light is destroyed violently.",
        "The distortion spreads.",
        "The keeper is freed."
    ],
    "npc_options": ["Ghost", "Specter", "Will-o'-Wisp"],
    "reward": {
        "gold": 75,
        "item": "Lantern Shard (1 use: reveal invisible for 1 min)",
        "reputation": "Trusted mediator."
    },
    "escalation": [
        "The light grows brighter nightly.",
        "More vanishings occur.",
        "Reality warps around the hill."
    ]
},

{
    "title": "The Orchard That Ripens Overnight",
    "duration_min": 45,
    "hook": "The orchard owner begs you to investigate fruit that appears overnight and leaves villagers sleepwalking.",
    "premise": "A fey crossing beneath the orchard feeds on emotions through enchanted fruit.",
    "stakes": "The village becomes dependent and the crossing stabilizes permanently.",
    "scenes": [
        {"name": "Dreaming Orchard", "tags": ["glowing fruit", "whispers"]},
        {"name": "Root Hollow", "tags": ["thin veil", "fey sigils"]},
        {"name": "Twilight Crossing", "tags": ["mutable terrain"]}
    ],
    "npcs": [
        {"name": "Fey Emissary", "role": "deal-maker", "motivation": "cultivate emotional energy", "mannerisms": "never lies directly"},
        {"name": "Orchard Owner", "role": "desperate local", "motivation": "save the orchard", "mannerisms": "already half-ensnared"}
    ],
    "complications": [
        "The PC experiences a vivid dream vision.",
        "Fruit overripens rapidly.",
        "Villagers defend the orchard."
    ],
    "outcomes": [
        "A fey pact is negotiated.",
        "The crossing is sealed.",
        "The orchard is transformed.",
        "The village becomes addicted."
    ],
    "npc_options": ["Dryad", "Sprite", "Satyr", "Blink Dog"],
    "reward": {
        "gold": 75,
        "item": "Fey Apple Seed (plant once for safe shelter overnight)",
        "reputation": "Known to the fey."
    },
    "escalation": [
        "Dreams intensify.",
        "Sleepwalking incidents rise.",
        "A permanent crossing forms."
    ]
},

{
    "title": "The Silent Bell Tower",
    "duration_min": 40,
    "hook": "A priest asks you to restore the town bell before a sacred ritual, after time itself starts slipping.",
    "premise": "A bound time spirit is trapped in the bell mechanism, distorting local time.",
    "stakes": "Rituals fail, commerce collapses, and time fractures further.",
    "scenes": [
        {"name": "Bell Tower Base", "tags": ["confused townsfolk"]},
        {"name": "Clockwork Interior", "tags": ["moving gears", "temporal echoes"]},
        {"name": "Bell Chamber", "tags": ["frozen dust", "time loops"]}
    ],
    "npcs": [
        {"name": "Bound Spirit", "role": "time entity", "motivation": "escape the loop", "mannerisms": "speaks in past and future tense"},
        {"name": "Local Priest", "role": "caretaker", "motivation": "maintain tradition", "mannerisms": "harried and sincere"}
    ],
    "complications": [
        "A short time rewind occurs.",
        "An object suddenly ages and crumbles.",
        "The bell rings prematurely."
    ],
    "outcomes": [
        "The spirit is freed.",
        "The spirit is rebound differently.",
        "The tower is dismantled.",
        "Time stabilizes only partially."
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
        "The day repeats in fragments."
    ]
},

{
    "title": "The Map That Draws Itself",
    "duration_min": 45,
    "hook": "A patron shows you a map that adds new streets each night and now predicts a disaster near your lodgings.",
    "premise": "A sentient cartographic spirit is trying to complete itself by redrawing the city.",
    "stakes": "Reality shifts to match the map and a neighborhood is overwritten.",
    "scenes": [
        {"name": "Study Room", "tags": ["animated ink"]},
        {"name": "Newly Drawn Alley", "tags": ["architecture mismatch"]},
        {"name": "Blank Space", "tags": ["reality thin"]}
    ],
    "npcs": [
        {"name": "Map Spirit", "role": "cartographic entity", "motivation": "be completed", "mannerisms": "adds locations when ignored"}
    ],
    "complications": ["Ink spreads.", "Locations shift."],
    "outcomes": ["The map is completed.", "The map is burned.", "The map bonds to the PC."],
    "npc_options": ["Animated Armor", "Flying Sword", "Rug of Smothering"],
    "reward": {
        "gold": 75,
        "item": "Self-Updating Map (marks nearest settlement once/day)",
        "reputation": "Local curiosity."
    },
    "escalation": ["More areas are drawn.", "Warnings appear.", "A district is redrawn overnight."]
},

{
    "title": "The House That Rearranges",
    "duration_min": 45,
    "hook": "A neighbor begs you to retrieve trapped residents from a house whose rooms keep moving.",
    "premise": "A lonely mimic-colony rearranges the interior to keep occupants forever.",
    "stakes": "Residents are lost and the house expands into the block.",
    "scenes": [
        {"name": "Entry Hall", "tags": ["familiar but wrong"]},
        {"name": "Moving Corridor", "tags": ["sliding walls"]},
        {"name": "Heart Room", "tags": ["organic beams"]}
    ],
    "npcs": [
        {"name": "House Entity", "role": "mimic colony", "motivation": "keep occupants", "mannerisms": "rearranges when ignored"}
    ],
    "complications": ["A room seals shut.", "Furniture moves on its own."],
    "outcomes": ["The entity is befriended.", "The house escapes town.", "The entity is dispersed."],
    "npc_options": ["Mimic", "Rug of Smothering", "Animated Armor"],
    "reward": {
        "gold": 75,
        "item": "Key of Familiar Doors (once: open known door within 60 ft)",
        "reputation": "Trusted rescuer."
    },
    "escalation": ["Rooms duplicate.", "Exits vanish.", "The structure expands."]
},

{
    "title": "The River That Flows Uphill",
    "duration_min": 45,
    "hook": "Millers hire you after the river reverses, ruining their livelihoods.",
    "premise": "An elemental imbalance upstream is reversing the river on a weekly cycle.",
    "stakes": "Flooding and droughts devastate the region.",
    "scenes": [
        {"name": "Riverbank", "tags": ["floating debris upstream"]},
        {"name": "Abandoned Mill", "tags": ["waterwheel stalled"]},
        {"name": "Source Pool", "tags": ["elemental rift"]}
    ],
    "npcs": [
        {"name": "Water Spirit", "role": "elemental mediator", "motivation": "correct the imbalance", "mannerisms": "responds to respectful offerings"}
    ],
    "complications": ["A sudden surge hits.", "Villagers argue over blame."],
    "outcomes": ["Balance is restored.", "The reversal becomes permanent.", "The spirit is angered."],
    "npc_options": ["Water Elemental", "Steam Mephit", "Merfolk"],
    "reward": {
        "gold": 75,
        "item": "Vial of Reversed Water (1 use: reverse gravity on small object briefly)",
        "reputation": "River-friend."
    },
    "escalation": ["Flooding begins.", "Downstream droughts.", "The rift widens."]
},

{
    "title": "The Whispering Statue Garden",
    "duration_min": 40,
    "hook": "A patron asks you to stop the statues that whisper secrets and are ruining reputations.",
    "premise": "Bound souls trapped in marble reveal truths at night.",
    "stakes": "Public panic and violence break out as secrets spread.",
    "scenes": [
        {"name": "Garden Path", "tags": ["soft whispers"]},
        {"name": "Workshop", "tags": ["unfinished sculpture"]},
        {"name": "Hidden Vault", "tags": ["soul-binding tools"]}
    ],
    "npcs": [
        {"name": "Stone Curator", "role": "collector", "motivation": "preserve the collection", "mannerisms": "denies wrongdoing"}
    ],
    "complications": ["A statue cracks.", "A secret is revealed publicly."],
    "outcomes": ["Souls are freed.", "The garden is destroyed.", "The curator is exposed."],
    "npc_options": ["Gargoyle", "Animated Armor", "Rug of Smothering"],
    "reward": {
        "gold": 75,
        "item": "Stone Whisper (1 use: ask a statue one question)",
        "reputation": "Seeker of truth."
    },
    "escalation": ["Whispers grow louder.", "Statues animate briefly.", "Public panic rises."]
},

{
    "title": "The Festival That Won't End",
    "duration_min": 45,
    "hook": "You arrive in a village caught in a looping festival day and the innkeeper begs for help.",
    "premise": "A joy spirit sustains celebration by resetting the day.",
    "stakes": "The village is trapped in an endless loop and memories fracture.",
    "scenes": [
        {"name": "Festival Grounds", "tags": ["repeating events"]},
        {"name": "Quiet Alley", "tags": ["memories flicker"]},
        {"name": "Center Stage", "tags": ["time anchor"]}
    ],
    "npcs": [
        {"name": "Joy Spirit", "role": "time anchor", "motivation": "sustain celebration", "mannerisms": "resets day if confronted violently"}
    ],
    "complications": ["Memory bleed occurs.", "Time stutters."],
    "outcomes": ["The loop ends.", "The loop is refined.", "The PC is trapped temporarily."],
    "npc_options": ["Satyr", "Sprite", "Blink Dog"],
    "reward": {
        "gold": 75,
        "item": "Ribbon of Recall (1 use: remember a prior failed interaction)",
        "reputation": "Festival friend."
    },
    "escalation": ["Glitches become visible.", "The day shortens.", "The loop destabilizes."]
},

{
    "title": "The Library With No Exit",
    "duration_min": 45,
    "hook": "Scholars hire you after several colleagues vanish inside the old archive.",
    "premise": "An extradimensional library consumes visitors to harvest their stories.",
    "stakes": "More scholars vanish and the archive expands into the city.",
    "scenes": [
        {"name": "Grand Stacks", "tags": ["infinite shelves"]},
        {"name": "Reading Alcove", "tags": ["books rewrite themselves"]},
        {"name": "Catalog Chamber", "tags": ["living index"]}
    ],
    "npcs": [
        {"name": "Archive Entity", "role": "librarian horror", "motivation": "acquire stories", "mannerisms": "trades safe exit for secrets"}
    ],
    "complications": ["The exit disappears.", "A book traps the reader."],
    "outcomes": ["The entity is bargained with.", "The library collapses.", "The PC is marked as an author."],
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
    "hook": "The mayor asks you to calm panic caused by a mirror that shows the future.",
    "premise": "A fragmented prophecy spirit speaks through a mirror in symbolic visions.",
    "stakes": "People act on flawed visions and unrest grows.",
    "scenes": [
        {"name": "Mayor's Hall", "tags": ["crowded anxiety"]},
        {"name": "Mirror Chamber", "tags": ["distorted reflections"]},
        {"name": "Vision Space", "tags": ["symbolic landscape"]}
    ],
    "npcs": [
        {"name": "Mirror Spirit", "role": "prophetic echo", "motivation": "be understood correctly", "mannerisms": "shows symbolic truths"}
    ],
    "complications": ["A false vision spreads.", "A reflection acts independently."],
    "outcomes": ["The spirit is clarified.", "The mirror is shattered.", "The visions are embraced."],
    "npc_options": ["Doppelganger", "Shadow", "Specter"],
    "reward": {
        "gold": 75,
        "item": "Shard of Foresight (1 use: glimpse likely outcome of action)",
        "reputation": "Voice of reason."
    },
    "escalation": ["Visions worsen.", "Public unrest grows.", "Prophecy manifests wrongly."]
},

{
    "title": "The Bridge That Demands Stories",
    "duration_min": 40,
    "hook": "Merchants hire you when the bridge refuses passage unless travelers tell a tale.",
    "premise": "An ancient narrative guardian demands meaningful stories before allowing trade.",
    "stakes": "Trade halts and tempers rise at the crossing.",
    "scenes": [
        {"name": "Bridge Span", "tags": ["echoing voice"]},
        {"name": "River Below", "tags": ["deep current"]},
        {"name": "Memory Echo", "tags": ["story made real briefly"]}
    ],
    "npcs": [
        {"name": "Bridge Guardian", "role": "narrative spirit", "motivation": "collect meaningful stories", "mannerisms": "rejects lies instantly"}
    ],
    "complications": ["A story manifests.", "A listener interrupts."],
    "outcomes": ["The guardian is satisfied.", "The guardian is tricked.", "The bridge collapses."],
    "npc_options": ["Ogre", "Troll", "Bandit"],
    "reward": {
        "gold": 75,
        "item": "Token of Telling (1 use: compel an honest answer)",
        "reputation": "Silver-tongued traveler."
    },
    "escalation": ["Demands deepen.", "Stories turn hostile.", "The bridge seals fully."]
},

{
    "title": "The Clockmaker's Secret",
    "duration_min": 45,
    "hook": "The festival organizer begs you to fix the clock tower before the opening ceremony.",
    "premise": "A clockmaker hid a mechanism that scrambles the chimes to conceal a secret.",
    "stakes": "The festival fails and the town turns on the clockmaker.",
    "scenes": [
        {"name": "Workshop", "tags": ["gears", "blueprints"]},
        {"name": "Clock Tower", "tags": ["hidden hatch", "spinning cogs"]},
        {"name": "Festival Square", "tags": ["confused crowd", "temporal glitches"]}
    ],
    "npcs": [
        {"name": "Clockmaker", "role": "artisan", "motivation": "hide a past transgression", "mannerisms": "misleads politely"},
        {"name": "Townsfolk", "role": "crowd", "motivation": "keep the festival on time", "mannerisms": "impatient"}
    ],
    "complications": ["The chimes go out of sequence.", "A blueprint goes missing.", "The clockmaker evades questions."],
    "outcomes": ["The secret is revealed.", "The clock is repaired.", "The tower is sealed."],
    "npc_options": ["Animated Armor", "Flying Sword", "Thug"],
    "reward": {
        "gold": 75,
        "item": "Pocket Cog (1 use: slow a small mechanism briefly)",
        "reputation": "Respected problem-solver."
    },
    "escalation": ["Chimes desynchronize.", "Crowd panic rises.", "The festival is disrupted."]
},

{
    "title": "The Lighthouse of Echoes",
    "duration_min": 50,
    "hook": "Coastguard hires you after sailors report hallucinations near the lighthouse.",
    "premise": "Psychic residue from a shipwreck lingers and repeats its final moments.",
    "stakes": "Accidents increase and the harbor closes.",
    "scenes": [
        {"name": "Beach", "tags": ["wreckage", "broken masts"]},
        {"name": "Lighthouse Base", "tags": ["strange sounds", "weathered stones"]},
        {"name": "Lantern Room", "tags": ["psychic resonance", "flickering light"]}
    ],
    "npcs": [
        {"name": "Shipwreck Ghosts", "role": "echoing survivors", "motivation": "relive the past", "mannerisms": "subtle, not directly harmful"},
        {"name": "Coastguard Captain", "role": "authority", "motivation": "protect sailors", "mannerisms": "blocks access without cause"}
    ],
    "complications": ["Whispers mislead the PC.", "Fog rolls in.", "Coastguard interrupts."],
    "outcomes": ["Spirits are guided to peace.", "The energy dissipates.", "Whispers are amplified."],
    "npc_options": ["Ghost", "Specter", "Will-o'-Wisp"],
    "reward": {
        "gold": 75,
        "item": "Shell of Calm (1 use: quiet mental interference for 1 minute)",
        "reputation": "Mariners trust you."
    },
    "escalation": ["Whispers intensify.", "Sailors are endangered.", "The light malfunctions."]
},

{
    "title": "The Clockwork Menagerie",
    "duration_min": 45,
    "hook": "A noble hires you after mechanical animals vanish from the garden.",
    "premise": "An automaton caretaker is malfunctioning and hiding missing constructs.",
    "stakes": "The garden collapses and the noble loses face.",
    "scenes": [
        {"name": "Garden Entrance", "tags": ["damaged automata", "broken hedges"]},
        {"name": "Workshop", "tags": ["spare parts", "schematics"]},
        {"name": "Fountain", "tags": ["water-activated gears", "lost automaton"]}
    ],
    "npcs": [
        {"name": "Caretaker Automaton", "role": "malfunctioning guardian", "motivation": "repair systems", "mannerisms": "denies negligence"},
        {"name": "Noble Patron", "role": "employer", "motivation": "maintain appearances", "mannerisms": "threatens dismissal"}
    ],
    "complications": ["Parts are scattered.", "An automaton behaves oddly.", "The caretaker misleads."],
    "outcomes": ["The menagerie is repaired.", "Automata escape.", "The noble is satisfied or displeased."],
    "npc_options": ["Animated Armor", "Flying Sword", "Rug of Smothering"],
    "reward": {
        "gold": 75,
        "item": "Clockwork Key (1 use: control a small automaton briefly)",
        "reputation": "Respected tinker."
    },
    "escalation": ["Automata malfunction.", "Garden damage escalates.", "Noble pressure increases."]
},

{
    "title": "The Deserted Carnival",
    "duration_min": 45,
    "hook": "Town guards ask you to rescue children lured into a silent carnival that glows at night.",
    "premise": "A lingering glamour keeps the carnival alive under a forgotten pact.",
    "stakes": "Children vanish and the town panics.",
    "scenes": [
        {"name": "Entrance Gate", "tags": ["glittering lights", "phantom music"]},
        {"name": "Carousel", "tags": ["moving animals", "illusion"]},
        {"name": "Big Tent", "tags": ["distorted size", "echoing laughter"]}
    ],
    "npcs": [
        {"name": "Carnival Spirit", "role": "glamour keeper", "motivation": "maintain festivity", "mannerisms": "cannot lie, misdirects playfully"},
        {"name": "Town Guard", "role": "rescuer", "motivation": "save children", "mannerisms": "blocks paths aggressively"}
    ],
    "complications": ["Music hypnotizes.", "Tents shift.", "A guard misfires."],
    "outcomes": ["Glamour is removed.", "Children are rescued.", "The spirit is placated."],
    "npc_options": ["Owlbear", "Doppelganger", "Sprite"],
    "reward": {
        "gold": 75,
        "item": "Carnival Coin (1 use: charm one creature briefly)",
        "reputation": "Hero to children."
    },
    "escalation": ["Illusions intensify.", "Children are lost.", "Town panic rises."]
},

{
    "title": "The Ship That Never Docked",
    "duration_min": 50,
    "hook": "The harbormaster hires you when a ghost ship circles nightly and sailors refuse to work.",
    "premise": "A captain's soul is tethered to an unfinished voyage.",
    "stakes": "Trade stops and the harbor shuts down.",
    "scenes": [
        {"name": "Dock", "tags": ["fog", "water reflections"]},
        {"name": "Captain's Cabin", "tags": ["floating charts", "spectral logs"]},
        {"name": "Deck", "tags": ["windy deck", "phantom rigging"]}
    ],
    "npcs": [
        {"name": "Ghost Captain", "role": "tethered soul", "motivation": "complete the journey", "mannerisms": "communicates cryptically"},
        {"name": "Harbormaster", "role": "employer", "motivation": "resume trade", "mannerisms": "refuses help at first"}
    ],
    "complications": ["The ship drifts unpredictably.", "The crew reacts emotionally.", "Fog reduces visibility."],
    "outcomes": ["The captain is freed.", "The ship dissipates.", "The tether remains partially."],
    "npc_options": ["Ghost", "Specter", "Wraith", "Skeleton"],
    "reward": {
        "gold": 75,
        "item": "Nautical Compass (1 use: detect ghostly presence)",
        "reputation": "Sailors trust you."
    },
    "escalation": ["The ship drifts into the harbor.", "Mariners panic.", "Trade is delayed further."]
},

{
    "title": "The Tower of Forgotten Letters",
    "duration_min": 45,
    "hook": "A noble hires you after old letters appear, accusing families of crimes that never happened.",
    "premise": "A poltergeist binds memory to parchment, rewriting history.",
    "stakes": "Political chaos erupts among noble houses.",
    "scenes": [
        {"name": "Archive Room", "tags": ["piles of letters", "ink flies"]},
        {"name": "Study", "tags": ["misleading documents"]},
        {"name": "Tower Top", "tags": ["letter windstorm"]}
    ],
    "npcs": [
        {"name": "Poltergeist", "role": "restless recorder", "motivation": "record its story", "mannerisms": "alters letters unpredictably"},
        {"name": "Noble Patron", "role": "employer", "motivation": "recover true history", "mannerisms": "demands immediate solutions"}
    ],
    "complications": ["Letters rearrange.", "Pages vanish.", "The poltergeist appears visibly."],
    "outcomes": ["The poltergeist is placated.", "History is corrected.", "The tower is sealed."],
    "npc_options": ["Ghost", "Specter", "Shadow"],
    "reward": {
        "gold": 75,
        "item": "Ink of Truth (1 use: detect written lies once)",
        "reputation": "Trusted historian."
    },
    "escalation": ["Letters proliferate.", "False claims spread.", "The poltergeist grows agitated."]
},

{
    "title": "The Floating Market",
    "duration_min": 50,
    "hook": "Merchants hire you after the floating market drifts and collides, losing goods daily.",
    "premise": "Unbalanced elemental currents are pushing the stalls across the lake.",
    "stakes": "The town's economy collapses and merchants turn violent.",
    "scenes": [
        {"name": "Dockside", "tags": ["floating planks", "waves"]},
        {"name": "Central Pier", "tags": ["colliding stalls"]},
        {"name": "Market Heart", "tags": ["elemental currents", "floating goods"]}
    ],
    "npcs": [
        {"name": "Water Elemental", "role": "current keeper", "motivation": "restore balance", "mannerisms": "reacts to offerings"},
        {"name": "Merchants", "role": "stakeholders", "motivation": "protect inventory", "mannerisms": "threaten sabotage"}
    ],
    "complications": ["Goods tumble.", "Currents shift.", "The elemental tests the PC."],
    "outcomes": ["Currents are stabilized.", "The market floats freely.", "Partial goods are lost."],
    "npc_options": ["Water Elemental", "Merfolk", "Sahuagin"],
    "reward": {
        "gold": 75,
        "item": "Water Token (1 use: calm moving water briefly)",
        "reputation": "Trusted by merchants."
    },
    "escalation": ["Currents strengthen.", "More goods are lost.", "Merchant panic spreads."]
},

{
    "title": "The Library of Living Shadows",
    "duration_min": 45,
    "hook": "A librarian pleads for help after visitors report their shadows walking away.",
    "premise": "A magical experiment caused shadows to detach and roam the stacks.",
    "stakes": "Visitors are trapped and books are destroyed.",
    "scenes": [
        {"name": "Entrance Hall", "tags": ["shadows move independently"]},
        {"name": "Stacks", "tags": ["animated books", "obscured paths"]},
        {"name": "Archivist Office", "tags": ["shadow swarm"]}
    ],
    "npcs": [
        {"name": "Library Guardian", "role": "protector", "motivation": "recover shadows", "mannerisms": "avoids harming the PC"},
        {"name": "Scholars", "role": "bystanders", "motivation": "preserve knowledge", "mannerisms": "interfere recklessly"}
    ],
    "complications": ["Shadows hide books.", "The PC gets lost.", "Shadows merge."],
    "outcomes": ["Shadows are returned.", "The experiment is contained.", "The library is partially ruined."],
    "npc_options": ["Shadow", "Specter", "Ghost"],
    "reward": {
        "gold": 75,
        "item": "Shadow Thread (1 use: control a shadow briefly)",
        "reputation": "Keeper of knowledge."
    },
    "escalation": ["Shadows grow.", "Books are lost.", "Visitors panic."]
},

{
    "title": "The Lantern Festival in Peril",
    "duration_min": 45,
    "hook": "The festival organizer asks you to intervene when the lanterns refuse to float.",
    "premise": "A distracted sky spirit has pulled its magic away from the town.",
    "stakes": "The festival fails and morale collapses.",
    "scenes": [
        {"name": "Festival Grounds", "tags": ["lantern racks", "crowd"]},
        {"name": "Riverside", "tags": ["floating lanterns", "water reflections"]},
        {"name": "Spirit Gate", "tags": ["visible aura", "ethereal tether"]}
    ],
    "npcs": [
        {"name": "Sky Spirit", "role": "aerial entity", "motivation": "attend its own realm", "mannerisms": "distracted and distant"},
        {"name": "Festival Organizer", "role": "community leader", "motivation": "launch lanterns", "mannerisms": "pushes unsafe shortcuts"}
    ],
    "complications": ["Lanterns fall.", "The spirit moves away.", "The crowd panics."],
    "outcomes": ["The spirit is appeased.", "Lanterns float.", "The festival partially succeeds."],
    "npc_options": ["Invisible Stalker", "Air Elemental", "Will-o'-Wisp"],
    "reward": {
        "gold": 75,
        "item": "Lantern Charm (1 use: levitate a small object for 1 min)",
        "reputation": "Festival hero."
    },
    "escalation": ["Lanterns keep failing.", "The spirit leaves.", "Crowd frustration rises."]
},

{
    "title": "The Abandoned Observatory",
    "duration_min": 50,
    "hook": "Traders hire you after navigation errors start wrecking shipments.",
    "premise": "A starbound artifact in the old observatory is misaligned.",
    "stakes": "Trade routes fail and ships go missing.",
    "scenes": [
        {"name": "Observatory Tower", "tags": ["broken telescope", "rotating lenses"]},
        {"name": "Star Deck", "tags": ["erratic readings", "astral patterns"]},
        {"name": "Artifact Chamber", "tags": ["floating orbs", "celestial alignment"]}
    ],
    "npcs": [
        {"name": "Astronomer Ghost", "role": "restless scholar", "motivation": "restore observation", "mannerisms": "gives cryptic guidance"},
        {"name": "Trade Representative", "role": "employer", "motivation": "ensure routes", "mannerisms": "ignores warnings"}
    ],
    "complications": ["The artifact shifts.", "Astral energy flares.", "The ghost misleads."],
    "outcomes": ["Alignment is restored.", "The artifact is neutralized.", "The ghost remains bound."],
    "npc_options": ["Will-o'-Wisp", "Specter", "Gargoyle"],
    "reward": {
        "gold": 75,
        "item": "Star Shard (1 use: glimpse direction at night)",
        "reputation": "Trusted navigator."
    },
    "escalation": ["Stars shift.", "Telescopes break.", "Traders panic."]
},

{
    "title": "The Market of Forgotten Things",
    "duration_min": 45,
    "hook": "A merchant guild hires you after rare items appear and vanish mid-sale.",
    "premise": "A temporal pocket overlaps the market, swapping goods across moments.",
    "stakes": "The market collapses under chaos and theft.",
    "scenes": [
        {"name": "Market Entrance", "tags": ["floating wares"]},
        {"name": "Stall Rows", "tags": ["items appear or disappear"]},
        {"name": "Hidden Pocket", "tags": ["temporal anomaly"]}
    ],
    "npcs": [
        {"name": "Temporal Keeper", "role": "anomaly steward", "motivation": "recover items", "mannerisms": "appears at random times"},
        {"name": "Traders", "role": "stakeholders", "motivation": "secure goods", "mannerisms": "attempt to seize items"}
    ],
    "complications": ["Goods vanish mid-trade.", "Stalls shift.", "The anomaly spreads."],
    "outcomes": ["Items are retrieved.", "The anomaly is sealed.", "The pocket remains unstable."],
    "npc_options": ["Dust Mephit", "Ice Mephit", "Magma Mephit", "Steam Mephit"],
    "reward": {
        "gold": 75,
        "item": "Time Coin (1 use: retrieve an object lost in the last minute)",
        "reputation": "Curator of lost things."
    },
    "escalation": ["Items vanish more frequently.", "Market chaos rises.", "The pocket grows."]
},

{
    "title": "The Catacombs of Whispers",
    "duration_min": 50,
    "hook": "Historians hire you to escort them after whispers in the catacombs begin revealing forbidden truths.",
    "premise": "Residual memories in the tomb walls repeat and distort the past.",
    "stakes": "The catacombs collapse and sacred relics are lost.",
    "scenes": [
        {"name": "Entry Passage", "tags": ["faint whispers", "narrow corridor"]},
        {"name": "Hall of Kings", "tags": ["statues whisper", "collapsed areas"]},
        {"name": "Memory Vault", "tags": ["fragments of events", "illusion"]}
    ],
    "npcs": [
        {"name": "Tomb Echo", "role": "memory spirit", "motivation": "preserve memory", "mannerisms": "repeats fragments"},
        {"name": "Historians", "role": "clients", "motivation": "document history", "mannerisms": "disturb structures"}
    ],
    "complications": ["Echoes mislead.", "Structures become unstable.", "Fragments animate."],
    "outcomes": ["Memories are preserved.", "The echo fades.", "Artifacts are lost."],
    "npc_options": ["Skeleton", "Zombie", "Ghoul", "Wight", "Specter"],
    "reward": {
        "gold": 75,
        "item": "Whisper Gem (1 use: hear one past event clearly)",
        "reputation": "Trusted historian."
    },
    "escalation": ["Whispers intensify.", "Corridors collapse.", "Artifacts are damaged."]
},

{
    "title": "The Garden of Mirrors",
    "duration_min": 45,
    "hook": "A gardener begs you to stop the mirror maze where reflections are harming visitors.",
    "premise": "Trapped magic in the mirrors produces independent reflections.",
    "stakes": "Visitors panic and the garden shuts down.",
    "scenes": [
        {"name": "Entrance Arch", "tags": ["distorted reflections"]},
        {"name": "Central Fountain", "tags": ["mirrored water", "walking reflections"]},
        {"name": "Maze of Mirrors", "tags": ["paths shift", "illusion triggers"]}
    ],
    "npcs": [
        {"name": "Mirror Spirit", "role": "trapped magic", "motivation": "express itself", "mannerisms": "shadows the PC"},
        {"name": "Head Gardener", "role": "caretaker", "motivation": "restore the garden", "mannerisms": "moves panes recklessly"}
    ],
    "complications": ["Reflections mislead.", "The maze shifts.", "The water mirror floods."],
    "outcomes": ["Magic is freed.", "The garden is stabilized.", "Some mirrors remain enchanted."],
    "npc_options": ["Doppelganger", "Shadow", "Specter"],
    "reward": {
        "gold": 75,
        "item": "Mirror Shard (1 use: see a reflection of a distant area)",
        "reputation": "Master of perception."
    },
    "escalation": ["Reflections grow bolder.", "Paths rearrange.", "Visitors panic."]
}

]
