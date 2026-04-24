import { appState } from "./state.js";
import { sheetBody } from "./dom.js";
import { addMessage } from "./ui.js";

export function enforceMaxTargets(selectEl) {
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

export function setRollPending(actionId, pending) {
  if (pending) {
    appState.pendingRolls.add(actionId);
    appState.pendingRollGlobal = true;
  } else {
    appState.pendingRolls.delete(actionId);
    if (appState.pendingRolls.size === 0) {
      appState.pendingRollGlobal = false;
    }
  }
  updateRollPendingUI(actionId, pending);
}

export function updateRollPendingUI(activeActionId, pending) {
  const allControls = sheetBody.querySelectorAll("[data-roll-controls]");
  allControls.forEach((controls) => {
    const isActive = controls.dataset.rollControls === activeActionId;
    if (appState.pendingRollGlobal) {
      controls.classList.add("pending");
    } else {
      controls.classList.remove("pending");
    }
    controls.querySelectorAll("button, select, input").forEach((el) => {
      el.disabled = appState.pendingRollGlobal;
    });
    const status = controls.querySelector("[data-roll-status]");
    if (!status) {
      return;
    }
    if (pending && isActive) {
      status.innerHTML = `<span class="spinner"></span> Executing...`;
    } else {
      status.textContent = "";
    }
  });
}
