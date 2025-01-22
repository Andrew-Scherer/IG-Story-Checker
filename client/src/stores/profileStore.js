import { create } from 'zustand';
import { profiles } from '../api';

const useProfileStore = create((set, get) => ({
  // State
  profiles: [],
  filters: {
    nicheId: null
  },
  loading: false,
  error: null,
  selectedProfileIds: [],

  // Actions
  fetchProfiles: async () => {
    try {
      console.log('=== Fetching Profiles ===');
      console.log('1. Setting loading state...');
      set({ loading: true, error: null });
      
      console.log('2. Making API request to /api/profiles...');
      const response = await profiles.list();
      console.log('3. API Response:', response);
      
      console.log('4. Updating store with profiles...');
      set({ 
        profiles: response,
        loading: false 
      });
      console.log('5. Store updated successfully');
    } catch (error) {
      console.error('!!! Error fetching profiles !!!');
      console.error('Error details:', error);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      if (error.response) {
        console.error('Server response:', error.response);
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
      }
      set({ 
        error: error.message,
        loading: false
      });
    }
  },

  refreshStories: async () => {
    try {
      set({ loading: true, error: null });
      await profiles.refreshStories();
      // Fetch profiles again to get updated active_story states
      await get().fetchProfiles();
    } catch (error) {
      console.error('Failed to refresh stories:', error);
      set({ 
        error: error.message,
        loading: false
      });
    }
  },

  updateProfile: async (id, updates) => {
    try {
      set({ loading: true, error: null });
      const response = await profiles.update(id, updates);
      set(state => ({
        profiles: state.profiles.map(profile =>
          profile.id === id ? response : profile
        ),
        loading: false
      }));
    } catch (error) {
      console.error('Failed to update profile:', error);
      set({ 
        error: error.message,
        loading: false
      });
    }
  },

  importFromFile: async (file) => {
    try {
      set({ loading: true, error: null });
      
      if (!get().filters.nicheId) {
        throw new Error('Please select a niche before importing profiles');
      }

      const response = await profiles.import(get().filters.nicheId, file);
      set(state => ({ 
        profiles: [...state.profiles, ...response.created]
      }));
      return response;
    } catch (error) {
      console.error('Import failed:', error);
      set({ 
        error: error.message,
        loading: false
      });
      throw error;
    } finally {
      set({ loading: false });
    }
  },

  setFilters: (newFilters) => {
    set({ filters: { ...get().filters, ...newFilters } });
  },

  // Selectors
  getProfilesByNiche: (nicheId) => {
    return get().profiles.filter(profile => profile.niche_id === nicheId);
  },

  getFilteredProfiles: () => {
    const { profiles, filters } = get();
    return profiles.filter(profile => 
      filters.nicheId ? profile.niche_id === filters.nicheId : true
    );
  },

  // Selection actions
  setSelectedProfiles: (profileIds) => {
    set({ selectedProfileIds: profileIds });
  },

  getSelectedProfiles: () => {
    const { profiles, selectedProfileIds } = get();
    return profiles.filter(profile => selectedProfileIds.includes(profile.id));
  }
}));

export default useProfileStore;
