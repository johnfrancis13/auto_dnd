const state = {
  session: false,
  character: null,
  combat: null,
  actionRolls: {},
  pendingRolls: new Set(),
  pendingRollGlobal: false,
};
const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const startButton = document.getElementById("start-game");
const newGameButton = document.getElementById("new-game");
const charForm = document.getElementById("char-form");
const imageGrid = document.getElementById("image-grid");
const sessionIndicator = document.getElementById("session-indicator");
const gameStateEl = document.getElementById("game-state");
const sheetTabs = document.getElementById("sheet-tabs");
const sheetBody = document.getElementById("sheet-body");
const setupScreen = document.getElementById("setup-screen");
const gameScreen = document.getElementById("game-screen");
const thinkingIndicator = document.getElementById("thinking-indicator");
const equipmentModal = document.getElementById("equipment-modal");
const equipmentFormEl = document.getElementById("equipment-choices-form");
const equipmentSubmit = document.getElementById("equipment-choices-submit");
const equipmentErrorsEl = document.getElementById("equipment-choices-errors");
const spellModal = document.getElementById("spell-modal");
const spellFormEl = document.getElementById("spell-choices-form");
const spellSubmit = document.getElementById("spell-choices-submit");
const spellSummaryEl = document.getElementById("spell-choices-summary");
const spellErrorsEl = document.getElementById("spell-choices-errors");
const combatPanel = document.getElementById("combat-panel");
const combatActionSelect = document.getElementById("combat-action");
const combatTargetSelect = document.getElementById("combat-target");
const combatSubmit = document.getElementById("combat-submit");
const combatTurn = document.getElementById("combat-turn");
const combatEndTurn = document.getElementById("combat-end-turn");
const initiativeOrderEl = document.getElementById("initiative-order");
const turnStateEl = document.getElementById("turn-state");
const combatMapEl = document.getElementById("combat-map");
let selectedTargets = [];
let activeTab = "about";
let pendingStartPayload = null;
let pendingEquipmentChoices = [];
let pendingSpellChoices = [];
let llmPendingCount = 0;
let spellFilterPreparedOnly = false;
let spellFilterLevel = "all";

