import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BatchControl from '../BatchControl';

describe('BatchControl Component', () => {
  const mockOnStart = jest.fn();
  const mockOnCancel = jest.fn();
  const defaultProps = {
    onStart: mockOnStart,
    onCancel: mockOnCancel,
    isRunning: false,
    selectedProfiles: [
      { id: 1, username: 'user1' },
      { id: 2, username: 'user2' }
    ]
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Batch Creation', () => {
    it('renders start button when not running', () => {
      const { getByRole } = render(<BatchControl {...defaultProps} />);
      expect(getByRole('button', { name: /start/i })).toBeInTheDocument();
    });

    it('disables start button when no profiles selected', () => {
      const { getByRole } = render(
        <BatchControl {...defaultProps} selectedProfiles={[]} />
      );
      expect(getByRole('button', { name: /start/i })).toBeDisabled();
    });

    it('shows selected profile count', () => {
      const { getByText } = render(<BatchControl {...defaultProps} />);
      expect(getByText(/2 profiles selected/i)).toBeInTheDocument();
    });

    it('calls onStart when start button clicked', () => {
      const { getByRole } = render(<BatchControl {...defaultProps} />);
      fireEvent.click(getByRole('button', { name: /start/i }));
      expect(mockOnStart).toHaveBeenCalled();
    });
  });

  describe('Status Updates', () => {
    it('shows cancel button when running', () => {
      const { getByRole } = render(
        <BatchControl {...defaultProps} isRunning={true} />
      );
      expect(getByRole('button', { name: /cancel batch/i })).toBeInTheDocument();
    });

    it('disables start button while running', () => {
      const { getByRole } = render(
        <BatchControl {...defaultProps} isRunning={true} />
      );
      expect(getByRole('button', { name: /start/i })).toBeDisabled();
    });

    it('shows running status text', () => {
      const { getByText } = render(
        <BatchControl {...defaultProps} isRunning={true} />
      );
      expect(getByText(/batch in progress/i)).toBeInTheDocument();
    });
  });

  describe('Cancellation', () => {
    it('calls onCancel when cancel button clicked', async () => {
      const { getByTestId } = render(
        <BatchControl {...defaultProps} isRunning={true} />
      );
      
      fireEvent.click(getByTestId('cancel-batch-button'));
      fireEvent.click(getByTestId('confirm-cancel-button'));
      
      await waitFor(() => {
        expect(mockOnCancel).toHaveBeenCalled();
      });
    });

    it('shows confirmation dialog before cancelling', () => {
      const { getByTestId, getByText } = render(
        <BatchControl {...defaultProps} isRunning={true} />
      );
      
      fireEvent.click(getByTestId('cancel-batch-button'));
      
      expect(getByText(/are you sure/i)).toBeInTheDocument();
      expect(getByTestId('confirm-cancel-button')).toBeInTheDocument();
      expect(getByTestId('dismiss-cancel-button')).toBeInTheDocument();
    });

    it('does not call onCancel if confirmation is cancelled', () => {
      const { getByTestId } = render(
        <BatchControl {...defaultProps} isRunning={true} />
      );
      
      fireEvent.click(getByTestId('cancel-batch-button'));
      fireEvent.click(getByTestId('dismiss-cancel-button'));
      
      expect(mockOnCancel).not.toHaveBeenCalled();
    });

    it('calls onCancel if confirmation is confirmed', async () => {
      const { getByTestId } = render(
        <BatchControl {...defaultProps} isRunning={true} />
      );
      
      fireEvent.click(getByTestId('cancel-batch-button'));
      fireEvent.click(getByTestId('confirm-cancel-button'));
      
      await waitFor(() => {
        expect(mockOnCancel).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error message when provided', () => {
      const error = 'Test error message';
      const { getByText } = render(
        <BatchControl {...defaultProps} error={error} />
      );
      expect(getByText(error)).toBeInTheDocument();
    });

    it('clears error when starting new batch', () => {
      const error = 'Test error message';
      const { getByText, getByRole, queryByText } = render(
        <BatchControl {...defaultProps} error={error} />
      );
      
      expect(getByText(error)).toBeInTheDocument();
      
      fireEvent.click(getByRole('button', { name: /start/i }));
      
      expect(queryByText(error)).not.toBeInTheDocument();
    });
  });
});
