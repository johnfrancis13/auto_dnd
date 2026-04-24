import { appState, uiState } from "./state.js";
import {
  messagesEl,
  charForm,
  equipmentErrorsEl,
  proficiencyErrorsEl,
  languageErrorsEl,
  spellErrorsEl,
  startErrorsEl,
  sheetTabs,
  thinkingIndicator,
} from "./dom.js";
import { addMessage, addCombatLogEntries, setLlmPending, setSessionActive, showGameScreen, showSetupScreen } from "./ui.js";
import { renderCharacter, renderImages } from "./render.js";
import { renderCombat } from "./combat.js";
import {
  renderEquipmentChoices,
  validateEquipmentSelections,
  renderProficiencyChoices,
  renderLanguageChoices,
  renderSpellChoices,
  collectEquipmentSelections,
  collectProficiencySelections,
  collectLanguageSelections,
  collectSpellSelections,
} from "./forms.js";
import { setRollPending } from "./rolls.js";

function syncRollRequest(data) {
  if (!data || !Object.prototype.hasOwnProperty.call(data, "roll_request")) {
    return;
  }
  appState.pendingRollRequest = data.roll_request || null;
}

function applySessionResponse(data, options = {}) {
  const {
    markSession = false,
    announceRollRequest = true,
  } = options;

  if (!data) {
    return;
  }
  if (markSession) {
    appState.session = true;
  }
  syncRollRequest(data);
  const incomingRequestId = String(data?.roll_request?.request_id || "");
  const shouldAnnounce =
    announceRollRequest &&
    data.roll_request &&
    (!incomingRequestId || incomingRequestId !== appState.lastAnnouncedRollRequestId);
  if (shouldAnnounce) {
    addMessage("dm", formatRollRequest(data.roll_request));
    if (incomingRequestId) {
      appState.lastAnnouncedRollRequestId = incomingRequestId;
    }
  }
  if (data.combat_log) {
    addCombatLogEntries(data.combat_log, data.combat_log_meta);
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
  if (data.images) {
    renderImages(data.images);
  }
}

async function executeIntent(payload) {
  const res = await fetch("/api/intent/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

function formatRollRequest(request) {
  if (!request) {
    return "";
  }
  if (request.type === "skill") {
    return `Roll requested: ${String(request.skill || "").replace(/_/g, " ")} skill check. Resolve it in the Abilities tab.`;
  }
  if (request.type === "ability") {
    return `Roll requested: ${request.ability || "Ability"} ability check. Resolve it in the Abilities tab.`;
  }
  if (request.type === "save") {
    return `Roll requested: ${request.ability || "Ability"} saving throw. Resolve it in the Abilities tab.`;
  }
  if (request.type === "initiative") {
    return "Roll requested: initiative. Resolve it in the Abilities tab.";
  }
  return "A roll was requested.";
}

function logClient(message, data = {}, level = "info") {
  try {
    const payload = JSON.stringify({ message, data, level });
    if (navigator.sendBeacon) {
      const blob = new Blob([payload], { type: "application/json" });
      const ok = navigator.sendBeacon("/api/log", blob);
      if (ok) {
        return;
      }
    }
    fetch("/api/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
      keepalive: true,
    }).catch(() => {});
  } catch (err) {
    console.warn("Failed to send client log", err);
  }
}

export async function resetUI() {
  appState.session = false;
  appState.character = null;
  appState.actionRolls = {};
  appState.pendingRollRequest = null;
  appState.lastAnnouncedRollRequestId = null;
  appState.pendingRolls = new Set();
  appState.pendingRollGlobal = false;
  messagesEl.innerHTML = "";
  uiState.activeTab = "about";
  uiState.pendingStartPayload = null;
  uiState.llmPendingCount = 0;
  if (thinkingIndicator) {
    thinkingIndicator.classList.add("hidden");
  }
  if (startErrorsEl) {
    startErrorsEl.textContent = "";
  }
  renderEquipmentChoices([]);
  renderProficiencyChoices([]);
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

export async function checkPendingChoices() {
  try {
    const res = await fetch("/api/pending");
    const data = await res.json();
    if (!data || !data.pending) {
      return;
    }
    if (data.requires_proficiency_choices && Array.isArray(data.proficiency_choices)) {
      renderProficiencyChoices(data.proficiency_choices);
      showSetupScreen();
      return;
    }
    if (data.requires_language_choices && Array.isArray(data.language_choices)) {
      renderLanguageChoices(data.language_choices);
      showSetupScreen();
      return;
    }
    if (data.requires_spell_choices && Array.isArray(data.spell_choices)) {
      renderSpellChoices(data.spell_choices);
      showSetupScreen();
    }
  } catch (err) {
    console.warn("Failed to check pending choices", err);
  }
}

function beginStartLoading(message = "Starting adventure...") {
  showGameScreen();
  messagesEl.innerHTML = "";
  renderCharacter(null);
  renderImages([]);
  renderCombat({ active: false });
  setSessionActive(true, "exploration");
  addMessage("dm", message);
}

export async function startGame() {
  setLlmPending(true);
  const formData = new FormData(charForm);
  const payload = {
    character: Object.fromEntries(formData.entries()),
    model_name: "igorls/gemma-4-E4B-it-heretic-GGUF:Q6_K",
    think: false,
  };
  try {
    logClient("StartGame: submit", {
      character: payload.character,
    });
    uiState.pendingStartPayload = payload;
    if (startErrorsEl) {
      startErrorsEl.textContent = "";
    }
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    logClient("StartGame: response status", { status: res.status, ok: res.ok });
    const data = await res.json();
    logClient("StartGame: response data", {
      keys: Object.keys(data || {}),
      requires_choices: !!data.requires_choices,
      requires_proficiency_choices: !!data.requires_proficiency_choices,
      requires_language_choices: !!data.requires_language_choices,
      requires_spell_choices: !!data.requires_spell_choices,
      choices_len: Array.isArray(data.choices) ? data.choices.length : 0,
      proficiency_len: Array.isArray(data.proficiency_choices) ? data.proficiency_choices.length : 0,
      language_len: Array.isArray(data.language_choices) ? data.language_choices.length : 0,
      spell_len: Array.isArray(data.spell_choices) ? data.spell_choices.length : 0,
      session: !!data.session,
      error: data.error || null,
    });
    console.log("Start response", data);
    const hasEquipmentChoices = Array.isArray(data.choices) && data.choices.length > 0;
    const hasProficiencyChoices = Array.isArray(data.proficiency_choices) && data.proficiency_choices.length > 0;
    const hasLanguageChoices = Array.isArray(data.language_choices) && data.language_choices.length > 0;
    const hasSpellChoices = Array.isArray(data.spell_choices) && data.spell_choices.length > 0;
    if (
      data.requires_choices ||
      data.requires_proficiency_choices ||
      data.requires_language_choices ||
      data.requires_spell_choices ||
      hasEquipmentChoices ||
      hasProficiencyChoices ||
      hasLanguageChoices ||
      hasSpellChoices
    ) {
      console.warn("Start response requires additional choices.", {
        requires_choices: !!data.requires_choices,
        requires_proficiency_choices: !!data.requires_proficiency_choices,
        requires_language_choices: !!data.requires_language_choices,
        requires_spell_choices: !!data.requires_spell_choices,
      });
    }
    if (data.requires_choices || hasEquipmentChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Starting equipment choices required.";
      }
      if (!hasEquipmentChoices) {
        equipmentErrorsEl.textContent = "Equipment choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderEquipmentChoices(data.choices);
      equipmentErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_proficiency_choices || hasProficiencyChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Class proficiency choices required.";
      }
      if (!hasProficiencyChoices) {
        proficiencyErrorsEl.textContent = "Proficiency choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderProficiencyChoices(data.proficiency_choices);
      proficiencyErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_language_choices || hasLanguageChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Language choices required.";
      }
      if (!hasLanguageChoices) {
        languageErrorsEl.textContent = "Language choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderLanguageChoices(data.language_choices);
      languageErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_spell_choices || hasSpellChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Spell choices required.";
      }
      if (!hasSpellChoices) {
        spellErrorsEl.textContent = "Spell choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderSpellChoices(data.spell_choices);
      spellErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (!data.session) {
      equipmentErrorsEl.textContent = data.error || "Unable to start session.";
      if (startErrorsEl) {
        startErrorsEl.textContent = data.error || "Unable to start session.";
      }
      setSessionActive(false);
      showSetupScreen();
      await checkPendingChoices();
      return;
    }
    appState.session = data.session;
    messagesEl.innerHTML = "";
    renderCharacter(data.character);
    renderImages(data.images);
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
  if (!uiState.pendingEquipmentChoices || uiState.pendingEquipmentChoices.length === 0) {
    console.warn("No pending equipment choices at submit time.");
    if (startErrorsEl) {
      startErrorsEl.textContent = "No equipment choices were loaded. Please restart the flow.";
    }
    return;
  }
  const validation = validateEquipmentSelections();
  if (!validation.ok) {
    equipmentErrorsEl.textContent = validation.errors.join(" ");
    if (startErrorsEl) {
      startErrorsEl.textContent = "Please finish all equipment selections.";
    }
    return;
  }
  const checkedInputs = Array.from(
    document.querySelectorAll("#equipment-choices-form input:checked")
  ).map((el) => `${el.name}=${el.value}`);
  console.log("Equipment checked inputs", checkedInputs);
  const equipmentChoices = collectEquipmentSelections();
  console.log("Equipment choices payload", equipmentChoices);
  renderEquipmentChoices([]);
  const payload = {
    ...uiState.pendingStartPayload,
    equipment_choices: equipmentChoices,
  };
  uiState.pendingStartPayload = payload;
  if (startErrorsEl) {
    startErrorsEl.textContent = "";
  }
  beginStartLoading();
  setLlmPending(true);
  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    logClient("EquipmentSubmit: response status", { status: res.status, ok: res.ok });
    const data = await res.json();
    logClient("EquipmentSubmit: response data", {
      keys: Object.keys(data || {}),
      requires_choices: !!data.requires_choices,
      requires_proficiency_choices: !!data.requires_proficiency_choices,
      requires_language_choices: !!data.requires_language_choices,
      requires_spell_choices: !!data.requires_spell_choices,
      choices_len: Array.isArray(data.choices) ? data.choices.length : 0,
      proficiency_len: Array.isArray(data.proficiency_choices) ? data.proficiency_choices.length : 0,
      language_len: Array.isArray(data.language_choices) ? data.language_choices.length : 0,
      spell_len: Array.isArray(data.spell_choices) ? data.spell_choices.length : 0,
      session: !!data.session,
      error: data.error || null,
    });
    console.log("Start response (equipment)", data);
    const hasEquipmentChoices = Array.isArray(data.choices) && data.choices.length > 0;
    const hasProficiencyChoices = Array.isArray(data.proficiency_choices) && data.proficiency_choices.length > 0;
    const hasLanguageChoices = Array.isArray(data.language_choices) && data.language_choices.length > 0;
    const hasSpellChoices = Array.isArray(data.spell_choices) && data.spell_choices.length > 0;
    if (
      data.requires_choices ||
      data.requires_proficiency_choices ||
      data.requires_language_choices ||
      data.requires_spell_choices ||
      hasEquipmentChoices ||
      hasProficiencyChoices ||
      hasLanguageChoices ||
      hasSpellChoices
    ) {
      console.warn("Start response requires additional choices.", {
        requires_choices: !!data.requires_choices,
        requires_proficiency_choices: !!data.requires_proficiency_choices,
        requires_language_choices: !!data.requires_language_choices,
        requires_spell_choices: !!data.requires_spell_choices,
      });
    }
    if (data.requires_choices || hasEquipmentChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = data.errors
          ? `Starting equipment choices required: ${data.errors.join(" ")}`
          : "Starting equipment choices required.";
      }
      if (!hasEquipmentChoices) {
        equipmentErrorsEl.textContent = "Equipment choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderEquipmentChoices(data.choices);
      equipmentErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_proficiency_choices || hasProficiencyChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Class proficiency choices required.";
      }
      if (!hasProficiencyChoices) {
        proficiencyErrorsEl.textContent = "Proficiency choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderProficiencyChoices(data.proficiency_choices);
      proficiencyErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_language_choices || hasLanguageChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Language choices required.";
      }
      if (!hasLanguageChoices) {
        languageErrorsEl.textContent = "Language choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderLanguageChoices(data.language_choices);
      languageErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_spell_choices || hasSpellChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Spell choices required.";
      }
      if (!hasSpellChoices) {
        spellErrorsEl.textContent = "Spell choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderSpellChoices(data.spell_choices);
      spellErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (!data.session) {
      equipmentErrorsEl.textContent = data.error || "Unable to start session.";
      if (startErrorsEl) {
        startErrorsEl.textContent = data.error || "Unable to start session.";
      }
      setSessionActive(false);
      showSetupScreen();
      await checkPendingChoices();
      return;
    }
    renderEquipmentChoices([]);
    appState.session = data.session;
    messagesEl.innerHTML = "";
    renderCharacter(data.character);
    renderImages(data.images);
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
  if (startErrorsEl) {
    startErrorsEl.textContent = "";
  }
  beginStartLoading();
  setLlmPending(true);
  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    console.log("Start response (spells)", data);
    const hasEquipmentChoices = Array.isArray(data.choices) && data.choices.length > 0;
    const hasProficiencyChoices = Array.isArray(data.proficiency_choices) && data.proficiency_choices.length > 0;
    const hasLanguageChoices = Array.isArray(data.language_choices) && data.language_choices.length > 0;
    const hasSpellChoices = Array.isArray(data.spell_choices) && data.spell_choices.length > 0;
    if (
      data.requires_choices ||
      data.requires_proficiency_choices ||
      data.requires_language_choices ||
      data.requires_spell_choices ||
      hasEquipmentChoices ||
      hasProficiencyChoices ||
      hasLanguageChoices ||
      hasSpellChoices
    ) {
      console.warn("Start response requires additional choices.", {
        requires_choices: !!data.requires_choices,
        requires_proficiency_choices: !!data.requires_proficiency_choices,
        requires_language_choices: !!data.requires_language_choices,
        requires_spell_choices: !!data.requires_spell_choices,
      });
    }
    if (data.requires_language_choices || hasLanguageChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Language choices required.";
      }
      if (!hasLanguageChoices) {
        languageErrorsEl.textContent = "Language choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderLanguageChoices(data.language_choices);
      languageErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_proficiency_choices || hasProficiencyChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Class proficiency choices required.";
      }
      if (!hasProficiencyChoices) {
        proficiencyErrorsEl.textContent = "Proficiency choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderProficiencyChoices(data.proficiency_choices);
      proficiencyErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_spell_choices || hasSpellChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Spell choices required.";
      }
      if (!hasSpellChoices) {
        spellErrorsEl.textContent = "Spell choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderSpellChoices(data.spell_choices);
      spellErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (!data.session) {
      spellErrorsEl.textContent = data.error || "Unable to start session.";
      if (startErrorsEl) {
        startErrorsEl.textContent = data.error || "Unable to start session.";
      }
      setSessionActive(false);
      showSetupScreen();
      await checkPendingChoices();
      return;
    }
    appState.session = data.session;
    messagesEl.innerHTML = "";
    renderCharacter(data.character);
    renderImages(data.images);
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
  if (startErrorsEl) {
    startErrorsEl.textContent = "";
  }
  beginStartLoading();
  setLlmPending(true);
  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    console.log("Start response (languages)", data);
    const hasEquipmentChoices = Array.isArray(data.choices) && data.choices.length > 0;
    const hasProficiencyChoices = Array.isArray(data.proficiency_choices) && data.proficiency_choices.length > 0;
    const hasLanguageChoices = Array.isArray(data.language_choices) && data.language_choices.length > 0;
    const hasSpellChoices = Array.isArray(data.spell_choices) && data.spell_choices.length > 0;
    if (
      data.requires_choices ||
      data.requires_proficiency_choices ||
      data.requires_language_choices ||
      data.requires_spell_choices ||
      hasEquipmentChoices ||
      hasProficiencyChoices ||
      hasLanguageChoices ||
      hasSpellChoices
    ) {
      console.warn("Start response requires additional choices.", {
        requires_choices: !!data.requires_choices,
        requires_proficiency_choices: !!data.requires_proficiency_choices,
        requires_language_choices: !!data.requires_language_choices,
        requires_spell_choices: !!data.requires_spell_choices,
      });
    }
    if (data.requires_language_choices || hasLanguageChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Language choices required.";
      }
      if (!hasLanguageChoices) {
        languageErrorsEl.textContent = "Language choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderLanguageChoices(data.language_choices);
      languageErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_proficiency_choices || hasProficiencyChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Class proficiency choices required.";
      }
      if (!hasProficiencyChoices) {
        proficiencyErrorsEl.textContent = "Proficiency choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderProficiencyChoices(data.proficiency_choices);
      proficiencyErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_spell_choices || hasSpellChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Spell choices required.";
      }
      if (!hasSpellChoices) {
        spellErrorsEl.textContent = "Spell choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderSpellChoices(data.spell_choices);
      spellErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (!data.session) {
      languageErrorsEl.textContent = data.error || "Unable to start session.";
      if (startErrorsEl) {
        startErrorsEl.textContent = data.error || "Unable to start session.";
      }
      setSessionActive(false);
      showSetupScreen();
      await checkPendingChoices();
      return;
    }
    appState.session = data.session;
    messagesEl.innerHTML = "";
    renderCharacter(data.character);
    renderImages(data.images);
    addMessage("dm", data.narrative || "Adventure started.");
    setSessionActive(true, data.game_state?.mode || "exploration");
    renderCombat(data.combat);
    showGameScreen();
  } finally {
    setLlmPending(false);
  }
}

export async function submitProficiencyChoices() {
  if (!uiState.pendingStartPayload) {
    return;
  }
  const proficiencyChoices = collectProficiencySelections();
  renderProficiencyChoices([]);
  const payload = {
    ...uiState.pendingStartPayload,
    proficiency_choices: proficiencyChoices,
  };
  uiState.pendingStartPayload = payload;
  if (startErrorsEl) {
    startErrorsEl.textContent = "";
  }
  beginStartLoading();
  setLlmPending(true);
  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    console.log("Start response (proficiencies)", data);
    const hasEquipmentChoices = Array.isArray(data.choices) && data.choices.length > 0;
    const hasProficiencyChoices = Array.isArray(data.proficiency_choices) && data.proficiency_choices.length > 0;
    const hasLanguageChoices = Array.isArray(data.language_choices) && data.language_choices.length > 0;
    const hasSpellChoices = Array.isArray(data.spell_choices) && data.spell_choices.length > 0;
    if (
      data.requires_choices ||
      data.requires_proficiency_choices ||
      data.requires_language_choices ||
      data.requires_spell_choices ||
      hasEquipmentChoices ||
      hasProficiencyChoices ||
      hasLanguageChoices ||
      hasSpellChoices
    ) {
      console.warn("Start response requires additional choices.", {
        requires_choices: !!data.requires_choices,
        requires_proficiency_choices: !!data.requires_proficiency_choices,
        requires_language_choices: !!data.requires_language_choices,
        requires_spell_choices: !!data.requires_spell_choices,
      });
    }
    if (data.requires_proficiency_choices || hasProficiencyChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Class proficiency choices required.";
      }
      if (!hasProficiencyChoices) {
        proficiencyErrorsEl.textContent = "Proficiency choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderProficiencyChoices(data.proficiency_choices);
      proficiencyErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_language_choices || hasLanguageChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Language choices required.";
      }
      if (!hasLanguageChoices) {
        languageErrorsEl.textContent = "Language choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderLanguageChoices(data.language_choices);
      languageErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (data.requires_spell_choices || hasSpellChoices) {
      messagesEl.innerHTML = "";
      setSessionActive(false);
      if (startErrorsEl) {
        startErrorsEl.textContent = "Spell choices required.";
      }
      if (!hasSpellChoices) {
        spellErrorsEl.textContent = "Spell choices were required but not provided. Please restart.";
        showSetupScreen();
        return;
      }
      renderSpellChoices(data.spell_choices);
      spellErrorsEl.textContent = data.errors ? data.errors.join(" ") : "";
      showSetupScreen();
      return;
    }
    if (!data.session) {
      proficiencyErrorsEl.textContent = data.error || "Unable to start session.";
      if (startErrorsEl) {
        startErrorsEl.textContent = data.error || "Unable to start session.";
      }
      setSessionActive(false);
      showSetupScreen();
      await checkPendingChoices();
      return;
    }
    appState.session = data.session;
    messagesEl.innerHTML = "";
    renderCharacter(data.character);
    renderImages(data.images);
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
    applySessionResponse(data, { markSession: true });
  } finally {
    setLlmPending(false);
  }
}

export async function regenerateSceneImage() {
  setLlmPending(true);
  try {
    const res = await fetch("/api/images/regenerate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const data = await res.json();
    if (data.error) {
      addMessage("dm", data.error);
      return;
    }
    if (data.images) {
      renderImages(data.images);
    }
    if (data.message) {
      addMessage("dm", data.message);
    }
  } finally {
    setLlmPending(false);
  }
}

export async function sendCombatAction(actionId, targetIds) {
  setLlmPending(true);
  try {
    const data = await executeIntent({
      intent_type: "action",
      action_id: actionId,
      target_ids: targetIds,
    });
    if (data.error) {
      addMessage("dm", data.error);
      return;
    }
    applySessionResponse(data);
  } finally {
    setLlmPending(false);
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
  applySessionResponse(data);
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
  applySessionResponse(data);
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
  setLlmPending(true);
  try {
    const data = await executeIntent({
      intent_type: "action",
      action_id: actionId,
      advantage: options.advantage || null,
      target_ids: options.targetIds || [],
      target_text: options.targetText || null,
      player_text: options.playerText || null,
    });
    if (data.error) {
      addMessage("dm", data.error);
      return;
    }
    if (data.result?.summary) {
      addMessage("user", data.result.summary);
    } else {
      addMessage("user", `Executed ${actionId}.`);
    }
    if (data.result) {
      appState.actionRolls[actionId] = data.result;
    }
    applySessionResponse(data);
  } finally {
    setLlmPending(false);
    setRollPending(actionId, false);
  }
}

export async function executeCheck(checkType, options = {}) {
  const pendingKey = `check_${checkType}`;
  setRollPending(pendingKey, true);
  setLlmPending(true);
  try {
    const data = await executeIntent({
      intent_type: "check",
      check_type: checkType,
      skill: options.skill || null,
      ability: options.ability || null,
      advantage: options.advantage || null,
      player_text: options.playerText || null,
      expected_request_id: appState.pendingRollRequest?.request_id || null,
    });
    if (data.error) {
      addMessage("dm", data.error);
      return;
    }
    if (data.result) {
      const result = data.result;
      const label = result.check_type === "skill"
        ? `${result.skill} check`
        : result.check_type === "initiative"
          ? "initiative"
          : `${result.ability} ${result.check_type}`;
      addMessage("user", `[CHECK] ${label}: ${result.total}`);
      appState.actionRolls[pendingKey] = result;
    }
    applySessionResponse(data);
  } finally {
    setLlmPending(false);
    setRollPending(pendingKey, false);
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
