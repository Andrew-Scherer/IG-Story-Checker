import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import Table from '../common/Table';
import Button from '../common/Button';
import Input from '../common/Input';
import './ResultsDisplay.scss';

/**
 * @typedef {Object} StoryResult
 * @property {number} id - Profile ID
 * @property {string} username - Instagram username
 * @property {string} status - Check status ('success' | 'error')
 * @property {boolean} hasStory - Whether profile has a story
 * @property {string} [error] - Error message if status is 'error'
 * @property {string} checkedAt - ISO timestamp of check
 */

/**
 * Displays batch check results with filtering and sorting capabilities
 */
const ResultsDisplay = ({ results, onExport, onRetry, onClear }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [storyFilter, setStoryFilter] = useState('all');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: null });

  const filteredResults = useMemo(() => {
    return results.filter(result => {
      const matchesSearch = result.username.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || result.status === statusFilter;
      const matchesStory = storyFilter === 'all' || 
        (storyFilter === 'yes' && result.hasStory) || 
        (storyFilter === 'no' && !result.hasStory);
      
      return matchesSearch && matchesStatus && matchesStory;
    });
  }, [results, searchTerm, statusFilter, storyFilter]);

  const sortedResults = useMemo(() => {
    if (!sortConfig.key) return filteredResults;

    const sorted = [...filteredResults];
    sorted.sort((a, b) => {
      let aValue = a[sortConfig.key];
      let bValue = b[sortConfig.key];
      
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [filteredResults, sortConfig]);

  const handleSort = (key) => {
    setSortConfig(current => ({
      key,
      direction: current.key === key && current.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const failedResults = results.filter(r => r.status === 'error');

  const columns = [
    {
      key: 'username',
      header: 'Username',
      title: 'Username',
      sortable: true
    },
    {
      key: 'status',
      header: 'Status',
      title: 'Status',
      sortable: true,
      render: (result) => (
        <div className={`results-display__status results-display__status--${result.status}`}>
          {result.status === 'success' ? 'Success' : 'Error'}
          {result.error && <span>: {result.error}</span>}
        </div>
      )
    },
    {
      key: 'hasStory',
      header: 'Story',
      title: 'Story',
      sortable: true,
      render: (result) => (
        <div className={`results-display__story-indicator results-display__story-indicator--${result.hasStory ? 'yes' : 'no'}`}>
          {result.hasStory ? 'Yes' : 'No'}
        </div>
      )
    },
    {
      key: 'checkedAt',
      header: 'Checked At',
      title: 'Checked At',
      sortable: true,
      render: (result) => (
        <span className="results-display__timestamp">
          {formatTime(result.checkedAt)}
        </span>
      )
    }
  ];

  return (
    <div className="results-display">
      <div className="results-display__header">
        <h2 className="results-display__title">Results</h2>
        <div className="results-display__actions">
          <Button onClick={() => onExport(results)}>
            Export
          </Button>
          <Button 
            onClick={() => onRetry(failedResults)}
            disabled={!failedResults.length}
          >
            Retry Failed
          </Button>
          <Button 
            onClick={onClear}
            variant="secondary"
          >
            Clear
          </Button>
        </div>
      </div>

      <div className="results-display__filters">
        <Input
          type="text"
          placeholder="Search by username..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Status filter"
        >
          <option value="all">All Status</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
        </select>
        
        <select
          value={storyFilter}
          onChange={(e) => setStoryFilter(e.target.value)}
          aria-label="Story filter"
        >
          <option value="all">All Stories</option>
          <option value="yes">Has Story</option>
          <option value="no">No Story</option>
        </select>
      </div>

      {results.length > 0 ? (
        <Table
          className="results-display__table"
          data={sortedResults}
          columns={columns}
          sortConfig={sortConfig}
          onSort={handleSort}
        />
      ) : (
        <div className="results-display__empty">
          No results to display
        </div>
      )}
    </div>
  );
};

ResultsDisplay.propTypes = {
  /** Array of story check results */
  results: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.number.isRequired,
    username: PropTypes.string.isRequired,
    status: PropTypes.oneOf(['success', 'error']).isRequired,
    hasStory: PropTypes.bool.isRequired,
    error: PropTypes.string,
    checkedAt: PropTypes.string.isRequired
  })).isRequired,
  /** Callback when export button is clicked */
  onExport: PropTypes.func.isRequired,
  /** Callback when retry button is clicked */
  onRetry: PropTypes.func.isRequired,
  /** Callback when clear button is clicked */
  onClear: PropTypes.func.isRequired
};

export default ResultsDisplay;
