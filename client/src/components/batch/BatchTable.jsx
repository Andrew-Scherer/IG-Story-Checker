import React, { useState, useEffect, useCallback } from 'react';
import Button from '../common/Button';
import Table from '../common/Table';
import useBatchStore from '../../stores/batchStore';
import BatchLogModal from './BatchLogModal';
import './BatchTable.scss';

const BatchTable = () => {
  const [selectedBatches, setSelectedBatches] = useState([]);
  const [logModalOpen, setLogModalOpen] = useState(false);
  const [selectedBatchId, setSelectedBatchId] = useState(null);
  const {
    batches,
    loading,
    error,
    fetchBatches,
    startBatches,
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
        batch.total_profiles ?
          `${((batch.successful_checks / batch.total_profiles) * 100).toFixed(1)}%` :
          '0%'
    },
    {
      key: 'stories_found',
      title: 'Stories Found',
      render: (batch) =>
        `${batch.successful_checks}/${batch.total_profiles}`
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
    if (selectedBatches.length === 0) return;
    try {
      await startBatches(selectedBatches);
    } catch (error) {
      console.error('Failed to start batches:', error);
      if (error.response && error.response.status === 409) {
        const errorData = error.response.data;
        const runningBatchIds = errorData.running_batch_ids || [];
        const errorMessage = `Cannot start new batches. Batch${runningBatchIds.length > 1 ? 'es' : ''} ${runningBatchIds.join(', ')} ${runningBatchIds.length > 1 ? 'are' : 'is'} already running.`;
        useBatchStore.getState().setError(errorMessage);
      } else {
        useBatchStore.getState().setError('Failed to start batches. Please try again.');
      }
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

  return (
    <div className="batch-table">
      <div className="batch-table__controls">
        <Button onClick={handleDeleteSelected}>Delete Selection</Button>
        {selectedBatches.length > 0 && (
          <>
            <Button onClick={handleStartSelected}>Start Selected</Button>
            <Button onClick={handleStopSelected}>Stop Selected</Button>
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
    </div>
  );
};

export default BatchTable;
