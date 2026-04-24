export const appState = {
  session: false,
  character: null,
  combat: null,
  pendingRollRequest: null,
  lastAnnouncedRollRequestId: null,
  actionRolls: {},
  pendingRolls: new Set(),
  pendingRollGlobal: false,
};

export const uiState = {
  selectedTargets: [],
  selectedActionId: null,
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
