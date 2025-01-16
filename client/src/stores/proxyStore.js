import { create } from 'zustand';

const useProxyStore = create((set, get) => ({
  proxies: [],

  addProxy: (proxy) => set(state => ({
    proxies: [...state.proxies, { 
      ...proxy, 
      id: Date.now(),
      sessions: [] 
    }]
  })),

  addProxies: (newProxies) => set(state => ({
    proxies: [
      ...state.proxies,
      ...newProxies.map((proxy, index) => ({ 
        ...proxy, 
        id: Date.now() + index,
        sessions: []
      }))
    ]
  })),

  removeProxy: (ids) => set(state => ({
    proxies: state.proxies.filter(proxy => 
      Array.isArray(ids) ? !ids.includes(proxy.id) : proxy.id !== ids
    )
  })),

  testProxy: async (id) => {
    // Mark proxy as testing
    set(state => ({
      proxies: state.proxies.map(p => 
        p.id === id ? { ...p, status: 'testing' } : p
      )
    }));

    try {
      // TODO: Implement actual proxy testing logic
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      set(state => ({
        proxies: state.proxies.map(p => 
          p.id === id ? { ...p, status: 'working' } : p
        )
      }));
    } catch (error) {
      set(state => ({
        proxies: state.proxies.map(p => 
          p.id === id ? { ...p, status: 'failed' } : p
        )
      }));
    }
  },

  // Session Management
  addSession: (proxyId, sessionData) => set(state => ({
    proxies: state.proxies.map(proxy => {
      if (proxy.id === proxyId) {
        return {
          ...proxy,
          sessions: [
            ...proxy.sessions,
            {
              id: Date.now(),
              ...sessionData,
              status: 'active'
            }
          ]
        };
      }
      return proxy;
    })
  })),

  removeSession: (proxyId, sessionId) => set(state => ({
    proxies: state.proxies.map(proxy => {
      if (proxy.id === proxyId) {
        return {
          ...proxy,
          sessions: proxy.sessions.filter(session => session.id !== sessionId)
        };
      }
      return proxy;
    })
  })),

  updateSession: (proxyId, sessionId, updates) => set(state => ({
    proxies: state.proxies.map(proxy => {
      if (proxy.id === proxyId) {
        return {
          ...proxy,
          sessions: proxy.sessions.map(session => {
            if (session.id === sessionId) {
              return { ...session, ...updates };
            }
            return session;
          })
        };
      }
      return proxy;
    })
  }))
}));

export default useProxyStore;
