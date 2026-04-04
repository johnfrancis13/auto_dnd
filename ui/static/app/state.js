export const appState = {
  session: false,
  character: null,
  combat: null,
  actionRolls: {},
  pendingRolls: new Set(),
  pendingRollGlobal: false,
};

export const uiState = {
  selectedTargets: [],
  activeTab: "about",
  pendingStartPayload: null,
  pendingEquipmentChoices: [],
  pendingProficiencyChoices: [],
  pendingLanguageChoices: [],
  pendingSpellChoices: [],
  llmPendingCount: 0,
  spellFilterPreparedOnly: false,
  spellFilterLevel: "all",
};
