import { appState, uiState } from "./state.js";
import {
  startButton,
  equipmentSubmit,
  languageSubmit,
  spellSubmit,
  spellFormEl,
  languageFormEl,
  newGameButton,
  chatForm,
  chatInput,
  sheetBody,
  sheetTabs,
  combatSubmit,
  combatEndTurn,
  combatActionSelect,
  combatTargetSelect,
} from "./dom.js";
import { addMessage, setSessionActive, showSetupScreen } from "./ui.js";
import { renderCharacter, renderImages } from "./render.js";
import {
  renderCombat,
  setMoveHandler,
  getCurrentCombatPayload,
  getCurrentMap,
  updateTargetingHighlights,
  syncTargetSelect,
} from "./combat.js";
import { enforceSpellChoiceLimits, enforceLanguageChoiceLimits } from "./forms.js";
import { enforceMaxTargets } from "./rolls.js";
import {
  resetUI,
  startGame,
  submitEquipmentChoices,
  submitLanguageChoices,
  submitSpellChoices,
  sendMessage,
  sendCombatAction,
  sendCombatEndTurn,
  sendCombatMove,
  toggleEquip,
  togglePrepare,
  rollAction,
  useResource,
} from "./api.js";

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

export function boot() {
  setMoveHandler(handleMoveCellClick);

  startButton.addEventListener("click", () => {
    startGame().catch((err) => {
      addMessage("dm", `Failed to start: ${err}`);
    });
  });
  equipmentSubmit.addEventListener("click", () => {
    submitEquipmentChoices().catch((err) => {
      addMessage("dm", `Failed to start: ${err}`);
    });
  });
  languageSubmit.addEventListener("click", () => {
    submitLanguageChoices().catch((err) => {
      addMessage("dm", `Failed to start: ${err}`);
    });
  });
  spellSubmit.addEventListener("click", () => {
    submitSpellChoices().catch((err) => {
      addMessage("dm", `Failed to start: ${err}`);
    });
  });
  spellFormEl.addEventListener("change", (event) => {
    enforceSpellChoiceLimits(event.target);
  });
  languageFormEl.addEventListener("change", (event) => {
    enforceLanguageChoiceLimits(event.target);
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
      if (appState.pendingRollGlobal || appState.pendingRolls.has(actionId)) {
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
      uiState.spellFilterPreparedOnly = !!spellFilter.checked;
      renderCharacter(appState.character);
      return;
    }
    const spellFilterLevelSelect = event.target.closest("[data-spell-filter-level]");
    if (spellFilterLevelSelect) {
      uiState.spellFilterLevel = spellFilterLevelSelect.value || "all";
      renderCharacter(appState.character);
      return;
    }
    const targetSelect = event.target.closest("[data-roll-target]");
    if (targetSelect) {
      enforceMaxTargets(targetSelect);
    }
  });
  combatSubmit.addEventListener("click", () => {
    const actionId = combatActionSelect.value;
    const targetIds = uiState.selectedTargets.length
      ? uiState.selectedTargets
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
  sheetTabs.addEventListener("click", (event) => {
    const button = event.target.closest(".tab");
    if (!button) {
      return;
    }
    const nextTab = button.dataset.tab;
    if (!nextTab || nextTab === uiState.activeTab) {
      return;
    }
    uiState.activeTab = nextTab;
    sheetTabs.querySelectorAll(".tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.tab === uiState.activeTab);
    });
    renderCharacter(appState.character);
  });
  combatActionSelect.addEventListener("change", () => {
    const actions = appState.character?.actions?.actions || [];
    uiState.selectedTargets = [];
    syncTargetSelect();
    const combat = getCurrentCombatPayload();
    updateTargetingHighlights(getCurrentMap(), actions, combat, combat.targets || []);
  });
  combatTargetSelect.addEventListener("change", () => {
    uiState.selectedTargets = Array.from(combatTargetSelect.selectedOptions).map((opt) => opt.value);
    syncTargetSelect();
  });

  setSessionActive(false);
  renderCharacter(null);
  renderImages([]);
  renderCombat({ active: false });
  showSetupScreen();
}
