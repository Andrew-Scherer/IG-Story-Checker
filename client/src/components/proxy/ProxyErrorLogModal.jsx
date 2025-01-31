import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import { proxyStore } from '../../stores/proxyStore';
import './ProxyErrorLogModal.scss';

const ProxyErrorLogModal = ({ proxyId, isOpen, onClose }) => {
  const { fetchProxyErrorLogs, errorLogs, totalLogs, loadingLogs } = proxyStore();
  const [page, setPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    if (isOpen && proxyId) {
      fetchProxyErrorLogs(proxyId, pageSize, (page - 1) * pageSize);
    }
  }, [isOpen, proxyId, page, fetchProxyErrorLogs]);

  const handlePageChange = (newPage) => {
    setPage(newPage);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  const renderContent = () => {
    if (loadingLogs) {
      return <div className="loading">Loading logs...</div>;
    }

    if (!errorLogs || errorLogs.length === 0) {
      return <div className="no-logs">No error logs available for this proxy.</div>;
    }

    return (
      <>
        <table className="log-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Error Message</th>
              <th>State Change</th>
              <th>Recovery Time</th>
            </tr>
          </thead>
          <tbody>
            {errorLogs.map((log) => (
              <tr key={log.id} className={log.state_change ? 'state-change' : ''}>
                <td>{formatDate(log.timestamp)}</td>
                <td>{log.error_message}</td>
                <td>{log.state_change ? 'Yes' : 'No'}</td>
                <td>{formatDate(log.recovery_time)}</td>
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
    <Modal isOpen={isOpen} onClose={onClose} title="Proxy Error Logs">
      <div className="proxy-error-log-modal">
        {renderContent()}
      </div>
    </Modal>
  );
};

export default ProxyErrorLogModal;