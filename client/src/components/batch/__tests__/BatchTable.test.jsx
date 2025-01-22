import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import BatchTable from '../BatchTable';
import useBatchStore from '../../../stores/batchStore';

jest.mock('../../../stores/batchStore');

describe('BatchTable', () => {
  beforeEach(() => {
    useBatchStore.mockReturnValue({
      batches: [
        { id: '1', status: 'queued', niche: { name: 'Test Niche' }, completed_profiles: 0, total_profiles: 10 }
      ],
      loading: false,
      error: null,
      fetchBatches: jest.fn(),
      startBatches: jest.fn(),
      stopBatches: jest.fn(),
      deleteBatches: jest.fn(),
      clearError: jest.fn(),
      clearBatchLogs: jest.fn()
    });
  });

  it('renders BatchTable component', () => {
    render(<BatchTable />);
    expect(screen.getByText('Start Selected')).toBeInTheDocument();
  });

  it('calls startBatches when Start Selected button is clicked', async () => {
    const mockStartBatches = jest.fn();
    useBatchStore.mockReturnValue({
      ...useBatchStore(),
      startBatches: mockStartBatches
    });

    render(<BatchTable />);
    
    // Select the batch
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]); // Select the first batch checkbox (index 0 is the header checkbox)

    // Click the Start Selected button
    fireEvent.click(screen.getByText('Start Selected'));

    await waitFor(() => {
      expect(mockStartBatches).toHaveBeenCalledWith(['1']);
    });
  });
});
