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
    total_detections: 5
  },
  {
    id: 2,
    username: 'user2',
    status: 'inactive',
    active_story: false,
    last_story_detected: null,
    total_checks: 5,
    total_detections: 0
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
      fetchProfiles: jest.fn()
    });
  });

  it('renders the profile list', () => {
    render(<ProfileList nicheId={1} />);
    expect(screen.getByText('user1')).toBeInTheDocument();
    expect(screen.getByText('user2')).toBeInTheDocument();
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
