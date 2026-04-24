import { uiState } from "./state.js";
import {
  messagesEl,
  sessionIndicator,
  gameStateEl,
  setupScreen,
  gameScreen,
  thinkingIndicator,
} from "./dom.js";

export function setLlmPending(active) {
  uiState.llmPendingCount += active ? 1 : -1;
  if (uiState.llmPendingCount < 0) {
    uiState.llmPendingCount = 0;
  }
  const isActive = uiState.llmPendingCount > 0;
  if (thinkingIndicator) {
    thinkingIndicator.classList.toggle("hidden", !isActive);
  }
}

export function setSessionActive(active, mode = "exploration") {
  if (sessionIndicator) {
    sessionIndicator.textContent = active ? "Live" : "Idle";
    sessionIndicator.style.background = active ? "#e2b091" : "#e6e0d8";
  }
  if (!active) {
    gameStateEl.textContent = "No session running";
  } else {
    const label = mode ? mode.charAt(0).toUpperCase() + mode.slice(1) : "Exploration";
    gameStateEl.textContent = label;
  }
}

export function showSetupScreen() {
  setupScreen.classList.remove("hidden");
  gameScreen.classList.add("hidden");
}

export function showGameScreen() {
  setupScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");
}

export function addMessage(role, content) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = content;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

export function addLogMessage(content, tone = "") {
  const div = document.createElement("div");
  const toneClass = tone ? ` ${tone}` : "";
  div.className = `message log${toneClass}`;
  div.textContent = content;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function formatModifier(value) {
  if (!value) {
    return "";
  }
  return value > 0 ? `+${value}` : `${value}`;
}

function formatDiceList(dice) {
  if (!Array.isArray(dice) || dice.length === 0) {
    return "";
  }
  return dice.join(", ");
}

function formatAttackLine(log) {
  const detail = log.attack_roll_detail || {};
  const dice = formatDiceList(detail.dice);
  const adv = detail.advantage ? ` ${detail.advantage}` : "";
  const mod = formatModifier(detail.modifiers ?? 0);
  const total = detail.total ?? log.attack_total;
  const hit = log.hit === true ? "Hit" : (log.hit === false ? "Miss" : "");
  const crit = detail.critical || log.critical ? "CRIT" : "";
  const status = [hit, crit].filter(Boolean).join(", ");
  const statusText = status ? ` (${status})` : "";
  const diceText = dice ? ` [${dice}]` : "";
  const modText = mod ? ` ${mod}` : "";
  const totalText = total !== undefined && total !== null ? ` = ${total}` : "";
  return `Attack: d20${adv}${diceText}${modText}${totalText}${statusText}`;
}

function formatSaveLine(log) {
  const detail = log.save_roll_detail || {};
  const dice = formatDiceList(detail.dice);
  const mod = formatModifier(detail.modifiers ?? 0);
  const total = detail.total ?? log.save_total;
  const dc = log.save_dc ?? "?";
  const ability = log.save_ability || "Save";
  const outcome = log.save_success === true ? "Success" : (log.save_success === false ? "Fail" : "");
  const outcomeText = outcome ? ` (${outcome})` : "";
  const diceText = dice ? ` [${dice}]` : "";
  const modText = mod ? ` ${mod}` : "";
  const totalText = total !== undefined && total !== null ? ` = ${total}` : "";
  return `Save: ${ability} d20${diceText}${modText}${totalText} vs DC ${dc}${outcomeText}`;
}

function formatDamageLines(log) {
  if (Array.isArray(log.damage_rolls_detail) && log.damage_rolls_detail.length > 0) {
    return log.damage_rolls_detail.map((entry) => {
      const dice = formatDiceList(entry.dice);
      const mod = formatModifier(entry.modifiers ?? 0);
      const total = entry.total ?? log.damage_total;
      const diceAmount = entry.dice_amount ?? (Array.isArray(entry.dice) ? entry.dice.length : "?");
      const diceType = entry.dice_type ?? "?";
      const type = entry.type ? ` (${entry.type})` : "";
      const diceText = dice ? ` [${dice}]` : "";
      const modText = mod ? ` ${mod}` : "";
      const totalText = total !== undefined && total !== null ? ` = ${total}` : "";
      return `Damage${type}: ${diceAmount}d${diceType}${diceText}${modText}${totalText}`;
    });
  }
  if (log.damage_total !== undefined && log.damage_total !== null) {
    return [`Damage: ${log.damage_total}`];
  }
  return [];
}

export function addCombatLogEntries(logs, meta = null) {
  if (!Array.isArray(logs) || logs.length === 0) {
    return;
  }
  const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (meta && (meta.round || meta.current_turn)) {
    const roundText = meta.round ? `Round ${meta.round}` : "Round ?";
    const turnText = meta.current_turn ? `Turn: ${meta.current_turn}` : "Turn: ?";
    addLogMessage(`${roundText} - ${turnText}`, "meta");
  }
  logs.forEach((log) => {
    if (!log) {
      return;
    }
    const target = log.target || (Array.isArray(log.targets) ? log.targets.join(", ") : "Unknown");
    const header = `${log.actor || "Unknown"} -> ${target}: ${log.action_name || log.action_id || "Action"}`;
    const lines = [`---- ${timestamp} ----`, header];
    if (log.attack_total !== null || log.attack_roll_detail) {
      lines.push(formatAttackLine(log));
    }
    if (log.save_total !== null || log.save_roll_detail) {
      lines.push(formatSaveLine(log));
    }
    lines.push(...formatDamageLines(log));
    if (log.target_hp_before !== null && log.target_hp_after !== null) {
      lines.push(`HP: ${log.target_hp_before} -> ${log.target_hp_after}`);
    }
    if (log.notes) {
      lines.push(`Note: ${log.notes}`);
    }
    let tone = "";
    if (log.critical) {
      tone = "crit";
    } else if (log.hit === false) {
      tone = "miss";
    } else if (log.hit === true) {
      tone = "hit";
    }
    addLogMessage(lines.filter(Boolean).join("\n"), tone);
  });
}

