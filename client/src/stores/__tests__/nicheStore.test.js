import { act } from '@testing-library/react';
import useNicheStore from '../nicheStore';
import { niches } from '../../api';

jest.mock('../../api', () => ({
  niches: {
    list: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn()
  }
}));

describe('nicheStore', () => {
  const mockNiches = [
    { id: '1', name: 'Niche 1' },
    { id: '2', name: 'Niche 2' }
  ];

  beforeEach(() => {
    act(() => {
      useNicheStore.setState({
        niches: [],
        selectedNicheId: null,
        loading: false,
        error: null
      });
    });

    // Reset API mocks
    niches.list.mockResolvedValue(mockNiches);
    niches.create.mockResolvedValue(mockNiches[0]);
    niches.update.mockResolvedValue({ ...mockNiches[0], name: 'Updated' });
    niches.delete.mockResolvedValue();
  });

  describe('State Management', () => {
    it('initializes with default state', () => {
      const state = useNicheStore.getState();
      expect(state.niches).toEqual([]);
      expect(state.selectedNicheId).toBeNull();
      expect(state.loading).toBeFalsy();
      expect(state.error).toBeNull();
    });

    it('updates selected niche', () => {
      act(() => {
        useNicheStore.getState().setSelectedNicheId('1');
      });
      expect(useNicheStore.getState().selectedNicheId).toBe('1');
    });
  });

  describe('CRUD Operations', () => {
    it('fetches niches', async () => {
      await act(async () => {
        await useNicheStore.getState().fetchNiches();
      });

      expect(niches.list).toHaveBeenCalled();
      expect(useNicheStore.getState().niches).toEqual(mockNiches);
    });

    it('creates niche', async () => {
      const newNiche = { name: 'New Niche' };
      
      await act(async () => {
        await useNicheStore.getState().createNiche(newNiche);
      });

      expect(niches.create).toHaveBeenCalledWith(newNiche);
      expect(useNicheStore.getState().niches).toContainEqual(mockNiches[0]);
    });

    it('updates niche', async () => {
      const updates = { name: 'Updated' };
      
      await act(async () => {
        useNicheStore.setState({ niches: mockNiches });
        await useNicheStore.getState().updateNiche('1', updates);
      });

      expect(niches.update).toHaveBeenCalledWith('1', updates);
      expect(useNicheStore.getState().niches[0].name).toBe('Updated');
    });

    it('deletes niche', async () => {
      await act(async () => {
        useNicheStore.setState({ niches: mockNiches });
        await useNicheStore.getState().deleteNiche('1');
      });

      expect(niches.delete).toHaveBeenCalledWith('1');
      expect(useNicheStore.getState().niches).not.toContainEqual(mockNiches[0]);
    });
  });

  describe('Error Handling', () => {
    it('handles fetch error', async () => {
      const error = new Error('Fetch failed');
      niches.list.mockRejectedValue(error);

      await act(async () => {
        await useNicheStore.getState().fetchNiches();
      });

      expect(useNicheStore.getState().error).toBe(error.message);
    });

    it('handles operation errors', async () => {
      const error = new Error('Operation failed');
      niches.create.mockRejectedValue(error);

      await act(async () => {
        await useNicheStore.getState().createNiche({ name: 'Test' });
      });

      expect(useNicheStore.getState().error).toBe(error.message);
    });
  });
});
