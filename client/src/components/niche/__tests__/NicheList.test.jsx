import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import NicheList from '../NicheList';

describe('NicheList Component', () => {
  const mockNiches = [
    { id: 1, name: 'Fitness', profileCount: 150 },
    { id: 2, name: 'Travel', profileCount: 200 },
    { id: 3, name: 'Food', profileCount: 175 }
  ];

  const defaultProps = {
    niches: mockNiches,
    selectedNicheId: null,
    onSelect: jest.fn(),
    onReorder: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders list of niches', () => {
    const { getByText } = render(<NicheList {...defaultProps} />);
    
    mockNiches.forEach(niche => {
      expect(getByText(niche.name)).toBeInTheDocument();
      expect(getByText(niche.profileCount.toString())).toBeInTheDocument();
    });
  });

  it('shows empty state when no niches', () => {
    const { getByText } = render(
      <NicheList {...defaultProps} niches={[]} />
    );
    
    expect(getByText('No niches found')).toBeInTheDocument();
  });

  it('highlights selected niche', () => {
    const { getByText } = render(
      <NicheList {...defaultProps} selectedNicheId={2} />
    );
    
    const selectedNiche = getByText('Travel').closest('li');
    expect(selectedNiche).toHaveClass('niche-list__item--selected');
  });

  it('calls onSelect when clicking a niche', () => {
    const onSelect = jest.fn();
    const { getByText } = render(
      <NicheList {...defaultProps} onSelect={onSelect} />
    );
    
    fireEvent.click(getByText('Fitness'));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it('supports keyboard navigation', () => {
    const onSelect = jest.fn();
    const { getAllByRole } = render(
      <NicheList {...defaultProps} onSelect={onSelect} />
    );
    
    const items = getAllByRole('listitem');
    
    // Press Enter to select
    fireEvent.keyDown(items[0], { key: 'Enter' });
    expect(onSelect).toHaveBeenCalledWith(1);
    
    // Press Space to select
    fireEvent.keyDown(items[1], { key: ' ' });
    expect(onSelect).toHaveBeenCalledWith(2);
  });

  describe('Drag and Drop', () => {
    it('handles drag start', () => {
      const { getAllByRole } = render(<NicheList {...defaultProps} />);
      const items = getAllByRole('listitem');
      
      fireEvent.dragStart(items[0]);
      expect(items[0]).toHaveClass('niche-list__item--dragging');
    });

    it('handles drag over', () => {
      const { getAllByRole } = render(<NicheList {...defaultProps} />);
      const items = getAllByRole('listitem');
      
      fireEvent.dragStart(items[0]);
      fireEvent.dragOver(items[2]);
      
      expect(items[2]).toHaveClass('niche-list__item--over');
    });

    it('handles drop', () => {
      const onReorder = jest.fn();
      const { getAllByRole } = render(
        <NicheList {...defaultProps} onReorder={onReorder} />
      );
      
      const items = getAllByRole('listitem');
      
      fireEvent.dragStart(items[0]);
      fireEvent.dragOver(items[2]);
      fireEvent.drop(items[2]);
      
      expect(onReorder).toHaveBeenCalledWith(0, 2);
    });

    it('prevents dropping on itself', () => {
      const onReorder = jest.fn();
      const { getAllByRole } = render(
        <NicheList {...defaultProps} onReorder={onReorder} />
      );
      
      const items = getAllByRole('listitem');
      
      fireEvent.dragStart(items[0]);
      fireEvent.dragOver(items[0]);
      fireEvent.drop(items[0]);
      
      expect(onReorder).not.toHaveBeenCalled();
    });

    it('cleans up drag state after drop', () => {
      const { getAllByRole } = render(<NicheList {...defaultProps} />);
      const items = getAllByRole('listitem');
      
      fireEvent.dragStart(items[0]);
      fireEvent.dragOver(items[2]);
      fireEvent.drop(items[2]);
      
      expect(items[0]).not.toHaveClass('niche-list__item--dragging');
      expect(items[2]).not.toHaveClass('niche-list__item--over');
    });
  });
});
