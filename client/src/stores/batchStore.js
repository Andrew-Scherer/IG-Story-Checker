import { create } from 'zustand';
import { batches } from '../api';

const useBatchStore = create((set, get) => ({
  // State
  batches: [],
  loading: false,
  error: null,

  // Actions
  fetchBatches: async () => {
    try {
      set({ loading: true, error: null });
      const response = await batches.list();
      set({ batches: response, loading: false });
    } catch (error) {
      console.error('Failed to fetch batches:', error);
      set({ error: error.message, loading: false });
    }
  },

  createBatch: async (profileIds, nicheId) => {
    try {
      set({ error: null });
      const response = await batches.create({ profile_ids: profileIds, niche_id: nicheId });
      await get().fetchBatches();
      return response;
    } catch (error) {
      console.error('Failed to create batch:', error);
      set({ error: error.message });
      throw error;
    }
  },

  startBatches: async (batchIds) => {
    try {
      set({ error: null });
      // Ensure batch IDs are strings
      const cleanIds = batchIds.map(id => String(id).trim());
      console.log('Sending start request for batch IDs:', cleanIds);
      const response = await batches.start({ batch_ids: cleanIds });
      console.log('Received response from start request:', response);
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to start batches:', error);
      set({ error: error.message });
      throw error;
    }
  },

  resumeBatches: async (batchIds) => {
    try {
      set({ error: null });
      // Ensure batch IDs are strings
      const cleanIds = batchIds.map(id => String(id).trim());
      console.log('Sending resume request for batch IDs:', cleanIds);
      const response = await batches.resume({ batch_ids: cleanIds });
      console.log('Received response from resume request:', response);
      
      // Update store with preserved state from response
      const currentBatches = get().batches;
      const updatedBatches = currentBatches.map(batch => {
        const resumedBatch = response.find(r => r.id === batch.id);
        return resumedBatch || batch;
      });
      set({ batches: updatedBatches });
      
      // Single delayed fetch to sync any changes
      await new Promise(resolve => setTimeout(resolve, 1000));
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to resume batches:', error);
      set({ error: error.message });
      throw error;
    }
  },

  stopBatches: async (batchIds) => {
    try {
      set({ error: null });
      // Ensure batch IDs are strings
      const cleanIds = batchIds.map(id => String(id).trim());
      // Stop batches and use response to update store immediately
      const response = await batches.stop({ batch_ids: cleanIds });
      
      // Update store with preserved state from response
      const currentBatches = get().batches;
      const updatedBatches = currentBatches.map(batch => {
        const stoppedBatch = response.find(b => b.id === batch.id);
        return stoppedBatch || batch;
      });
      set({ batches: updatedBatches });
      
      // Single fetch to sync any changes
      await new Promise(resolve => setTimeout(resolve, 500));
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to stop batches:', error);
      set({ error: error.message });
      throw error;
    }
  },

  deleteBatches: async (batchIds) => {
    try {
      set({ error: null });
      // Ensure batch IDs are strings
      const cleanIds = batchIds.map(id => String(id).trim());
      await batches.delete({ batch_ids: cleanIds });
      await get().fetchBatches();
    } catch (error) {
      console.error('Failed to delete batches:', error);
      set({ error: error.message });
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
      set({ error: error.message, loadingLogs: false });
      throw error;
    }
  },

  setError: (errorMessage) => set({ error: errorMessage }),

  clearError: () => set({ error: null }),

  clearBatchLogs: () => set({ batchLogs: [], totalLogs: 0 })
}));

export default useBatchStore;
