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
    'Content-Type': 'application/json'
  }
});

axiosInstance.interceptors.request.use(
  config => {
    console.log(`=== API Request ===`);
    console.log(`${config.method.toUpperCase()} ${config.url}`);
    console.log('Request headers:', config.headers);
    console.log('Request data:', config.data);
    return config;
  },
  error => {
    console.error('!!! Request interceptor error !!!', error);
    return Promise.reject(error);
  }
);

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
      console.error('Full error object:', error);
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
  delete: (id) => axiosInstance.delete(`/niches/${id}`).then(res => res.data),
  import: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return axiosInstance.post('/niches/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }).then(res => res.data);
  }
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

// Add more detailed error logging
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
    } else if (error.request) {
      console.error('No response received');
      console.error('Request details:', error.request);
    } else {
      console.error('Error setting up request:', error.message);
    }
    console.error('Error config:', error.config);
    console.error('Full error object:', error);
    throw error;
  }
);

export const batches = {
  list: () => axiosInstance.get('/batches').then(res => res.data),
  create: (data) => axiosInstance.post('/batches', data).then(res => res.data),
  start: (data) => {
    console.log('Sending start request with data:', data);
    return axiosInstance.post('/batches/start', data)
      .then(res => {
        console.log('Received response from start request:', res.data);
        return res.data;
      })
      .catch(error => {
        console.error('Error in start request:', error);
        throw error;
      });
  },
  stop: (data) => axiosInstance.post('/batches/stop', data).then(res => res.data),
  delete: (data) => axiosInstance.delete('/batches', { data: { batch_ids: data.batch_ids } }).then(res => res.data),
  getLogs: (batchId, startTime, endTime, limit, offset) => 
    axiosInstance.get(`/batches/${batchId}/logs`, { params: { start_time: startTime, end_time: endTime, limit, offset } }).then(res => res.data)
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
  addSession: (proxyId, data) => axiosInstance.post(`/proxies/${proxyId}/sessions`, data).then(res => res.data),
  updateSession: (proxyId, sessionId, data) => axiosInstance.put(`/proxies/${proxyId}/sessions/${sessionId}`, data).then(res => res.data),
  removeSession: (proxyId, sessionId) => axiosInstance.delete(`/proxies/${proxyId}/sessions/${sessionId}`).then(res => res.data),
  test: (id) => axiosInstance.post(`/proxies/${id}/test`).then(res => res.data),
  updateHealth: (id, data) => axiosInstance.post(`/proxies/${id}/health`, data).then(res => res.data),
  updateLimit: (id, data) => axiosInstance.patch(`/proxies/${id}/limit`, data).then(res => res.data)
};

const api = {
  niches,
  profiles,
  batches,
  settings,
  proxies
};

export default api;
