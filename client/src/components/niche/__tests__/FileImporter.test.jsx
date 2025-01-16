import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FileImporter from '../FileImporter';

describe('FileImporter Component', () => {
  const mockOnImport = jest.fn();
  const defaultProps = {
    onImport: mockOnImport,
    allowedTypes: ['.csv', '.xlsx'],
    maxSize: 5 * 1024 * 1024 // 5MB
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders file input and drop zone', () => {
    const { getByText, getByTestId } = render(<FileImporter {...defaultProps} />);
    
    expect(getByText(/drag and drop/i)).toBeInTheDocument();
    expect(getByText(/or click to select/i)).toBeInTheDocument();
    expect(getByTestId('file-input')).toBeInTheDocument();
  });

  it('shows allowed file types', () => {
    const { getByText } = render(<FileImporter {...defaultProps} />);
    
    defaultProps.allowedTypes.forEach(type => {
      expect(getByText(new RegExp(type, 'i'))).toBeInTheDocument();
    });
  });

  it('handles file selection via input', async () => {
    const { getByTestId } = render(<FileImporter {...defaultProps} />);
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    
    const input = getByTestId('file-input');
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(mockOnImport).toHaveBeenCalledWith(file);
    });
  });

  it('handles file drop', async () => {
    const { getByTestId } = render(<FileImporter {...defaultProps} />);
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const dropZone = getByTestId('drop-zone');
    
    fireEvent.dragOver(dropZone);
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [file]
      }
    });
    
    await waitFor(() => {
      expect(mockOnImport).toHaveBeenCalledWith(file);
    });
  });

  it('validates file type', async () => {
    const { getByTestId, getByText } = render(<FileImporter {...defaultProps} />);
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    
    const input = getByTestId('file-input');
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(getByText(/invalid file type/i)).toBeInTheDocument();
      expect(mockOnImport).not.toHaveBeenCalled();
    });
  });

  it('validates file size', async () => {
    const { getByTestId, getByText } = render(<FileImporter {...defaultProps} />);
    const largeFile = new File(['x'.repeat(6 * 1024 * 1024)], 'large.csv', { type: 'text/csv' });
    
    const input = getByTestId('file-input');
    fireEvent.change(input, { target: { files: [largeFile] } });
    
    await waitFor(() => {
      expect(getByText(/file too large/i)).toBeInTheDocument();
      expect(mockOnImport).not.toHaveBeenCalled();
    });
  });

  it('shows loading state during import', async () => {
    const { getByTestId, getByRole } = render(<FileImporter {...defaultProps} />);
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    
    const input = getByTestId('file-input');
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles drag events correctly', () => {
    const { getByTestId } = render(<FileImporter {...defaultProps} />);
    const dropZone = getByTestId('drop-zone');
    
    fireEvent.dragEnter(dropZone);
    expect(dropZone).toHaveClass('file-importer__drop-zone--active');
    
    fireEvent.dragLeave(dropZone);
    expect(dropZone).not.toHaveClass('file-importer__drop-zone--active');
  });

  it('shows error on import failure', async () => {
    const mockError = new Error('Import failed');
    const mockOnImportWithError = jest.fn().mockRejectedValue(mockError);
    const { getByTestId, getByText } = render(
      <FileImporter {...defaultProps} onImport={mockOnImportWithError} />
    );
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const input = getByTestId('file-input');
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(getByText(/import failed/i)).toBeInTheDocument();
    });
  });
});
