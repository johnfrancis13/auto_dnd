import { appState, uiState } from "./state.js";
import {
  combatPanel,
  combatEndTurn,
  combatTurn,
  chatMain,
  initiativeOrderEl,
  currentTurnChipEl,
  turnStateEl,
  combatMapEl,
} from "./dom.js";

let moveHandler = null;

export function setMoveHandler(handler) {
  moveHandler = handler;
}

export function renderCombat(combat) {
  if (!combat || !combat.active) {
    combatPanel.classList.add("hidden");
    combatPanel.classList.remove("your-turn");
    if (chatMain) {
      chatMain.classList.remove("combat-active");
    }
    appState.combat = combat || null;
    uiState.selectedTargets = [];
    return;
  }
  combatPanel.classList.remove("hidden");
  if (chatMain) {
    chatMain.classList.add("combat-active");
  }
  appState.combat = combat;
  const playerName = appState.character?.identity?.name || "";
  const currentTurn = combat.current_turn || "";
  const isPlayerTurn = Boolean(currentTurn) && currentTurn === playerName;
  combatPanel.classList.toggle("your-turn", isPlayerTurn);
  combatTurn.textContent = currentTurn
    ? `Current turn: ${currentTurn}`
    : "Current turn: Unknown";
  if (currentTurnChipEl) {
    const roundText = combat.round_number ? `Round ${combat.round_number}` : "Round ?";
    const turnLabel = currentTurn || "Unknown";
    currentTurnChipEl.innerHTML = `${roundText} - <strong>${turnLabel}</strong>`;
    currentTurnChipEl.classList.toggle("active", isPlayerTurn);
  }
  const initiative = combat.initiative_order || [];
  const orderedInitiative = currentTurn
    ? [currentTurn, ...initiative.filter((entry) => entry !== currentTurn)]
    : initiative;
  initiativeOrderEl.innerHTML = orderedInitiative.length
    ? orderedInitiative.map((entry) => {
        const active = entry === currentTurn ? "initiative-chip active" : "initiative-chip";
        const playerClass = entry === playerName ? " player" : "";
        const position = initiative.indexOf(entry) + 1;
        return `<span class="${active}${playerClass}"><span class="initiative-index">${position}</span>${entry}</span>`;
      }).join("")
    : "<span class=\"muted\">Initiative not set</span>";
  const turnState = combat.turn_state || { action: false, bonus: false, reaction: false };
  const moveRemaining = combat.move_remaining ?? null;
  const moveMax = combat.move_max ?? null;
  turnStateEl.innerHTML = [
    `<span class="turn-status">${isPlayerTurn ? "Your turn" : `Waiting for ${currentTurn || "..."}`}</span>`,
    `<span>Action: ${turnState.action ? "Available" : "Used"}</span>`,
    `<span>Bonus: ${turnState.bonus ? "Available" : "Used"}</span>`,
    `<span>Reaction: ${turnState.reaction ? "Available" : "Used"}</span>`,
    moveRemaining !== null && moveMax !== null
      ? `<span>Move: ${moveRemaining}/${moveMax} ft</span>`
      : `<span>Move: --</span>`,
  ].join("");
  const targets = combat.targets || [];
  const playerTurn = Boolean(currentTurn) && currentTurn === playerName;
  combatEndTurn.disabled = !playerTurn;
  const actions = appState.character?.actions?.actions || [];
  normalizeSelectedTargets(actions, combat, targets);
  renderCombatMap(combat.map, combat);
}

export function renderCombatMap(map, combat) {
  if (!map || !map.tokens) {
    combatMapEl.innerHTML = "<div class=\"muted\">Map unavailable</div>";
    return;
  }
  const currentTurn = combat?.current_turn || "";
  const playerName = combat?.player_name || "";
  const moveRemaining = combat?.move_remaining ?? 0;
  const targetDetails = Array.isArray(combat?.targets_detail) ? combat.targets_detail : [];
  const detailLookup = new Map(targetDetails.map((entry) => [entry.id || entry.name, entry]));
  const playerStats = appState.character?.stats || {};
  if (playerName && playerStats?.hp) {
    detailLookup.set(playerName, {
      id: playerName,
      name: playerName,
      hp_current: playerStats.hp.current,
      hp_max: playerStats.hp.max,
      ac: playerStats.ac,
    });
  }
  uiState.selectedTargets = uiState.selectedTargets.filter((id) => map.tokens.some((t) => t.id === id));
  const width = map.width || 12;
  const height = map.height || 8;
  combatMapEl.style.gridTemplateColumns = `repeat(${width}, 28px)`;
  combatMapEl.innerHTML = "";
  const cellIndex = {};
  const origin = map.tokens.find((token) => token.id === playerName) || null;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const cell = document.createElement("div");
      cell.className = "combat-cell";
      cell.dataset.x = x;
      cell.dataset.y = y;
      const distance = origin
        ? Math.max(Math.abs(origin.x - x), Math.abs(origin.y - y)) * (map.grid_size || 5)
        : 0;
      if (playerName && currentTurn === playerName && origin) {
        if (distance <= moveRemaining) {
          cell.classList.add("reachable");
        }
      }
      if (playerName && currentTurn === playerName) {
        cell.title = `Move: ${distance} ft`;
      }
      cell.addEventListener("click", () => {
        if (moveHandler) {
          moveHandler(x, y);
        }
      });
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
    div.className = token.faction === "pc" ? "token pc" : "token npc";
    if (token.id === currentTurn) {
      div.classList.add("active");
    }
    if (uiState.selectedTargets.includes(token.id)) {
      div.classList.add("selected");
    }
    div.textContent = token.name.charAt(0).toUpperCase();
    const detail = detailLookup.get(token.id);
    if (detail && (detail.hp_current !== undefined || detail.hp_max !== undefined || detail.ac !== undefined)) {
      const hpCurrent = detail.hp_current ?? "?";
      const hpMax = detail.hp_max ?? "?";
      const ac = detail.ac ?? "?";
      div.title = `${token.name} (HP ${hpCurrent}/${hpMax}, AC ${ac})`;
    } else {
      div.title = token.name;
    }
    if (token.faction === "enemy") {
      div.addEventListener("click", (event) => {
        event.stopPropagation();
        toggleTargetSelection(token.id);
      });
    }
    cell.appendChild(div);
  });
}

