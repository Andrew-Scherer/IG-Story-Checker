import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './FileImporter.scss';

const FileImporter = ({ 
  onImport, 
  disabled = false, 
  disabledMessage = 'Please select a niche before importing profiles' 
}) => {
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = async (e) => {
    const file = e.target.files[0];
    if (!file || disabled) return;
    
    try {
      setError('');
      setIsLoading(true);

      if (!file.type.startsWith('text/') && 
          !file.name.match(/\.(txt|csv|list)$/i)) {
        throw new Error('Please upload a text file containing Instagram profile URLs');
      }

      await onImport(file);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`file-importer ${disabled ? 'file-importer--disabled' : ''}`}
         data-testid="file-importer">
      <div className="file-importer__input-group">
        <label className="file-importer__label">
          {isLoading ? 'Importing...' : 'Import Profiles'}
          <input
            type="file"
            onChange={handleInputChange}
            className="file-importer__input"
            disabled={isLoading || disabled}
            accept=".txt,.csv,.list"
            data-testid="file-input"
          />
        </label>
        {error && <div className="file-importer__error">{error}</div>}
        {disabled && <div className="file-importer__message">{disabledMessage}</div>}
      </div>
    </div>
  );
};

FileImporter.propTypes = {
  onImport: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  disabledMessage: PropTypes.string
};

export default FileImporter;
