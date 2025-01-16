import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import Modal from '../../../src/components/common/Modal';

describe('Modal Component', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    title: 'Test Modal'
  };

  it('renders when open', () => {
    const { getByText, getByRole } = render(
      <Modal {...defaultProps}>
        <div>Modal content</div>
      </Modal>
    );
    
    expect(getByRole('dialog')).toBeInTheDocument();
    expect(getByText('Test Modal')).toBeInTheDocument();
    expect(getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    const { queryByRole } = render(
      <Modal {...defaultProps} isOpen={false}>
        <div>Modal content</div>
      </Modal>
    );
    
    expect(queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('calls onClose when clicking backdrop', () => {
    const onClose = jest.fn();
    const { getByTestId } = render(
      <Modal {...defaultProps} onClose={onClose}>
        <div>Modal content</div>
      </Modal>
    );
    
    fireEvent.click(getByTestId('modal-backdrop'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when pressing Escape key', () => {
    const onClose = jest.fn();
    const { getByRole } = render(
      <Modal {...defaultProps} onClose={onClose}>
        <div>Modal content</div>
      </Modal>
    );
    
    fireEvent.keyDown(getByRole('dialog'), { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not close when clicking modal content', () => {
    const onClose = jest.fn();
    const { getByText } = render(
      <Modal {...defaultProps} onClose={onClose}>
        <div>Modal content</div>
      </Modal>
    );
    
    fireEvent.click(getByText('Modal content'));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('renders with custom size', () => {
    const { getByRole } = render(
      <Modal {...defaultProps} size="large">
        <div>Modal content</div>
      </Modal>
    );
    
    expect(getByRole('dialog')).toHaveClass('modal--large');
  });

  it('renders with custom className', () => {
    const { getByRole } = render(
      <Modal {...defaultProps} className="custom-modal">
        <div>Modal content</div>
      </Modal>
    );
    
    expect(getByRole('dialog')).toHaveClass('custom-modal');
  });

  it('prevents body scroll when open', () => {
    const { unmount } = render(
      <Modal {...defaultProps}>
        <div>Modal content</div>
      </Modal>
    );
    
    expect(document.body.style.overflow).toBe('hidden');
    
    unmount();
    expect(document.body.style.overflow).toBe('');
  });

  it('supports custom close button text', () => {
    const { getByText } = render(
      <Modal {...defaultProps} closeButtonText="Done">
        <div>Modal content</div>
      </Modal>
    );
    
    expect(getByText('Done')).toBeInTheDocument();
  });

  it('supports footer content', () => {
    const { getByText } = render(
      <Modal
        {...defaultProps}
        footer={<button>Custom Footer</button>}
      >
        <div>Modal content</div>
      </Modal>
    );
    
    expect(getByText('Custom Footer')).toBeInTheDocument();
  });
});
