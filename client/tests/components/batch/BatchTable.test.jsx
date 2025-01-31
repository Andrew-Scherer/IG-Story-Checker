import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BatchTable from '../../../src/components/batch/BatchTable';
import useBatchStore from '../../../src/stores/batchStore';

// Mock the batch store
jest.mock('../../../src/stores/batchStore');

describe('BatchTable', () => {
  const mockBatches = [
    {
      id: '1',
      niche: { name: 'Test Niche' },
      status: 'queued',
      position: 1,
      completed_profiles: 5,
      total_profiles: 10,
      successful_checks: 3,
      completed_at: null,
      profiles_with_stories: ['user1', 'user2']
    },
    {
      id: '2',
      niche: { name: 'Test Niche 2' },
      status: 'running',
      position: 0,
      completed_profiles: 8,
      total_profiles: 10,
      successful_checks: 6,
      completed_at: new Date().toISOString(),
      profiles_with_stories: ['user3']
    }
  ];

  const mockStore = {
    batches: mockBatches,
    loading: false,
    error: null,
    fetchBatches: jest.fn(),
    resumeBatches: jest.fn(),
    stopBatches: jest.fn(),
    deleteBatches: jest.fn(),
    clearError: jest.fn(),
    clearBatchLogs: jest.fn()
  };

  beforeEach(() => {
    useBatchStore.mockImplementation((selector) => selector(mockStore));
    jest.clearAllMocks();
  });

  it('renders batch table with data', () => {
    render(<BatchTable />);
    
    // Check if niche names are displayed
    expect(screen.getByText('Test Niche')).toBeInTheDocument();
    expect(screen.getByText('Test Niche 2')).toBeInTheDocument();
    
    // Check if progress is displayed
    expect(screen.getByText('5/10')).toBeInTheDocument();
    expect(screen.getByText('8/10')).toBeInTheDocument();
    
    // Check if queue positions are displayed correctly
    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('handles batch selection', () => {
    render(<BatchTable />);
    
    // Find and click checkboxes
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]); // Select first batch
    
    // Check if action buttons appear
    expect(screen.getByText('Stop Selected')).toBeInTheDocument();
  });

  it('handles stop action', async () => {
    render(<BatchTable />);
    
    // Select a batch and click stop
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]);
    
    const stopButton = screen.getByText('Stop Selected');
    fireEvent.click(stopButton);
    
    await waitFor(() => {
      expect(mockStore.stopBatches).toHaveBeenCalled();
    });
  });

  it('handles resume action for paused batches', async () => {
    const pausedBatch = {
      ...mockBatches[0],
      status: 'paused',
      position: null
    };
    
    const mockStoreWithPaused = {
      ...mockStore,
      batches: [pausedBatch, mockBatches[1]]
    };
    
    useBatchStore.mockImplementation((selector) => selector(mockStoreWithPaused));
    
    render(<BatchTable />);
    
    // Select the paused batch
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]);
    
    // Check if resume button appears and click it
    const resumeButton = screen.getByText('Resume Selected');
    fireEvent.click(resumeButton);
    
    await waitFor(() => {
      expect(mockStore.resumeBatches).toHaveBeenCalled();
    });
  });

  it('handles delete action', async () => {
    render(<BatchTable />);
    
    // Select a batch and click delete
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]);
    
    const deleteButton = screen.getByText('Delete Selection');
    fireEvent.click(deleteButton);
    
    await waitFor(() => {
      expect(mockStore.deleteBatches).toHaveBeenCalled();
    });
  });

  it('displays error message when present', () => {
    const mockStoreWithError = {
      ...mockStore,
      error: 'Test error message'
    };
    
    useBatchStore.mockImplementation((selector) => selector(mockStoreWithError));
    
    render(<BatchTable />);
    
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    const mockStoreLoading = {
      ...mockStore,
      loading: true
    };
    
    useBatchStore.mockImplementation((selector) => selector(mockStoreLoading));
    
    render(<BatchTable />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('handles refresh action', async () => {
    render(<BatchTable />);
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(mockStore.fetchBatches).toHaveBeenCalled();
    });
  });
});