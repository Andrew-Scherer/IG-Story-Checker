import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NicheFeed from '../NicheFeed';
import useNicheStore from '../../../stores/nicheStore';
import useProfileStore from '../../../stores/profileStore';

jest.mock('../../../stores/nicheStore');
jest.mock('../../../stores/profileStore');

describe('NicheFeed', () => {
  const mockNiches = [
    { id: '1', name: 'Niche 1' },
    { id: '2', name: 'Niche 2' }
  ];

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
      niche_id: '1',
      status: 'inactive',
      total_checks: 20,
      total_detections: 15
    }
  ];

  beforeEach(() => {
    useNicheStore.mockImplementation(() => ({
      niches: mockNiches,
      selectedNicheId: null,
      setSelectedNicheId: jest.fn(),
      deleteNiche: jest.fn(),
      updateNiche: jest.fn(),
      createNiche: jest.fn(),
      getNiches: () => mockNiches,
      fetchNiches: jest.fn()
    }));

    useProfileStore.mockImplementation(() => ({
      profiles: mockProfiles,
      getFilteredProfiles: () => mockProfiles,
      fetchProfiles: jest.fn(),
      importFromFile: jest.fn(),
      updateProfile: jest.fn(),
      setFilters: jest.fn(),
      loading: false,
      error: null
    }));
  });

  describe('Niche Management', () => {
    it('displays Add Niche button and creates new niche', async () => {
      render(<NicheFeed />);
      const { createNiche } = useNicheStore.mock.results[0].value;

      await userEvent.click(screen.getByText('Add Niche'));
      const input = screen.getByPlaceholderText('Enter niche name');
      await userEvent.type(input, 'New Niche');
      await userEvent.click(screen.getByText('Save'));

      expect(createNiche).toHaveBeenCalledWith({ name: 'New Niche' });
    });

    it('renders niche list with names and profile counts', () => {
      render(<NicheFeed />);
      mockNiches.forEach(niche => {
        const nicheItem = screen.getByTestId('niche-item');
        expect(within(nicheItem).getByDisplayValue(niche.name)).toBeInTheDocument();
        expect(within(nicheItem).getByText(/profiles$/)).toBeInTheDocument();
      });
    });

    it('allows renaming and deleting niches', async () => {
      render(<NicheFeed />);
      const { updateNiche, deleteNiche } = useNicheStore.mock.results[0].value;

      // Rename
      const nameInput = screen.getAllByTestId('niche-name-input')[0];
      await userEvent.clear(nameInput);
      await userEvent.type(nameInput, 'Updated Niche');
      expect(updateNiche).toHaveBeenCalledWith('1', { name: 'Updated Niche' });

      // Delete
      await userEvent.click(screen.getAllByTestId('delete-button')[0]);
      expect(deleteNiche).toHaveBeenCalledWith('1');
    });
  });

  describe('Profile Management', () => {
    beforeEach(() => {
      useNicheStore.mockImplementation(() => ({
        ...useNicheStore(),
        selectedNicheId: '1'
      }));
    });

    it('shows profile list with correct columns', () => {
      render(<NicheFeed />);
      const headers = ['Username', 'Status', 'Total Checks', 'Total Stories'];
      headers.forEach(header => {
        expect(screen.getByText(header)).toBeInTheDocument();
      });
    });

    it('allows toggling profile status', async () => {
      render(<NicheFeed />);
      const { updateProfile } = useProfileStore.mock.results[0].value;

      const statusBadge = screen.getByText('active');
      await userEvent.click(statusBadge);
      expect(updateProfile).toHaveBeenCalledWith('1', { status: 'inactive' });
    });

    it('supports importing profiles from file', async () => {
      render(<NicheFeed />);
      const { importFromFile } = useProfileStore.mock.results[0].value;

      const file = new File(['profile1\nprofile2'], 'profiles.txt', { type: 'text/plain' });
      const input = screen.getByTestId('file-input');
      await userEvent.upload(input, file);

      expect(importFromFile).toHaveBeenCalledWith(file);
    });

    it('shows empty state when no profiles', () => {
      useProfileStore.mockImplementation(() => ({
        ...useProfileStore(),
        getFilteredProfiles: () => []
      }));
      render(<NicheFeed />);
      expect(screen.getByText('No profiles found')).toBeInTheDocument();
    });
  });

  it('fetches initial data on mount', () => {
    render(<NicheFeed />);
    const { fetchNiches } = useNicheStore.mock.results[0].value;
    const { fetchProfiles } = useProfileStore.mock.results[0].value;
    
    expect(fetchNiches).toHaveBeenCalled();
    expect(fetchProfiles).toHaveBeenCalled();
  });
});
