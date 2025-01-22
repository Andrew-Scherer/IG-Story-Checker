import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { api } from '../../src/api';

describe('API Client', () => {
  let mock;

  beforeEach(() => {
    mock = new MockAdapter(axios);
    jest.useFakeTimers();
  });

  afterEach(() => {
    mock.reset();
    jest.useRealTimers();
  });

  describe('Core API Client', () => {
    it('should configure base request settings', () => {
      expect(api.defaults.baseURL).toBe(process.env.REACT_APP_API_URL);
      expect(api.defaults.timeout).toBe(30000);
      expect(api.defaults.headers.common['Content-Type']).toBe('application/json');
    });

    it('should handle authentication headers', () => {
      const token = 'test-token';
      api.setAuthToken(token);
      expect(api.defaults.headers.common['Authorization']).toBe(`Bearer ${token}`);
    });

    it('should handle request interceptors', async () => {
      mock.onGet('/test').reply(200);
      const requestSpy = jest.spyOn(api.interceptors.request, 'use');
      
      await api.get('/test');
      
      expect(requestSpy).toHaveBeenCalled();
    });

    it('should handle response interceptors', async () => {
      mock.onGet('/test').reply(200, { data: 'test' });
      const responseSpy = jest.spyOn(api.interceptors.response, 'use');
      
      await api.get('/test');
      
      expect(responseSpy).toHaveBeenCalled();
    });

    it('should handle request cancellation', async () => {
      mock.onGet('/test').reply(() => new Promise(resolve => setTimeout(resolve, 1000)));
      
      const promise = api.get('/test');
      api.cancelRequest('test');
      
      await expect(promise).rejects.toThrow('Request canceled');
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mock.onGet('/test').networkError();
      await expect(api.get('/test')).rejects.toThrow('Network Error');
    });

    it('should handle timeout errors', async () => {
      mock.onGet('/test').timeout();
      await expect(api.get('/test')).rejects.toThrow('timeout');
    });

    it('should handle rate limit responses', async () => {
      mock.onGet('/test').reply(429, {
        error: 'Too Many Requests',
        retryAfter: 60
      });
      
      await expect(api.get('/test')).rejects.toMatchObject({
        status: 429,
        retryAfter: 60
      });
    });

    it('should handle invalid auth responses', async () => {
      mock.onGet('/test').reply(401, { error: 'Unauthorized' });
      await expect(api.get('/test')).rejects.toMatchObject({
        status: 401
      });
    });

    it('should handle server error responses', async () => {
      mock.onGet('/test').reply(500, { error: 'Internal Server Error' });
      await expect(api.get('/test')).rejects.toMatchObject({
        status: 500
      });
    });

    it('should handle validation error responses', async () => {
      mock.onPost('/test').reply(400, {
        error: 'Validation Error',
        fields: { name: 'Required' }
      });
      
      await expect(api.post('/test', {})).rejects.toMatchObject({
        status: 400,
        fields: { name: 'Required' }
      });
    });
  });

  describe('Retry Logic', () => {
    it('should implement exponential backoff', async () => {
      mock.onGet('/test')
        .replyOnce(500)
        .replyOnce(500)
        .replyOnce(200, { data: 'success' });

      const result = await api.get('/test');
      
      expect(result.data).toEqual({ data: 'success' });
      expect(setTimeout).toHaveBeenCalledTimes(2);
      expect(setTimeout).toHaveBeenNthCalledWith(1, expect.any(Function), 1000);
      expect(setTimeout).toHaveBeenNthCalledWith(2, expect.any(Function), 2000);
    });

    it('should respect max retry attempts', async () => {
      mock.onGet('/test').reply(500);
      
      await expect(api.get('/test')).rejects.toThrow();
      expect(setTimeout).toHaveBeenCalledTimes(3); // Default max retries
    });

    it('should handle retry conditions', async () => {
      mock.onGet('/test').reply(404); // Non-retryable status
      
      await expect(api.get('/test')).rejects.toMatchObject({
        status: 404
      });
      expect(setTimeout).not.toHaveBeenCalled();
    });

    it('should handle retry abort conditions', async () => {
      mock.onGet('/test').reply(401); // Non-retryable auth error
      
      await expect(api.get('/test')).rejects.toMatchObject({
        status: 401
      });
      expect(setTimeout).not.toHaveBeenCalled();
    });
  });

  describe('Endpoint-Specific Tests', () => {
    describe('Niche API', () => {
      it('should handle niche creation', async () => {
        const niche = { name: 'Test Niche' };
        mock.onPost('/niches').reply(201, niche);
        
        const response = await api.niches.create(niche);
        expect(response).toEqual(niche);
      });

      it('should handle niche updates', async () => {
        const niche = { id: 1, name: 'Updated Niche' };
        mock.onPut('/niches/1').reply(200, niche);
        
        const response = await api.niches.update(1, niche);
        expect(response).toEqual(niche);
      });

      it('should handle niche deletion', async () => {
        mock.onDelete('/niches/1').reply(204);
        await expect(api.niches.delete(1)).resolves.not.toThrow();
      });

      it('should handle niche reordering', async () => {
        const order = [2, 1, 3];
        mock.onPatch('/niches/reorder').reply(200);
        
        await expect(api.niches.reorder(order)).resolves.not.toThrow();
      });

      it('should handle profile association', async () => {
        mock.onPost('/niches/1/profiles').reply(200);
        await expect(api.niches.addProfiles(1, [1, 2])).resolves.not.toThrow();
      });
    });

    describe('Profile API', () => {
      it('should handle profile CRUD operations', async () => {
        // Create
        const profile = { username: 'test' };
        mock.onPost('/profiles').reply(201, profile);
        expect(await api.profiles.create(profile)).toEqual(profile);

        // Read
        mock.onGet('/profiles/1').reply(200, profile);
        expect(await api.profiles.get(1)).toEqual(profile);

        // Update
        mock.onPut('/profiles/1').reply(200, profile);
        expect(await api.profiles.update(1, profile)).toEqual(profile);

        // Delete
        mock.onDelete('/profiles/1').reply(204);
        await expect(api.profiles.delete(1)).resolves.not.toThrow();
      });

      it('should handle bulk operations', async () => {
        const profiles = [
          { username: 'test1' },
          { username: 'test2' }
        ];
        
        mock.onPost('/profiles/bulk').reply(201, profiles);
        expect(await api.profiles.bulkCreate(profiles)).toEqual(profiles);
      });

      it('should handle status updates', async () => {
        mock.onPatch('/profiles/1/status').reply(200);
        await expect(api.profiles.updateStatus(1, 'active')).resolves.not.toThrow();
      });
    });

    describe('Batch API', () => {
      it('should handle batch creation', async () => {
        const batch = { profiles: [1, 2] };
        mock.onPost('/batches').reply(201, batch);
        expect(await api.batches.create(batch)).toEqual(batch);
      });

      it('should handle progress tracking', async () => {
        mock.onGet('/batches/1/progress').reply(200, { progress: 50 });
        expect(await api.batches.getProgress(1)).toEqual({ progress: 50 });
      });

      it('should handle result retrieval', async () => {
        mock.onGet('/batches/1/results').reply(200, { results: [] });
        expect(await api.batches.getResults(1)).toEqual({ results: [] });
      });
    });

    describe('Settings API', () => {
      it('should handle proxy configuration', async () => {
        const proxy = { host: 'localhost', port: 8080 };
        mock.onPost('/settings/proxies').reply(201, proxy);
        expect(await api.settings.addProxy(proxy)).toEqual(proxy);
      });

      it('should handle system settings', async () => {
        const settings = { theme: 'dark' };
        mock.onPut('/settings').reply(200, settings);
        expect(await api.settings.update(settings)).toEqual(settings);
      });

      it('should handle target management', async () => {
        const target = { daily: 100 };
        mock.onPut('/settings/targets').reply(200, target);
        expect(await api.settings.updateTargets(target)).toEqual(target);
      });
    });

    describe('Health Check', () => {
      it('should handle server status checks', async () => {
        mock.onGet('/health').reply(200, { status: 'healthy' });
        expect(await api.health.check()).toEqual({ status: 'healthy' });
      });

      it('should handle proxy health checks', async () => {
        mock.onGet('/health/proxies/1').reply(200, { status: 'healthy' });
        expect(await api.health.checkProxy(1)).toEqual({ status: 'healthy' });
      });
    });
  });
});
