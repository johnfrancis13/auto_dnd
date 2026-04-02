import { appState, uiState } from "./state.js";
import {
  messagesEl,
  charForm,
  equipmentErrorsEl,
  languageErrorsEl,
  spellErrorsEl,
  sheetTabs,
  thinkingIndicator,
} from "./dom.js";
import { addMessage, setLlmPending, setSessionActive, showGameScreen, showSetupScreen } from "./ui.js";
import { renderCharacter, renderImages } from "./render.js";
import { renderCombat } from "./combat.js";
import {
  renderEquipmentChoices,
  renderLanguageChoices,
  renderSpellChoices,
  collectEquipmentSelections,
  collectLanguageSelections,
  collectSpellSelections,
} from "./forms.js";
import { setRollPending } from "./rolls.js";

export async function resetUI() {
  appState.session = false;
  appState.character = null;
  appState.actionRolls = {};
  appState.pendingRolls = new Set();
  appState.pendingRollGlobal = false;
  messagesEl.innerHTML = "";
  uiState.activeTab = "about";
  uiState.pendingStartPayload = null;
  uiState.llmPendingCount = 0;
  if (thinkingIndicator) {
    thinkingIndicator.classList.add("hidden");
  }
  renderEquipmentChoices([]);
  renderLanguageChoices([]);
  renderSpellChoices([]);
  sheetTabs.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === uiState.activeTab);
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

export async function startGame() {
  setLlmPending(true);
  const formData = new FormData(charForm);
  const payload = {
    character: Object.fromEntries(formData.entries()),
    model_name: "qwen3:8b",
    think: false,
  };
  try {
    uiState.pendingStartPayload = payload;
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
    if (data.requires_language_choices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      renderLanguageChoices(data.language_choices);
      languageErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
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
    appState.session = data.session;
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

export async function submitEquipmentChoices() {
  if (!uiState.pendingStartPayload) {
    return;
  }
  const equipmentChoices = collectEquipmentSelections();
  renderEquipmentChoices([]);
  const payload = {
    ...uiState.pendingStartPayload,
    equipment_choices: equipmentChoices,
  };
  uiState.pendingStartPayload = payload;
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
    if (data.requires_language_choices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      renderLanguageChoices(data.language_choices);
      languageErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
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
    appState.session = data.session;
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

export async function submitSpellChoices() {
  if (!uiState.pendingStartPayload) {
    return;
  }
  const spellChoices = collectSpellSelections();
  renderSpellChoices([]);
  const payload = {
    ...uiState.pendingStartPayload,
    spell_choices: spellChoices,
  };
  uiState.pendingStartPayload = payload;
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
    if (data.requires_language_choices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      renderLanguageChoices(data.language_choices);
      languageErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
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
      spellErrorsEl.textContent = data.error || "Unable to start session.";
      setSessionActive(false);
      showSetupScreen();
      return;
    }
    appState.session = data.session;
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

export async function submitLanguageChoices() {
  if (!uiState.pendingStartPayload) {
    return;
  }
  const languageChoices = collectLanguageSelections();
  renderLanguageChoices([]);
  const payload = {
    ...uiState.pendingStartPayload,
    language_choices: languageChoices,
  };
  uiState.pendingStartPayload = payload;
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
    if (data.requires_language_choices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      renderLanguageChoices(data.language_choices);
      languageErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
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
      languageErrorsEl.textContent = data.error || "Unable to start session.";
      setSessionActive(false);
      showSetupScreen();
      return;
    }
    appState.session = data.session;
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

export async function sendMessage(content) {
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
    appState.session = true;
    if (data.narrative) {
      addMessage("dm", data.narrative);
    }
    if (data.character) {
      renderCharacter(data.character);
    }
    if (data.combat) {
      renderCombat(data.combat);
    }
    if (data.game_state) {
      setSessionActive(true, data.game_state.mode || "exploration");
    }
    if (data.images) {
      renderImages(data.images);
    }
  } finally {
    setLlmPending(false);
  }
}

export async function sendCombatAction(actionId, targetIds) {
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
  if (data.narrative) {
    addMessage("dm", data.narrative);
  }
  if (data.character) {
    renderCharacter(data.character);
  }
  if (data.combat) {
    renderCombat(data.combat);
  }
  if (data.game_state) {
    setSessionActive(true, data.game_state.mode || "exploration");
  }
}

export async function sendCombatEndTurn() {
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
  if (data.narrative) {
    addMessage("dm", data.narrative);
  }
  if (data.character) {
    renderCharacter(data.character);
  }
  if (data.combat) {
    renderCombat(data.combat);
  }
  if (data.game_state) {
    setSessionActive(true, data.game_state.mode || "exploration");
  }
}

export async function sendCombatMove(x, y) {
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
  if (data.narrative) {
    addMessage("dm", data.narrative);
  }
  if (data.character) {
    renderCharacter(data.character);
  }
  if (data.combat) {
    renderCombat(data.combat);
  }
  if (data.game_state) {
    setSessionActive(true, data.game_state.mode || "exploration");
  }
}

export async function toggleEquip(itemName, equipped) {
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

export async function togglePrepare(spellName, prepared) {
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

export async function rollAction(actionId, options = {}) {
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
      appState.actionRolls[actionId] = data.result;
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

export async function useResource(resourceId, resourceName) {
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
