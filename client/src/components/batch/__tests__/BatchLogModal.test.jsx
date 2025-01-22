import React from 'react';
import { render, screen } from '@testing-library/react';
import BatchLogModal from '../BatchLogModal';
import useBatchStore from '../../../stores/batchStore';

// Mock the useBatchStore hook
jest.mock('../../../stores/batchStore');

describe('BatchLogModal', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
  });

  it('renders without crashing when batchLogs is undefined', () => {
    useBatchStore.mockReturnValue({
      batchLogs: undefined,
      totalLogs: 0,
      loadingLogs: false,
      fetchBatchLogs: jest.fn(),
    });

    render(<BatchLogModal batchId="123" isOpen={true} onClose={() => {}} />);
    
    expect(screen.getByText('No logs available for this batch.')).toBeInTheDocument();
  });

  it('displays loading message when loadingLogs is true', () => {
    useBatchStore.mockReturnValue({
      batchLogs: [],
      totalLogs: 0,
      loadingLogs: true,
      fetchBatchLogs: jest.fn(),
    });

    render(<BatchLogModal batchId="123" isOpen={true} onClose={() => {}} />);
    
    expect(screen.getByText('Loading logs...')).toBeInTheDocument();
  });

  it('renders batch logs when available', () => {
    const mockLogs = [
      { id: '1', timestamp: '2023-05-20T10:00:00Z', event_type: 'BATCH_START', message: 'Batch started' },
      { id: '2', timestamp: '2023-05-20T10:01:00Z', event_type: 'PROFILE_CHECK', message: 'Checking profile' },
    ];

    useBatchStore.mockReturnValue({
      batchLogs: mockLogs,
      totalLogs: 2,
      loadingLogs: false,
      fetchBatchLogs: jest.fn(),
    });

    render(<BatchLogModal batchId="123" isOpen={true} onClose={() => {}} />);
    
    expect(screen.getByText('Batch started')).toBeInTheDocument();
    expect(screen.getByText('Checking profile')).toBeInTheDocument();
  });

  it('displays no logs message when batchLogs is an empty array', () => {
    useBatchStore.mockReturnValue({
      batchLogs: [],
      totalLogs: 0,
      loadingLogs: false,
      fetchBatchLogs: jest.fn(),
    });

    render(<BatchLogModal batchId="123" isOpen={true} onClose={() => {}} />);
    
    expect(screen.getByText('No logs available for this batch.')).toBeInTheDocument();
  });
});
