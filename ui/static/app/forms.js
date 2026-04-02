import { uiState } from "./state.js";
import {
  equipmentModal,
  equipmentFormEl,
  equipmentErrorsEl,
  spellModal,
  spellFormEl,
  spellSummaryEl,
  spellErrorsEl,
  languageModal,
  languageFormEl,
  languageErrorsEl,
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
    const optionsHtml = group.options.map((option) => {
      const desc = (option.description || "").trim();
      const descHtml = desc
        ? `
          <details class="spell-option-details">
            <summary>Show description</summary>
            <div class="spell-option-desc">${desc.replace(/\n/g, "<br />")}</div>
          </details>
        `
        : "";
      return `
        <label class="equipment-option">
          <input type="${inputType}" name="${group.id}" value="${option.id}" />
          <span>${option.label}</span>
        </label>
        ${descHtml}
      `;
    }).join("");
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

export function renderLanguageChoices(choices) {
  uiState.pendingLanguageChoices = choices || [];
  const modal = languageModal || equipmentModal;
  const formEl = languageFormEl || equipmentFormEl;
  const errorsEl = languageErrorsEl || equipmentErrorsEl;
  if (!modal || !formEl || !errorsEl) {
    return;
  }
  if (!uiState.pendingLanguageChoices.length) {
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
    formEl.innerHTML = "";
    errorsEl.textContent = "";
    return;
  }
  errorsEl.textContent = "";
  formEl.innerHTML = uiState.pendingLanguageChoices.map((group) => {
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
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
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

export function collectLanguageSelections() {
  const formEl = languageFormEl || equipmentFormEl;
  if (!formEl) {
    return {};
  }
  const selections = {};
  uiState.pendingLanguageChoices.forEach((group) => {
    const selected = Array.from(
      formEl.querySelectorAll(`input[name="${group.id}"]:checked`)
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

export function enforceLanguageChoiceLimits(input) {
  if (!input || input.type !== "checkbox") {
    return;
  }
  const formEl = languageFormEl || equipmentFormEl;
  const errorsEl = languageErrorsEl || equipmentErrorsEl;
  if (!formEl || !errorsEl) {
    return;
  }
  const groupId = input.name;
  const group = uiState.pendingLanguageChoices.find((g) => g.id === groupId);
  if (!group) {
    return;
  }
  const max = group.choose || 1;
  const checked = formEl.querySelectorAll(`input[name="${groupId}"]:checked`);
  if (checked.length > max) {
    input.checked = false;
    errorsEl.textContent = `Choose only ${max} option(s) for "${group.label}".`;
  } else {
    errorsEl.textContent = "";
  }
}