function setLlmPending(active) {
  llmPendingCount += active ? 1 : -1;
  if (llmPendingCount < 0) {
    llmPendingCount = 0;
  }
  const isActive = llmPendingCount > 0;
  if (thinkingIndicator) {
    thinkingIndicator.classList.toggle("hidden", !isActive);
  }
}
function setSessionActive(active, mode = "exploration") {
  sessionIndicator.textContent = active ? "Live" : "Idle";
  sessionIndicator.style.background = active ? "#e2b091" : "#e6e0d8";
  if (!active) {
    gameStateEl.textContent = "No session running";
  } else {
    const label = mode ? mode.charAt(0).toUpperCase() + mode.slice(1) : "Exploration";
    gameStateEl.textContent = label;
  }
}
function showSetupScreen() {
  setupScreen.classList.remove("hidden");
  gameScreen.classList.add("hidden");
}
function showGameScreen() {
  setupScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");
}
function addMessage(role, content) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = content;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
function renderCharacter(character) {
  state.character = character;
  if (!character) {
    sheetBody.innerHTML = "<div class=\"muted\">Start a game to load stats.</div>";
    return;
  }
  const identity = character.identity;
  const stats = character.stats;
  const aboutHtml = `
    <div class="entry">
      <strong>${identity.name}</strong>
      <div class="muted">${identity.race} ${identity.classes.join("/")} · Level ${identity.level}</div>
      <div class="muted">Background: ${identity.background}</div>
      <p>${identity.description || ""}</p>
      <ul>
        <li><span>HP</span><strong>${stats.hp.current}/${stats.hp.max}</strong></li>
        <li><span>AC</span><strong>${stats.ac}</strong></li>
      </ul>
    </div>
    <h3>Features</h3>
    ${character.about.features.length === 0 ? "<p>No features yet.</p>" : character.about.features.map(f => `
      <details class="entry">
        <summary><strong>${f.name}</strong></summary>
        <div class="detail-body">
          <div>${f.source || "Unknown"} ${f.type ? `· ${f.type}` : ""}</div>
          <div>${f.description || ""}</div>
        </div>
      </details>
    `).join("")}
    <h3>Proficiencies</h3>
    ${Object.entries(character.about.proficiencies).map(([key, vals]) => `
      <div class="entry">
        <strong>${key}</strong>
        <div class="chip-list">
          ${vals.length ? vals.map(v => `<span class="chip">${v}</span>`).join("") : "<span class=\"muted\">None</span>"}
        </div>
      </div>
    `).join("")}
  `;
  const abilitiesHtml = `
    <h3>Ability Scores</h3>
    <ul>
      ${Object.entries(character.abilities.ability_scores).map(([k, v]) => `<li><span>${k}</span><strong>${v}</strong></li>`).join("")}
    </ul>
    <h3>Skill Scores</h3>
    <ul>
      ${Object.entries(character.abilities.skill_scores).map(([k, v]) => `<li><span>${k}</span><strong>${v}</strong></li>`).join("")}
    </ul>
    <h3>Saving Throws</h3>
    <ul>
      ${Object.entries(character.abilities.saving_throws).map(([k, v]) => `<li><span>${k}</span><strong>${v}</strong></li>`).join("")}
    </ul>
  `;
  const inventoryHtml = `
    ${character.inventory.items.length === 0 ? "<p>No items.</p>" : character.inventory.items.map(item => `
      <div class="entry">
        <div class="entry-row">
          <strong>${item.name}</strong>
          ${item.equippable ? `
            <button type="button" class="toggle-button ${item.equipped ? "on" : "off"}" data-equip-toggle data-item-name="${item.name}" data-equipped="${item.equipped}">
              ${item.equipped ? "Equipped" : "Equip"}
            </button>
          ` : `<span class="muted">Not equippable</span>`}
        </div>
        <div class="muted">${item.type || "Item"}${item.subtype ? ` · ${item.subtype}` : ""}${item.rarity ? ` · ${item.rarity}` : ""}</div>
        ${item.description ? `<div class="muted">${item.description}</div>` : ""}
        <div class="muted">Qty: ${item.quantity}</div>
      </div>
    `).join("")}
  `;
  const resourceList = [
    ...character.actions.resources.custom,
    ...character.actions.resources.spell_slots,
    ...character.actions.resources.spell_access,
  ].filter((res) => !((res.current ?? 0) === 0 && (res.maximum ?? 0) === 0));
  const actionsHtml = `
    <h3>Actions</h3>
    ${character.actions.actions.length === 0 ? "<p>No actions.</p>" : character.actions.actions.map(action => `
      <details class="entry">
        <summary><strong>${action.name}</strong></summary>
        <div class="detail-body">
          <div>${action.type} ${action.source ? `· ${action.source}` : ""}</div>
          ${renderActionBadges(action)}
          ${action.proficiency_type ? `<div>Proficiency: ${action.proficiency_type}</div>` : ""}
          ${renderActionRollInfo(action, character)}
          ${renderActionControls(action, character)}
        </div>
      </details>
    `).join("")}
    <h3>Resources</h3>
    ${resourceList.length === 0 ? "<p>No resources.</p>" : resourceList.map(res => `
      <details class="entry">
        <summary>
          <div class="entry-row">
            <strong>${res.name}</strong>
            <button type="button" class="toggle-button" data-resource-use data-resource-id="${res.id}" data-resource-name="${res.name}" ${res.current > 0 ? "" : "disabled"}>
              Use (${res.current}/${res.maximum})
            </button>
          </div>
        </summary>
        <div class="detail-body">
          <div>${formatResourceMeta(res)}</div>
          <div>${res.current}/${res.maximum}</div>
        </div>
      </details>
    `).join("")}
  `;
  const preparedLimit = character.spells.prepared_limit;
  const preparedCount = character.spells.prepared.length;
  const preparedMeta = preparedLimit
    ? `<div class="muted">Prepared: ${preparedCount}/${preparedLimit}</div>`
    : "";
  let knownSpells = spellFilterPreparedOnly
    ? character.spells.known.filter((spell) => spell.prepared)
    : character.spells.known;
  if (spellFilterLevel === "cantrip") {
    knownSpells = knownSpells.filter((spell) => spell.level === 0);
  } else if (spellFilterLevel === "leveled") {
    knownSpells = knownSpells.filter((spell) => spell.level > 0);
  }
  const spellsHtml = `
    <h3>Spellcasting</h3>
    <div class="entry">
      <div class="muted">Ability: ${character.spells.spellcasting_ability || "Unknown"}</div>
      <div class="muted">Save DC: ${character.spells.spell_save_dc || "Unknown"}</div>
      ${preparedMeta}
      <label class="spell-filter">
        <input type="checkbox" data-spell-filter ${spellFilterPreparedOnly ? "checked" : ""} />
        Show prepared only
      </label>
      <label class="spell-filter">
        Filter
        <select data-spell-filter-level>
          <option value="all" ${spellFilterLevel === "all" ? "selected" : ""}>All</option>
          <option value="cantrip" ${spellFilterLevel === "cantrip" ? "selected" : ""}>Cantrips</option>
          <option value="leveled" ${spellFilterLevel === "leveled" ? "selected" : ""}>Leveled</option>
        </select>
      </label>
    </div>
    <h3>Known Spells</h3>
    ${knownSpells.length === 0 ? "<p>No spells to show.</p>" : knownSpells.map(spell => `
      <details class="entry">
        <summary>
          <div class="entry-row">
            <strong>${spell.name}</strong>
            <button type="button" class="toggle-button ${spell.level === 0 ? "on" : (spell.prepared ? "on" : "off")}" data-prepare-toggle data-spell-name="${spell.name}" data-prepared="${spell.prepared}" ${spell.level === 0 ? "disabled" : ""}>
              ${spell.level === 0 ? "Cantrip" : (spell.prepared ? "Prepared" : "Prepare")}
            </button>
          </div>
        </summary>
        <div class="detail-body">
          <div>Level ${spell.level} · ${spell.school}</div>
          <div>${spell.cast_time} · ${spell.range} · ${spell.duration}</div>
          ${spell.description ? `<div class="muted">${spell.description}</div>` : ""}
        </div>
      </details>
    `).join("")}
  `;
  const tabContent = {
    about: aboutHtml,
    abilities: abilitiesHtml,
    inventory: inventoryHtml,
    actions: actionsHtml,
    spells: spellsHtml,
  };
  sheetBody.innerHTML = tabContent[activeTab] || aboutHtml;
}

function renderActionRollInfo(action, character) {
  const lines = [];
  if (action.attack_roll) {
    const ability = formatAbility(action.attack_roll.ability, character);
    const bonus = action.attack_roll.bonus || 0;
    lines.push(`Attack: d20 + ${ability}${bonus ? ` + ${bonus}` : ""}${action.proficiency_type ? " + prof" : ""}`);
  }
  if (action.save) {
    const dc = action.save.dc === "spell_save_dc" ? character.spells.spell_save_dc : action.save.dc;
    lines.push(`Save: ${action.save.ability} vs DC ${dc || "?"} (${action.save.on_success || "none"} on success)`);
  }
  if (action.damage_roll && action.damage_roll.length) {
    const dmgLine = action.damage_roll.map((dmg) => {
      const ability = formatAbility(dmg.ability, character);
      const bonus = dmg.bonus || 0;
      const modPart = ability ? ` + ${ability}` : "";
      const bonusPart = bonus ? ` + ${bonus}` : "";
      return `${dmg.dice_amount}d${dmg.dice_type}${modPart}${bonusPart} ${dmg.dmg_type}`;
    }).join(" + ");
    lines.push(`Damage: ${dmgLine}`);
  }
  if (!lines.length) {
    return `<div class="muted">No rolls available.</div>`;
  }
  return lines.map((line) => `<div>${line}</div>`).join("");
}

