import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './FileImporter.scss';

const FileImporter = ({ onImport, allowedTypes, maxSize }) => {
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const validateFile = (file) => {
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(extension)) {
      throw new Error('Invalid file type. Allowed types: ' + allowedTypes.join(', '));
    }
    
    if (file.size > maxSize) {
      throw new Error('File too large. Maximum size: ' + (maxSize / (1024 * 1024)) + 'MB');
    }
  };

  const handleFile = async (file) => {
    try {
      setError('');
      setIsLoading(true);
      validateFile(file);
      await onImport(file);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFile(file);
    }
  };

  return (
    <div className="file-importer">
      <div className="file-importer__input-group">
        <input
          type="file"
          accept={allowedTypes.join(',')}
          onChange={handleInputChange}
          className="file-importer__input"
          disabled={isLoading}
        />
        {isLoading && <span>Importing...</span>}
        {error && <span className="file-importer__error">{error}</span>}
      </div>
    </div>
  );
};

FileImporter.propTypes = {
  onImport: PropTypes.func.isRequired,
  allowedTypes: PropTypes.arrayOf(PropTypes.string).isRequired,
  maxSize: PropTypes.number.isRequired
};

export default FileImporter;
