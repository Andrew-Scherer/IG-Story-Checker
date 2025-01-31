import React, { useState, useEffect, useCallback } from 'react';
import Button from '../common/Button';
import Table from '../common/Table';
import Modal from '../common/Modal';
import useBatchStore from '../../stores/batchStore';
import BatchLogModal from './BatchLogModal';
import './BatchTable.scss';

// Position display helper
function getPositionDisplay(batch) {
  if (batch.position === 0) return 'Running';
  if (batch.position > 0) return `#${batch.position}`;
  return '-';  // null position
}

const BatchTable = () => {
  const [selectedBatches, setSelectedBatches] = useState([]);
  const [logModalOpen, setLogModalOpen] = useState(false);
  const [selectedBatchId, setSelectedBatchId] = useState(null);
  const [storiesModalOpen, setStoriesModalOpen] = useState(false);
  const [storiesUsernames, setStoriesUsernames] = useState([]);

  const {
    batches,
    loading,
    error,
    fetchBatches,
    startBatches,
    resumeBatches,
    stopBatches,
    deleteBatches,
    clearError,
    clearBatchLogs
  } = useBatchStore();

  useEffect(() => {
    fetchBatches();
  }, [fetchBatches]);

  const handleRefresh = useCallback(() => {
    fetchBatches();
  }, [fetchBatches]);

  const handleStoriesClick = (batch) => {
    if (batch.profiles_with_stories && batch.profiles_with_stories.length > 0) {
      setStoriesUsernames(batch.profiles_with_stories);
      setStoriesModalOpen(true);
    }
  };

  const columns = [
    {
      key: 'niche',
      title: 'Niche',
      render: (batch) => batch.niche.name
    },
    {
      key: 'progress',
      title: 'Progress',
      render: (batch) => `${batch.completed_profiles}/${batch.total_profiles}`
    },
    {
      key: 'status',
      title: 'Status',
      render: (batch) => batch.status
    },
    {
      key: 'completed_at',
      title: 'Time Completed',
      render: (batch) =>
        batch.completed_at
          ? new Date(batch.completed_at).toLocaleString()
          : '-'
    },
    {
      key: 'position',
      title: 'Queue Position',
      render: (batch) => getPositionDisplay(batch)
    },
    {
      key: 'success_rate',
      title: 'Success Rate',
      render: (batch) =>
        batch.total_profiles
          ? `${((batch.successful_checks / batch.total_profiles) * 100).toFixed(1)}%`
          : '0%'
    },
    {
      key: 'stories_found',
      title: 'Stories Found',
      render: (batch) => (
        <span
          className="stories-found"
          onClick={() => handleStoriesClick(batch)}
          style={{ cursor: 'pointer', color: batch.profiles_with_stories?.length ? 'blue' : 'gray' }}
        >
          {`${batch.successful_checks}/${batch.total_profiles}`}
        </span>
      )
    },
    {
      key: 'actions',
      title: 'Actions',
      render: (batch) => (
        <Button onClick={() => handleViewLogs(batch.id)}>View Logs</Button>
      )
    }
  ];

  const handleDeleteSelected = async () => {
    if (selectedBatches.length === 0) return;
    try {
      await deleteBatches(selectedBatches);
      setSelectedBatches([]);
    } catch (error) {
      console.error('Failed to delete batches:', error);
    }
  };

  const handleResumeSelected = async () => {
    if (selectedBatches.length === 0) return;
    try {
      await resumeBatches(selectedBatches);
    } catch (error) {
      console.error('Failed to resume batches:', error);
    }
  };

  const handleStopSelected = async () => {
    if (selectedBatches.length === 0) return;
    try {
      await stopBatches(selectedBatches);
    } catch (error) {
      console.error('Failed to stop batches:', error);
    }
  };

  const handleViewLogs = (batchId) => {
    setSelectedBatchId(batchId);
    setLogModalOpen(true);
  };

  const handleCloseLogModal = () => {
    setLogModalOpen(false);
    clearBatchLogs();
  };
const handleStartSelected = async () => {
  if (selectedBatches.length === 0) return;
  try {
    await startBatches(selectedBatches);
  } catch (error) {
    console.error('Failed to start batches:', error);
  }
};

// Check if any selected batch is paused or queued
const hasSelectedPausedBatches = selectedBatches.length > 0 &&
  batches.some(batch => selectedBatches.includes(batch.id) && batch.status === 'paused');

const hasSelectedQueuedBatches = selectedBatches.length > 0 &&
  batches.some(batch => selectedBatches.includes(batch.id) && batch.status === 'queued');

return (
  <div className="batch-table">
      <div className="batch-table__controls">
        <Button onClick={handleDeleteSelected}>Delete Selection</Button>
        {selectedBatches.length > 0 && (
          <>
            {hasSelectedQueuedBatches && (
              <Button onClick={handleStartSelected}>
                Start Selected
              </Button>
            )}
            {hasSelectedPausedBatches && (
              <Button onClick={handleResumeSelected}>
                Resume Selected
              </Button>
            )}
            <Button onClick={handleStopSelected}>
              Stop Selected
            </Button>
          </>
        )}
        <Button onClick={handleRefresh}>Refresh</Button>
      </div>
      {error && (
        <div className="batch-table__error" onClick={clearError}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="batch-table__loading">Loading...</div>
      ) : (
        <Table
          data={batches}
          columns={columns}
          selectable={true}
          selectedRows={selectedBatches}
          onSelectionChange={setSelectedBatches}
        />
      )}

      <BatchLogModal
        batchId={selectedBatchId}
        isOpen={logModalOpen}
        onClose={handleCloseLogModal}
      />

      {storiesModalOpen && (
        <Modal
          title="Profiles with Stories"
          isOpen={storiesModalOpen}
          onClose={() => setStoriesModalOpen(false)}
        >
          <div className="stories-modal">
            {storiesUsernames.length > 0 ? (
              <textarea
                readOnly
                value={storiesUsernames.join('\n')}
                style={{ width: '100%', height: '200px' }}
              />
            ) : (
              <p>No profiles with stories found.</p>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};

export default BatchTable;