function formatAbility(value, character) {
  if (!value) {
    return "";
  }
  const upper = String(value).toUpperCase();
  if (upper === "SPELLCASTING" || upper === "SPELL") {
    return character.spells.spellcasting_ability || "Spellcasting";
  }
  return upper;
}

function formatResourceMeta(res) {
  const parts = [];
  if (res.category) {
    const label = String(res.category).replace(/_/g, " ");
    parts.push(label.replace(/\b\w/g, (c) => c.toUpperCase()));
  }
  if (res.recharge && res.recharge !== "none") {
    const label = String(res.recharge).replace(/_/g, " ");
    parts.push(label.replace(/\b\w/g, (c) => c.toUpperCase()));
  }
  if (res.source) {
    parts.push(res.source);
  }
  return parts.length ? parts.join(" · ") : "Resource";
}

function renderActionControls(action, character) {
  const targets = state.combat?.targets || [];
  const inCombat = state.combat?.active;
  const maxTargets = action.max_targets ?? null;
  const slotResource = getSpellSlotResource(character, action.spell_level);
  const hasSlots = !action.spell_level || (slotResource && slotResource.current > 0);
  const targetSelect = targets.length
    ? `
      <label class="roll-control">
        Target
        <select data-roll-target="${action.id}" data-max-targets="${maxTargets ?? ""}" multiple size="4">
          ${targets.map((t) => `<option value="${t}">${t}</option>`).join("")}
        </select>
        ${maxTargets ? `<div class="muted">Max targets: ${maxTargets}</div>` : ""}
      </label>
    `
    : "";
  const targetText = !inCombat
    ? `
      <label class="roll-control">
        Target (optional)
        <input type="text" data-roll-target-text="${action.id}" placeholder="e.g., the guard, the door" />
      </label>
    `
    : "";
  const narrateButton = !inCombat
    ? `<button type="button" class="roll-button primary" data-roll-action="${action.id}" data-roll-narrate="true">Roll + Narrate</button>`
    : "";
  const slotNote = action.spell_level && slotResource
    ? `<div class="muted">Spell slots (Level ${action.spell_level}): ${slotResource.current}/${slotResource.maximum}</div>`
    : (action.spell_level ? `<div class="muted">Spell slots (Level ${action.spell_level}): 0/0</div>` : "");
  return `
    <div class="roll-controls" data-roll-controls="${action.id}">
      <label class="roll-control">
        Advantage
        <select data-roll-advantage="${action.id}">
          <option value="">Normal</option>
          <option value="adv">Advantage</option>
          <option value="dis">Disadvantage</option>
        </select>
      </label>
      ${targetSelect}
      ${targetText}
      <div class="roll-status" data-roll-status="${action.id}"></div>
      ${slotNote}
      <div class="roll-buttons">
        <button type="button" class="roll-button" data-roll-action="${action.id}" ${hasSlots ? "" : "disabled"}>Roll</button>
        ${hasSlots ? narrateButton : ""}
      </div>
    </div>
  `;
}
function renderActionBadges(action) {
  const roll = state.actionRolls?.[action.id];
  if (!roll) {
    return "";
  }
  const chips = [];
  if (roll.attack_roll?.total !== undefined) {
    chips.push(`Atk ${roll.attack_roll.total}`);
  }
  if (roll.save?.dc !== undefined && roll.save?.dc !== null) {
    chips.push(`Save DC ${roll.save.dc}`);
  }
  if (roll.damage_total !== undefined && roll.damage_total !== null) {
    chips.push(`Dmg ${roll.damage_total}`);
  }
  if (!chips.length) {
    return "";
  }
  return `<div class="chip-list">${chips.map((c) => `<span class="chip">${c}</span>`).join("")}</div>`;
}

