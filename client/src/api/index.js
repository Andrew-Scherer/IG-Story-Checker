import axios from 'axios';

export const API_URL = 'http://localhost:5000/api';

class ApiError extends Error {
  constructor(message, response) {
    super(message);
    this.name = 'ApiError';
    this.response = response;
  }

  static fromResponse(response) {
    const message = response?.data?.message || response?.statusText || 'Unknown error';
    return new ApiError(message, response);
  }
}

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: true,
  timeout: 10000, // Reduced timeout to fail faster
  validateStatus: status => {
    return status >= 200 && status < 300; // Only resolve for 2xx status codes
  },
  // Retry configuration
  retry: 3,
  retryDelay: (retryCount) => {
    return retryCount * 1000; // Time between retries (1s, 2s, 3s)
  }
});

// Add retry interceptor
axiosInstance.interceptors.response.use(undefined, async (err) => {
  const { config } = err;
  if (!config || !config.retry) {
    return Promise.reject(err);
  }
  
  config.retryCount = config.retryCount || 0;
  
  if (config.retryCount >= config.retry) {
    return Promise.reject(err);
  }
  
  config.retryCount += 1;
  console.log(`Retrying request (${config.retryCount}/${config.retry})`);
  
  const delayMs = config.retryDelay(config.retryCount);
  await new Promise(resolve => setTimeout(resolve, delayMs));
  
  return axiosInstance(config);
});

// Request interceptor for debugging
axiosInstance.interceptors.request.use(
  config => {
    console.log(`=== API Request ===`);
    console.log(`${config.method.toUpperCase()} ${config.url}`);
    console.log('Request headers:', config.headers);
    console.log('Request data:', config.data);
    console.log('Request params:', config.params);
    return config;
  },
  error => {
    console.error('!!! Request interceptor error !!!', error);
    return Promise.reject(error);
  }
);

// Response interceptor for debugging
axiosInstance.interceptors.response.use(
  response => {
    console.log(`=== API Response ===`);
    console.log(`Status: ${response.status}`);
    console.log('Response headers:', response.headers);
    console.log('Response data:', response.data);
    return response;
  },
  error => {
    console.error('!!! API Error !!!');
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response headers:', error.response.headers);
      console.error('Response data:', error.response.data);
      throw ApiError.fromResponse(error.response);
    }
    console.error('Network error details:', error);
    throw new ApiError('Network Error');
  }
);

export const niches = {
  list: () => axiosInstance.get('/niches').then(res => res.data),
  create: (data) => axiosInstance.post('/niches', data).then(res => res.data),
  update: (id, data) => axiosInstance.put(`/niches/${id}`, data).then(res => res.data),
  delete: (id) => axiosInstance.delete(`/niches/${id}`).then(res => res.data)
};

export const profiles = {
  list: (params) => axiosInstance.get('/profiles', { params }).then(res => res.data),
  create: (data) => axiosInstance.post('/profiles', data).then(res => res.data),
  update: (id, data) => axiosInstance.put(`/profiles/${id}`, data).then(res => res.data),
  delete: (id) => axiosInstance.delete(`/profiles/${id}`).then(res => res.data),
  import: (nicheId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return axiosInstance.post(`/profiles/niches/${nicheId}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }).then(res => res.data);
  },
  refreshStories: () => axiosInstance.post('/profiles/refresh-stories').then(res => res.data)
};

export const batches = {
  list: () => axiosInstance.get('/batches').then(res => res.data),
  create: (data) => axiosInstance.post('/batches', data).then(res => res.data),
  start: (data) => axiosInstance.post('/batches/start', data).then(res => res.data),
  stop: (data) => axiosInstance.post('/batches/stop', data).then(res => res.data),
  resume: (data) => axiosInstance.post('/batches/resume', data).then(res => res.data),
  reset: (data) => axiosInstance.post('/batches/reset', data).then(res => res.data),
  delete: (data) => axiosInstance.delete('/batches', { data: { batch_ids: data.batch_ids } }).then(res => res.data),
  getLogs: (batchId, startTime, endTime, limit, offset) =>
    axiosInstance.get(`/batches/${batchId}/logs`, { 
      params: { 
        start_time: startTime, 
        end_time: endTime, 
        limit, 
        offset 
      } 
    }).then(res => res.data)
};

export const settings = {
  get: () => axiosInstance.get('/settings').then(res => res.data),
  update: (data) => axiosInstance.put('/settings', data).then(res => res.data)
};

export const proxies = {
  list: () => axiosInstance.get('/proxies').then(res => res.data),
  create: (data) => axiosInstance.post('/proxies', data).then(res => res.data),
  delete: (id) => axiosInstance.delete(`/proxies/${id}`).then(res => res.data),
  updateStatus: (id, data) => axiosInstance.patch(`/proxies/${id}/status`, data).then(res => res.data),
  getErrorLogs: (proxyId, limit = 20, offset = 0) => 
    axiosInstance.get(`/proxies/${proxyId}/error-logs`, { params: { limit, offset } }).then(res => res.data)
};

const api = {
  niches,
  profiles,
  batches,
  settings,
  proxies
};

export default api;
