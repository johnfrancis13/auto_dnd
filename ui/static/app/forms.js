import { uiState } from "./state.js";
import {
  equipmentModal,
  equipmentFormEl,
  equipmentErrorsEl,
  spellModal,
  spellFormEl,
  spellSummaryEl,
  spellErrorsEl,
  proficiencyModal,
  proficiencyFormEl,
  proficiencyErrorsEl,
  languageModal,
  languageFormEl,
  languageErrorsEl,
} from "./dom.js";

function hideModal(modal) {
  if (!modal) {
    return;
  }
  const active = document.activeElement;
  if (active && modal.contains(active)) {
    active.blur();
    if (document.body && typeof document.body.focus === "function") {
      document.body.focus();
    }
  }
  modal.inert = true;
  // Defer aria-hidden toggle until after focus changes propagate.
  setTimeout(() => {
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
  }, 0);
}

function showModal(modal) {
  if (!modal) {
    return;
  }
  modal.inert = false;
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
}

export function renderEquipmentChoices(choices) {
  uiState.pendingEquipmentChoices = choices || [];
  if (!uiState.pendingEquipmentChoices.length) {
    hideModal(equipmentModal);
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
  showModal(equipmentModal);
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

export function validateEquipmentSelections() {
  const errors = [];
  uiState.pendingEquipmentChoices.forEach((group) => {
    const selected = Array.from(
      equipmentFormEl.querySelectorAll(`input[name="${group.id}"]:checked`)
    );
    const choose = group.choose || 1;
    if (selected.length !== choose) {
      errors.push(`"${group.label}" requires ${choose} selection(s).`);
    }
  });
  return { ok: errors.length === 0, errors };
}

export function renderSpellChoices(choices) {
  uiState.pendingSpellChoices = choices || [];
  if (!spellModal || !spellFormEl || !spellErrorsEl) {
    console.warn("Spell modal elements not found; cannot render spell choices.");
    return;
  }
  if (!uiState.pendingSpellChoices.length) {
    hideModal(spellModal);
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
  showModal(spellModal);
}

export function renderLanguageChoices(choices) {
  uiState.pendingLanguageChoices = choices || [];
  const modal = languageModal || equipmentModal;
  const formEl = languageFormEl || equipmentFormEl;
  const errorsEl = languageErrorsEl || equipmentErrorsEl;
  if (!modal || !formEl || !errorsEl) {
    console.warn("Language modal elements not found; cannot render language choices.");
    return;
  }
  if (!uiState.pendingLanguageChoices.length) {
    hideModal(modal);
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
  showModal(modal);
}

export function renderProficiencyChoices(choices) {
  uiState.pendingProficiencyChoices = choices || [];
  if (!proficiencyModal || !proficiencyFormEl || !proficiencyErrorsEl) {
    console.warn("Proficiency modal elements not found; cannot render proficiency choices.");
    return;
  }
  if (!uiState.pendingProficiencyChoices.length) {
    hideModal(proficiencyModal);
    proficiencyFormEl.innerHTML = "";
    proficiencyErrorsEl.textContent = "";
    return;
  }
  proficiencyErrorsEl.textContent = "";
  proficiencyFormEl.innerHTML = uiState.pendingProficiencyChoices.map((group) => {
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
  showModal(proficiencyModal);
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

export function collectProficiencySelections() {
  if (!proficiencyFormEl) {
    return {};
  }
  const selections = {};
  uiState.pendingProficiencyChoices.forEach((group) => {
    const selected = Array.from(
      proficiencyFormEl.querySelectorAll(`input[name="${group.id}"]:checked`)
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

export function enforceProficiencyChoiceLimits(input) {
  if (!input || input.type !== "checkbox") {
    return;
  }
  if (!proficiencyFormEl || !proficiencyErrorsEl) {
    return;
  }
  const groupId = input.name;
  const group = uiState.pendingProficiencyChoices.find((g) => g.id === groupId);
  if (!group) {
    return;
  }
  const max = group.choose || 1;
  const checked = proficiencyFormEl.querySelectorAll(`input[name="${groupId}"]:checked`);
  if (checked.length > max) {
    input.checked = false;
    proficiencyErrorsEl.textContent = `Choose only ${max} option(s) for "${group.label}".`;
  } else {
    proficiencyErrorsEl.textContent = "";
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
