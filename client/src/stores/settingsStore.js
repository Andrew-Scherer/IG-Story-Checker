import { create } from 'zustand';
import { settings } from '../api';

const defaultSettings = {
  // Story Management
  storiesPerDay: 10,
  storyRetentionHours: 24,

  // Rate Limiting
  profilesPerMinute: 30,
  threadCount: 5,
  systemRateLimit: 1000,

  // Batch Configuration
  defaultBatchSize: 100,
  minTriggerInterval: 15,
  autoTriggerEnabled: false,
  autoTriggerStartHour: 0,
  autoTriggerEndHour: 24,

  // Proxy Configuration
  proxyTestTimeout: 10000,
  proxyMaxFailures: 3,
  proxyHourlyLimit: 150,
  proxyDefaultSettings: {
    retryAttempts: 3,
    retryDelay: 1000,
    rotationInterval: 60
  }
};

const useSettingsStore = create((set, get) => ({
  settings: defaultSettings,
  loading: false,
  error: null,

  // Fetch settings from API
  fetchSettings: async () => {
    try {
      set({ loading: true, error: null });
      const response = await settings.list();
      set({ 
        settings: { ...defaultSettings, ...response },
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to fetch settings',
        loading: false
      });
    }
  },

  // Update settings
  updateSettings: async (updates) => {
    try {
      set({ loading: true, error: null });
      const response = await settings.update(updates);
      set({ 
        settings: { ...get().settings, ...response },
        loading: false
      });
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to update settings',
        loading: false
      });
    }
  },

  // Story Retention
  updateStoryRetention: async (hours) => {
    try {
      set({ loading: true, error: null });
      const response = await settings.updateStoryRetention({ hours });
      set(state => ({
        settings: { ...state.settings, storyRetentionHours: response.hours },
        loading: false
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to update story retention',
        loading: false
      });
    }
  },

  // Auto-Trigger Settings
  updateAutoTrigger: async (autoTriggerSettings) => {
    try {
      set({ loading: true, error: null });
      const response = await settings.updateAutoTrigger(autoTriggerSettings);
      set(state => ({
        settings: { 
          ...state.settings,
          autoTriggerEnabled: response.enabled,
          autoTriggerStartHour: response.startHour,
          autoTriggerEndHour: response.endHour,
          minTriggerInterval: response.interval
        },
        loading: false
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to update auto-trigger settings',
        loading: false
      });
    }
  },

  // Proxy Configuration
  updateProxyDefaults: async (defaults) => {
    try {
      set({ loading: true, error: null });
      const response = await settings.updateProxyDefaults(defaults);
      set(state => ({
        settings: { 
          ...state.settings,
          proxyDefaultSettings: response
        },
        loading: false
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to update proxy defaults',
        loading: false
      });
    }
  },

  updateProxyLimits: async (limits) => {
    try {
      set({ loading: true, error: null });
      const response = await settings.updateProxyLimits(limits);
      set(state => ({
        settings: { 
          ...state.settings,
          proxyTestTimeout: response.testTimeout,
          proxyMaxFailures: response.maxFailures,
          proxyHourlyLimit: response.hourlyLimit
        },
        loading: false
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to update proxy limits',
        loading: false
      });
    }
  },

  // System Rate Limiting
  updateSystemRateLimit: async (limit) => {
    try {
      set({ loading: true, error: null });
      const response = await settings.updateRateLimit({ limit });
      set(state => ({
        settings: { ...state.settings, systemRateLimit: response.limit },
        loading: false
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to update rate limit',
        loading: false
      });
    }
  },

  // Batch Configuration
  updateBatchDefaults: async (defaults) => {
    try {
      set({ loading: true, error: null });
      const response = await settings.updateBatchDefaults(defaults);
      set(state => ({
        settings: { 
          ...state.settings,
          defaultBatchSize: response.batchSize
        },
        loading: false
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to update batch defaults',
        loading: false
      });
    }
  },

  // Error Handling
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),

  // Loading State
  setLoading: (loading) => set({ loading })
}));

export default useSettingsStore;