function getSpellSlotResource(character, spellLevel) {
  if (!character || !spellLevel || spellLevel <= 0) {
    return null;
  }
  const slots = character.actions?.resources?.spell_slots || [];
  const name = `Level_${spellLevel} Spell Slots`;
  return slots.find((slot) => slot.name === name) || null;
}
function renderImages(images) {
  imageGrid.innerHTML = "";
  if (!images || images.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "No images yet";
    imageGrid.appendChild(empty);
    return;
  }
  images.forEach((url) => {
    const card = document.createElement("div");
    card.className = "image-card";
    const img = document.createElement("img");
    img.src = url;
    img.alt = "Scene";
    card.appendChild(img);
    imageGrid.appendChild(card);
  });
}
function renderCombat(combat) {
  if (!combat || !combat.active) {
    combatPanel.classList.add("hidden");
    state.combat = combat || null;
    selectedTargets = [];
    return;
  }
  combatPanel.classList.remove("hidden");
  state.combat = combat;
  const playerName = state.character?.identity?.name || "";
  const currentTurn = combat.current_turn || "";
  combatTurn.textContent = currentTurn
    ? `Current turn: ${currentTurn}`
    : "Current turn: Unknown";
  const initiative = combat.initiative_order || [];
  initiativeOrderEl.innerHTML = initiative.length
    ? initiative.map((entry) => {
        const active = entry === currentTurn ? "initiative-chip active" : "initiative-chip";
        return `<span class="${active}">${entry}</span>`;
      }).join("")
    : "<span class=\"muted\">Initiative not set</span>";
  const turnState = combat.turn_state || { action: false, bonus: false, reaction: false };
  const moveRemaining = combat.move_remaining ?? null;
  const moveMax = combat.move_max ?? null;
  turnStateEl.innerHTML = [
    `<span>Action: ${turnState.action ? "Available" : "Used"}</span>`,
    `<span>Bonus: ${turnState.bonus ? "Available" : "Used"}</span>`,
    `<span>Reaction: ${turnState.reaction ? "Available" : "Used"}</span>`,
    moveRemaining !== null && moveMax !== null
      ? `<span>Move: ${moveRemaining}/${moveMax} ft</span>`
      : `<span>Move: --</span>`,
  ].join("");
  const actions = state.character?.actions?.actions || [];
  combatActionSelect.innerHTML = actions.length
    ? actions.map((action) => {
        const typeLabel = action.type.charAt(0).toUpperCase() + action.type.slice(1);
        const label = `${typeLabel}: ${action.name}`;
        const disabled =
          (action.type === "action" && !turnState.action) ||
          (action.type === "bonus" && !turnState.bonus) ||
          (action.type === "reaction" && !turnState.reaction);
        return `<option value="${action.id}" ${disabled ? "disabled" : ""}>${label}</option>`;
      }).join("")
    : "<option value=\"\">No actions available</option>";
  const targets = combat.targets || [];
  combatTargetSelect.innerHTML = targets.length
    ? targets.map((target) => `<option value="${target}">${target}</option>`).join("")
    : "<option value=\"\">No targets available</option>";
  const playerTurn = !currentTurn || currentTurn === playerName;
  const canAct = playerTurn && actions.length > 0;
  combatActionSelect.disabled = !canAct;
  combatTargetSelect.disabled = !canAct || targets.length === 0;
  combatSubmit.disabled = !canAct || targets.length === 0;
  combatEndTurn.disabled = !playerTurn;
  renderCombatMap(combat.map, combat);
  updateTargetingHighlights(combat.map, actions, combat, targets);
}
function renderEquipmentChoices(choices) {
  pendingEquipmentChoices = choices || [];
  if (!pendingEquipmentChoices.length) {
    equipmentModal.classList.add("hidden");
    equipmentModal.setAttribute("aria-hidden", "true");
    equipmentFormEl.innerHTML = "";
    equipmentErrorsEl.textContent = "";
    return;
  }
  equipmentErrorsEl.textContent = "";
  equipmentFormEl.innerHTML = pendingEquipmentChoices.map((group) => {
    const inputType = group.choose > 1 ? "checkbox" : "radio";
    const optionsHtml = group.options.map((option) => `
      <label class="equipment-option">
        <input type="${inputType}" name="${group.id}" value="${option.id}" />
        <span>${option.label}</span>
      </label>
    `).join("");
    return `
      <div class="equipment-group">
        <h3>${group.label}</h3>
        <div class="muted">Choose ${group.choose}</div>
        ${optionsHtml}
      </div>
    `;
  }).join("");
  equipmentModal.classList.remove("hidden");
  equipmentModal.setAttribute("aria-hidden", "false");
}
function collectEquipmentSelections() {
  const selections = {};
  pendingEquipmentChoices.forEach((group) => {
    const selected = Array.from(
      equipmentFormEl.querySelectorAll(`input[name="${group.id}"]:checked`)
    ).map((input) => input.value);
    if (selected.length) {
      selections[group.id] = selected;
    }
  });
  return selections;
}
function renderSpellChoices(choices) {
  pendingSpellChoices = choices || [];
  if (!pendingSpellChoices.length) {
    spellModal.classList.add("hidden");
    spellModal.setAttribute("aria-hidden", "true");
    spellFormEl.innerHTML = "";
    spellErrorsEl.textContent = "";
    if (spellSummaryEl) {
      spellSummaryEl.textContent = "";
    }
    return;
  }
  spellErrorsEl.textContent = "";
  if (spellSummaryEl) {
    const summaryLines = pendingSpellChoices.map((group) => {
      const total = (group.options || []).length;
      const label = group.label || "Spells";
      return `${label}: choose ${group.choose} of ${total}`;
    });
    spellSummaryEl.textContent = summaryLines.join(" · ");
  }
  spellFormEl.innerHTML = pendingSpellChoices.map((group) => {
    const inputType = group.choose > 1 ? "checkbox" : "radio";
    const optionsHtml = group.options.map((option) => `
      <label class="equipment-option">
        <input type="${inputType}" name="${group.id}" value="${option.id}" />
        <span>${option.label}</span>
      </label>
      ${option.description ? `
        <details class="spell-option-details">
          <summary>Show details</summary>
          <div class="spell-option-desc muted">${option.description}</div>
        </details>
      ` : ""}
    `).join("");
    return `
      <div class="equipment-group">
        <h3>${group.label}</h3>
        <div class="muted">Choose ${group.choose}</div>
        ${optionsHtml}
      </div>
    `;
  }).join("");
  spellModal.classList.remove("hidden");
  spellModal.setAttribute("aria-hidden", "false");
}
function collectSpellSelections() {
  const selections = {};
  pendingSpellChoices.forEach((group) => {
    const selected = Array.from(
      spellFormEl.querySelectorAll(`input[name="${group.id}"]:checked`)
    ).map((input) => input.value);
    if (selected.length) {
      selections[group.id] = selected;
    }
  });
  return selections;
}
function enforceMaxTargets(selectEl) {
  const max = Number(selectEl.dataset.maxTargets || 0);
  if (!max) {
    return;
  }
  const selected = Array.from(selectEl.selectedOptions);
  if (selected.length <= max) {
    return;
  }
  selected[selected.length - 1].selected = false;
  addMessage("dm", `Max targets for this action is ${max}.`);
}

function setRollPending(actionId, pending) {
  if (pending) {
    state.pendingRolls.add(actionId);
    state.pendingRollGlobal = true;
  } else {
    state.pendingRolls.delete(actionId);
    if (state.pendingRolls.size === 0) {
      state.pendingRollGlobal = false;
    }
  }
  updateRollPendingUI(actionId, pending);
}

