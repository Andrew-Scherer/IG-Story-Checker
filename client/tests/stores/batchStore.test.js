import useBatchStore from '../../src/stores/batchStore';

describe('Batch Store', () => {
  let store;

  beforeEach(() => {
    // Clear the store before each test
    useBatchStore.setState({
      currentBatch: null,
      detections: [],
      loading: false,
      error: null
    });
    store = useBatchStore.getState();
  });

  describe('State Updates', () => {
    it('initializes with default state', () => {
      expect(store.currentBatch).toBeNull();
      expect(Array.isArray(store.detections)).toBeTruthy();
      expect(store.loading).toBeFalsy();
      expect(store.error).toBeNull();
    });

    it('updates loading state', () => {
      store.setLoading(true);
      expect(useBatchStore.getState().loading).toBeTruthy();
      
      store.setLoading(false);
      expect(useBatchStore.getState().loading).toBeFalsy();
    });

    it('updates error state', () => {
      const error = 'Test error';
      store.setError(error);
      expect(useBatchStore.getState().error).toBe(error);
      
      store.clearError();
      expect(useBatchStore.getState().error).toBeNull();
    });
  });

  describe('Batch Operations', () => {
    it('starts a new batch', async () => {
      const nicheId = 1;
      await store.runBatch(nicheId);
      
      const currentBatch = useBatchStore.getState().currentBatch;
      expect(currentBatch).toBeTruthy();
      expect(currentBatch.nicheId).toBe(nicheId);
      expect(currentBatch.current).toBe(0);
      expect(currentBatch.total).toBe(100);
      expect(currentBatch.startTime).toBeTruthy();
    });

    it('prevents running multiple batches simultaneously', async () => {
      const nicheId1 = 1;
      const nicheId2 = 2;
      
      await store.runBatch(nicheId1);
      await store.runBatch(nicheId2);
      
      const currentBatch = useBatchStore.getState().currentBatch;
      expect(currentBatch.nicheId).toBe(nicheId1);
    });

    it('adds detection', () => {
      const detection = {
        id: 1,
        nicheId: 1,
        username: 'test_user',
        detectedAt: new Date().toISOString()
      };
      
      store.addDetection(detection);
      expect(useBatchStore.getState().detections).toContainEqual(detection);
    });

    it('clears expired detections', () => {
      const now = new Date();
      const recent = new Date(now - 12 * 60 * 60 * 1000); // 12 hours ago
      const expired = new Date(now - 25 * 60 * 60 * 1000); // 25 hours ago
      
      const detections = [
        { id: 1, nicheId: 1, username: 'user1', detectedAt: recent.toISOString() },
        { id: 2, nicheId: 1, username: 'user2', detectedAt: expired.toISOString() }
      ];
      
      useBatchStore.setState({ detections });
      store.clearExpiredDetections();
      
      const remainingDetections = useBatchStore.getState().detections;
      expect(remainingDetections.length).toBe(1);
      expect(remainingDetections[0].id).toBe(1);
    });
  });

  describe('Clipboard Operations', () => {
    it('copies usernames to clipboard', () => {
      // Mock clipboard API
      const mockClipboard = {
        writeText: jest.fn().mockResolvedValue(undefined)
      };
      global.navigator.clipboard = mockClipboard;
      
      const usernames = ['user1', 'user2', 'user3'];
      store.copyToClipboard(usernames);
      
      expect(mockClipboard.writeText).toHaveBeenCalledWith(usernames.join('\n'));
    });

    it('handles clipboard errors', () => {
      // Mock clipboard API with error
      const mockClipboard = {
        writeText: jest.fn().mockRejectedValue(new Error('Clipboard error'))
      };
      global.navigator.clipboard = mockClipboard;
      
      // Mock console.error
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      const usernames = ['user1', 'user2'];
      store.copyToClipboard(usernames);
      
      expect(mockClipboard.writeText).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });

  describe('Batch Progress', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('updates batch progress over time', async () => {
      const nicheId = 1;
      await store.runBatch(nicheId);
      
      // Fast-forward 200ms (2 intervals)
      jest.advanceTimersByTime(200);
      
      const currentBatch = useBatchStore.getState().currentBatch;
      expect(currentBatch.current).toBeGreaterThan(0);
    });

    it('completes batch when reaching total', async () => {
      const nicheId = 1;
      await store.runBatch(nicheId);
      
      // Set progress near completion
      useBatchStore.setState({
        currentBatch: {
          nicheId,
          current: 99,
          total: 100,
          startTime: new Date().toISOString()
        }
      });
      
      // Fast-forward 200ms
      jest.advanceTimersByTime(200);
      
      expect(useBatchStore.getState().currentBatch).toBeNull();
    });
  });
});
