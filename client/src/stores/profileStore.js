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
  totalProfiles: 0,
  currentPage: 1,
  pageSize: 1000,
  sortColumn: null,
  sortDirection: 'asc',

  // Actions
  fetchProfiles: async ({ page, pageSize, sortColumn, sortDirection } = {}) => {
    try {
      console.log('=== Fetching Profiles ===');
      console.log('1. Setting loading state...');
      set({ loading: true, error: null });
      
      const currentState = get();
      const params = {
        niche_id: currentState.filters.nicheId,
        page: page || currentState.currentPage,
        page_size: pageSize || currentState.pageSize,
        sort_by: sortColumn || currentState.sortColumn,
        sort_direction: sortDirection || currentState.sortDirection
      };

      // Handle 'niche.name' and 'niche__name' sorting
      if (params.sort_by === 'niche.name' || params.sort_by === 'niche__name') {
        params.sort_by = 'niche__name';
      }
      
      console.log('2. Making API request to /api/profiles with params:', params);
      console.log('Current filters:', currentState.filters);
      const response = await profiles.list(params);
      console.log('3. API Response:', response);
      
      console.log('4. Updating store with profiles...');
      set({
        profiles: response.profiles,
        totalProfiles: response.total,
        currentPage: params.page,
        pageSize: params.page_size,
        sortColumn: (sortColumn === 'niche__name' ? 'niche.name' : sortColumn) || currentState.sortColumn,
        sortDirection: params.sort_direction,
        loading: false
      });
      console.log('5. Store updated successfully');
      console.log('6. Updated profiles:', response.profiles);
      console.log('7. Updated sort column:', sortColumn || currentState.sortColumn);
      console.log('8. Updated sort direction:', params.sort_direction);

      // Check if the niche property exists and is correctly structured
      const sampleProfile = response.profiles[0];
      if (sampleProfile) {
        console.log('9. Sample profile:', sampleProfile);
        console.log('10. Sample profile niche:', sampleProfile.niche);
      }

      // Log the niche_id of each profile
      console.log('11. Profile niche_ids:', response.profiles.map(p => p.niche_id));
    } catch (error) {
      console.error('!!! Error fetching profiles !!!');
      console.error('Error details:', error);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      if (error.response) {
        console.error('Server response:', error.response);
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
      } else if (error.request) {
        console.error('No response received');
        console.error('Request details:', error.request);
      } else {
        console.error('Error setting up request:', error.message);
      }
      console.error('Error config:', error.config);
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
  
        console.log('Starting profile import...');
        const response = await profiles.import(get().filters.nicheId, file);
        console.log(`Import response received. Created: ${response.created.length}, Errors: ${response.errors.length}`);
  
        if (response.errors.length > 0) {
          console.warn('Some profiles were not imported:', response.errors);
        }
  
        console.log('Refetching profiles after import...');
        await get().fetchProfiles({ page: 1 }); // Reset to first page and refetch
  
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
    const profiles = get().profiles;
    console.log('getProfilesByNiche called with nicheId:', nicheId);
    console.log('Current profiles:', profiles);
    if (!profiles) {
      console.error('Profiles is undefined in getProfilesByNiche');
      return [];
    }
    return profiles.filter(profile => profile.niche_id === nicheId);
  },

  getFilteredProfiles: () => {
    const { profiles, filters } = get();
    console.log('getFilteredProfiles called');
    console.log('Current profiles:', profiles);
    console.log('Current filters:', filters);
    if (!profiles) {
      console.error('Profiles is undefined in getFilteredProfiles');
      return [];
    }
    return profiles.filter(profile =>
      filters.nicheId ? (profile.niche_id === filters.nicheId || profile.niche_id === null) : true
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
