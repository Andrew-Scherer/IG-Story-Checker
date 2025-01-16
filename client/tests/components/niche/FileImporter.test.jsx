import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import FileImporter from '../../../src/components/niche/FileImporter';

describe('FileImporter Component', () => {
  const defaultProps = {
    onImport: jest.fn(),
    isLoading: false
  };

  const createFile = (content, type = 'text/plain') => {
    return new File([content], 'profiles.txt', { type });
  };

  it('renders file input and import button', () => {
    const { getByText, getByLabelText } = render(
      <FileImporter {...defaultProps} />
    );
    
    expect(getByLabelText('Choose file')).toBeInTheDocument();
    expect(getByText('Import Profiles')).toBeInTheDocument();
  });

  it('handles valid file selection', async () => {
    const { getByLabelText, getByText } = render(
      <FileImporter {...defaultProps} />
    );
    
    const file = createFile('@user1\n@user2\n@user3');
    const input = getByLabelText('Choose file');
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(getByText('profiles.txt')).toBeInTheDocument();
      expect(getByText('3 profiles found')).toBeInTheDocument();
    });
  });

  it('validates file type', async () => {
    const { getByLabelText, getByText } = render(
      <FileImporter {...defaultProps} />
    );
    
    const file = createFile('invalid', 'application/pdf');
    const input = getByLabelText('Choose file');
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(getByText('Invalid file type. Please select a text file.')).toBeInTheDocument();
    });
  });

  it('validates file content', async () => {
    const { getByLabelText, getByText } = render(
      <FileImporter {...defaultProps} />
    );
    
    const file = createFile('invalid content\nno usernames');
    const input = getByLabelText('Choose file');
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(getByText('No valid Instagram usernames found')).toBeInTheDocument();
    });
  });

  it('handles import process', async () => {
    const onImport = jest.fn();
    const { getByLabelText, getByText } = render(
      <FileImporter {...defaultProps} onImport={onImport} />
    );
    
    const file = createFile('@user1\n@user2\n@user3');
    const input = getByLabelText('Choose file');
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      fireEvent.click(getByText('Import Profiles'));
      expect(onImport).toHaveBeenCalledWith(['@user1', '@user2', '@user3']);
    });
  });

  it('shows loading state', () => {
    const { getByText } = render(
      <FileImporter {...defaultProps} isLoading={true} />
    );
    
    expect(getByText('Importing...')).toBeInTheDocument();
    expect(getByText('Importing...')).toBeDisabled();
  });

  it('allows file removal', async () => {
    const { getByLabelText, getByText, queryByText } = render(
      <FileImporter {...defaultProps} />
    );
    
    const file = createFile('@user1\n@user2');
    const input = getByLabelText('Choose file');
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(getByText('profiles.txt')).toBeInTheDocument();
      fireEvent.click(getByText('Remove'));
      expect(queryByText('profiles.txt')).not.toBeInTheDocument();
    });
  });

  it('validates duplicate usernames', async () => {
    const { getByLabelText, getByText } = render(
      <FileImporter {...defaultProps} />
    );
    
    const file = createFile('@user1\n@user1\n@user2');
    const input = getByLabelText('Choose file');
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(getByText('2 unique profiles found (1 duplicate removed)')).toBeInTheDocument();
    });
  });
});