function updateRollPendingUI(activeActionId, pending) {
  const allControls = sheetBody.querySelectorAll("[data-roll-controls]");
  allControls.forEach((controls) => {
    const isActive = controls.dataset.rollControls === activeActionId;
    if (state.pendingRollGlobal) {
      controls.classList.add("pending");
    } else {
      controls.classList.remove("pending");
    }
    controls.querySelectorAll("button, select, input").forEach((el) => {
      el.disabled = state.pendingRollGlobal;
    });
    const status = controls.querySelector("[data-roll-status]");
    if (!status) {
      return;
    }
    if (pending && isActive) {
      status.innerHTML = `<span class="spinner"></span> Rolling...`;
    } else {
      status.textContent = "";
    }
  });
}
function enforceSpellChoiceLimits(input) {
  if (!input || input.type !== "checkbox") {
    return;
  }
  const groupId = input.name;
  const group = pendingSpellChoices.find((g) => g.id === groupId);
  if (!group) {
    return;
  }
  const max = group.choose || 1;
  const checked = spellFormEl.querySelectorAll(`input[name="${groupId}"]:checked`);
  if (checked.length > max) {
    input.checked = false;
    spellErrorsEl.textContent = `Choose only ${max} option(s) for "${group.label}".`;
  } else {
    spellErrorsEl.textContent = "";
  }
}
async function resetUI() {
  state.session = false;
  state.character = null;
  state.actionRolls = {};
  state.pendingRolls = new Set();
  state.pendingRollGlobal = false;
  messagesEl.innerHTML = "";
  activeTab = "about";
  pendingStartPayload = null;
  llmPendingCount = 0;
  if (thinkingIndicator) {
    thinkingIndicator.classList.add("hidden");
  }
  renderEquipmentChoices([]);
  renderSpellChoices([]);
  sheetTabs.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === activeTab);
  });
  renderCharacter(null);
  renderImages([]);
  renderCombat({ active: false });
  setSessionActive(false);
  showSetupScreen();
  try {
    await fetch("/api/reset", { method: "POST" });
  } catch (err) {
    addMessage("dm", `Failed to reset session: ${err}`);
  }
}
async function startGame() {
  setLlmPending(true);
  const formData = new FormData(charForm);
  const payload = {
    character: Object.fromEntries(formData.entries()),
    model_name: "qwen3:8b",
    think: false,
  };
  try {
    pendingStartPayload = payload;
    showGameScreen();
    messagesEl.innerHTML = "";
    renderCharacter(null);
    renderImages([]);
    renderCombat({ active: false });
    setSessionActive(true, "exploration");
    addMessage("dm", "Starting adventure...");
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.requires_choices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      renderEquipmentChoices(data.choices);
      equipmentErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_spell_choices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      renderSpellChoices(data.spell_choices);
      spellErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (!data.session) {
      equipmentErrorsEl.textContent = data.error || "Unable to start session.";
      setSessionActive(false);
      showSetupScreen();
      return;
    }
    state.session = data.session;
    renderCharacter(data.character);
    renderImages(data.images);
    messagesEl.innerHTML = "";
    addMessage("dm", data.narrative || "Adventure started.");
    setSessionActive(true, data.game_state?.mode || "exploration");
    renderCombat(data.combat);
    showGameScreen();
  } finally {
    setLlmPending(false);
  }
}
async function submitEquipmentChoices() {
  if (!pendingStartPayload) {
    return;
  }
  const equipmentChoices = collectEquipmentSelections();
  renderEquipmentChoices([]);
  const payload = {
    ...pendingStartPayload,
    equipment_choices: equipmentChoices,
  };
  pendingStartPayload = payload;
  showGameScreen();
  messagesEl.innerHTML = "";
  renderCharacter(null);
  renderImages([]);
  renderCombat({ active: false });
  setSessionActive(true, "exploration");
  addMessage("dm", "Starting adventure...");
  setLlmPending(true);
  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.requires_choices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      renderEquipmentChoices(data.choices);
      equipmentErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_spell_choices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      renderSpellChoices(data.spell_choices);
      spellErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (!data.session) {
      equipmentErrorsEl.textContent = data.error || "Unable to start session.";
      setSessionActive(false);
      showSetupScreen();
      return;
    }
    renderEquipmentChoices([]);
    state.session = data.session;
    renderCharacter(data.character);
    renderImages(data.images);
    messagesEl.innerHTML = "";
    addMessage("dm", data.narrative || "Adventure started.");
    setSessionActive(true, data.game_state?.mode || "exploration");
    renderCombat(data.combat);
    showGameScreen();
  } finally {
    setLlmPending(false);
  }
}
async function submitSpellChoices() {
  if (!pendingStartPayload) {
    return;
  }
  const spellChoices = collectSpellSelections();
  renderSpellChoices([]);
  const payload = {
    ...pendingStartPayload,
    spell_choices: spellChoices,
  };
  showGameScreen();
  messagesEl.innerHTML = "";
  renderCharacter(null);
  renderImages([]);
  renderCombat({ active: false });
  setSessionActive(true, "exploration");
  addMessage("dm", "Starting adventure...");
  setLlmPending(true);
  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.requires_spell_choices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      renderSpellChoices(data.spell_choices);
      spellErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (!data.session) {
      spellErrorsEl.textContent = data.error || "Unable to start session.";
      setSessionActive(false);
      showSetupScreen();
      return;
    }
    state.session = data.session;
    renderCharacter(data.character);
    renderImages(data.images);
    messagesEl.innerHTML = "";
    addMessage("dm", data.narrative || "Adventure started.");
    setSessionActive(true, data.game_state?.mode || "exploration");
    renderCombat(data.combat);
    showGameScreen();
  } finally {
    setLlmPending(false);
  }
}
async function sendMessage(content) {
  setLlmPending(true);
  try {
    const res = await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    const data = await res.json();
    if (data.error) {
      addMessage("dm", data.error);
      return;
    }
    selectedTargets = [];
    if (data.character) {
      renderCharacter(data.character);
    }
    if (data.game_state?.mode) {
      setSessionActive(true, data.game_state.mode);
    }
    if (data.combat) {
      renderCombat(data.combat);
    }
    addMessage("dm", data.narrative || "...");
  } finally {
    setLlmPending(false);
  }
}
async function sendCombatAction(actionId, targetIds) {
  setLlmPending(true);
  try {
    const res = await fetch("/api/combat_action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: actionId, target_ids: targetIds }),
    });
    const data = await res.json();
    if (data.error) {
      addMessage("dm", data.error);
      return;
    }
    selectedTargets = [];
    if (data.character) {
      renderCharacter(data.character);
    }
    if (data.game_state?.mode) {
      setSessionActive(true, data.game_state.mode);
    }
    if (data.combat) {
      renderCombat(data.combat);
    }
    addMessage("dm", data.narrative || "...");
  } finally {
    setLlmPending(false);
  }
}
async function sendCombatEndTurn() {
  setLlmPending(true);
  try {
    const res = await fetch("/api/combat_action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ end_turn: true }),
    });
    const data = await res.json();
    if (data.error) {
      addMessage("dm", data.error);
      return;
    }
    selectedTargets = [];
    if (data.character) {
      renderCharacter(data.character);
    }
    if (data.game_state?.mode) {
      setSessionActive(true, data.game_state.mode);
    }
    if (data.combat) {
      renderCombat(data.combat);
    }
    addMessage("dm", data.narrative || "...");
  } finally {
    setLlmPending(false);
  }
}
async function sendCombatMove(x, y) {
  setLlmPending(true);
  try {
    const res = await fetch("/api/combat_move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x, y }),
    });
    const data = await res.json();
    if (data.error) {
      addMessage("dm", data.error);
      return;
    }
    if (data.character) {
      renderCharacter(data.character);
    }
    if (data.game_state?.mode) {
      setSessionActive(true, data.game_state.mode);
    }
    if (data.combat) {
      renderCombat(data.combat);
    }
    if (data.narrative) {
      addMessage("dm", data.narrative);
    }
  } finally {
    setLlmPending(false);
  }
}
startButton.addEventListener("click", () => {
  startGame().catch((err) => {
    addMessage("dm", `Failed to start: ${err}`);
  });
});
equipmentSubmit.addEventListener("click", () => {
  submitEquipmentChoices().catch((err) => {
    equipmentErrorsEl.textContent = `Failed to start: ${err}`;
  });
});
spellSubmit.addEventListener("click", () => {
  submitSpellChoices().catch((err) => {
    spellErrorsEl.textContent = `Failed to start: ${err}`;
  });
});
spellFormEl.addEventListener("change", (event) => {
  enforceSpellChoiceLimits(event.target);
});
newGameButton.addEventListener("click", () => {
  resetUI();
});
chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const content = chatInput.value.trim();
  if (!content) {
    return;
  }
  addMessage("user", content);
  chatInput.value = "";
  sendMessage(content).catch((err) => {
    addMessage("dm", `Failed to send: ${err}`);
  });
});
sheetBody.addEventListener("click", (event) => {
  const equipBtn = event.target.closest("[data-equip-toggle]");
  if (equipBtn) {
    const itemName = equipBtn.dataset.itemName;
    const equipped = equipBtn.dataset.equipped === "true";
    toggleEquip(itemName, !equipped).catch((err) => {
      addMessage("dm", `Failed to equip: ${err}`);
    });
    return;
  }
  const resourceBtn = event.target.closest("[data-resource-use]");
  if (resourceBtn) {
    const resourceId = resourceBtn.dataset.resourceId;
    const resourceName = resourceBtn.dataset.resourceName || "Resource";
    useResource(resourceId, resourceName).catch((err) => {
      addMessage("dm", `Failed to use resource: ${err}`);
    });
    return;
  }
  const prepareBtn = event.target.closest("[data-prepare-toggle]");
  if (prepareBtn) {
    const spellName = prepareBtn.dataset.spellName;
    const prepared = prepareBtn.dataset.prepared === "true";
    togglePrepare(spellName, !prepared).catch((err) => {
      addMessage("dm", `Failed to prepare: ${err}`);
    });
    return;
  }
  const rollBtn = event.target.closest("[data-roll-action]");
  if (rollBtn) {
    const actionId = rollBtn.dataset.rollAction;
    if (state.pendingRollGlobal || state.pendingRolls.has(actionId)) {
      return;
    }
    const narrate = rollBtn.dataset.rollNarrate === "true";
    const advSelect = sheetBody.querySelector(`[data-roll-advantage="${actionId}"]`);
    const targetSelect = sheetBody.querySelector(`[data-roll-target="${actionId}"]`);
    const targetTextEl = sheetBody.querySelector(`[data-roll-target-text="${actionId}"]`);
    const advantage = advSelect ? advSelect.value : "";
    const targetIds = targetSelect
      ? Array.from(targetSelect.selectedOptions).map((opt) => opt.value)
      : [];
    const targetText = targetTextEl ? targetTextEl.value.trim() : "";
    rollAction(actionId, { advantage, targetIds, targetText, narrate }).catch((err) => {
      addMessage("dm", `Failed to roll: ${err}`);
    });
  }
});
sheetBody.addEventListener("change", (event) => {
  const spellFilter = event.target.closest("[data-spell-filter]");
  if (spellFilter) {
    spellFilterPreparedOnly = !!spellFilter.checked;
    renderCharacter(state.character);
    return;
  }
  const spellFilterLevelSelect = event.target.closest("[data-spell-filter-level]");
  if (spellFilterLevelSelect) {
    spellFilterLevel = spellFilterLevelSelect.value || "all";
    renderCharacter(state.character);
    return;
  }
  const targetSelect = event.target.closest("[data-roll-target]");
  if (targetSelect) {
    enforceMaxTargets(targetSelect);
  }
});
combatSubmit.addEventListener("click", () => {
  const actionId = combatActionSelect.value;
  const targetIds = selectedTargets.length
    ? selectedTargets
    : Array.from(combatTargetSelect.selectedOptions).map((opt) => opt.value);
  if (!actionId || targetIds.length === 0) {
    return;
  }
  const targetsLabel = targetIds.join(", ");
  addMessage("user", `${combatActionSelect.options[combatActionSelect.selectedIndex].text} → ${targetsLabel}`);
  sendCombatAction(actionId, targetIds).catch((err) => {
    addMessage("dm", `Failed to resolve action: ${err}`);
  });
});
combatEndTurn.addEventListener("click", () => {
  addMessage("user", "End Turn");
  sendCombatEndTurn().catch((err) => {
    addMessage("dm", `Failed to end turn: ${err}`);
  });
});
function handleMoveCellClick(x, y) {
  const combat = getCurrentCombatPayload();
  const playerName = combat.player_name;
  if (!combat.active || !playerName) {
    return;
  }
  if (combat.current_turn !== playerName) {
    return;
  }
  const map = combat.map;
  if (!map) {
    return;
  }
  const origin = map.tokens.find((token) => token.id === playerName);
  if (!origin) {
    return;
  }
  if (map.tokens.some((token) => token.x === x && token.y === y && token.id !== playerName)) {
    return;
  }
  const squares = Math.max(Math.abs(origin.x - x), Math.abs(origin.y - y));
  const distance = squares * (map.grid_size || 5);
  if (distance > (combat.move_remaining ?? 0)) {
    return;
  }
  addMessage("user", `Move to (${x}, ${y})`);
  sendCombatMove(x, y).catch((err) => {
    addMessage("dm", `Failed to move: ${err}`);
  });
}
sheetTabs.addEventListener("click", (event) => {
  const button = event.target.closest(".tab");
  if (!button) {
    return;
  }
  const nextTab = button.dataset.tab;
  if (!nextTab || nextTab === activeTab) {
    return;
  }
  activeTab = nextTab;
  sheetTabs.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === activeTab);
  });
  renderCharacter(state.character);
});
setSessionActive(false);
renderCharacter(null);
renderImages([]);
renderCombat({ active: false });
showSetupScreen();
function renderCombatMap(map, combat) {
  if (!map || !map.tokens) {
    combatMapEl.innerHTML = "<div class=\"muted\">Map unavailable</div>";
    return;
  }
  const currentTurn = combat?.current_turn || "";
  const playerName = combat?.player_name || "";
  const moveRemaining = combat?.move_remaining ?? 0;
  selectedTargets = selectedTargets.filter((id) => map.tokens.some((t) => t.id === id));
  const width = map.width || 12;
  const height = map.height || 8;
  combatMapEl.style.gridTemplateColumns = `repeat(${width}, 28px)`;
  combatMapEl.innerHTML = "";
  const cellIndex = {};
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const cell = document.createElement("div");
      cell.className = "combat-cell";
      cell.dataset.x = x;
      cell.dataset.y = y;
      if (playerName && currentTurn === playerName) {
        const origin = map.tokens.find((token) => token.id === playerName);
        if (origin) {
          const squares = Math.max(Math.abs(origin.x - x), Math.abs(origin.y - y));
          const distance = squares * (map.grid_size || 5);
          if (distance <= moveRemaining) {
            cell.classList.add("reachable");
          }
        }
      }
      cell.addEventListener("click", () => handleMoveCellClick(x, y));
      combatMapEl.appendChild(cell);
      cellIndex[`${x},${y}`] = cell;
    }
  }
  map.tokens.forEach((token) => {
    const cell = cellIndex[`${token.x},${token.y}`];
    if (!cell) {
      return;
    }
    const div = document.createElement("div");
    div.className = `token ${token.faction || "neutral"}`;
    div.dataset.tokenId = token.id;
    div.textContent = token.name
      ? token.name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase()
      : "?";
    div.title = token.name || token.id;
    if (token.id === currentTurn) {
      div.classList.add("active");
    }
    if (selectedTargets.includes(token.id)) {
      div.classList.add("selected");
    }
    div.addEventListener("click", () => toggleTargetSelection(token.id));
    cell.appendChild(div);
  });
}
function getSelectedAction(actions) {
  const actionId = combatActionSelect.value;
  return actions.find((action) => action.id === actionId);
}
function updateTargetingHighlights(map, actions, combat, allowedTargets = []) {
  if (!map || !map.tokens) {
    return;
  }
  const action = getSelectedAction(actions);
  const playerName = combat.player_name;
  const origin = map.tokens.find((token) => token.id === playerName);
  const targets = map.tokens.filter((token) => allowedTargets.includes(token.id));
  const validTargets = new Set();
  if (action && origin) {
    const primary = selectedTargets.length ? selectedTargets[0] : null;
    const shapeTargets = computeTargetableTokens(action, origin, targets, primary, map.grid_size || 5);
    shapeTargets.forEach((id) => validTargets.add(id));
  } else {
    targets.forEach((token) => validTargets.add(token.id));
  }
  combatTargetSelect.querySelectorAll("option").forEach((opt) => {
    opt.disabled = !validTargets.has(opt.value);
  });
  document.querySelectorAll(".token").forEach((tokenEl) => {
    const tokenId = tokenEl.dataset.tokenId;
    if (!tokenId || tokenId === playerName || !allowedTargets.includes(tokenId)) {
      return;
    }
    if (validTargets.has(tokenId)) {
      tokenEl.classList.remove("out-of-range");
    } else {
      tokenEl.classList.add("out-of-range");
      tokenEl.classList.remove("selected");
      selectedTargets = selectedTargets.filter((id) => id !== tokenId);
    }
  });
  syncTargetSelect();
}
function toggleTargetSelection(tokenId) {
  const option = combatTargetSelect.querySelector(`option[value="${tokenId}"]`);
  if (!option || option.disabled) {
    return;
  }
  const action = getSelectedAction(state.character?.actions?.actions || []);
  const maxTargets = action?.max_targets ?? null;
  if (selectedTargets.includes(tokenId)) {
    selectedTargets = selectedTargets.filter((id) => id !== tokenId);
  } else {
    if (maxTargets === 1) {
      selectedTargets = [tokenId];
    } else if (maxTargets && selectedTargets.length >= maxTargets) {
      return;
    } else {
      selectedTargets.push(tokenId);
    }
  }
  syncTargetSelect();
  const actions = state.character?.actions?.actions || [];
  const combat = getCurrentCombatPayload();
  updateTargetingHighlights(getCurrentMap(), actions, combat, combat.targets || []);
}
function syncTargetSelect() {
  combatTargetSelect.querySelectorAll("option").forEach((opt) => {
    opt.selected = selectedTargets.includes(opt.value);
  });
  document.querySelectorAll(".token").forEach((tokenEl) => {
    const tokenId = tokenEl.dataset.tokenId;
    if (tokenId && selectedTargets.includes(tokenId)) {
      tokenEl.classList.add("selected");
    } else if (tokenId) {
      tokenEl.classList.remove("selected");
    }
  });
}
function computeTargetableTokens(action, origin, targets, primaryId, gridSize) {
  const actionRange = action.range || null;
  const targeting = action.targeting || { shape: "single" };
  const shape = targeting.shape || "single";
  const originPos = { x: origin.x, y: origin.y };
  const primaryTarget = targets.find((token) => token.id === primaryId);
  if (shape === "single") {
    return targets.filter((token) => withinRange(originPos, token, actionRange, gridSize)).map((t) => t.id);
  }
  if (shape === "circle") {
    const radius = targeting.radius || actionRange;
    const center = targeting.origin === "target" && primaryTarget ? { x: primaryTarget.x, y: primaryTarget.y } : originPos;
    return targets.filter((token) => withinRange(center, token, radius, gridSize)).map((t) => t.id);
  }
  if (shape === "cone" || shape === "line") {
    const length = targeting.length || actionRange;
    if (!primaryTarget) {
      return targets.filter((token) => withinRange(originPos, token, length, gridSize)).map((t) => t.id);
    }
    return targets.filter((token) => withinLinearShape(originPos, primaryTarget, token, targeting, shape, length, gridSize)).map((t) => t.id);
  }
  return targets.map((token) => token.id);
}
function withinRange(origin, token, range, gridSize) {
  if (!range) {
    return true;
  }
  const dx = Math.abs(origin.x - token.x);
  const dy = Math.abs(origin.y - token.y);
  return Math.max(dx, dy) * gridSize <= range;
}
function withinLinearShape(origin, primary, token, targeting, shape, length, gridSize) {
  if (!length) {
    return true;
  }
  const ox = origin.x;
  const oy = origin.y;
  const fx = primary.x - ox;
  const fy = primary.y - oy;
  if (fx === 0 && fy === 0) {
    return true;
  }
  const tx = token.x - ox;
  const ty = token.y - oy;
  const dist = Math.max(Math.abs(tx), Math.abs(ty)) * gridSize;
  if (dist > length) {
    return false;
  }
  const forwardLen = Math.sqrt(fx * fx + fy * fy);
  const fxNorm = fx / forwardLen;
  const fyNorm = fy / forwardLen;
  const dot = (tx * fxNorm + ty * fyNorm);
  if (shape === "line") {
    const width = targeting.width || gridSize;
    if (dot < 0 || dot > length / gridSize) {
      return false;
    }
    const perp = Math.abs(tx * fyNorm - ty * fxNorm) * gridSize;
    return perp <= width / 2;
  }
  const angle = targeting.angle || 60;
  const half = angle / 2;
  const vLen = Math.sqrt(tx * tx + ty * ty);
  if (vLen === 0) {
    return true;
  }
  const cos = Math.max(-1, Math.min(1, (tx * fx + ty * fy) / (vLen * forwardLen)));
  const theta = Math.acos(cos) * (180 / Math.PI);
  return theta <= half;
}
function getCurrentMap() {
  return state.combat?.map || null;
}
function getCurrentCombatPayload() {
  return state.combat || {};
}
combatActionSelect.addEventListener("change", () => {
  const actions = state.character?.actions?.actions || [];
  selectedTargets = [];
  syncTargetSelect();
  const combat = getCurrentCombatPayload();
  updateTargetingHighlights(getCurrentMap(), actions, combat, combat.targets || []);
});
combatTargetSelect.addEventListener("change", () => {
  selectedTargets = Array.from(combatTargetSelect.selectedOptions).map((opt) => opt.value);
  syncTargetSelect();
});

