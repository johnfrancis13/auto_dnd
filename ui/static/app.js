const state = {
  session: false,
  character: null,
  combat: null,
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
const equipmentModal = document.getElementById("equipment-modal");
const equipmentFormEl = document.getElementById("equipment-choices-form");
const equipmentSubmit = document.getElementById("equipment-choices-submit");
const equipmentErrorsEl = document.getElementById("equipment-choices-errors");
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
      <details class="entry">
        <summary><strong>${item.name}</strong></summary>
        <div class="detail-body">
          <div>${item.type || "Item"}${item.subtype ? ` · ${item.subtype}` : ""}${item.rarity ? ` · ${item.rarity}` : ""}</div>
          <div>Qty: ${item.quantity}</div>
        </div>
      </details>
    `).join("")}
  `;

  const resourceList = [
    ...character.actions.resources.custom,
    ...character.actions.resources.spell_slots,
    ...character.actions.resources.spell_access,
  ];

  const actionsHtml = `
    <h3>Actions</h3>
    ${character.actions.actions.length === 0 ? "<p>No actions.</p>" : character.actions.actions.map(action => `
      <details class="entry">
        <summary><strong>${action.name}</strong></summary>
        <div class="detail-body">
          <div>${action.type} ${action.source ? `· ${action.source}` : ""}</div>
          ${action.proficiency_type ? `<div>Proficiency: ${action.proficiency_type}</div>` : ""}
        </div>
      </details>
    `).join("")}
    <h3>Resources</h3>
    ${resourceList.length === 0 ? "<p>No resources.</p>" : resourceList.map(res => `
      <details class="entry">
        <summary><strong>${res.name}</strong></summary>
        <div class="detail-body">
          <div>${res.category} · ${res.recharge} · ${res.source || "Unknown"}</div>
          <div>${res.current}/${res.maximum}</div>
        </div>
      </details>
    `).join("")}
  `;

  const spellsHtml = `
    <h3>Spellcasting</h3>
    <div class="entry">
      <div class="muted">Ability: ${character.spells.spellcasting_ability || "Unknown"}</div>
      <div class="muted">Save DC: ${character.spells.spell_save_dc || "Unknown"}</div>
    </div>
    <h3>Known Spells</h3>
    ${character.spells.known.length === 0 ? "<p>No known spells.</p>" : character.spells.known.map(spell => `
      <details class="entry">
        <summary><strong>${spell.name}</strong></summary>
        <div class="detail-body">
          <div>Level ${spell.level} · ${spell.school}</div>
          <div>${spell.cast_time} · ${spell.range} · ${spell.duration}</div>
        </div>
      </details>
    `).join("")}
    <h3>Prepared Spells</h3>
    ${character.spells.prepared.length === 0 ? "<p>No prepared spells.</p>" : character.spells.prepared.map(spell => `
      <details class="entry">
        <summary><strong>${spell.name}</strong></summary>
        <div class="detail-body">
          <div>Level ${spell.level} · ${spell.school}</div>
          <div>${spell.cast_time} · ${spell.range} · ${spell.duration}</div>
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

async function resetUI() {
  state.session = false;
  state.character = null;
  messagesEl.innerHTML = "";
  activeTab = "about";
  pendingStartPayload = null;
  renderEquipmentChoices([]);
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
  const formData = new FormData(charForm);
  const payload = {
    character: Object.fromEntries(formData.entries()),
    model_name: "qwen3:8b",
    think: false,
  };
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
}

async function sendMessage(content) {
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
}

async function sendCombatAction(actionId, targetIds) {
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
}

async function sendCombatEndTurn() {
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
}

async function sendCombatMove(x, y) {
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
