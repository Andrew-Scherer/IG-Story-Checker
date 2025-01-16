import create from 'zustand';

// Initial dummy data for testing
const dummyProfiles = [
  { 
    id: 1, 
    username: 'fitness_guru', 
    nicheId: 1,
    status: 'active',
    lastChecked: new Date().toISOString(),
    lastDetected: new Date().toISOString(),
    totalChecks: 15,
    totalDetections: 8
  },
  { 
    id: 2, 
    username: 'fashion_trends', 
    nicheId: 2,
    status: 'active',
    lastChecked: new Date().toISOString(),
    lastDetected: new Date().toISOString(),
    totalChecks: 12,
    totalDetections: 5
  },
  { 
    id: 3, 
    username: 'foodie_delights', 
    nicheId: 3,
    status: 'active',
    lastChecked: new Date().toISOString(),
    lastDetected: new Date().toISOString(),
    totalChecks: 10,
    totalDetections: 3
  }
];

const useProfileStore = create((set, get) => ({
  // State
  profiles: dummyProfiles, // Initialize with dummy data
  filters: {
    nicheId: null,
    status: 'active',
    search: ''
  },
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0
  },
  loading: false,
  error: null,

  // Actions
  setProfiles: (profiles) => set({ profiles }),

  addProfiles: (newProfiles) => {
    const currentProfiles = get().profiles;
    const uniqueProfiles = newProfiles.filter(
      newProfile => !currentProfiles.some(p => p.username === newProfile.username)
    );
    set({ profiles: [...currentProfiles, ...uniqueProfiles] });
  },

  updateProfile: (id, updates) => {
    const profiles = get().profiles.map(profile =>
      profile.id === id ? { ...profile, ...updates } : profile
    );
    set({ profiles });
  },

  deleteProfiles: (ids) => {
    const profiles = get().profiles.filter(profile => !ids.includes(profile.id));
    set({ profiles });
  },

  assignToNiche: (profileIds, nicheId) => {
    const profiles = get().profiles.map(profile =>
      profileIds.includes(profile.id) ? { ...profile, nicheId } : profile
    );
    set({ profiles });
  },

  setFilters: (newFilters) => {
    set(state => ({
      filters: { ...state.filters, ...newFilters },
      pagination: { ...state.pagination, page: 1 }
    }));
  },

  setPagination: (updates) => {
    set(state => ({
      pagination: { ...state.pagination, ...updates }
    }));
  },

  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),

  // Selectors
  getProfilesByNiche: (nicheId) => {
    const state = get();
    return state.profiles.filter(profile => profile.nicheId === nicheId);
  },

  getFilteredProfiles: () => {
    const { profiles, filters } = get();
    return profiles.filter(profile => {
      if (filters.nicheId && profile.nicheId !== filters.nicheId) return false;
      if (filters.status !== 'all' && profile.status !== filters.status) return false;
      if (filters.search && !profile.username.toLowerCase().includes(filters.search.toLowerCase())) return false;
      return true;
    });
  }
}));

export default useProfileStore;
