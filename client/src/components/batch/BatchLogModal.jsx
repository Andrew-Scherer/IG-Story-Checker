import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import useBatchStore from '../../stores/batchStore';
import './BatchLogModal.scss';

const BatchLogModal = ({ batchId, isOpen, onClose }) => {
  const { fetchBatchLogs, batchLogs, totalLogs, loadingLogs } = useBatchStore();
  const [page, setPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    if (isOpen && batchId) {
      fetchBatchLogs(batchId, null, null, pageSize, (page - 1) * pageSize);
    }
  }, [isOpen, batchId, page, fetchBatchLogs]);

  const handlePageChange = (newPage) => {
    setPage(newPage);
  };

  const renderContent = () => {
    if (loadingLogs) {
      return <div className="loading">Loading logs...</div>;
    }

    if (!batchLogs || batchLogs.length === 0) {
      return <div className="no-logs">No logs available for this batch.</div>;
    }

    return (
      <>
        <table className="log-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Event Type</th>
              <th>Message</th>
              <th>Profile ID</th>
              <th>Proxy ID</th>
            </tr>
          </thead>
          <tbody>
            {batchLogs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
                <td>{log.event_type}</td>
                <td>{log.message}</td>
                <td>{log.profile_id || 'N/A'}</td>
                <td>{log.proxy_id || 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="pagination">
          <button
            onClick={() => handlePageChange(page - 1)}
            disabled={page === 1}
          >
            Previous
          </button>
          <span>Page {page}</span>
          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={page * pageSize >= totalLogs}
          >
            Next
          </button>
        </div>
      </>
    );
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Batch Logs">
      <div className="batch-log-modal">
        {renderContent()}
      </div>
    </Modal>
  );
};

export default BatchLogModal;
