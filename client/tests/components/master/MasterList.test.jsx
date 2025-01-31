import React from 'react';
import { render, fireEvent, act } from '@testing-library/react';
import MasterList from '../../../src/components/master/MasterList';
import { useFilterStore } from '../../../src/stores/filterStore';
import useProfileStore from '../../../src/stores/profileStore';
import useNicheStore from '../../../src/stores/nicheStore';

// Mock the stores
jest.mock('../../../src/stores/profileStore');
jest.mock('../../../src/stores/filterStore');
jest.mock('../../../src/stores/nicheStore');

describe('MasterList', () => {
  const mockProfiles = [
    { id: '1', username: 'user1', niche_id: '1', status: 'active' },
    { id: '2', username: 'user2', niche_id: '2', status: 'inactive' }
  ];

  const mockNiches = [
    { id: '1', name: 'Niche 1' },
    { id: '2', name: 'Niche 2' }
  ];

  beforeEach(() => {
    // Reset store states
    useProfileStore.mockImplementation(() => ({
      profiles: mockProfiles,
      loading: false,
      error: null,
      fetchProfiles: jest.fn(),
      selectedProfileIds: [],
      setSelectedProfiles: jest.fn(),
      updateProfile: jest.fn(),
      deleteProfiles: jest.fn(),
      refreshStories: jest.fn()
    }));

    useFilterStore.mockImplementation(() => ({
      filters: {
        search: '',
        nicheId: null,
        status: null
      },
      setFilter: jest.fn()
    }));

    useNicheStore.mockImplementation(() => ({
      niches: mockNiches
    }));
  });

  it('updates search filter when searching', () => {
    const setFilter = jest.fn();
    useFilterStore.mockImplementation(() => ({
      filters: { search: '' },
      setFilter
    }));

    const { getByPlaceholderText } = render(<MasterList />);
    const searchInput = getByPlaceholderText('Search profiles...');
    
    fireEvent.change(searchInput, { target: { value: 'test' } });
    expect(setFilter).toHaveBeenCalledWith('search', 'test');
  });

  it('updates niche filter when selecting niche', () => {
    const setFilter = jest.fn();
    useFilterStore.mockImplementation(() => ({
      filters: { nicheId: null },
      setFilter
    }));

    const { getByRole } = render(<MasterList />);
    const nicheSelect = getByRole('combobox');
    
    fireEvent.change(nicheSelect, { target: { value: '1' } });
    expect(setFilter).toHaveBeenCalledWith('nicheId', '1');
  });

  it('updates status filter when selecting status', () => {
    const setFilter = jest.fn();
    useFilterStore.mockImplementation(() => ({
      filters: { status: null },
      setFilter
    }));

    const { getByRole } = render(<MasterList />);
    const statusSelect = getByRole('combobox', { name: /status/i });
    
    fireEvent.change(statusSelect, { target: { value: 'active' } });
    expect(setFilter).toHaveBeenCalledWith('status', 'active');
  });

  it('fetches profiles when filters change', () => {
    const fetchProfiles = jest.fn();
    useProfileStore.mockImplementation(() => ({
      ...useProfileStore(),
      fetchProfiles
    }));

    render(<MasterList />);
    expect(fetchProfiles).toHaveBeenCalled();
  });

  it('displays loading state', () => {
    useProfileStore.mockImplementation(() => ({
      ...useProfileStore(),
      loading: true
    }));

    const { getByText } = render(<MasterList />);
    expect(getByText('Loading...')).toBeInTheDocument();
  });

  it('displays error state', () => {
    const errorMessage = 'Failed to load profiles';
    useProfileStore.mockImplementation(() => ({
      ...useProfileStore(),
      error: errorMessage
    }));

    const { getByText } = render(<MasterList />);
    expect(getByText(errorMessage)).toBeInTheDocument();
  });

  it('selects active stories', () => {
    const setSelectedProfiles = jest.fn();
    useProfileStore.mockImplementation(() => ({
      ...useProfileStore(),
      setSelectedProfiles
    }));

    const { getByText } = render(<MasterList />);
    const selectButton = getByText('Select Active Stories');
    
    fireEvent.click(selectButton);
    expect(setSelectedProfiles).toHaveBeenCalled();
  });
});