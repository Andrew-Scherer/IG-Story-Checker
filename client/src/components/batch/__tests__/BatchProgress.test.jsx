import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import BatchProgress from '../BatchProgress';

describe('BatchProgress Component', () => {
  const defaultProps = {
    total: 100,
    completed: 0,
    failed: 0,
    isRunning: false,
    error: null
  };

  describe('Progress Display', () => {
    it('shows correct progress percentage', () => {
      const props = { ...defaultProps, completed: 50 };
      render(<BatchProgress {...props} />);
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('shows completed count', () => {
      const props = { ...defaultProps, completed: 25 };
      render(<BatchProgress {...props} />);
      expect(screen.getByText(/25 completed/i)).toBeInTheDocument();
    });

    it('shows failed count', () => {
      const props = { ...defaultProps, failed: 10 };
      render(<BatchProgress {...props} />);
      expect(screen.getByText(/10 failed/i)).toBeInTheDocument();
    });
  });

  describe('Status Updates', () => {
    it('shows running status when active', () => {
      const props = { ...defaultProps, isRunning: true };
      render(<BatchProgress {...props} />);
      expect(screen.getByText(/in progress/i)).toBeInTheDocument();
    });

    it('shows completed status when done', () => {
      const props = { ...defaultProps, completed: 100 };
      render(<BatchProgress {...props} />);
      expect(screen.getByText('Completed', { exact: true })).toBeInTheDocument();
    });

    it('shows error message when provided', () => {
      const props = { ...defaultProps, error: 'Network error' };
      render(<BatchProgress {...props} />);
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  describe('Progress Bar', () => {
    it('updates progress bar width', () => {
      const props = { ...defaultProps, completed: 75 };
      render(<BatchProgress {...props} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveStyle({ width: '75%' });
    });

    it('shows error state in progress bar', () => {
      const props = { ...defaultProps, error: 'Error occurred' };
      render(<BatchProgress {...props} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveClass('batch-progress__bar--error');
    });

    it('shows success state when complete', () => {
      const props = { ...defaultProps, completed: 100 };
      render(<BatchProgress {...props} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveClass('batch-progress__bar--success');
    });
  });
});
