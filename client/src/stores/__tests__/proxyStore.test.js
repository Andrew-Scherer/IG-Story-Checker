import { proxyStore } from '../proxyStore';

describe('proxyStore', () => {
  beforeEach(() => {
    proxyStore.setState({
      proxies: [],
      loading: false,
      error: null
    });
  });

  describe('Proxy-Session Management', () => {
    it('should add a new proxy with session', () => {
      const proxy = {
        id: 1,
        host: '192.168.1.1',
        port: 8080,
        username: 'testuser',
        sessions: [{
          id: 1,
          session: 'test-session',
          status: 'active'
        }]
      };

      proxyStore.getState().addProxy(proxy);
      
      const expectedProxy = {
        ...proxy,
        healthHistory: []
      };
      expect(proxyStore.getState().proxies).toContainEqual(expectedProxy);
    });

    it('should update proxy session', () => {
      const proxy = {
        id: 1,
        host: '192.168.1.1',
        port: 8080,
        sessions: [{
          id: 1,
          session: 'old-session',
          status: 'active'
        }]
      };
      
      proxyStore.getState().addProxy(proxy);
      
      const updatedSession = {
        id: 1,
        session: 'new-session',
        status: 'disabled'
      };
      
      proxyStore.getState().updateSession(1, 1, updatedSession);
      
      const updatedProxy = proxyStore.getState().proxies.find(p => p.id === 1);
      expect(updatedProxy.sessions[0]).toEqual(updatedSession);
    });

    it('should remove proxy session', () => {
      const proxy = {
        id: 1,
        host: '192.168.1.1',
        port: 8080,
        sessions: [{
          id: 1,
          session: 'test-session',
          status: 'active'
        }]
      };
      
      proxyStore.getState().addProxy(proxy);
      proxyStore.getState().removeSession(1, 1);
      
      const updatedProxy = proxyStore.getState().proxies.find(p => p.id === 1);
      expect(updatedProxy.sessions).toHaveLength(0);
    });
  });

  describe('Status Management', () => {
    it('should update proxy status', () => {
      const proxy = {
        id: 1,
        host: '192.168.1.1',
        port: 8080,
        status: 'active'
      };
      
      proxyStore.getState().addProxy(proxy);
      proxyStore.getState().updateProxyStatus(1, 'disabled');
      
      const updatedProxy = proxyStore.getState().proxies.find(p => p.id === 1);
      expect(updatedProxy.status).toBe('disabled');
    });

    it('should handle bulk status updates', () => {
      const proxies = [
        { id: 1, host: '192.168.1.1', port: 8080, status: 'active' },
        { id: 2, host: '192.168.1.2', port: 8080, status: 'active' }
      ];
      
      proxies.forEach(proxy => proxyStore.getState().addProxy(proxy));
      proxyStore.getState().updateBulkStatus([1, 2], 'disabled');
      
      const updatedProxies = proxyStore.getState().proxies;
      expect(updatedProxies.every(p => p.status === 'disabled')).toBe(true);
    });
  });

  describe('Health Monitoring', () => {
    it('should update health metrics', () => {
      const proxy = {
        id: 1,
        host: '192.168.1.1',
        port: 8080,
        health: {
          status: 'healthy',
          latency: 100,
          uptime: 99.9,
          lastCheck: new Date().toISOString()
        }
      };
      
      proxyStore.getState().addProxy(proxy);
      
      const newHealth = {
        status: 'degraded',
        latency: 500,
        uptime: 95.5,
        lastCheck: new Date().toISOString()
      };
      
      proxyStore.getState().updateHealth(1, newHealth);
      
      const updatedProxy = proxyStore.getState().proxies.find(p => p.id === 1);
      expect(updatedProxy.health).toEqual(newHealth);
    });

    it('should track health history', () => {
      const proxy = {
        id: 1,
        host: '192.168.1.1',
        port: 8080,
        health: {
          status: 'healthy',
          latency: 100,
          uptime: 99.9,
          lastCheck: new Date().toISOString()
        },
        healthHistory: []
      };
      
      proxyStore.getState().addProxy(proxy);
      
      const newHealth = {
        status: 'degraded',
        latency: 500,
        uptime: 95.5,
        lastCheck: new Date().toISOString()
      };
      
      proxyStore.getState().updateHealth(1, newHealth);
      
      const updatedProxy = proxyStore.getState().proxies.find(p => p.id === 1);
      expect(updatedProxy.healthHistory).toHaveLength(1);
      expect(updatedProxy.healthHistory[0]).toEqual(proxy.health);
    });

    it('should limit health history size', () => {
      const proxy = {
        id: 1,
        host: '192.168.1.1',
        port: 8080,
        health: {
          status: 'healthy',
          latency: 100,
          uptime: 99.9,
          lastCheck: new Date().toISOString()
        },
        healthHistory: []
      };
      
      proxyStore.getState().addProxy(proxy);
      
      // Add 11 health updates (max size is 10)
      for (let i = 0; i < 11; i++) {
        proxyStore.getState().updateHealth(1, {
          status: 'healthy',
          latency: 100 + i,
          uptime: 99.9,
          lastCheck: new Date().toISOString()
        });
      }
      
      const updatedProxy = proxyStore.getState().proxies.find(p => p.id === 1);
      expect(updatedProxy.healthHistory).toHaveLength(10);
    });
  });

  describe('Error Handling', () => {
    it('should handle proxy not found errors', () => {
      expect(() => {
        proxyStore.getState().updateHealth(999, {
          status: 'healthy',
          latency: 100,
          uptime: 99.9,
          lastCheck: new Date().toISOString()
        });
      }).toThrow('Proxy not found');
    });

    it('should handle session not found errors', () => {
      const proxy = {
        id: 1,
        host: '192.168.1.1',
        port: 8080,
        sessions: []
      };
      
      proxyStore.getState().addProxy(proxy);
      
      expect(() => {
        proxyStore.getState().updateSession(1, 999, {
          session: 'test',
          status: 'active'
        });
      }).toThrow('Session not found');
    });
  });
});
