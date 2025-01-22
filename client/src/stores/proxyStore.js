import { create } from 'zustand';

const MAX_HEALTH_HISTORY = 10;

export const proxyStore = create((set, get) => ({
  proxies: [],
  loading: false,
  error: null,

  // Proxy Management
  addProxy: (proxy) => {
    set((state) => ({
      proxies: [...state.proxies, {
        ...proxy,
        healthHistory: proxy.healthHistory || []
      }]
    }));
  },

  removeProxy: (proxyId) => {
    set((state) => ({
      proxies: state.proxies.filter(p => p.id !== proxyId)
    }));
  },

  // Session Management
  addSession: (proxyId, session) => {
    set((state) => ({
      proxies: state.proxies.map(proxy => 
        proxy.id === proxyId
          ? {
              ...proxy,
              sessions: [...(proxy.sessions || []), session]
            }
          : proxy
      )
    }));
  },

  updateSession: (proxyId, sessionId, updatedSession) => {
    set((state) => {
      const proxy = state.proxies.find(p => p.id === proxyId);
      if (!proxy) throw new Error('Proxy not found');

      const sessionIndex = proxy.sessions?.findIndex(s => s.id === sessionId);
      if (sessionIndex === -1) throw new Error('Session not found');

      return {
        proxies: state.proxies.map(p =>
          p.id === proxyId
            ? {
                ...p,
                sessions: p.sessions.map((s, i) =>
                  i === sessionIndex
                    ? { ...s, ...updatedSession }
                    : s
                )
              }
            : p
        )
      };
    });
  },

  removeSession: (proxyId, sessionId) => {
    set((state) => ({
      proxies: state.proxies.map(proxy =>
        proxy.id === proxyId
          ? {
              ...proxy,
              sessions: proxy.sessions.filter(s => s.id !== sessionId)
            }
          : proxy
      )
    }));
  },

  // Status Management
  updateProxyStatus: (proxyId, status) => {
    set((state) => ({
      proxies: state.proxies.map(proxy =>
        proxy.id === proxyId
          ? { ...proxy, status }
          : proxy
      )
    }));
  },

  updateBulkStatus: (proxyIds, status) => {
    set((state) => ({
      proxies: state.proxies.map(proxy =>
        proxyIds.includes(proxy.id)
          ? { ...proxy, status }
          : proxy
      )
    }));
  },

  // Health Monitoring
  updateHealth: (proxyId, newHealth) => {
    set((state) => {
      const proxy = state.proxies.find(p => p.id === proxyId);
      if (!proxy) throw new Error('Proxy not found');

      const updatedHealthHistory = [
        ...(proxy.health ? [proxy.health] : []),
        ...(proxy.healthHistory || [])
      ].slice(0, MAX_HEALTH_HISTORY);

      return {
        proxies: state.proxies.map(p =>
          p.id === proxyId
            ? {
                ...p,
                health: newHealth,
                healthHistory: updatedHealthHistory
              }
            : p
        )
      };
    });
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
  getDegradedProxies: () => get().proxies.filter(p => p.health?.status === 'degraded')
}));
