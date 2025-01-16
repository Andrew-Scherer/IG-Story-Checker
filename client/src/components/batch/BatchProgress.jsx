import React from 'react';
import './BatchProgress.scss';

const BatchProgress = ({
  total,
  completed,
  failed,
  isRunning,
  error
}) => {
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  const isComplete = completed === total && total > 0;
  const hasError = !!error;

  const getBarClass = () => {
    if (hasError) return 'batch-progress__bar--error';
    if (isComplete) return 'batch-progress__bar--success';
    return '';
  };

  const getStatusText = () => {
    if (hasError) return error;
    if (isComplete) return 'Completed';
    if (isRunning) return 'In Progress';
    return 'Ready';
  };

  const getStatusClass = () => {
    if (hasError) return 'batch-progress__status--error';
    if (isComplete) return 'batch-progress__status--success';
    if (isRunning) return 'batch-progress__status--running';
    return '';
  };

  return (
    <div className="batch-progress">
      <div className="batch-progress__header">
        <div className="batch-progress__percentage">
          {percentage}%
        </div>
        <div className="batch-progress__stats">
          <span>{completed} completed</span>
          <span>{failed} failed</span>
        </div>
      </div>

      <div className="batch-progress__track">
        <div 
          className={`batch-progress__bar ${getBarClass()}`}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      <div className={`batch-progress__status ${getStatusClass()}`}>
        {getStatusText()}
      </div>
    </div>
  );
};

export default BatchProgress;
