import React, { useState } from 'react';
import Button from '../common/Button';
import './BatchControl.scss';

/**
 * @typedef {Object} BatchControlProps
 * @property {Function} onStart - Callback when batch is started
 * @property {Function} onCancel - Callback when batch is cancelled
 * @property {boolean} isRunning - Whether a batch is currently running
 * @property {Array} selectedProfiles - Array of selected profiles
 * @property {string} [error] - Error message to display
 */

/**
 * Component for controlling batch operations
 * @param {BatchControlProps} props
 */
const BatchControl = ({ onStart, onCancel, isRunning, selectedProfiles, error: initialError }) => {
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [error, setError] = useState(initialError);

  const handleStart = () => {
    setError(null);
    onStart();
  };

  const handleCancelClick = () => {
    setShowConfirmation(true);
  };

  const handleConfirmCancel = () => {
    setShowConfirmation(false);
    onCancel();
  };

  const handleCancelConfirmation = () => {
    setShowConfirmation(false);
  };

  return (
    <div className="batch-control">
      <div className="batch-control__header">
        <h2 className="batch-control__title">Batch Control</h2>
        <div className={`batch-control__status ${isRunning ? 'batch-control__status--running' : ''}`}>
          {isRunning ? 'Batch in Progress' : `${selectedProfiles.length} Profiles Selected`}
        </div>
      </div>

      <div className="batch-control__actions">
        <Button
          onClick={handleStart}
          disabled={isRunning || selectedProfiles.length === 0}
        >
          Start
        </Button>
        
        {isRunning && (
          <Button
            onClick={handleCancelClick}
            variant="secondary"
            data-testid="cancel-batch-button"
          >
            Cancel Batch
          </Button>
        )}
      </div>

      {error && (
        <div className="batch-control__error">
          {error}
        </div>
      )}

      {showConfirmation && (
        <div className="batch-control__confirmation">
          <p>Are you sure you want to cancel the current batch?</p>
          <div className="batch-control__confirmation-actions">
            <Button 
              onClick={handleConfirmCancel}
              data-testid="confirm-cancel-button"
            >
              Confirm Cancel
            </Button>
            <Button 
              onClick={handleCancelConfirmation}
              variant="secondary"
              data-testid="dismiss-cancel-button"
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchControl;
