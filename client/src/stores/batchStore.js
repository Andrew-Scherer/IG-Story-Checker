import create from 'zustand';

// Generate some dummy detections from the last 24 hours
const generateDummyDetections = () => {
  const detections = [];
  const now = new Date();
  const nicheIds = [1, 2, 3]; // Match the dummy niches from nicheStore

  // Generate 50 random detections
  for (let i = 0; i < 50; i++) {
    const nicheId = nicheIds[Math.floor(Math.random() * nicheIds.length)];
    const hoursAgo = Math.random() * 24; // Random time within last 24 hours
    const detectedAt = new Date(now - hoursAgo * 60 * 60 * 1000);

    detections.push({
      id: i + 1,
      nicheId,
      username: `${nicheId === 1 ? 'fitness' : nicheId === 2 ? 'fashion' : 'food'}_user_${i + 1}`,
      detectedAt: detectedAt.toISOString()
    });
  }

  return detections;
};

const useBatchStore = create((set, get) => ({
  // State
  currentBatch: null,
  detections: generateDummyDetections(),
  loading: false,
  error: null,

  // Actions
  runBatch: async (nicheId) => {
    const state = get();
    if (state.currentBatch) return;

    // Create sample batch
    set({
      currentBatch: {
        nicheId,
        current: 0,
        total: 100,
        startTime: new Date().toISOString()
      }
    });

    // Simulate batch progress
    const interval = setInterval(() => {
      const current = get().currentBatch;
      if (!current || current.nicheId !== nicheId) {
        clearInterval(interval);
        return;
      }

      if (current.current >= current.total) {
        clearInterval(interval);
        set({ currentBatch: null });
        return;
      }

      // 20% chance to add detection
      if (Math.random() > 0.8) {
        const detection = {
          id: Date.now(),
          nicheId,
          username: `${nicheId === 1 ? 'fitness' : nicheId === 2 ? 'fashion' : 'food'}_user_${Math.floor(Math.random() * 1000)}`,
          detectedAt: new Date().toISOString()
        };
        get().addDetection(detection);
      }

      set({
        currentBatch: {
          ...current,
          current: current.current + 1
        }
      });
    }, 100); // Update every 100ms for demo
  },

  addDetection: (detection) => {
    const state = get();
    set({
      detections: [...state.detections, detection]
    });
  },

  clearExpiredDetections: () => {
    const state = get();
    const now = new Date();
    const cutoff = new Date(now - 24 * 60 * 60 * 1000); // 24 hours ago

    const validDetections = state.detections.filter(detection => {
      const detectionTime = new Date(detection.detectedAt);
      return detectionTime > cutoff;
    });

    if (validDetections.length !== state.detections.length) {
      set({ detections: validDetections });
    }
  },

  copyToClipboard: (usernames) => {
    const text = usernames.join('\n');
    navigator.clipboard.writeText(text).catch(error => {
      console.error('Failed to copy:', error);
    });
  },

  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null })
}));

export default useBatchStore;
