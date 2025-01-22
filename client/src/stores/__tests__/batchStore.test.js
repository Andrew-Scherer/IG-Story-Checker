import { act } from '@testing-library/react';
import useBatchStore from '../../stores/batchStore';
import { batches } from '../../api';

// Mock API
jest.mock('../../api', () => ({
  batches: {
    list: jest.fn(),
    create: jest.fn(),
    start: jest.fn(),
    stop: jest.fn(),
    delete: jest.fn()
  }
}));

describe('batchStore', () => {
  let store;

  beforeEach(() => {
    // Reset store
    useBatchStore.setState({
      batches: [],
      loading: false,
      error: null
    });
    store = useBatchStore.getState();
    
    // Clear mocks
    jest.clearAllMocks();
  });

  describe('Batch Start Flow', () => {
    it('starts selected batches successfully', async () => {
      // Mock API response
      const mockBatch = {
        id: '1',
        status: 'in_progress',
        total_profiles: 10,
        completed_profiles: 0,
        successful_checks: 0,
        failed_checks: 0
      };
      batches.start.mockResolvedValue([mockBatch]);
      batches.list.mockResolvedValue([mockBatch]);

      // Start batch
      await act(async () => {
        await store.startBatches(['1']);
      });

      // Verify API called correctly
      expect(batches.start).toHaveBeenCalledWith({ batch_ids: ['1'] });
      
      // Verify store updated
      expect(store.loading).toBe(false);
      expect(store.error).toBe(null);
      expect(store.batches).toEqual([mockBatch]);
    });

    it('handles start batch failure', async () => {
      // Mock API error
      const error = new Error('Failed to start batch');
      batches.start.mockRejectedValue(error);

      // Attempt to start batch
      await act(async () => {
        try {
          await store.startBatches(['1']);
        } catch (e) {
          // Error should be thrown
        }
      });

      // Verify error handling
      expect(store.loading).toBe(false);
      expect(store.error).toBe(error.message);
      expect(batches.start).toHaveBeenCalledWith({ batch_ids: ['1'] });
    });

    it('prevents starting multiple batches', async () => {
      // Mock API responses
      const mockBatch1 = { id: '1', status: 'in_progress' };
      const mockBatch2 = { id: '2', status: 'queued' };
      
      batches.start.mockImplementation(async ({ batch_ids }) => {
        if (batch_ids.includes('1')) {
          return [mockBatch1];
        }
        throw new Error('Another batch is running');
      });
      
      // Start first batch
      await act(async () => {
        await store.startBatches(['1']);
      });

      // Try to start second batch
      await act(async () => {
        try {
          await store.startBatches(['2']);
        } catch (e) {
          expect(e.message).toBe('Another batch is running');
        }
      });

      // Verify only first batch started
      expect(batches.start).toHaveBeenCalledTimes(2);
      expect(store.error).toBe('Another batch is running');
    });
  });

  describe('Batch Progress Tracking', () => {
    it('updates batch progress', async () => {
      // Mock initial batch
      const initialBatch = {
        id: '1',
        status: 'in_progress',
        total_profiles: 10,
        completed_profiles: 0,
        successful_checks: 0,
        failed_checks: 0
      };

      // Mock progress updates
      const progressUpdates = [
        { ...initialBatch, completed_profiles: 5, successful_checks: 3 },
        { ...initialBatch, completed_profiles: 10, successful_checks: 7, status: 'done' }
      ];

      // Setup API mocks
      batches.start.mockResolvedValue([initialBatch]);
      batches.list.mockImplementation(async () => {
        return [progressUpdates[batches.list.mock.calls.length - 1]];
      });

      // Start batch
      await act(async () => {
        await store.startBatches(['1']);
      });

      // Verify initial state
      expect(store.batches[0].completed_profiles).toBe(0);

      // Simulate progress updates
      await act(async () => {
        await store.fetchBatches();
      });
      expect(store.batches[0].completed_profiles).toBe(5);
      expect(store.batches[0].successful_checks).toBe(3);

      await act(async () => {
        await store.fetchBatches();
      });
      expect(store.batches[0].completed_profiles).toBe(10);
      expect(store.batches[0].successful_checks).toBe(7);
      expect(store.batches[0].status).toBe('done');
    });

    it('handles progress update failures', async () => {
      // Mock initial batch
      const mockBatch = {
        id: '1',
        status: 'in_progress',
        total_profiles: 10,
        completed_profiles: 0
      };

      // Setup API mocks
      batches.start.mockResolvedValue([mockBatch]);
      batches.list.mockRejectedValue(new Error('Failed to fetch progress'));

      // Start batch
      await act(async () => {
        await store.startBatches(['1']);
      });

      // Attempt progress update
      await act(async () => {
        await store.fetchBatches();
      });

      // Verify error handling
      expect(store.error).toBe('Failed to fetch progress');
      expect(store.loading).toBe(false);
    });
  });

  describe('Batch Management', () => {
    it('fetches batches on mount', async () => {
      const mockBatches = [
        { id: '1', status: 'queued' },
        { id: '2', status: 'in_progress' }
      ];
      batches.list.mockResolvedValue(mockBatches);

      await act(async () => {
        await store.fetchBatches();
      });

      expect(batches.list).toHaveBeenCalled();
      expect(store.batches).toEqual(mockBatches);
      expect(store.loading).toBe(false);
    });

    it('stops running batch', async () => {
      const mockBatch = { id: '1', status: 'queued' };
      batches.stop.mockResolvedValue([mockBatch]);
      batches.list.mockResolvedValue([mockBatch]);

      await act(async () => {
        await store.stopBatches(['1']);
      });

      expect(batches.stop).toHaveBeenCalledWith({ batch_ids: ['1'] });
      expect(store.batches[0].status).toBe('queued');
    });

    it('deletes batch', async () => {
      const mockBatch = { id: '1' };
      batches.delete.mockResolvedValue();
      batches.list.mockResolvedValue([]);

      await act(async () => {
        await store.deleteBatches(['1']);
      });

      expect(batches.delete).toHaveBeenCalledWith({ batch_ids: ['1'] });
      expect(store.batches).toHaveLength(0);
    });
  });
});
