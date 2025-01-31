import React, { useState, useEffect, useCallback } from 'react';
import Button from '../common/Button';
import Table from '../common/Table';
import Modal from '../common/Modal';
import useBatchStore from '../../stores/batchStore';
import BatchLogModal from './BatchLogModal';
import './BatchTable.scss';

const BatchTable = () => {
  const [selectedBatches, setSelectedBatches] = useState([]);
  const [logModalOpen, setLogModalOpen] = useState(false);
  const [selectedBatchId, setSelectedBatchId] = useState(null);
  const [storiesModalOpen, setStoriesModalOpen] = useState(false);
  const [storiesUsernames, setStoriesUsernames] = useState([]);
  const [resumingBatches, setResumingBatches] = useState(false);
  const [startingBatches, setStartingBatches] = useState(false);
  const [stoppingBatches, setStoppingBatches] = useState(false);

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
      key: 'queue_position',
      title: 'Queue Position',
      render: (batch) => {
        if (batch.status === 'in_progress') return '0 (Running)';
        if (batch.status === 'queued') return `#${batch.queue_position}`;
        return '-';
      }
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

  const handleStartSelected = async () => {
    if (selectedBatches.length === 0 || startingBatches) return;
    try {
      setStartingBatches(true);
      await startBatches(selectedBatches);
    } catch (error) {
      console.error('Failed to start batches:', error);
      if (error.response && error.response.status === 409) {
        const errorData = error.response.data;
        const runningBatchIds = errorData.running_batch_ids || [];
        const errorMessage = `Cannot start new batches. Batch${
          runningBatchIds.length > 1 ? 'es' : ''
        } ${runningBatchIds.join(', ')} ${
          runningBatchIds.length > 1 ? 'are' : 'is'
        } already running.`;
        useBatchStore.getState().setError(errorMessage);
      } else {
        useBatchStore.getState().setError('Failed to start batches. Please try again.');
      }
    } finally {
      setStartingBatches(false);
    }
  };

  const handleResumeSelected = async () => {
    if (selectedBatches.length === 0 || resumingBatches) return;
    try {
      setResumingBatches(true);
      await resumeBatches(selectedBatches);
    } catch (error) {
      console.error('Failed to resume batches:', error);
      useBatchStore.getState().setError('Failed to resume batches. Please try again.');
    } finally {
      setResumingBatches(false);
    }
  };

  const handleStopSelected = async () => {
    if (selectedBatches.length === 0 || stoppingBatches) return;
    try {
      setStoppingBatches(true);
      await stopBatches(selectedBatches);
    } catch (error) {
      console.error('Failed to stop batches:', error);
      useBatchStore.getState().setError('Failed to stop batches. Please try again.');
    } finally {
      setStoppingBatches(false);
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

  // Check if any selected batch is paused
  const hasSelectedPausedBatches = selectedBatches.length > 0 && 
    batches.some(batch => selectedBatches.includes(batch.id) && batch.status === 'paused');

  return (
    <div className="batch-table">
      <div className="batch-table__controls">
        <Button onClick={handleDeleteSelected}>Delete Selection</Button>
        {selectedBatches.length > 0 && (
          <>
            <Button
              onClick={handleStartSelected}
              disabled={startingBatches || stoppingBatches}
            >
              {startingBatches ? 'Starting...' : 'Start Selected'}
            </Button>
            {hasSelectedPausedBatches && (
              <Button
                onClick={handleResumeSelected}
                disabled={resumingBatches || startingBatches || stoppingBatches}
              >
                {resumingBatches ? 'Resuming...' : 'Resume Selected'}
              </Button>
            )}
            <Button
              onClick={handleStopSelected}
              disabled={stoppingBatches || startingBatches}
            >
              {stoppingBatches ? 'Stopping...' : 'Stop Selected'}
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
