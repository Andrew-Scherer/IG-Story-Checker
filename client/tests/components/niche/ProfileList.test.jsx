import React from 'react';
import { render, fireEvent, act } from '@testing-library/react';
import ProfileList from '../../../src/components/niche/ProfileList';
import { useFilterStore } from '../../../src/stores/filterStore';
import useProfileStore from '../../../src/stores/profileStore';

// Mock the stores
jest.mock('../../../src/stores/profileStore');
jest.mock('../../../src/stores/filterStore');

describe('ProfileList', () => {
  const mockProfiles = [
    { id: '1', username: 'user1', niche_id: '1', status: 'active' },
    { id: '2', username: 'user2', niche_id: '1', status: 'inactive' }
  ];

  beforeEach(() => {
    // Reset store states
    useProfileStore.mockImplementation(() => ({
      profiles: mockProfiles,
      loading: false,
      error: null,
      fetchProfiles: jest.fn(),
      selectedProfileIds: [],
      setSelectedProfiles: jest.fn()
    }));

    useFilterStore.mockImplementation(() => ({
      filters: {
        search: '',
        nicheId: null,
        status: null
      },
      setFilter: jest.fn()
    }));
  });

  it('updates filters when niche changes', () => {
    const nicheId = '1';
    const setFilter = jest.fn();
    useFilterStore.mockImplementation(() => ({
      filters: { nicheId: null },
      setFilter
    }));

    render(<ProfileList nicheId={nicheId} />);
    expect(setFilter).toHaveBeenCalledWith('nicheId', nicheId);
  });

  it('fetches profiles when filters change', () => {
    const fetchProfiles = jest.fn();
    useProfileStore.mockImplementation(() => ({
      ...useProfileStore(),
      fetchProfiles
    }));

    render(<ProfileList nicheId="1" />);
    expect(fetchProfiles).toHaveBeenCalled();
  });

  it('displays loading state', () => {
    useProfileStore.mockImplementation(() => ({
      ...useProfileStore(),
      loading: true
    }));

    const { getByText } = render(<ProfileList nicheId="1" />);
    expect(getByText('Loading...')).toBeInTheDocument();
  });

  it('displays error state', () => {
    const errorMessage = 'Failed to load profiles';
    useProfileStore.mockImplementation(() => ({
      ...useProfileStore(),
      error: errorMessage
    }));

    const { getByText } = render(<ProfileList nicheId="1" />);
    expect(getByText(errorMessage)).toBeInTheDocument();
  });
});