export function getSelectedAction(actions) {
  if (!actions || actions.length === 0) {
    return null;
  }
  const actionId = uiState.selectedActionId || "";
  return actions.find((action) => action.id === actionId) || null;
}

export function updateTargetingHighlights(map, actions, combat, allowedTargets = []) {
  if (!map || !map.tokens || !combatMapEl) {
    return;
  }
  const action = getSelectedAction(actions);
  const playerName = combat?.player_name;
  if (!action || !playerName) {
    return;
  }
  const playerToken = map.tokens.find((token) => token.id === playerName);
  if (!playerToken) {
    return;
  }
  const targetTokens = map.tokens.filter((token) => allowedTargets.includes(token.id));
  const primaryId = uiState.selectedTargets[0] || allowedTargets[0] || null;
  const targetable = new Set(
    computeTargetableTokens(action, playerToken, targetTokens, primaryId, map.grid_size || 5)
  );
  combatMapEl.querySelectorAll(".combat-cell").forEach((cell) => {
    cell.classList.remove("targetable");
  });
  map.tokens.forEach((token) => {
    if (!targetable.has(token.id)) {
      return;
    }
    const cell = combatMapEl.querySelector(`.combat-cell[data-x="${token.x}"][data-y="${token.y}"]`);
    if (cell) {
      cell.classList.add("targetable");
    }
  });
}

export function toggleTargetSelection(tokenId) {
  if (!tokenId) {
    return;
  }
  const combat = getCurrentCombatPayload();
  const allowedTargets = combat.targets || [];
  if (!allowedTargets.includes(tokenId)) {
    return;
  }
  if (uiState.selectedTargets.includes(tokenId)) {
    uiState.selectedTargets = uiState.selectedTargets.filter((id) => id !== tokenId);
  } else {
    uiState.selectedTargets = [...uiState.selectedTargets, tokenId];
  }
  const actions = appState.character?.actions?.actions || [];
  normalizeSelectedTargets(actions, combat, allowedTargets);
  updateTargetingHighlights(getCurrentMap(), actions, combat, allowedTargets);
}

export function computeTargetableTokens(action, origin, targets, primaryId, gridSize) {
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

export function normalizeSelectedTargets(actions, combat, allowedTargets = []) {
  const uniqueAllowed = Array.isArray(allowedTargets) ? Array.from(new Set(allowedTargets)) : [];
  const selectedAction = getSelectedAction(actions || []);
  let targetableSet = new Set(uniqueAllowed);
  if (selectedAction && combat?.map?.tokens && combat?.player_name) {
    const playerToken = combat.map.tokens.find((token) => token.id === combat.player_name);
    const targetTokens = combat.map.tokens.filter((token) => uniqueAllowed.includes(token.id));
    if (playerToken && targetTokens.length > 0) {
      const primaryId = uiState.selectedTargets[0] || uniqueAllowed[0] || null;
      targetableSet = new Set(
        computeTargetableTokens(
          selectedAction,
          playerToken,
          targetTokens,
          primaryId,
          combat.map.grid_size || 5
        )
      );
    }
  }

  let selected = uiState.selectedTargets.filter((id) => uniqueAllowed.includes(id) && targetableSet.has(id));
  const maxTargets = selectedAction?.max_targets ?? null;
  if (maxTargets && selected.length > maxTargets) {
    selected = selected.slice(-maxTargets);
  }
  if (selected.length === 0) {
    const fallback = uniqueAllowed.find((id) => targetableSet.has(id));
    if (fallback) {
      selected = [fallback];
    }
  }
  uiState.selectedTargets = selected;
}

export function withinRange(origin, token, range, gridSize) {
  if (!range) {
    return true;
  }
  const dx = Math.abs(origin.x - token.x);
  const dy = Math.abs(origin.y - token.y);
  return Math.max(dx, dy) * gridSize <= range;
}

export function withinLinearShape(origin, primary, token, targeting, shape, length, gridSize) {
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

export function getCurrentMap() {
  return appState.combat?.map || null;
}

export function getCurrentCombatPayload() {
  return appState.combat || {};
}
