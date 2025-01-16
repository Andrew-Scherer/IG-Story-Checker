import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProfileList from '../ProfileList';

describe('ProfileList Component', () => {
  const mockProfiles = [
    { id: 1, username: '@fitness_guru', status: 'active', lastChecked: '2024-02-20T10:00:00Z' },
    { id: 2, username: '@travel_expert', status: 'inactive', lastChecked: '2024-02-19T15:30:00Z' },
    { id: 3, username: '@food_lover', status: 'active', lastChecked: '2024-02-18T09:15:00Z' }
  ];

  const defaultProps = {
    profiles: mockProfiles,
    onStatusChange: jest.fn(),
    onDelete: jest.fn(),
    onSort: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders profiles in a table', () => {
    const { getByText, getAllByText } = render(<ProfileList {...defaultProps} />);
    
    mockProfiles.forEach(profile => {
      expect(getByText(profile.username)).toBeInTheDocument();
      const statusElements = getAllByText(profile.status);
      expect(statusElements.length).toBeGreaterThan(0);
    });
  });

  it('shows empty state when no profiles', () => {
    const { getByText } = render(
      <ProfileList {...defaultProps} profiles={[]} />
    );
    
    expect(getByText('No profiles found')).toBeInTheDocument();
  });

  it('handles status toggle', () => {
    const onStatusChange = jest.fn();
    const { getByTestId } = render(
      <ProfileList {...defaultProps} onStatusChange={onStatusChange} />
    );
    
    const statusToggle = getByTestId('status-indicator-1');
    fireEvent.click(statusToggle);
    
    expect(onStatusChange).toHaveBeenCalledWith(1, 'inactive');
  });

  it('handles profile deletion', () => {
    const onDelete = jest.fn();
    const { getAllByTestId } = render(
      <ProfileList {...defaultProps} onDelete={onDelete} />
    );
    
    const deleteButtons = getAllByTestId('delete-button');
    fireEvent.click(deleteButtons[0]);
    
    expect(onDelete).toHaveBeenCalledWith(1);
  });

  it('supports column sorting', () => {
    const onSort = jest.fn();
    const { getByText } = render(
      <ProfileList {...defaultProps} onSort={onSort} />
    );
    
    fireEvent.click(getByText('Username'));
    expect(onSort).toHaveBeenCalledWith('username', 'asc');
  });

  it('formats dates correctly', () => {
    const { getByText } = render(<ProfileList {...defaultProps} />);
    
    expect(getByText('Feb 20, 2024')).toBeInTheDocument();
    expect(getByText('Feb 19, 2024')).toBeInTheDocument();
  });

  it('supports filtering by status', () => {
    const { getByTestId, queryByText } = render(<ProfileList {...defaultProps} />);
    
    const statusFilter = getByTestId('status-filter');
    fireEvent.change(statusFilter, { target: { value: 'active' } });
    
    expect(queryByText('@fitness_guru')).toBeInTheDocument();
    expect(queryByText('@travel_expert')).not.toBeInTheDocument();
  });

  it('supports bulk selection', () => {
    const { getByTestId, getAllByTestId } = render(<ProfileList {...defaultProps} />);
    
    const selectAll = getByTestId('select-all');
    fireEvent.click(selectAll);
    
    const checkboxes = getAllByTestId('profile-checkbox');
    checkboxes.forEach(checkbox => {
      expect(checkbox).toBeChecked();
    });
  });

  it('displays correct status indicators', () => {
    const { getByTestId } = render(<ProfileList {...defaultProps} />);
    
    expect(getByTestId('status-indicator-1')).toHaveClass('status--active');
    expect(getByTestId('status-indicator-2')).toHaveClass('status--inactive');
  });
});
