import { act } from 'react-dom/test-utils';
import useBatchStore from '../batchStore';
import { batches } from '../../api';

// Mock the API module
jest.mock('../../api', () => ({
  batches: {
    list: jest.fn(),
    create: jest.fn(),
    resume: jest.fn(),
    stop: jest.fn(),
    delete: jest.fn(),
    refresh: jest.fn(),
    getLogs: jest.fn()
  }
}));

describe('batchStore', () => {
  beforeEach(() => {
    // Clear store between tests
    useBatchStore.setState({
      batches: [],
      loading: false,
      error: null,
      batchLogs: [],
      totalLogs: 0,
      loadingLogs: false
    });
    // Clear all mocks
    jest.clearAllMocks();
  });

  describe('fetchBatches', () => {
    it('should fetch and update batches', async () => {
      const mockBatches = [
        { id: '1', status: 'queued', position: 1 },
        { id: '2', status: 'running', position: 0 }
      ];
      batches.list.mockResolvedValue(mockBatches);

      await act(async () => {
        await useBatchStore.getState().fetchBatches();
      });

      expect(useBatchStore.getState().batches).toEqual(mockBatches);
      expect(useBatchStore.getState().loading).toBe(false);
      expect(useBatchStore.getState().error).toBe(null);
    });

    it('should handle fetch errors', async () => {
      batches.list.mockRejectedValue(new Error('Network error'));

      await act(async () => {
        await useBatchStore.getState().fetchBatches();
      });

      expect(useBatchStore.getState().batches).toEqual([]);
      expect(useBatchStore.getState().loading).toBe(false);
      expect(useBatchStore.getState().error).toBe('Network error occurred');
    });
  });

  describe('resumeBatches', () => {
    it('should resume batches and refresh state', async () => {
      const batchIds = ['1', '2'];
      batches.resume.mockResolvedValue([]);
      batches.list.mockResolvedValue([
        { id: '1', status: 'queued', position: 1 },
        { id: '2', status: 'queued', position: 2 }
      ]);

      await act(async () => {
        await useBatchStore.getState().resumeBatches(batchIds);
      });

      expect(batches.resume).toHaveBeenCalledWith({ batch_ids: batchIds });
      expect(batches.list).toHaveBeenCalled();
      expect(useBatchStore.getState().error).toBe(null);
    });

    it('should handle already running error', async () => {
      const error = new Error('Already running');
      error.response = { status: 409 };
      batches.resume.mockRejectedValue(error);

      await act(async () => {
        try {
          await useBatchStore.getState().resumeBatches(['1']);
        } catch (e) {
          // Expected error
        }
      });

      expect(useBatchStore.getState().error).toBe('Batch is already running');
    });
  });

  describe('stopBatches', () => {
    it('should stop batches and refresh state', async () => {
      const batchIds = ['1', '2'];
      batches.stop.mockResolvedValue([]);
      batches.list.mockResolvedValue([
        { id: '1', status: 'paused', position: null },
        { id: '2', status: 'paused', position: null }
      ]);

      await act(async () => {
        await useBatchStore.getState().stopBatches(batchIds);
      });

      expect(batches.stop).toHaveBeenCalledWith({ batch_ids: batchIds });
      expect(batches.list).toHaveBeenCalled();
      expect(useBatchStore.getState().error).toBe(null);
    });
  });

  describe('deleteBatches', () => {
    it('should delete batches and refresh state', async () => {
      const batchIds = ['1', '2'];
      batches.delete.mockResolvedValue();
      batches.list.mockResolvedValue([]);

      await act(async () => {
        await useBatchStore.getState().deleteBatches(batchIds);
      });

      expect(batches.delete).toHaveBeenCalledWith({ batch_ids: batchIds });
      expect(batches.list).toHaveBeenCalled();
      expect(useBatchStore.getState().error).toBe(null);
    });
  });

  describe('fetchBatchLogs', () => {
    it('should fetch batch logs', async () => {
      const mockLogs = {
        logs: [{ id: '1', message: 'test' }],
        total: 1
      };
      batches.getLogs.mockResolvedValue(mockLogs);

      await act(async () => {
        await useBatchStore.getState().fetchBatchLogs('1');
      });

      expect(useBatchStore.getState().batchLogs).toEqual(mockLogs.logs);
      expect(useBatchStore.getState().totalLogs).toBe(mockLogs.total);
      expect(useBatchStore.getState().loadingLogs).toBe(false);
    });
  });
});
