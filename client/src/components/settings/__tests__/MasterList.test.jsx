import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MasterList from '../MasterList';

describe('MasterList Component', () => {
  const mockProfiles = [
    { id: 1, username: 'user1', status: 'active', lastChecked: '2023-01-01T12:00:00Z' },
    { id: 2, username: 'user2', status: 'inactive', lastChecked: '2023-01-02T12:00:00Z' },
    { id: 3, username: 'user3', status: 'active', lastChecked: '2023-01-03T12:00:00Z' }
  ];

  const defaultProps = {
    profiles: mockProfiles,
    onUpdateProfile: jest.fn(),
    onDeleteProfile: jest.fn(),
    onBulkDelete: jest.fn()
  };

  describe('Profile Display', () => {
    it('renders profile list with correct columns', () => {
      render(<MasterList {...defaultProps} />);
      
      expect(screen.getByText('Username')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Last Checked')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('displays profile data correctly', () => {
      render(<MasterList {...defaultProps} />);
      
      mockProfiles.forEach(profile => {
        expect(screen.getByText(profile.username)).toBeInTheDocument();
        const statusElement = screen.getByTestId(`status-${profile.id}`);
        expect(statusElement).toHaveTextContent(profile.status);
      });
    });

    it('shows empty state when no profiles', () => {
      render(<MasterList {...defaultProps} profiles={[]} />);
      expect(screen.getByText(/no profiles found/i)).toBeInTheDocument();
    });
  });

  describe('Filtering and Sorting', () => {
    it('filters profiles by username', () => {
      render(<MasterList {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/search profiles/i);
      fireEvent.change(searchInput, { target: { value: 'user1' } });
      
      expect(screen.getByText('user1')).toBeInTheDocument();
      expect(screen.queryByText('user2')).not.toBeInTheDocument();
    });

    it('filters profiles by status', () => {
      render(<MasterList {...defaultProps} />);
      
      const statusFilter = screen.getByLabelText(/status filter/i);
      fireEvent.change(statusFilter, { target: { value: 'active' } });
      
      expect(screen.getByText('user1')).toBeInTheDocument();
      expect(screen.getByText('user3')).toBeInTheDocument();
      expect(screen.queryByText('user2')).not.toBeInTheDocument();
    });

    it('sorts profiles by username', () => {
      render(<MasterList {...defaultProps} />);
      
      const usernameHeader = screen.getByText('Username');
      fireEvent.click(usernameHeader);
      
      const usernames = screen.getAllByRole('cell', { name: /user\d/ })
        .map(cell => cell.textContent);
      expect(usernames).toEqual(['user1', 'user2', 'user3']);
      
      fireEvent.click(usernameHeader); // reverse sort
      const reversedUsernames = screen.getAllByRole('cell', { name: /user\d/ })
        .map(cell => cell.textContent);
      expect(reversedUsernames).toEqual(['user3', 'user2', 'user1']);
    });
  });

  describe('Profile Actions', () => {
    it('updates profile status', () => {
      render(<MasterList {...defaultProps} />);
      
      const statusToggle = screen.getAllByRole('button', { name: /toggle status/i })[0];
      fireEvent.click(statusToggle);
      
      expect(defaultProps.onUpdateProfile).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 1,
          status: 'inactive'
        })
      );
    });

    it('deletes single profile', () => {
      render(<MasterList {...defaultProps} />);
      
      const deleteButton = screen.getAllByRole('button', { name: /delete/i })[0];
      fireEvent.click(deleteButton);
      
      // Should show confirmation dialog
      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);
      
      expect(defaultProps.onDeleteProfile).toHaveBeenCalledWith(1);
    });

    it('supports bulk deletion', () => {
      render(<MasterList {...defaultProps} />);
      
      // Select profiles
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[1]); // First profile checkbox
      fireEvent.click(checkboxes[2]); // Second profile checkbox
      
      const bulkDeleteButton = screen.getByRole('button', { name: /delete selected/i });
      fireEvent.click(bulkDeleteButton);
      
      // Should show confirmation dialog
      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);
      
      expect(defaultProps.onBulkDelete).toHaveBeenCalledWith([1, 2]);
    });
  });

  describe('Pagination', () => {
    const manyProfiles = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      username: `user${i + 1}`,
      status: 'active',
      lastChecked: new Date().toISOString()
    }));

    it('shows correct number of profiles per page', () => {
      render(<MasterList {...defaultProps} profiles={manyProfiles} />);
      
      const rows = screen.getAllByRole('row');
      expect(rows.length).toBe(11); // 10 profiles + header row
    });

    it('navigates between pages', () => {
      render(<MasterList {...defaultProps} profiles={manyProfiles} />);
      
      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);
      
      expect(screen.getByText('user11')).toBeInTheDocument();
      expect(screen.queryByText('user1')).not.toBeInTheDocument();
    });

    it('updates items per page', () => {
      render(<MasterList {...defaultProps} profiles={manyProfiles} />);
      
      const pageSizeSelect = screen.getByLabelText(/items per page/i);
      fireEvent.change(pageSizeSelect, { target: { value: '25' } });
      
      const rows = screen.getAllByRole('row');
      expect(rows.length).toBe(26); // 25 profiles + header row
    });
  });
});
