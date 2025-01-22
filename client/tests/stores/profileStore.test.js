import useProfileStore from '../../src/stores/profileStore';

describe('Profile Store', () => {
  let store;

  beforeEach(() => {
    // Reset store to initial state before each test
    useProfileStore.setState({
      profiles: [],
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
      error: null
    });
    store = useProfileStore.getState();
  });

  describe('State Updates', () => {
    it('initializes with default state', () => {
      expect(store.profiles).toEqual([]);
      expect(store.filters).toEqual({
        nicheId: null,
        status: 'active',
        search: ''
      });
      expect(store.pagination).toEqual({
        page: 1,
        pageSize: 20,
        total: 0
      });
      expect(store.loading).toBeFalsy();
      expect(store.error).toBeNull();
    });

    it('updates loading state', () => {
      store.setLoading(true);
      expect(useProfileStore.getState().loading).toBeTruthy();
      
      store.setLoading(false);
      expect(useProfileStore.getState().loading).toBeFalsy();
    });

    it('updates error state', () => {
      const error = 'Test error';
      store.setError(error);
      expect(useProfileStore.getState().error).toBe(error);
      
      store.clearError();
      expect(useProfileStore.getState().error).toBeNull();
    });
  });

  describe('Profile Operations', () => {
    const testProfiles = [
      { 
        id: 1, 
        username: 'test_user1',
        nicheId: 1,
        status: 'active',
        lastChecked: '2023-01-01T00:00:00Z',
        lastDetected: '2023-01-01T00:00:00Z',
        totalChecks: 10,
        totalDetections: 5
      },
      { 
        id: 2, 
        username: 'test_user2',
        nicheId: 2,
        status: 'active',
        lastChecked: '2023-01-01T00:00:00Z',
        lastDetected: '2023-01-01T00:00:00Z',
        totalChecks: 8,
        totalDetections: 3
      }
    ];

    it('sets profiles', () => {
      store.setProfiles(testProfiles);
      expect(useProfileStore.getState().profiles).toEqual(testProfiles);
    });

    it('adds new profiles', () => {
      store.setProfiles([testProfiles[0]]);
      store.addProfiles([testProfiles[1]]);
      
      expect(useProfileStore.getState().profiles).toEqual(testProfiles);
    });

    it('prevents duplicate profiles when adding', () => {
      store.setProfiles([testProfiles[0]]);
      store.addProfiles([testProfiles[0], testProfiles[1]]);
      
      expect(useProfileStore.getState().profiles).toEqual(testProfiles);
    });

    it('updates profile', () => {
      store.setProfiles(testProfiles);
      
      const updates = { status: 'inactive', totalChecks: 11 };
      store.updateProfile(1, updates);
      
      const updatedProfile = useProfileStore.getState().profiles.find(p => p.id === 1);
      expect(updatedProfile).toEqual({ ...testProfiles[0], ...updates });
    });

    it('deletes profiles', () => {
      store.setProfiles(testProfiles);
      store.deleteProfiles([1]);
      
      const remainingProfiles = useProfileStore.getState().profiles;
      expect(remainingProfiles).toEqual([testProfiles[1]]);
    });

    it('assigns profiles to niche', () => {
      store.setProfiles(testProfiles);
      const newNicheId = 3;
      store.assignToNiche([1], newNicheId);
      
      const updatedProfiles = useProfileStore.getState().profiles;
      expect(updatedProfiles.find(p => p.id === 1).nicheId).toBe(newNicheId);
      expect(updatedProfiles.find(p => p.id === 2).nicheId).toBe(2);
    });
  });

  describe('Filter Operations', () => {
    it('updates filters', () => {
      const newFilters = { nicheId: 1, status: 'inactive' };
      store.setFilters(newFilters);
      
      const state = useProfileStore.getState();
      expect(state.filters).toEqual({ ...state.filters, ...newFilters });
      expect(state.pagination.page).toBe(1); // Should reset page
    });

    it('updates pagination', () => {
      const updates = { page: 2, total: 50 };
      store.setPagination(updates);
      
      const pagination = useProfileStore.getState().pagination;
      expect(pagination).toEqual({ ...pagination, ...updates });
    });
  });

  describe('Selectors', () => {
    const testProfiles = [
      { id: 1, username: 'user1', nicheId: 1, status: 'active' },
      { id: 2, username: 'user2', nicheId: 1, status: 'inactive' },
      { id: 3, username: 'test3', nicheId: 2, status: 'active' }
    ];

    beforeEach(() => {
      store.setProfiles(testProfiles);
    });

    it('gets profiles by niche', () => {
      const niche1Profiles = store.getProfilesByNiche(1);
      expect(niche1Profiles).toHaveLength(2);
      expect(niche1Profiles.every(p => p.nicheId === 1)).toBeTruthy();
    });

    describe('getFilteredProfiles', () => {
      it('filters by nicheId', () => {
        store.setFilters({ nicheId: 1 });
        const filtered = store.getFilteredProfiles();
        expect(filtered).toHaveLength(2);
        expect(filtered.every(p => p.nicheId === 1)).toBeTruthy();
      });

      it('filters by status', () => {
        store.setFilters({ status: 'active' });
        const filtered = store.getFilteredProfiles();
        expect(filtered).toHaveLength(2);
        expect(filtered.every(p => p.status === 'active')).toBeTruthy();
      });

      it('filters by search term', () => {
        store.setFilters({ search: 'test' });
        const filtered = store.getFilteredProfiles();
        expect(filtered).toHaveLength(1);
        expect(filtered[0].username).toBe('test3');
      });

      it('combines multiple filters', () => {
        store.setFilters({
          nicheId: 1,
          status: 'active',
          search: 'user'
        });
        const filtered = store.getFilteredProfiles();
        expect(filtered).toHaveLength(1);
        expect(filtered[0]).toEqual(testProfiles[0]);
      });

      it('returns all profiles when no filters active', () => {
        store.setFilters({
          nicheId: null,
          status: 'all',
          search: ''
        });
        const filtered = store.getFilteredProfiles();
        expect(filtered).toHaveLength(testProfiles.length);
      });
    });
  });
});
