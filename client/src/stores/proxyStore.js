import { create } from 'zustand';
import { proxies } from '../api';

const MAX_HEALTH_HISTORY = 10;

class ApiError extends Error {
  constructor(response) {
    const message = response.data?.message || 'An error occurred';
    super(message);
    this.name = 'ApiError';
    this.details = response.data?.details;
    this.error = response.data?.error;
    this.status = response.status;
  }
}

export const proxyStore = create((set, get) => ({
  proxies: [],
  loading: false,
  error: null,
  rotationSettings: {
    enabled: false,
    interval: 60, // minutes
    lastRotation: null
  },

  // Initial Load
  loadProxies: async () => {
    try {
      set({ loading: true, error: null });
      console.log('Loading proxies...');
      const response = await proxies.list();
      console.log('Proxies loaded:', response);
      
      set({
        proxies: response.map(proxy => ({
          ...proxy,
          healthHistory: [],
          performanceMetrics: {
            successRate: 0,
            avgLatency: 0,
            requestCount: 0,
            failureCount: 0,
            lastUsed: null
          }
        })),
        loading: false
      });
    } catch (error) {
      console.error('Failed to load proxies:', error.response?.data || error);
      const apiError = new ApiError(error.response || error);
      set({ 
        error: apiError,
        loading: false
      });
      throw apiError;
    }
  },

  // Proxy Management
  addProxy: async (proxyData) => {
    try {
      set({ loading: true, error: null });
      console.log('Creating proxy with data:', { ...proxyData, session: '[REDACTED]' });
      const response = await proxies.create(proxyData);
      console.log('Proxy created successfully:', response);

      set((state) => ({
        proxies: [...state.proxies, {
          ...response,
          healthHistory: [],
          performanceMetrics: {
            successRate: 0,
            avgLatency: 0,
            requestCount: 0,
            failureCount: 0,
            lastUsed: null
          }
        }],
        loading: false
      }));
      return response;
    } catch (error) {
      console.error('Failed to create proxy:', error.response?.data || error);
      const apiError = new ApiError(error.response || error);
      set({ 
        error: apiError,
        loading: false
      });
      throw apiError;
    }
  },

  removeProxy: async (proxyId) => {
    try {
      set({ loading: true, error: null });
      console.log('Removing proxy:', proxyId);
      await proxies.delete(proxyId);
      console.log('Proxy removed successfully');
      
      set((state) => ({
        proxies: state.proxies.filter(p => p.id !== proxyId),
        loading: false
      }));
    } catch (error) {
      console.error('Failed to remove proxy:', error.response?.data || error);
      const apiError = new ApiError(error.response || error);
      set({ 
        error: apiError,
        loading: false
      });
      throw apiError;
    }
  },

  // Status Management
  updateProxyStatus: async (proxyId, status) => {
    try {
      set({ loading: true, error: null });
      console.log('Updating proxy status:', { proxyId, status });
      const response = await proxies.updateStatus(proxyId, { status });
      console.log('Status updated successfully');

      set((state) => ({
        proxies: state.proxies.map(proxy =>
          proxy.id === proxyId
            ? { ...proxy, ...response }
            : proxy
        ),
        loading: false
      }));
    } catch (error) {
      console.error('Failed to update status:', error.response?.data || error);
      const apiError = new ApiError(error.response || error);
      set({ 
        error: apiError,
        loading: false
      });
      throw apiError;
    }
  },

  // Health Monitoring
  updateHealth: async (proxyId, newHealth) => {
    try {
      set({ loading: true, error: null });
      console.log('Updating proxy health:', { proxyId, newHealth });
      const response = await proxies.updateHealth(proxyId, newHealth);
      console.log('Health updated successfully');

      set((state) => {
        const proxy = state.proxies.find(p => p.id === proxyId);
        if (!proxy) return state;

        const updatedHealthHistory = [
          response,
          ...(proxy.healthHistory || [])
        ].slice(0, MAX_HEALTH_HISTORY);

        return {
          proxies: state.proxies.map(p =>
            p.id === proxyId
              ? {
                  ...p,
                  health: response,
                  healthHistory: updatedHealthHistory
                }
              : p
          ),
          loading: false
        };
      });
    } catch (error) {
      console.error('Failed to update health:', error.response?.data || error);
      const apiError = new ApiError(error.response || error);
      set({ 
        error: apiError,
        loading: false
      });
      throw apiError;
    }
  },

  // Performance Tracking
  updatePerformanceMetrics: (proxyId, metrics) => {
    set((state) => ({
      proxies: state.proxies.map(proxy =>
        proxy.id === proxyId
          ? {
              ...proxy,
              performanceMetrics: {
                ...proxy.performanceMetrics,
                ...metrics,
                lastUsed: new Date().toISOString()
              }
            }
          : proxy
      )
    }));
  },

  // Proxy Rotation
  toggleRotation: (enabled) => {
    set((state) => ({
      rotationSettings: {
        ...state.rotationSettings,
        enabled,
        lastRotation: enabled ? new Date().toISOString() : state.rotationSettings.lastRotation
      }
    }));
  },

  setRotationInterval: (minutes) => {
    set((state) => ({
      rotationSettings: {
        ...state.rotationSettings,
        interval: minutes
      }
    }));
  },

  // Proxy Testing
  testProxy: async (proxyId) => {
    try {
      set({ loading: true, error: null });
      console.log('Testing proxy:', proxyId);
      const startTime = Date.now();
      const response = await proxies.test(proxyId);
      const latency = Date.now() - startTime;
      console.log('Test completed successfully:', response);

      // Update performance metrics
      get().updatePerformanceMetrics(proxyId, {
        lastLatency: latency,
        avgLatency: response.avgLatency,
        successRate: response.successRate,
        requestCount: response.requestCount
      });

      set({ loading: false });
      return { success: true, latency, ...response };
    } catch (error) {
      console.error('Test failed:', error.response?.data || error);
      get().updatePerformanceMetrics(proxyId, {
        failureCount: get().proxies.find(p => p.id === proxyId)?.performanceMetrics.failureCount + 1 || 1
      });

      const apiError = new ApiError(error.response || error);
      set({ 
        error: apiError,
        loading: false
      });
      return { success: false, error: apiError.message };
    }
  },

  // Error Handling
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),

  // Loading State
  setLoading: (loading) => set({ loading }),

  // Selectors
  getProxyById: (proxyId) => get().proxies.find(p => p.id === proxyId),
  getActiveProxies: () => get().proxies.filter(p => p.status === 'active'),
  getHealthyProxies: () => get().proxies.filter(p => p.health?.status === 'healthy'),
  getDegradedProxies: () => get().proxies.filter(p => p.health?.status === 'degraded'),
  getAvailableProxies: () => get().proxies.filter(p => 
    p.status === 'active' && 
    p.health?.status === 'healthy'
  )
}));
