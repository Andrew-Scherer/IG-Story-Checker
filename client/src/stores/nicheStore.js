import create from 'zustand';

// Initial dummy data for testing
const dummyNiches = [
  { id: 1, name: 'Fitness', order: 1 },
  { id: 2, name: 'Fashion', order: 2 },
  { id: 3, name: 'Food', order: 3 }
];

const useNicheStore = create((set, get) => ({
  // State
  niches: dummyNiches, // Initialize with dummy data
  selectedNicheId: null,
  loading: false,
  error: null,

  // Actions
  setNiches: (niches) => set({ niches }),
  
  setSelectedNicheId: (id) => set({ selectedNicheId: id }),
  
  addNiche: (niche) => {
    const niches = get().niches;
    const newNiche = {
      ...niche,
      id: Date.now(), // Simple ID generation
      order: niches.length + 1
    };
    set({ niches: [...niches, newNiche] });
  },

  updateNiche: (id, updates) => {
    const niches = get().niches.map(niche =>
      niche.id === id ? { ...niche, ...updates } : niche
    );
    set({ niches });
  },

  deleteNiche: (id) => {
    const niches = get().niches.filter(niche => niche.id !== id);
    set({ 
      niches,
      selectedNicheId: get().selectedNicheId === id ? null : get().selectedNicheId
    });
  },

  reorderNiches: (fromIndex, toIndex) => {
    const niches = [...get().niches];
    const [movedNiche] = niches.splice(fromIndex, 1);
    niches.splice(toIndex, 0, movedNiche);
    
    // Update order property for each niche
    const updatedNiches = niches.map((niche, index) => ({
      ...niche,
      order: index + 1
    }));
    
    set({ niches: updatedNiches });
  },

  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),

  // Selectors
  getSortedNiches: () => {
    const { niches } = get();
    return [...niches].sort((a, b) => a.order - b.order);
  },

  getSelectedNiche: () => {
    const { niches, selectedNicheId } = get();
    return niches.find(niche => niche.id === selectedNicheId) || null;
  }
}));

export default useNicheStore;
