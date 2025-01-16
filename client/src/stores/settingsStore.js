import create from 'zustand';

const useSettingsStore = create((set) => ({
  settings: {
    // Daily Story Targets
    storiesPerDay: 10,

    // Rate Limiting
    profilesPerMinute: 30,
    threadCount: 5
  },

  // Actions
  updateSettings: (updates) => set(state => ({
    settings: {
      ...state.settings,
      ...updates
    }
  })),

  // Proxy management moved to its own store
  proxies: [],
  addProxy: () => {},
  removeProxy: () => {},
  updateProxy: () => {},
  testProxy: () => {}
}));

export default useSettingsStore;
