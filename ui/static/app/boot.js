import { appState, uiState } from "./state.js";
import {
  startButton,
  equipmentSubmit,
  proficiencySubmit,
  languageSubmit,
  spellSubmit,
  spellFormEl,
  proficiencyFormEl,
  languageFormEl,
  newGameButton,
  chatForm,
  chatInput,
  sheetBody,
  sheetTabs,
  collapseButtons,
  imagesPanel,
  regenerateSceneButton,
  chatMain,
  combatPanel,
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
  updateTargetCount,
} from "./combat.js";
import {
  enforceSpellChoiceLimits,
  enforceLanguageChoiceLimits,
  enforceProficiencyChoiceLimits,
} from "./forms.js";
import { enforceMaxTargets } from "./rolls.js";
import {
  resetUI,
  startGame,
  submitEquipmentChoices,
  submitProficiencyChoices,
  submitLanguageChoices,
  submitSpellChoices,
  checkPendingChoices,
  sendMessage,
  sendCombatAction,
  sendCombatEndTurn,
  sendCombatMove,
  toggleEquip,
  togglePrepare,
  rollAction,
  useResource,
  regenerateSceneImage,
} from "./api.js?v=20260403n";

function setupCollapseToggles() {
  const targets = {
    images: { el: imagesPanel, className: "collapsed" },
    combat: { el: combatPanel, className: "collapsed" },
    chat: { el: chatMain, className: "chat-collapsed" },
  };

  collapseButtons.forEach((button) => {
    const key = button.dataset.collapse;
    const target = targets[key];
    if (!target || !target.el) {
      return;
    }
    const applyState = (collapsed) => {
      button.setAttribute("aria-expanded", String(!collapsed));
      button.textContent = collapsed ? "Expand" : "Collapse";
    };
    applyState(target.el.classList.contains(target.className));
    button.addEventListener("click", () => {
      const collapsed = target.el.classList.toggle(target.className);
      applyState(collapsed);
    });
  });
}

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
  fetch("/api/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level: "info", message: "BOOT: init", data: {} }),
    keepalive: true,
  }).catch(() => {});
  setMoveHandler(handleMoveCellClick);

  if (startButton) {
    startButton.addEventListener("click", () => {
      startGame().catch((err) => {
        addMessage("dm", `Failed to start: ${err}`);
      });
    });
  }
  if (equipmentSubmit) {
    equipmentSubmit.addEventListener("click", () => {
      submitEquipmentChoices().catch((err) => {
        addMessage("dm", `Failed to start: ${err}`);
      });
    });
  }
  if (proficiencySubmit) {
    proficiencySubmit.addEventListener("click", () => {
      submitProficiencyChoices().catch((err) => {
        addMessage("dm", `Failed to start: ${err}`);
      });
    });
  }
  if (languageSubmit) {
    languageSubmit.addEventListener("click", () => {
      submitLanguageChoices().catch((err) => {
        addMessage("dm", `Failed to start: ${err}`);
      });
    });
  }
  if (spellSubmit) {
    spellSubmit.addEventListener("click", () => {
      submitSpellChoices().catch((err) => {
        addMessage("dm", `Failed to start: ${err}`);
      });
    });
  }
  if (spellFormEl) {
    spellFormEl.addEventListener("change", (event) => {
      enforceSpellChoiceLimits(event.target);
    });
  }
  if (proficiencyFormEl) {
    proficiencyFormEl.addEventListener("change", (event) => {
      enforceProficiencyChoiceLimits(event.target);
    });
  }
  if (languageFormEl) {
    languageFormEl.addEventListener("change", (event) => {
      enforceLanguageChoiceLimits(event.target);
    });
  }
  if (newGameButton) {
    newGameButton.addEventListener("click", () => {
      resetUI();
    });
  }
  if (regenerateSceneButton) {
    regenerateSceneButton.addEventListener("click", () => {
      regenerateSceneImage().catch((err) => {
        addMessage("dm", `Failed to regenerate scene: ${err}`);
      });
    });
  }
  if (chatForm) {
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
  }
  if (sheetBody) {
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
  }
  if (sheetBody) {
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
  }
  if (combatSubmit) {
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
  }
  if (combatEndTurn) {
    combatEndTurn.addEventListener("click", () => {
    addMessage("user", "End Turn");
    sendCombatEndTurn().catch((err) => {
      addMessage("dm", `Failed to end turn: ${err}`);
    });
    });
  }
  if (sheetTabs) {
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
  }
  if (combatActionSelect) {
    combatActionSelect.addEventListener("change", () => {
    const actions = appState.character?.actions?.actions || [];
    uiState.selectedTargets = [];
    syncTargetSelect();
    updateTargetCount(actions);
    const combat = getCurrentCombatPayload();
    updateTargetingHighlights(getCurrentMap(), actions, combat, combat.targets || []);
    });
  }
  if (combatTargetSelect) {
    combatTargetSelect.addEventListener("change", () => {
    uiState.selectedTargets = Array.from(combatTargetSelect.selectedOptions).map((opt) => opt.value);
    syncTargetSelect();
    const actions = appState.character?.actions?.actions || [];
    updateTargetCount(actions);
    });
  }

  setupCollapseToggles();

  setSessionActive(false);
  renderCharacter(null);
  renderImages([]);
  renderCombat({ active: false });
  showSetupScreen();
  checkPendingChoices();
}
