import { nicheStore } from '../../src/stores/nicheStore';

describe('Niche Store', () => {
  beforeEach(() => {
    nicheStore.reset();
  });

  describe('State Updates', () => {
    it('initializes with empty state', () => {
      expect(nicheStore.niches).toEqual([]);
      expect(nicheStore.selectedNicheId).toBeNull();
      expect(nicheStore.isLoading).toBeFalsy();
      expect(nicheStore.error).toBeNull();
    });

    it('updates niches list', () => {
      const mockNiches = [
        { id: 1, name: 'Niche 1', order: 1 },
        { id: 2, name: 'Niche 2', order: 2 }
      ];
      
      nicheStore.setNiches(mockNiches);
      expect(nicheStore.niches).toEqual(mockNiches);
    });

    it('updates selected niche', () => {
      const nicheId = 1;
      nicheStore.setSelectedNicheId(nicheId);
      expect(nicheStore.selectedNicheId).toBe(nicheId);
    });

    it('updates loading state', () => {
      nicheStore.setLoading(true);
      expect(nicheStore.isLoading).toBeTruthy();
      
      nicheStore.setLoading(false);
      expect(nicheStore.isLoading).toBeFalsy();
    });

    it('updates error state', () => {
      const error = 'Test error';
      nicheStore.setError(error);
      expect(nicheStore.error).toBe(error);
    });
  });

  describe('Actions', () => {
    it('fetches niches', async () => {
      const mockNiches = [
        { id: 1, name: 'Niche 1', order: 1 },
        { id: 2, name: 'Niche 2', order: 2 }
      ];
      
      const mockApi = {
        get: jest.fn().mockResolvedValue({ data: mockNiches })
      };
      
      await nicheStore.fetchNiches(mockApi);
      
      expect(mockApi.get).toHaveBeenCalledWith('/niches');
      expect(nicheStore.niches).toEqual(mockNiches);
      expect(nicheStore.isLoading).toBeFalsy();
      expect(nicheStore.error).toBeNull();
    });

    it('handles fetch error', async () => {
      const error = new Error('API Error');
      const mockApi = {
        get: jest.fn().mockRejectedValue(error)
      };
      
      await nicheStore.fetchNiches(mockApi);
      
      expect(mockApi.get).toHaveBeenCalledWith('/niches');
      expect(nicheStore.niches).toEqual([]);
      expect(nicheStore.isLoading).toBeFalsy();
      expect(nicheStore.error).toBe(error.message);
    });

    it('creates niche', async () => {
      const newNiche = { name: 'New Niche' };
      const createdNiche = { id: 1, name: 'New Niche', order: 1 };
      
      const mockApi = {
        post: jest.fn().mockResolvedValue({ data: createdNiche })
      };
      
      await nicheStore.createNiche(mockApi, newNiche);
      
      expect(mockApi.post).toHaveBeenCalledWith('/niches', newNiche);
      expect(nicheStore.niches).toContainEqual(createdNiche);
      expect(nicheStore.isLoading).toBeFalsy();
      expect(nicheStore.error).toBeNull();
    });

    it('updates niche', async () => {
      const existingNiche = { id: 1, name: 'Old Name', order: 1 };
      const updatedNiche = { id: 1, name: 'New Name', order: 1 };
      
      nicheStore.setNiches([existingNiche]);
      
      const mockApi = {
        put: jest.fn().mockResolvedValue({ data: updatedNiche })
      };
      
      await nicheStore.updateNiche(mockApi, updatedNiche);
      
      expect(mockApi.put).toHaveBeenCalledWith(`/niches/${updatedNiche.id}`, updatedNiche);
      expect(nicheStore.niches).toContainEqual(updatedNiche);
      expect(nicheStore.niches).not.toContainEqual(existingNiche);
      expect(nicheStore.isLoading).toBeFalsy();
      expect(nicheStore.error).toBeNull();
    });

    it('deletes niche', async () => {
      const nicheToDelete = { id: 1, name: 'Niche', order: 1 };
      nicheStore.setNiches([nicheToDelete]);
      
      const mockApi = {
        delete: jest.fn().mockResolvedValue({})
      };
      
      await nicheStore.deleteNiche(mockApi, nicheToDelete.id);
      
      expect(mockApi.delete).toHaveBeenCalledWith(`/niches/${nicheToDelete.id}`);
      expect(nicheStore.niches).not.toContainEqual(nicheToDelete);
      expect(nicheStore.isLoading).toBeFalsy();
      expect(nicheStore.error).toBeNull();
    });

    it('reorders niches', async () => {
      const niches = [
        { id: 1, name: 'Niche 1', order: 1 },
        { id: 2, name: 'Niche 2', order: 2 },
        { id: 3, name: 'Niche 3', order: 3 }
      ];
      
      nicheStore.setNiches(niches);
      
      const mockApi = {
        put: jest.fn().mockResolvedValue({})
      };
      
      // Move niche from index 0 to index 2
      await nicheStore.reorderNiches(mockApi, 0, 2);
      
      const expectedOrder = [
        { id: 2, name: 'Niche 2', order: 1 },
        { id: 3, name: 'Niche 3', order: 2 },
        { id: 1, name: 'Niche 1', order: 3 }
      ];
      
      expect(mockApi.put).toHaveBeenCalledWith('/niches/reorder', {
        nicheIds: expectedOrder.map(n => n.id)
      });
      expect(nicheStore.niches).toEqual(expectedOrder);
      expect(nicheStore.isLoading).toBeFalsy();
      expect(nicheStore.error).toBeNull();
    });
  });

  describe('Selectors', () => {
    it('gets selected niche', () => {
      const niches = [
        { id: 1, name: 'Niche 1', order: 1 },
        { id: 2, name: 'Niche 2', order: 2 }
      ];
      
      nicheStore.setNiches(niches);
      nicheStore.setSelectedNicheId(1);
      
      expect(nicheStore.selectedNiche).toEqual(niches[0]);
    });

    it('returns null for selected niche when no selection', () => {
      const niches = [
        { id: 1, name: 'Niche 1', order: 1 },
        { id: 2, name: 'Niche 2', order: 2 }
      ];
      
      nicheStore.setNiches(niches);
      nicheStore.setSelectedNicheId(null);
      
      expect(nicheStore.selectedNiche).toBeNull();
    });

    it('gets niches sorted by order', () => {
      const unsortedNiches = [
        { id: 3, name: 'Niche 3', order: 3 },
        { id: 1, name: 'Niche 1', order: 1 },
        { id: 2, name: 'Niche 2', order: 2 }
      ];
      
      nicheStore.setNiches(unsortedNiches);
      
      const sortedNiches = nicheStore.sortedNiches;
      expect(sortedNiches).toEqual([
        { id: 1, name: 'Niche 1', order: 1 },
        { id: 2, name: 'Niche 2', order: 2 },
        { id: 3, name: 'Niche 3', order: 3 }
      ]);
    });
  });
});
