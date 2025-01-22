import { act } from '@testing-library/react';
import useProfileStore from '../profileStore';
import { profiles } from '../../api';

jest.mock('../../api', () => ({
  profiles: {
    list: jest.fn(),
    create: jest.fn(),
    update: jest.fn()
  }
}));

describe('profileStore', () => {
  const mockProfiles = [
    {
      id: '1',
      username: 'user1',
      niche_id: '1',
      status: 'active',
      total_checks: 10,
      total_detections: 5
    },
    {
      id: '2',
      username: 'user2',
      niche_id: '2',
      status: 'inactive',
      total_checks: 20,
      total_detections: 15
    }
  ];

  beforeEach(() => {
    act(() => {
      useProfileStore.setState({
        profiles: [],
        filters: {
          nicheId: null
        },
        loading: false,
        error: null
      });
    });

    // Reset API mocks
    profiles.list.mockResolvedValue(mockProfiles);
    profiles.create.mockResolvedValue(mockProfiles[0]);
    profiles.update.mockImplementation((id, updates) => ({ ...mockProfiles[0], ...updates }));
  });

  describe('State Management', () => {
    it('initializes with default state', () => {
      const state = useProfileStore.getState();
      expect(state.profiles).toEqual([]);
      expect(state.filters.nicheId).toBeNull();
      expect(state.loading).toBeFalsy();
      expect(state.error).toBeNull();
    });

    it('updates niche filter', () => {
      act(() => {
        useProfileStore.getState().setFilters({ nicheId: '1' });
      });
      expect(useProfileStore.getState().filters.nicheId).toBe('1');
    });
  });

  describe('Profile Operations', () => {
    it('fetches profiles', async () => {
      await act(async () => {
        await useProfileStore.getState().fetchProfiles();
      });

      expect(profiles.list).toHaveBeenCalled();
      expect(useProfileStore.getState().profiles).toEqual(mockProfiles);
    });

    it('updates profile status', async () => {
      await act(async () => {
        useProfileStore.setState({ profiles: mockProfiles });
        await useProfileStore.getState().updateProfile('1', { status: 'inactive' });
      });

      expect(profiles.update).toHaveBeenCalledWith('1', { status: 'inactive' });
      expect(useProfileStore.getState().profiles[0].status).toBe('inactive');
    });

    it('filters profiles by niche', () => {
      act(() => {
        useProfileStore.setState({ 
          profiles: mockProfiles,
          filters: { nicheId: '1' }
        });
      });

      const filtered = useProfileStore.getState().getFilteredProfiles();
      expect(filtered).toHaveLength(1);
      expect(filtered[0].niche_id).toBe('1');
    });
  });

  describe('File Import', () => {
    it('imports profiles from file', async () => {
      const fileContent = 'https://instagram.com/user1\nhttps://instagram.com/user2';
      const file = {
        text: jest.fn().mockResolvedValue(fileContent),
        type: 'text/plain',
        name: 'profiles.txt'
      };
      profiles.create.mockResolvedValue(mockProfiles[0]);

      await act(async () => {
        useProfileStore.setState({ filters: { nicheId: '1' } });
        await useProfileStore.getState().importFromFile(file);
      });

      expect(profiles.create).toHaveBeenCalledWith({
        username: 'user1',
        status: 'active',
        niche_id: '1'
      });
      expect(file.text).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('handles fetch error', async () => {
      const error = new Error('Fetch failed');
      profiles.list.mockRejectedValue(error);

      await act(async () => {
        await useProfileStore.getState().fetchProfiles();
      });

      expect(useProfileStore.getState().error).toBe(error.message);
    });

    it('handles operation errors', async () => {
      const error = new Error('Operation failed');
      profiles.update.mockRejectedValue(error);

      await act(async () => {
        await useProfileStore.getState().updateProfile('1', { status: 'inactive' });
      });

      expect(useProfileStore.getState().error).toBe(error.message);
    });
  });
});
