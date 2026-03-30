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
  sessionIndicator.textContent = active ? "Live" : "Idle";
  sessionIndicator.style.background = active ? "#e2b091" : "#e6e0d8";
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
