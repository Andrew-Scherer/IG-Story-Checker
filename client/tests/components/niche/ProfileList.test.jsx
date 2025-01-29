import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import ProfileList from '../../../src/components/niche/ProfileList';
import useProfileStore from '../../../src/stores/profileStore';

// Mock the profileStore
jest.mock('../../../src/stores/profileStore');

const mockProfiles = [
  {
    id: 1,
    username: 'user1',
    status: 'active',
    active_story: true,
    last_story_detected: '2023-05-01T12:00:00Z',
    total_checks: 10,
    total_detections: 5,
    niche: { id: 1, name: 'Fashion' }
  },
  {
    id: 2,
    username: 'user2',
    status: 'inactive',
    active_story: false,
    last_story_detected: null,
    total_checks: 5,
    total_detections: 0,
    niche: { id: 2, name: 'Travel' }
  },
  {
    id: 3,
    username: 'user3',
    status: 'active',
    active_story: true,
    last_story_detected: '2023-05-02T12:00:00Z',
    total_checks: 15,
    total_detections: 8,
    niche: null
  }
];

describe('ProfileList', () => {
  beforeEach(() => {
    useProfileStore.mockReturnValue({
      setFilters: jest.fn(),
      getFilteredProfiles: jest.fn(() => mockProfiles),
      updateProfile: jest.fn(),
      loading: false,
      error: null,
      selectedProfileIds: [],
      setSelectedProfiles: jest.fn(),
      fetchProfiles: jest.fn(),
      sortColumn: null,
      sortDirection: 'asc'
    });
  });

  it('renders the profile list', () => {
    render(<ProfileList nicheId={1} />);
    expect(screen.getByText('user1')).toBeInTheDocument();
    expect(screen.getByText('user2')).toBeInTheDocument();
    expect(screen.getByText('user3')).toBeInTheDocument();
  });

  it('sorts profiles by niche name', async () => {
    const mockFetchProfiles = jest.fn();
    const mockProfiles = [
      { id: 1, username: 'user1', niche: { id: 1, name: 'Fashion' } },
      { id: 2, username: 'user2', niche: { id: 2, name: 'Travel' } },
      { id: 3, username: 'user3', niche: null },
    ];
    let currentProfiles = [...mockProfiles];
    useProfileStore.mockReturnValue({
      ...useProfileStore(),
      fetchProfiles: mockFetchProfiles,
      profiles: currentProfiles,
    });

    const { rerender } = render(<ProfileList nicheId={1} />);

    // Find the Niche column header and click it for ascending order
    const nicheHeader = screen.getByText('Niche');
    fireEvent.click(nicheHeader);

    // Check if fetchProfiles was called with the correct sorting parameters
    await waitFor(() => {
      expect(mockFetchProfiles).toHaveBeenCalledWith({
        sortColumn: 'niche__name',
        sortDirection: 'asc'
      });
    });

    // Simulate the response from the API (sorted profiles)
    currentProfiles = [
      { id: 1, username: 'user1', niche: { id: 1, name: 'Fashion' } },
      { id: 2, username: 'user2', niche: { id: 2, name: 'Travel' } },
      { id: 3, username: 'user3', niche: null },
    ];
    useProfileStore.mockReturnValue({
      ...useProfileStore(),
      fetchProfiles: mockFetchProfiles,
      profiles: currentProfiles,
    });
    rerender(<ProfileList nicheId={1} />);

    // Check if profiles are displayed in the correct order
    const usernames = screen.getAllByText(/user\d/).map(el => el.textContent);
    expect(usernames).toEqual(['user1', 'user2', 'user3']);

    // Click again to test descending order
    fireEvent.click(nicheHeader);

    await waitFor(() => {
      expect(mockFetchProfiles).toHaveBeenCalledWith({
        sortColumn: 'niche__name',
        sortDirection: 'desc'
      });
    });

    // Simulate the response from the API (sorted profiles in descending order)
    currentProfiles = [
      { id: 2, username: 'user2', niche: { id: 2, name: 'Travel' } },
      { id: 1, username: 'user1', niche: { id: 1, name: 'Fashion' } },
      { id: 3, username: 'user3', niche: null },
    ];
    useProfileStore.mockReturnValue({
      ...useProfileStore(),
      fetchProfiles: mockFetchProfiles,
      profiles: currentProfiles,
    });
    rerender(<ProfileList nicheId={1} />);

    // Check if profiles are displayed in the correct descending order
    const usernamesDesc = screen.getAllByText(/user\d/).map(el => el.textContent);
    expect(usernamesDesc).toEqual(['user2', 'user1', 'user3']);

    // Check if profiles without niches are displayed correctly
    expect(screen.getByText('Fashion')).toBeInTheDocument();
    expect(screen.getByText('Travel')).toBeInTheDocument();
    expect(screen.getByText('-')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    useProfileStore.mockReturnValue({
      ...useProfileStore(),
      loading: true
    });
    render(<ProfileList nicheId={1} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays error state', () => {
    const errorMessage = 'Failed to load profiles';
    useProfileStore.mockReturnValue({
      ...useProfileStore(),
      error: errorMessage
    });
    render(<ProfileList nicheId={1} />);
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('toggles profile status', async () => {
    const { updateProfile } = useProfileStore();
    render(<ProfileList nicheId={1} />);
    
    const statusBadge = screen.getByText('active');
    fireEvent.click(statusBadge);

    await waitFor(() => {
      expect(updateProfile).toHaveBeenCalledWith(1, { status: 'inactive' });
    });
  });

  it('displays correct active story status', () => {
    render(<ProfileList nicheId={1} />);
    expect(screen.getByText('Yes')).toHaveClass('profile-list__story-status--active');
    expect(screen.getByText('No')).not.toHaveClass('profile-list__story-status--active');
  });

  it('formats date correctly', () => {
    render(<ProfileList nicheId={1} />);
    expect(screen.getByText('5/1/2023, 12:00:00 PM')).toBeInTheDocument();
    expect(screen.getByText('Never')).toBeInTheDocument();
  });

  it('displays total checks and detections', () => {
    render(<ProfileList nicheId={1} />);
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('displays empty state when no profiles', () => {
    useProfileStore.mockReturnValue({
      ...useProfileStore(),
      getFilteredProfiles: jest.fn(() => [])
    });
    render(<ProfileList nicheId={1} />);
    expect(screen.getByText('No profiles found')).toBeInTheDocument();
    expect(screen.getByText('Import profiles using the file importer above')).toBeInTheDocument();
  });
});
