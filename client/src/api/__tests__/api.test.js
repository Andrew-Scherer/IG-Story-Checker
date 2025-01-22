import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { createApi } from '../index';

describe('API Client', () => {
  let mock;
  let testApi;
  let requestSpy;
  let responseSpy;
  let setTimeoutSpy;

  beforeEach(() => {
    // Mock setTimeout
    setTimeoutSpy = jest.spyOn(global, 'setTimeout');
    
    // Create spies before creating API instance
    const requestInterceptor = jest.fn(config => config);
    const responseInterceptor = jest.fn(response => response);
    
    // Create new API instance for each test
    testApi = createApi();
    
    // Add test interceptors
    testApi.interceptors.request.use(requestInterceptor);
    testApi.interceptors.response.use(responseInterceptor);
    
    // Store spies for assertions
    requestSpy = requestInterceptor;
    responseSpy = responseInterceptor;
    
    // Create mock adapter
    mock = new MockAdapter(testApi);
    
    // Setup timer mocks
    jest.useFakeTimers();
  });

  afterEach(() => {
    mock.reset();
    jest.useRealTimers();
    setTimeoutSpy.mockRestore();
  });

  describe('Core API Client', () => {
    it('should configure base request settings', () => {
      expect(testApi.defaults.baseURL).toBe('http://localhost:3000/api');
      expect(testApi.defaults.timeout).toBe(30000);
      expect(testApi.defaults.headers.common['Content-Type']).toBe('application/json');
    });

    it('should handle authentication headers', () => {
      const token = 'test-token';
      testApi.setAuthToken(token);
      expect(testApi.defaults.headers.common['Authorization']).toBe(`Bearer ${token}`);
    });

    it('should handle request interceptors', async () => {
      mock.onGet('/test').reply(200);
      await testApi.get('/test');
      expect(requestSpy).toHaveBeenCalled();
    });

    it('should handle response interceptors', async () => {
      mock.onGet('/test').reply(200, { data: 'test' });
      await testApi.get('/test');
      expect(responseSpy).toHaveBeenCalled();
    });

    it('should handle request cancellation', async () => {
      mock.onGet('/test').reply(() => new Promise(resolve => setTimeout(resolve, 100)));
      const promise = testApi.get('/test', { cancelId: 'test' });
      testApi.cancelRequest('test');
      await expect(promise).rejects.toThrow('Request canceled');
    }, 1000);
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mock.onGet('/test').networkError();
      await expect(testApi.get('/test')).rejects.toThrow('Network Error');
    });

    it('should handle timeout errors', async () => {
      mock.onGet('/test').timeout();
      await expect(testApi.get('/test')).rejects.toThrow('timeout');
    });

    it('should handle rate limit responses', async () => {
      mock.onGet('/test').reply(429, {
        error: 'Too Many Requests',
        retryAfter: 60
      });
      
      await expect(testApi.get('/test')).rejects.toMatchObject({
        message: 'Rate Limited',
        status: 429,
        retryAfter: 60
      });
    });

    it('should handle invalid auth responses', async () => {
      mock.onGet('/test').reply(401, { error: 'Unauthorized' });
      await expect(testApi.get('/test')).rejects.toMatchObject({
        message: 'Unauthorized',
        status: 401
      });
    });

    it('should handle server error responses', async () => {
      mock.onGet('/test').reply(500, { error: 'Internal Server Error' });
      await expect(testApi.get('/test')).rejects.toMatchObject({
        message: 'Internal Server Error',
        status: 500
      });
    });

    it('should handle validation error responses', async () => {
      mock.onGet('/test').reply(400, {
        error: 'Validation Error',
        fields: { name: 'Required' }
      });
      
      await expect(testApi.get('/test')).rejects.toMatchObject({
        message: 'Validation Error',
        status: 400,
        fields: { name: 'Required' }
      });
    });
  });

  describe('Retry Logic', () => {
    it('should implement exponential backoff', async () => {
      mock
        .onGet('/test')
        .reply(500)
        .onGet('/test')
        .reply(500)
        .onGet('/test')
        .reply(200, { data: 'success' });

      const promise = testApi.get('/test');
      
      // Fast-forward through retries
      jest.runAllTimers();
      
      const result = await promise;
      expect(result).toEqual({ data: 'success' });
      expect(setTimeoutSpy).toHaveBeenCalledTimes(2);
      expect(setTimeoutSpy).toHaveBeenNthCalledWith(1, expect.any(Function), 1000);
      expect(setTimeoutSpy).toHaveBeenNthCalledWith(2, expect.any(Function), 2000);
    });

    it('should respect max retry attempts', async () => {
      mock.onGet('/test').reply(500);
      
      const promise = testApi.get('/test');
      jest.runAllTimers();
      
      await expect(promise).rejects.toMatchObject({
        message: 'Internal Server Error',
        status: 500
      });
      expect(setTimeoutSpy).toHaveBeenCalledTimes(3);
    });

    it('should handle retry conditions', async () => {
      mock
        .onGet('/test')
        .reply(500)
        .onGet('/test')
        .reply(200, { data: 'success' });
      
      const promise = testApi.get('/test');
      jest.runAllTimers();
      
      const result = await promise;
      expect(result).toEqual({ data: 'success' });
      expect(setTimeoutSpy).toHaveBeenCalledTimes(1);
      expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 1000);
    });

    it('should handle retry abort conditions', async () => {
      mock.onGet('/test').reply(401, { error: 'Unauthorized' });
      
      const promise = testApi.get('/test');
      jest.runAllTimers();
      
      await expect(promise).rejects.toMatchObject({
        message: 'Unauthorized',
        status: 401
      });
      expect(setTimeoutSpy).not.toHaveBeenCalled();
    });
  });

  describe('Endpoint-Specific Tests', () => {
    describe('Niche API', () => {
      it('should handle niche creation', async () => {
        const niche = { name: 'Test Niche' };
        mock.onPost('/niches').reply(201, niche);
        
        const response = await testApi.niches.create(niche);
        expect(response).toEqual(niche);
      });

      it('should handle niche updates', async () => {
        const niche = { id: 1, name: 'Updated Niche' };
        mock.onPut('/niches/1').reply(200, niche);
        
        const response = await testApi.niches.update(1, niche);
        expect(response).toEqual(niche);
      });

      it('should handle niche deletion', async () => {
        mock.onDelete('/niches/1').reply(204);
        await expect(testApi.niches.delete(1)).resolves.not.toThrow();
      });

      it('should handle niche reordering', async () => {
        const order = [2, 1, 3];
        mock.onPatch('/niches/reorder').reply(200);
        
        await expect(testApi.niches.reorder(order)).resolves.not.toThrow();
      });

      it('should handle profile association', async () => {
        mock.onPost('/niches/1/profiles').reply(200);
        await expect(testApi.niches.addProfiles(1, [1, 2])).resolves.not.toThrow();
      });
    });

    describe('Profile API', () => {
      it('should handle profile CRUD operations', async () => {
        // Create
        const profile = { username: 'test' };
        mock.onPost('/profiles').reply(201, profile);
        expect(await testApi.profiles.create(profile)).toEqual(profile);

        // Read
        mock.onGet('/profiles/1').reply(200, profile);
        expect(await testApi.profiles.get(1)).toEqual(profile);

        // Update
        mock.onPut('/profiles/1').reply(200, profile);
        expect(await testApi.profiles.update(1, profile)).toEqual(profile);

        // Delete
        mock.onDelete('/profiles/1').reply(204);
        await expect(testApi.profiles.delete(1)).resolves.not.toThrow();
      });

      it('should handle bulk operations', async () => {
        const profiles = [
          { username: 'test1' },
          { username: 'test2' }
        ];
        
        mock.onPost('/profiles/bulk').reply(201, profiles);
        expect(await testApi.profiles.bulkCreate(profiles)).toEqual(profiles);
      });

      it('should handle status updates', async () => {
        mock.onPatch('/profiles/1/status').reply(200);
        await expect(testApi.profiles.updateStatus(1, 'active')).resolves.not.toThrow();
      });
    });

    describe('Batch API', () => {
      it('should handle batch creation', async () => {
        const batch = { profiles: [1, 2] };
        mock.onPost('/batches').reply(201, batch);
        expect(await testApi.batches.create(batch)).toEqual(batch);
      });

      it('should handle progress tracking', async () => {
        mock.onGet('/batches/1/progress').reply(200, { progress: 50 });
        expect(await testApi.batches.getProgress(1)).toEqual({ progress: 50 });
      });

      it('should handle result retrieval', async () => {
        mock.onGet('/batches/1/results').reply(200, { results: [] });
        expect(await testApi.batches.getResults(1)).toEqual({ results: [] });
      });
    });

    describe('Settings API', () => {
      it('should handle proxy configuration', async () => {
        const proxy = { host: 'localhost', port: 8080 };
        mock.onPost('/settings/proxies').reply(201, proxy);
        expect(await testApi.settings.addProxy(proxy)).toEqual(proxy);
      });

      it('should handle system settings', async () => {
        const settings = { theme: 'dark' };
        mock.onPut('/settings').reply(200, settings);
        expect(await testApi.settings.update(settings)).toEqual(settings);
      });

      it('should handle target management', async () => {
        const target = { daily: 100 };
        mock.onPut('/settings/targets').reply(200, target);
        expect(await testApi.settings.updateTargets(target)).toEqual(target);
      });
    });

    describe('Health Check', () => {
      it('should handle server status checks', async () => {
        mock.onGet('/health').reply(200, { status: 'healthy' });
        expect(await testApi.health.check()).toEqual({ status: 'healthy' });
      });

      it('should handle proxy health checks', async () => {
        mock.onGet('/health/proxies/1').reply(200, { status: 'healthy' });
        expect(await testApi.health.checkProxy(1)).toEqual({ status: 'healthy' });
      });
    });
  });
});
