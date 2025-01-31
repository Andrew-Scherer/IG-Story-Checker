import { create } from 'zustand';
import { batches } from '../api';

// Simple, clear states that match the server
const BATCH_STATES = {
  QUEUED: 'queued',    // In queue with position > 0
  RUNNING: 'running',  // Currently processing (position = 0)
  PAUSED: 'paused',    // Stopped (position = null)
  DONE: 'done'        // Completed (position = null)
};

// Basic error types
const BATCH_ERRORS = {
  ALREADY_RUNNING: 'Batch is already running',
  INVALID_STATE: 'Invalid batch state for operation',
  NETWORK_ERROR: 'Network error occurred'
};

const useBatchStore = create((set, get) => ({
  // State
  batches: [],
  loading: false,
  error: null,
  batchLogs: [],
  totalLogs: 0,
  loadingLogs: false,

  // Actions
  fetchBatches: async () => {
    try {
      set({ loading: true, error: null });
      const response = await batches.list();
      set({ batches: response, loading: false });
    } catch (error) {
      console.error('Failed to fetch batches:', error);
      set({ error: BATCH_ERRORS.NETWORK_ERROR, loading: false });
    }
  },

  createBatch: async (profileIds, nicheId) => {
    try {
      set({ error: null });
      await batches.create({ profile_ids: profileIds, niche_id: nicheId });
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to create batch:', error);
      set({ error: error.message });
      throw error;
    }
  },

  startBatches: async (batchIds) => {
    try {
      set({ error: null });
      const cleanIds = batchIds.map(id => String(id).trim());
      await batches.start({ batch_ids: cleanIds });
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to start batches:', error);
      set({ error: error.response?.status === 409 ? BATCH_ERRORS.ALREADY_RUNNING : BATCH_ERRORS.NETWORK_ERROR });
      throw error;
    }
  },

  resumeBatches: async (batchIds) => {
    try {
      set({ error: null });
      const cleanIds = batchIds.map(id => String(id).trim());
      await batches.resume({ batch_ids: cleanIds });
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to resume batches:', error);
      set({ error: error.response?.status === 409 ? BATCH_ERRORS.ALREADY_RUNNING : BATCH_ERRORS.NETWORK_ERROR });
      throw error;
    }
  },

  stopBatches: async (batchIds) => {
    try {
      set({ error: null });
      const cleanIds = batchIds.map(id => String(id).trim());
      await batches.stop({ batch_ids: cleanIds });
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to stop batches:', error);
      set({ error: BATCH_ERRORS.NETWORK_ERROR });
      throw error;
    }
  },

  deleteBatches: async (batchIds) => {
    try {
      set({ error: null });
      const cleanIds = batchIds.map(id => String(id).trim());
      await batches.delete({ batch_ids: cleanIds });
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to delete batches:', error);
      set({ error: BATCH_ERRORS.NETWORK_ERROR });
      throw error;
    }
  },

  refreshBatches: async (batchIds) => {
    try {
      set({ error: null });
      const cleanIds = batchIds.map(id => String(id).trim());
      await batches.refresh({ batch_ids: cleanIds });
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to refresh batches:', error);
      set({ error: BATCH_ERRORS.NETWORK_ERROR });
      throw error;
    }
  },

  fetchBatchLogs: async (batchId, startTime, endTime, limit = 100, offset = 0) => {
    try {
      set({ error: null, loadingLogs: true });
      const response = await batches.getLogs(batchId, startTime, endTime, limit, offset);
      set({ batchLogs: response.logs, totalLogs: response.total, loadingLogs: false });
      return response;
    } catch (error) {
      console.error('Failed to fetch batch logs:', error);
      set({ error: BATCH_ERRORS.NETWORK_ERROR, loadingLogs: false });
      throw error;
    }
  },

  setError: (errorMessage) => set({ error: errorMessage }),
  clearError: () => set({ error: null }),
  clearBatchLogs: () => set({ batchLogs: [], totalLogs: 0 })
}));

export default useBatchStore;
