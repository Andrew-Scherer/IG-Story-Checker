import React, { act } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import StoryTargets from '../StoryTargets';

describe('StoryTargets Component', () => {
  const mockTargets = {
    minStories: 3,
    maxStories: 10,
    minFollowers: 1000,
    maxFollowers: 100000,
    minEngagement: 2.5,
    maxEngagement: 8.0
  };

  const defaultProps = {
    targets: mockTargets,
    onUpdate: jest.fn()
  };

  describe('Target Display', () => {
    it('renders all target fields with current values', async () => {
      await act(async () => {
        render(<StoryTargets {...defaultProps} />);
      });

      expect(screen.getByLabelText(/minimum stories/i)).toHaveValue(mockTargets.minStories);
      expect(screen.getByLabelText(/maximum stories/i)).toHaveValue(mockTargets.maxStories);
      expect(screen.getByLabelText(/minimum followers/i)).toHaveValue(mockTargets.minFollowers);
      expect(screen.getByLabelText(/maximum followers/i)).toHaveValue(mockTargets.maxFollowers);
      expect(screen.getByLabelText(/minimum engagement/i)).toHaveValue(mockTargets.minEngagement);
      expect(screen.getByLabelText(/maximum engagement/i)).toHaveValue(mockTargets.maxEngagement);
    });

    it('shows validation errors for invalid inputs', async () => {
      await act(async () => {
        render(<StoryTargets {...defaultProps} />);
      });
      
      const minStoriesInput = screen.getByLabelText(/minimum stories/i);
      await act(async () => {
        fireEvent.change(minStoriesInput, { target: { value: '-1' } });
      });
      expect(screen.getByText(/must be a positive number/i)).toBeInTheDocument();

      const maxFollowersInput = screen.getByLabelText(/maximum followers/i);
      fireEvent.change(maxFollowersInput, { target: { value: '999' } });
      expect(screen.getByText(/must be at least 1000/i)).toBeInTheDocument();
    });
  });

  describe('Target Updates', () => {
    it('updates target values on valid input', async () => {
      await act(async () => {
        render(<StoryTargets {...defaultProps} />);
      });
      
      const minStoriesInput = screen.getByLabelText(/minimum stories/i);
      await act(async () => {
        fireEvent.change(minStoriesInput, { target: { value: '5' } });
      });
      
      expect(defaultProps.onUpdate).toHaveBeenCalledWith({
        ...mockTargets,
        minStories: 5
      });
    });

    it('validates min/max relationships', async () => {
      await act(async () => {
        render(<StoryTargets {...defaultProps} />);
      });
      
      const maxStoriesInput = screen.getByLabelText(/maximum stories/i);
      await act(async () => {
        fireEvent.change(maxStoriesInput, { target: { value: '2' } });
      });
      
      expect(screen.getByText(/maximum must be greater than minimum/i)).toBeInTheDocument();
      expect(defaultProps.onUpdate).not.toHaveBeenCalled();
    });

    it('formats engagement rates as percentages', async () => {
      await act(async () => {
        render(<StoryTargets {...defaultProps} />);
      });
      
      const minEngagementInput = screen.getByLabelText(/minimum engagement/i);
      expect(minEngagementInput).toHaveValue(2.5);
      
      await act(async () => {
        fireEvent.change(minEngagementInput, { target: { value: '3.75' } });
      });
      expect(defaultProps.onUpdate).toHaveBeenCalledWith({
        ...mockTargets,
        minEngagement: 3.75
      });
    });
  });

  describe('Persistence', () => {
    it('saves changes when form is submitted', async () => {
      render(<StoryTargets {...defaultProps} />);
      
      const minStoriesInput = screen.getByLabelText(/minimum stories/i);
      const maxStoriesInput = screen.getByLabelText(/maximum stories/i);
      
      await act(async () => {
        fireEvent.change(minStoriesInput, { target: { value: '4' } });
        fireEvent.change(maxStoriesInput, { target: { value: '12' } });
        
        const saveButton = screen.getByRole('button', { name: /save/i });
        fireEvent.click(saveButton);
      });
      
      expect(defaultProps.onUpdate).toHaveBeenCalledWith({
        ...mockTargets,
        minStories: 4,
        maxStories: 12
      });
    });

    it('shows success message after saving', async () => {
      render(<StoryTargets {...defaultProps} />);
      
      await act(async () => {
        const saveButton = screen.getByRole('button', { name: /save/i });
        fireEvent.click(saveButton);
      });
      
      expect(await screen.findByText(/settings saved/i)).toBeInTheDocument();
    });

    it('shows error message when save fails', async () => {
      const failingProps = {
        ...defaultProps,
        onUpdate: jest.fn().mockRejectedValue(new Error('Save failed'))
      };
      
      render(<StoryTargets {...failingProps} />);
      
      await act(async () => {
        const saveButton = screen.getByRole('button', { name: /save/i });
        fireEvent.click(saveButton);
      });
      
      expect(await screen.findByText(/failed to save settings/i)).toBeInTheDocument();
    });
  });
});
