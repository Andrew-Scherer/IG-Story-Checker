import { create } from 'zustand';
import { profiles } from '../api';
import { useFilterStore } from './filterStore';
import { usePaginationStore } from './paginationStore';
import { useSortStore } from './sortStore';

const useProfileStore = create((set, get) => ({
  // State
  profiles: [],
  loading: false,
  error: null,
  selectedProfileIds: [],

  // Actions
  fetchProfiles: async () => {
    try {
      set({ loading: true, error: null });
      usePaginationStore.getState().setLoading(true);

      // Combine pagination, filter, and sort params
      const paginationParams = usePaginationStore.getState().getQueryParams();
      const filterParams = useFilterStore.getState().getQueryParams();
      const sortParams = useSortStore.getState().getQueryParams();
      
      const response = await profiles.list({
        ...paginationParams,
        ...filterParams,
        ...sortParams
      });

      // Update pagination store with total count
      usePaginationStore.getState().setTotalItems(response.total);
      
      set({
        profiles: response.profiles || [],
        loading: false
      });
    } catch (error) {
      set({
        error: error.message,
        loading: false,
        profiles: []
      });
    } finally {
      usePaginationStore.getState().setLoading(false);
    }
  },

  updateProfile: async (id, updates) => {
    try {
      set({ loading: true, error: null });
      await profiles.update(id, updates);
      await get().fetchProfiles();
    } catch (error) {
      set({
        error: error.message,
        loading: false
      });
      throw error;
    }
  },

  deleteProfiles: async (profileIds) => {
    try {
      set({ loading: true, error: null });
      await Promise.all(profileIds.map(id => profiles.delete(id)));
      await get().fetchProfiles();
    } catch (error) {
      set({
        error: error.message,
        loading: false
      });
      throw error;
    }
  },

  setSelectedProfiles: (profileIds) => {
    set({ selectedProfileIds: profileIds });
  },

  refreshStories: async () => {
    try {
      set({ loading: true, error: null });
      await profiles.refreshStories();
      await get().fetchProfiles();
    } catch (error) {
      console.error('Failed to refresh stories:', error);
      set({ 
        error: error.message,
        loading: false
      });
    }
  },

  importFromFile: async (file) => {
    try {
      set({ loading: true, error: null });
      
      const nicheId = useFilterStore.getState().filters.nicheId;
      if (!nicheId) {
        throw new Error('Please select a niche before importing profiles');
      }

      const response = await profiles.import(nicheId, file);
      
      if (response?.errors?.length > 0) {
        console.warn('Some profiles were not imported:', response.errors);
      }

      await get().fetchProfiles();
      return response;
    } catch (error) {
      console.error('Import failed:', error);
      set({
        error: error.message,
        loading: false
      });
      throw error;
    }
  },

  getSelectedProfiles: () => {
    const { profiles, selectedProfileIds } = get();
    return (profiles || []).filter(profile => selectedProfileIds.includes(profile.id));
  }
}));

export default useProfileStore;