async function toggleEquip(itemName, equipped) {
  const res = await fetch("/api/inventory/equip", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_name: itemName, equipped }),
  });
  const data = await res.json();
  if (data.error) {
    addMessage("dm", data.error);
    return;
  }
  if (data.character) {
    renderCharacter(data.character);
  }
  if (data.combat) {
    renderCombat(data.combat);
  }
}

async function togglePrepare(spellName, prepared) {
  const res = await fetch("/api/spells/prepare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ spell_name: spellName, prepared }),
  });
  const data = await res.json();
  if (data.error) {
    addMessage("dm", data.error);
    return;
  }
  if (data.character) {
    renderCharacter(data.character);
  }
  if (data.combat) {
    renderCombat(data.combat);
  }
}

async function rollAction(actionId, options = {}) {
  setRollPending(actionId, true);
  const shouldShowThinking = !!options.narrate;
  if (shouldShowThinking) {
    setLlmPending(true);
  }
  try {
    const payload = {
      action_id: actionId,
      advantage: options.advantage || null,
      target_ids: options.targetIds || [],
      target_text: options.targetText || null,
      narrate: !!options.narrate,
    };
    const res = await fetch("/api/action/roll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.error) {
      addMessage("dm", data.error);
      return;
    }
    if (data.result?.summary) {
      addMessage("user", data.result.summary);
    } else {
      addMessage("user", `Rolled ${actionId}.`);
    }
    if (data.result) {
      state.actionRolls[actionId] = data.result;
    }
    if (data.narrative) {
      addMessage("dm", data.narrative);
    }
    if (data.character) {
      renderCharacter(data.character);
    }
    if (data.combat) {
      renderCombat(data.combat);
    }
  } finally {
    if (shouldShowThinking) {
      setLlmPending(false);
    }
    setRollPending(actionId, false);
  }
}

async function useResource(resourceId, resourceName) {
  if (!resourceId) {
    return;
  }
  const res = await fetch("/api/resource/use", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resource_id: resourceId, amount: 1 }),
  });
  const data = await res.json();
  if (data.error) {
    addMessage("dm", data.error);
    return;
  }
  addMessage("user", `Use ${resourceName}`);
  addMessage("dm", `${resourceName} used.`);
  if (data.character) {
    renderCharacter(data.character);
  }
  if (data.combat) {
    renderCombat(data.combat);
  }
}
