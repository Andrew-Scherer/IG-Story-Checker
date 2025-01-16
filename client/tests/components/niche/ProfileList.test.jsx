import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import ProfileList from '../../../src/components/niche/ProfileList';

describe('ProfileList Component', () => {
  const mockProfiles = [
    { id: 1, username: '@fitness_guru', status: 'active', lastChecked: '2024-02-20' },
    { id: 2, username: '@travel_expert', status: 'inactive', lastChecked: '2024-02-19' },
    { id: 3, username: '@food_lover', status: 'active', lastChecked: '2024-02-18' }
  ];

  const defaultProps = {
    profiles: mockProfiles,
    onStatusChange: jest.fn(),
    onDelete: jest.fn(),
    onSort: jest.fn()
  };

  it('renders list of profiles', () => {
    const { getByText } = render(<ProfileList {...defaultProps} />);
    
    expect(getByText('@fitness_guru')).toBeInTheDocument();
    expect(getByText('@travel_expert')).toBeInTheDocument();
    expect(getByText('@food_lover')).toBeInTheDocument();
  });

  it('displays status indicators', () => {
    const { getAllByTestId } = render(<ProfileList {...defaultProps} />);
    
    const statusIndicators = getAllByTestId('status-indicator');
    expect(statusIndicators[0]).toHaveClass('status-indicator--active');
    expect(statusIndicators[1]).toHaveClass('status-indicator--inactive');
  });

  it('handles status toggle', () => {
    const onStatusChange = jest.fn();
    const { getAllByTestId } = render(
      <ProfileList {...defaultProps} onStatusChange={onStatusChange} />
    );
    
    fireEvent.click(getAllByTestId('status-toggle')[0]);
    expect(onStatusChange).toHaveBeenCalledWith(1, 'inactive');
  });

  it('handles profile deletion', () => {
    const onDelete = jest.fn();
    const { getAllByTestId } = render(
      <ProfileList {...defaultProps} onDelete={onDelete} />
    );
    
    fireEvent.click(getAllByTestId('delete-button')[0]);
    expect(onDelete).toHaveBeenCalledWith(1);
  });

  it('supports column sorting', () => {
    const onSort = jest.fn();
    const { getByText } = render(
      <ProfileList {...defaultProps} onSort={onSort} />
    );
    
    fireEvent.click(getByText('Username'));
    expect(onSort).toHaveBeenCalledWith('username', 'asc');
    
    fireEvent.click(getByText('Username'));
    expect(onSort).toHaveBeenCalledWith('username', 'desc');
  });

  it('shows empty state when no profiles', () => {
    const { getByText } = render(
      <ProfileList {...defaultProps} profiles={[]} />
    );
    
    expect(getByText('No profiles found')).toBeInTheDocument();
  });

  it('displays last checked date', () => {
    const { getByText } = render(<ProfileList {...defaultProps} />);
    
    expect(getByText('2024-02-20')).toBeInTheDocument();
    expect(getByText('2024-02-19')).toBeInTheDocument();
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

  it('filters profiles by status', () => {
    const { getByTestId, queryByText } = render(<ProfileList {...defaultProps} />);
    
    const statusFilter = getByTestId('status-filter');
    fireEvent.change(statusFilter, { target: { value: 'active' } });
    
    expect(queryByText('@travel_expert')).not.toBeInTheDocument();
  });
});
