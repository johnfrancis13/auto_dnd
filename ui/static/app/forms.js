import { uiState } from "./state.js";
import {
  equipmentModal,
  equipmentFormEl,
  equipmentErrorsEl,
  spellModal,
  spellFormEl,
  spellSummaryEl,
  spellErrorsEl,
} from "./dom.js";

export function renderEquipmentChoices(choices) {
  uiState.pendingEquipmentChoices = choices || [];
  if (!uiState.pendingEquipmentChoices.length) {
    equipmentModal.classList.add("hidden");
    equipmentModal.setAttribute("aria-hidden", "true");
    equipmentFormEl.innerHTML = "";
    equipmentErrorsEl.textContent = "";
    return;
  }
  equipmentErrorsEl.textContent = "";
  equipmentFormEl.innerHTML = uiState.pendingEquipmentChoices.map((group) => {
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

export function collectEquipmentSelections() {
  const selections = {};
  uiState.pendingEquipmentChoices.forEach((group) => {
    const selected = Array.from(
      equipmentFormEl.querySelectorAll(`input[name="${group.id}"]:checked`)
    ).map((input) => input.value);
    if (selected.length) {
      selections[group.id] = selected;
    }
  });
  return selections;
}

export function renderSpellChoices(choices) {
  uiState.pendingSpellChoices = choices || [];
  if (!uiState.pendingSpellChoices.length) {
    spellModal.classList.add("hidden");
    spellModal.setAttribute("aria-hidden", "true");
    spellFormEl.innerHTML = "";
    spellSummaryEl.textContent = "";
    spellErrorsEl.textContent = "";
    return;
  }
  spellErrorsEl.textContent = "";
  spellSummaryEl.textContent = "";
  spellFormEl.innerHTML = uiState.pendingSpellChoices.map((group) => {
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
  spellModal.classList.remove("hidden");
  spellModal.setAttribute("aria-hidden", "false");
}

export function collectSpellSelections() {
  const selections = {};
  uiState.pendingSpellChoices.forEach((group) => {
    const selected = Array.from(
      spellFormEl.querySelectorAll(`input[name="${group.id}"]:checked`)
    ).map((input) => input.value);
    if (selected.length) {
      selections[group.id] = selected;
    }
  });
  return selections;
}

export function enforceSpellChoiceLimits(input) {
  if (!input || input.type !== "checkbox") {
    return;
  }
  const groupId = input.name;
  const group = uiState.pendingSpellChoices.find((g) => g.id === groupId);
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
