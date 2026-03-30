import { appState, uiState } from "./state.js";
import { sheetBody, imageGrid } from "./dom.js";

export function renderCharacter(character) {
  appState.character = character;
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
  let knownSpells = uiState.spellFilterPreparedOnly
    ? character.spells.known.filter((spell) => spell.prepared)
    : character.spells.known;
  if (uiState.spellFilterLevel === "cantrip") {
    knownSpells = knownSpells.filter((spell) => spell.level === 0);
  } else if (uiState.spellFilterLevel === "leveled") {
    knownSpells = knownSpells.filter((spell) => spell.level > 0);
  }
  const spellsHtml = `
    <h3>Spellcasting</h3>
    <div class="entry">
      <div class="muted">Ability: ${character.spells.spellcasting_ability || "Unknown"}</div>
      <div class="muted">Save DC: ${character.spells.spell_save_dc || "Unknown"}</div>
      ${preparedMeta}
      <label class="spell-filter">
        <input type="checkbox" data-spell-filter ${uiState.spellFilterPreparedOnly ? "checked" : ""} />
        Show prepared only
      </label>
      <label class="spell-filter">
        Filter
        <select data-spell-filter-level>
          <option value="all" ${uiState.spellFilterLevel === "all" ? "selected" : ""}>All</option>
          <option value="cantrip" ${uiState.spellFilterLevel === "cantrip" ? "selected" : ""}>Cantrips</option>
          <option value="leveled" ${uiState.spellFilterLevel === "leveled" ? "selected" : ""}>Leveled</option>
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
  sheetBody.innerHTML = tabContent[uiState.activeTab] || aboutHtml;
}

export function renderActionRollInfo(action, character) {
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

export function formatAbility(value, character) {
  if (!value) {
    return "";
  }
  const upper = String(value).toUpperCase();
  if (upper === "SPELLCASTING" || upper === "SPELL") {
    return character.spells.spellcasting_ability || "Spellcasting";
  }
  return upper;
}

export function formatResourceMeta(res) {
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

export function renderActionControls(action, character) {
  const targets = appState.combat?.targets || [];
  const inCombat = appState.combat?.active;
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

export function renderActionBadges(action) {
  const roll = appState.actionRolls?.[action.id];
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

export function getSpellSlotResource(character, spellLevel) {
  if (!character || !spellLevel || spellLevel <= 0) {
    return null;
  }
  const slots = character.actions?.resources?.spell_slots || [];
  const name = `Level_${spellLevel} Spell Slots`;
  return slots.find((slot) => slot.name === name) || null;
}

export function renderImages(images) {
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
