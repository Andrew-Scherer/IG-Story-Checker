import create from 'zustand';

const useProxyStore = create((set, get) => ({
  proxies: [],

  addProxy: (proxy) => set(state => ({
    proxies: [...state.proxies, { ...proxy, id: Date.now() }]
  })),

  addProxies: (newProxies) => set(state => ({
    proxies: [
      ...state.proxies,
      ...newProxies.map((proxy, index) => ({ 
        ...proxy, 
        id: Date.now() + index 
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
  }
}));

export default useProxyStore;
