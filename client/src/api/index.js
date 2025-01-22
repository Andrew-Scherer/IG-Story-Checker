import axios from 'axios';

// Constants
const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY = 1000;
const RETRY_STATUS_CODES = [408, 500, 502, 503, 504];

// Custom error class for API errors
class ApiError extends Error {
  constructor(message, status, data = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    Object.assign(this, data);
  }
}

// Request cancellation map
const cancelTokens = new Map();

// Create API instance factory to allow recreation in tests
export const createApi = () => {
  const instance = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3000/api',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json'
    }
  });

  // Setup interceptors
  instance.interceptors.request.use(
    config => {
      // Cancel any existing requests with the same ID
      if (config.cancelId) {
        if (cancelTokens.has(config.cancelId)) {
          cancelTokens.get(config.cancelId).cancel('Request canceled');
        }
        const source = axios.CancelToken.source();
        cancelTokens.set(config.cancelId, source);
        config.cancelToken = source.token;
      }
      return config;
    },
    error => Promise.reject(error)
  );

  instance.interceptors.response.use(
    response => response.data,
    error => {
      if (axios.isCancel(error)) {
        throw new ApiError('Request canceled', 0, { canceled: true });
      }

      const status = error.response?.status;
      const data = error.response?.data;

      // Handle specific error types
      switch (status) {
        case 400:
          throw new ApiError('Validation Error', status, { fields: data.fields });
        case 401:
          throw new ApiError('Unauthorized', status);
        case 429:
          throw new ApiError('Rate Limited', status, { retryAfter: data.retryAfter });
        default:
          throw new ApiError(
            data?.error || error.message || 'Unknown Error',
            status || 0
          );
      }
    }
  );

  // Add custom methods
  instance.setAuthToken = function(token) {
    this.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  instance.cancelRequest = function(id) {
    if (cancelTokens.has(id)) {
      cancelTokens.get(id).cancel();
      cancelTokens.delete(id);
    }
  };

  // Add endpoint implementations
  instance.niches = {
    create: (niche) => instance.post('/niches', niche),
    update: (id, niche) => instance.put(`/niches/${id}`, niche),
    delete: (id) => instance.delete(`/niches/${id}`),
    reorder: (order) => instance.patch('/niches/reorder', { order }),
    addProfiles: (nicheId, profileIds) => 
      instance.post(`/niches/${nicheId}/profiles`, { profileIds })
  };

  instance.profiles = {
    create: (profile) => instance.post('/profiles', profile),
    get: (id) => instance.get(`/profiles/${id}`),
    update: (id, profile) => instance.put(`/profiles/${id}`, profile),
    delete: (id) => instance.delete(`/profiles/${id}`),
    bulkCreate: (profiles) => instance.post('/profiles/bulk', { profiles }),
    updateStatus: (id, status) => 
      instance.patch(`/profiles/${id}/status`, { status })
  };

  instance.batches = {
    create: (batch) => instance.post('/batches', batch),
    getProgress: (id) => instance.get(`/batches/${id}/progress`),
    getResults: (id) => instance.get(`/batches/${id}/results`)
  };

  instance.settings = {
    addProxy: (proxy) => instance.post('/settings/proxies', proxy),
    update: (settings) => instance.put('/settings', settings),
    updateTargets: (targets) => instance.put('/settings/targets', targets)
  };

  instance.health = {
    check: () => instance.get('/health'),
    checkProxy: (id) => instance.get(`/health/proxies/${id}`)
  };

  // Apply retry mechanism
  const originalRequest = instance.request;
  instance.request = async function(config) {
    let retryCount = 0;
    const maxRetries = 3;
    const initialDelay = 1000;

    while (true) {
      try {
        return await originalRequest.call(instance, config);
      } catch (error) {
        const status = error.response?.status;

        if (
          retryCount >= maxRetries ||
          !RETRY_STATUS_CODES.includes(status) ||
          status === 401 ||
          status === 404 ||
          status === 400
        ) {
          throw error;
        }

        const delay = initialDelay * Math.pow(2, retryCount);
        await new Promise(resolve => setTimeout(resolve, delay));
        retryCount++;
      }
    }
  };

  return instance;
};

// Export default instance
export const api = createApi();


export default api;
