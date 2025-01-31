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

      const result = await onImport(file);
      
      // Handle import errors
      if (result?.errors?.length > 0) {
        const nicheErrors = result.errors.filter(e => e.error.includes('niche'));
        const duplicateErrors = result.errors.filter(e => e.error.includes('exists'));
        const formatErrors = result.errors.filter(e => e.error.includes('format'));
        
        const errorMessages = [];
        
        if (nicheErrors.length > 0) {
          errorMessages.push(`Niche validation failed for ${nicheErrors.length} profiles`);
        }
        if (duplicateErrors.length > 0) {
          errorMessages.push(`${duplicateErrors.length} profiles already exist`);
        }
        if (formatErrors.length > 0) {
          errorMessages.push(`${formatErrors.length} profiles had invalid format`);
        }
        
        if (result.created.length > 0) {
          errorMessages.unshift(`Successfully imported ${result.created.length} profiles.`);
        }
        
        setError(errorMessages.join('\n'));
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message;
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      // Reset the file input
      e.target.value = '';
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
        {error && (
          <div className="file-importer__error">
            {error.split('\n').map((line, i) => (
              <div 
                key={i} 
                className={`file-importer__error-line ${
                  line.includes('Successfully') ? 'file-importer__error-line--success' : ''
                }`}
              >
                {line}
              </div>
            ))}
          </div>
        )}
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
