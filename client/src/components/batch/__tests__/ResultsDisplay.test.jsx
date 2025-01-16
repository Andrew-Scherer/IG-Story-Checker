import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResultsDisplay from '../ResultsDisplay';

describe('ResultsDisplay Component', () => {
  const mockResults = [
    { id: 1, username: 'user1', status: 'success', hasStory: true, checkedAt: '2023-01-01T12:00:00Z' },
    { id: 2, username: 'user2', status: 'error', error: 'Not found', checkedAt: '2023-01-01T12:01:00Z' },
    { id: 3, username: 'user3', status: 'success', hasStory: false, checkedAt: '2023-01-01T12:02:00Z' }
  ];

  const defaultProps = {
    results: mockResults,
    onExport: jest.fn(),
    onRetry: jest.fn(),
    onClear: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Results Display', () => {
    it('renders results in a table', () => {
      const { getByText, getAllByRole } = render(<ResultsDisplay {...defaultProps} />);
      
      expect(getByText('Results')).toBeInTheDocument();
      expect(getAllByRole('row')).toHaveLength(mockResults.length + 1); // +1 for header row
      
      mockResults.forEach(result => {
        expect(getByText(result.username)).toBeInTheDocument();
      });
    });

    it('shows empty state when no results', () => {
      const { getByText } = render(<ResultsDisplay {...defaultProps} results={[]} />);
      expect(getByText(/no results to display/i)).toBeInTheDocument();
    });

    it('formats timestamps correctly', () => {
      const { getByText } = render(<ResultsDisplay {...defaultProps} />);
      expect(getByText('05:00:00')).toBeInTheDocument();
    });
  });

  describe('Filtering', () => {
    it('filters by status', () => {
      const { getByRole, queryByText } = render(<ResultsDisplay {...defaultProps} />);
      
      fireEvent.change(getByRole('combobox', { name: /status/i }), {
        target: { value: 'success' }
      });
      
      expect(queryByText('user1')).toBeInTheDocument();
      expect(queryByText('user2')).not.toBeInTheDocument();
    });

    it('filters by story presence', () => {
      const { getByRole, queryByText } = render(<ResultsDisplay {...defaultProps} />);
      
      fireEvent.change(getByRole('combobox', { name: /story/i }), {
        target: { value: 'yes' }
      });
      
      expect(queryByText('user1')).toBeInTheDocument();
      expect(queryByText('user3')).not.toBeInTheDocument();
    });

    it('supports text search', () => {
      const { getByPlaceholderText, queryByText } = render(<ResultsDisplay {...defaultProps} />);
      
      fireEvent.change(getByPlaceholderText(/search/i), {
        target: { value: 'user1' }
      });
      
      expect(queryByText('user1')).toBeInTheDocument();
      expect(queryByText('user2')).not.toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('exports results', () => {
      const { getByRole } = render(<ResultsDisplay {...defaultProps} />);
      
      fireEvent.click(getByRole('button', { name: /export/i }));
      expect(defaultProps.onExport).toHaveBeenCalledWith(mockResults);
    });

    it('retries failed checks', () => {
      const { getByRole } = render(<ResultsDisplay {...defaultProps} />);
      
      fireEvent.click(getByRole('button', { name: /retry failed/i }));
      expect(defaultProps.onRetry).toHaveBeenCalledWith(
        expect.arrayContaining([mockResults[1]])
      );
    });

    it('clears results', () => {
      const { getByRole } = render(<ResultsDisplay {...defaultProps} />);
      
      fireEvent.click(getByRole('button', { name: /clear/i }));
      expect(defaultProps.onClear).toHaveBeenCalled();
    });

    it('disables retry button when no failed checks', () => {
      const successResults = mockResults.map(r => ({ ...r, status: 'success' }));
      const { getByRole } = render(
        <ResultsDisplay {...defaultProps} results={successResults} />
      );
      
      expect(getByRole('button', { name: /retry failed/i })).toBeDisabled();
    });
  });

  describe('Sorting', () => {
    it('sorts by username', () => {
      const { getAllByRole, getByRole } = render(<ResultsDisplay {...defaultProps} />);
      
      fireEvent.click(getByRole('columnheader', { name: /username/i }));
      const cells = getAllByRole('cell');
      expect(cells[0]).toHaveTextContent('user1');
      
      fireEvent.click(getByRole('columnheader', { name: /username/i }));
      expect(cells[0]).toHaveTextContent('user3');
    });

    it('sorts by status', () => {
      const { getAllByRole, getByRole } = render(<ResultsDisplay {...defaultProps} />);
      
      fireEvent.click(getByRole('columnheader', { name: /status/i }));
      const cells = getAllByRole('cell');
      expect(cells[1]).toHaveTextContent('Error: Not found');
      
      fireEvent.click(getByRole('columnheader', { name: /status/i }));
      expect(cells[1]).toHaveTextContent('Success');
    });

    it('sorts by timestamp', () => {
      const { getAllByRole, getByRole } = render(<ResultsDisplay {...defaultProps} />);
      
      fireEvent.click(getByRole('columnheader', { name: /checked at/i }));
      const cells = getAllByRole('cell');
      expect(cells[3]).toHaveTextContent('05:00:00');
      
      fireEvent.click(getByRole('columnheader', { name: /checked at/i }));
      expect(cells[3]).toHaveTextContent('05:02:00');
    });
  });
});
