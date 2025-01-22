import { proxyStore } from '../proxyStore';
import { proxies } from '../../api';

// Mock the API module
jest.mock('../../api', () => ({
  proxies: {
    list: jest.fn(),
    create: jest.fn(),
    delete: jest.fn(),
    updateStatus: jest.fn(),
    updateHealth: jest.fn(),
    test: jest.fn()
  }
}));

describe('proxyStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    proxyStore.setState({
      proxies: [],
      loading: false,
      error: null,
      rotationSettings: {
        enabled: false,
        interval: 60,
        lastRotation: null
      }
    });
  });

  describe('Initial Loading', () => {
    it('should load proxies successfully', async () => {
      const mockProxies = [
        { id: 1, ip: '192.168.1.1', port: 8080 },
        { id: 2, ip: '192.168.1.2', port: 8081 }
      ];
      proxies.list.mockResolvedValue(mockProxies);

      await proxyStore.getState().loadProxies();

      expect(proxyStore.getState().proxies).toHaveLength(2);
      expect(proxyStore.getState().loading).toBe(false);
      expect(proxyStore.getState().error).toBeNull();
      // Verify performance metrics initialization
      expect(proxyStore.getState().proxies[0].performanceMetrics).toEqual({
        successRate: 0,
        avgLatency: 0,
        requestCount: 0,
        failureCount: 0,
        lastUsed: null
      });
    });

    it('should handle loading errors', async () => {
      const error = new Error('Network error');
      proxies.list.mockRejectedValue({ response: { data: { message: 'Network error' } } });

      await expect(proxyStore.getState().loadProxies()).rejects.toThrow();
      expect(proxyStore.getState().loading).toBe(false);
      expect(proxyStore.getState().error).toBeTruthy();
    });
  });

  describe('Proxy Management', () => {
    it('should add proxy with performance tracking', async () => {
      const newProxy = {
        ip: '192.168.1.1',
        port: 8080,
        username: 'test',
        password: 'pass'
      };
      proxies.create.mockResolvedValue({ ...newProxy, id: 1 });

      await proxyStore.getState().addProxy(newProxy);

      expect(proxyStore.getState().proxies).toHaveLength(1);
      expect(proxyStore.getState().proxies[0].performanceMetrics).toBeDefined();
    });

    it('should remove proxy and clean up', async () => {
      const proxy = { id: 1, ip: '192.168.1.1', port: 8080 };
      proxyStore.setState({ proxies: [proxy] });
      proxies.delete.mockResolvedValue();

      await proxyStore.getState().removeProxy(1);

      expect(proxyStore.getState().proxies).toHaveLength(0);
    });
  });

  describe('Performance Monitoring', () => {
    it('should update performance metrics', () => {
      const proxy = {
        id: 1,
        ip: '192.168.1.1',
        port: 8080,
        performanceMetrics: {
          successRate: 0,
          avgLatency: 0,
          requestCount: 0,
          failureCount: 0,
          lastUsed: null
        }
      };
      proxyStore.setState({ proxies: [proxy] });

      const newMetrics = {
        successRate: 95,
        avgLatency: 150,
        requestCount: 100
      };
      proxyStore.getState().updatePerformanceMetrics(1, newMetrics);

      const updatedProxy = proxyStore.getState().proxies[0];
      expect(updatedProxy.performanceMetrics.successRate).toBe(95);
      expect(updatedProxy.performanceMetrics.avgLatency).toBe(150);
      expect(updatedProxy.performanceMetrics.requestCount).toBe(100);
      expect(updatedProxy.performanceMetrics.lastUsed).toBeTruthy();
    });

    it('should track health history with limit', async () => {
      const proxy = {
        id: 1,
        ip: '192.168.1.1',
        port: 8080,
        healthHistory: []
      };
      proxyStore.setState({ proxies: [proxy] });

      // Add 11 health updates (max is 10)
      for (let i = 0; i < 11; i++) {
        const health = { status: 'healthy', latency: 100 + i };
        proxies.updateHealth.mockResolvedValue(health);
        await proxyStore.getState().updateHealth(1, health);
      }

      const updatedProxy = proxyStore.getState().proxies[0];
      expect(updatedProxy.healthHistory).toHaveLength(10);
    });
  });

  describe('Proxy Testing', () => {
    it('should test proxy and update metrics', async () => {
      const proxy = {
        id: 1,
        ip: '192.168.1.1',
        port: 8080,
        performanceMetrics: {
          successRate: 0,
          avgLatency: 0,
          requestCount: 0,
          failureCount: 0,
          lastUsed: null
        }
      };
      proxyStore.setState({ proxies: [proxy] });

      const testResult = {
        success: true,
        avgLatency: 150,
        successRate: 95,
        requestCount: 100
      };
      proxies.test.mockResolvedValue(testResult);

      const result = await proxyStore.getState().testProxy(1);

      expect(result.success).toBe(true);
      expect(result.latency).toBeDefined();
      const updatedProxy = proxyStore.getState().proxies[0];
      expect(updatedProxy.performanceMetrics.avgLatency).toBe(150);
      expect(updatedProxy.performanceMetrics.successRate).toBe(95);
    });

    it('should handle test failures', async () => {
      const proxy = {
        id: 1,
        ip: '192.168.1.1',
        port: 8080,
        performanceMetrics: {
          successRate: 95,
          avgLatency: 150,
          requestCount: 100,
          failureCount: 0,
          lastUsed: null
        }
      };
      proxyStore.setState({ proxies: [proxy] });

      proxies.test.mockRejectedValue({ response: { data: { message: 'Connection failed' } } });

      const result = await proxyStore.getState().testProxy(1);

      expect(result.success).toBe(false);
      const updatedProxy = proxyStore.getState().proxies[0];
      expect(updatedProxy.performanceMetrics.failureCount).toBe(1);
    });
  });

  describe('Proxy Rotation', () => {
    it('should toggle rotation settings', () => {
      proxyStore.getState().toggleRotation(true);
      
      const state = proxyStore.getState();
      expect(state.rotationSettings.enabled).toBe(true);
      expect(state.rotationSettings.lastRotation).toBeTruthy();
    });

    it('should update rotation interval', () => {
      proxyStore.getState().setRotationInterval(120);
      
      expect(proxyStore.getState().rotationSettings.interval).toBe(120);
    });
  });

  describe('Selectors', () => {
    beforeEach(() => {
      const proxies = [
        { id: 1, status: 'active', health: { status: 'healthy' } },
        { id: 2, status: 'active', health: { status: 'degraded' } },
        { id: 3, status: 'disabled', health: { status: 'healthy' } }
      ];
      proxyStore.setState({ proxies });
    });

    it('should get proxy by id', () => {
      const proxy = proxyStore.getState().getProxyById(1);
      expect(proxy).toBeTruthy();
      expect(proxy.id).toBe(1);
    });

    it('should get active proxies', () => {
      const active = proxyStore.getState().getActiveProxies();
      expect(active).toHaveLength(2);
    });

    it('should get healthy proxies', () => {
      const healthy = proxyStore.getState().getHealthyProxies();
      expect(healthy).toHaveLength(2);
    });

    it('should get degraded proxies', () => {
      const degraded = proxyStore.getState().getDegradedProxies();
      expect(degraded).toHaveLength(1);
    });

    it('should get available proxies', () => {
      const available = proxyStore.getState().getAvailableProxies();
      expect(available).toHaveLength(1);
      expect(available[0].id).toBe(1);
    });
  });
});
