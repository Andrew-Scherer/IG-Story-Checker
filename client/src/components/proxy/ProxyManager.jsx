import React, { useState, useCallback, useEffect } from 'react';
import classNames from 'classnames';
import Button from '../common/Button';
import Modal from '../common/Modal';
import Input from '../common/Input';
import ProxyErrorLogModal from './ProxyErrorLogModal';
import { proxyStore } from '../../stores/proxyStore';
import './ProxyManager.scss';

const ProxyManager = () => {
  const { 
    proxies,
    loadProxies,
    addProxy,
    removeProxy,
    testProxy,
    updateProxyStatus,
    updateHealth,
    toggleRotation,
    setRotationInterval,
    rotationSettings,
    loading,
    error,
    clearError
  } = proxyStore();

  // Load proxies on mount
  useEffect(() => {
    const fetchProxies = async () => {
      try {
        await loadProxies();
      } catch (error) {
        console.error('Failed to load proxies:', error);
      }
    };
    fetchProxies();
  }, []);

  const [proxyInput, setProxyInput] = useState('');
  const [sessionInput, setSessionInput] = useState('');
  const [errors, setErrors] = useState({});
  const [selectedProxies, setSelectedProxies] = useState([]);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [proxyToRemove, setProxyToRemove] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [showHealthHistory, setShowHealthHistory] = useState(null);
  const [showRotationSettings, setShowRotationSettings] = useState(false);
  const [showAddDialog, setShowAddDialog] = useState(false);

  // Error Log Modal state
  const [showErrorLog, setShowErrorLog] = useState(false);
  const [selectedProxyId, setSelectedProxyId] = useState(null);

  const validateProxies = useCallback((proxyLines) => {
    const errors = {};
    const proxyRegex = /^(\d{1,3}\.){3}\d{1,3}:\d+:[^:]+:[^:]+$/;
    
    proxyLines.forEach((line, index) => {
      if (!proxyRegex.test(line)) {
        errors[index] = 'Invalid format. Use: ip:port:username:password';
      }
    });
    
    return errors;
  }, []);

  const handleAdd = async () => {
    // ... (existing handleAdd implementation)
  };

  const handleConfirmRemove = (proxy) => {
    setProxyToRemove(proxy);
    setShowConfirmation(true);
  };

  const confirmRemove = () => {
    if (proxyToRemove) {
      removeProxy(proxyToRemove.id);
      setShowConfirmation(false);
      setProxyToRemove(null);
    }
  };

  const handleSelectProxy = (proxyId) => {
    setSelectedProxies(prev => {
      if (prev.includes(proxyId)) {
        return prev.filter(id => id !== proxyId);
      }
      return [...prev, proxyId];
    });
  };

  const handleRemoveSelected = () => {
    if (selectedProxies.length > 0) {
      selectedProxies.forEach(id => removeProxy(id));
      setSelectedProxies([]);
    }
  };

  const handleToggleSessionStatus = (proxyId, sessionId, currentStatus) => {
    updateProxyStatus(proxyId, currentStatus === 'active' ? 'disabled' : 'active');
  };

  const handleToggleRotation = () => {
    toggleRotation(!rotationSettings.enabled);
  };

  const handleUpdateRotationInterval = (minutes) => {
    setRotationInterval(parseInt(minutes, 10));
  };

  const handleShowErrorLog = (proxyId) => {
    setSelectedProxyId(proxyId);
    setShowErrorLog(true);
  };

  const handleCloseErrorLog = () => {
    setShowErrorLog(false);
    setSelectedProxyId(null);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (ms) => {
    if (!ms) return '-';
    return `${Math.round(ms)}ms`;
  };

  const renderError = () => {
    if (!error) return null;
    
    let errorMessage = error.message || error;
    if (error.details) {
      if (error.details.field) {
        errorMessage += ` (${error.details.field})`;
      }
      if (error.details.valid_range) {
        errorMessage += ` Valid range: ${error.details.valid_range}`;
      }
    }
    
    return (
      <div className="proxy-manager__error" onClick={() => clearError()}>
        {errorMessage}
        <span className="proxy-manager__error-close">×</span>
      </div>
    );
  };

  return (
    <div className="proxy-manager">
      <div className="proxy-manager__header">
        <div className="proxy-manager__controls">
          <Button
            variant="primary"
            onClick={() => setShowAddDialog(true)}
          >
            Add Proxy-Session Pair
          </Button>
          <div className="proxy-manager__rotation-controls">
            <Button
              variant={rotationSettings.enabled ? 'primary' : 'secondary'}
              onClick={handleToggleRotation}
            >
              Auto-Rotation: {rotationSettings.enabled ? 'On' : 'Off'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setShowRotationSettings(true)}
            >
              Rotation Settings
            </Button>
          </div>
        </div>
      </div>

      {loading && <div className="proxy-manager__loading">Loading...</div>}
      {renderError()}

      <div className="proxy-manager__list">
        {proxies.length === 0 ? (
          <div className="proxy-manager__empty">No proxies configured</div>
        ) : (
          <>
            <div className="proxy-manager__controls">
              {selectedProxies.length > 0 && (
                <Button variant="danger" onClick={handleRemoveSelected}>
                  Remove Selected ({selectedProxies.length})
                </Button>
              )}
            </div>
            <div className="proxy-manager__table">
              <table>
                <thead>
                  <tr>
                    <th></th>
                    <th>Proxy</th>
                    <th>Session</th>
                    <th>Status</th>
                    <th>Avg Response</th>
                    <th>Connection Rate</th>
                    <th>Last Success</th>
                    <th>Last Error</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {proxies.map(proxy => (
                    <tr key={proxy.id} className={classNames({
                      'proxy-manager__row--selected': selectedProxies.includes(proxy.id)
                    })}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedProxies.includes(proxy.id)}
                          onChange={() => handleSelectProxy(proxy.id)}
                        />
                      </td>
                      <td>{`${proxy.ip}:${proxy.port}`}</td>
                      <td>
                        {proxy.sessions?.map(session => (
                          <div key={session.id} className="proxy-manager__session">
                            <div className="proxy-manager__session-data">
                              {session.session}
                            </div>
                          </div>
                        ))}
                      </td>
                      <td>
                        <Button
                          variant={proxy.is_active ? 'success' : 'secondary'}
                          size="small"
                          onClick={() => handleToggleSessionStatus(proxy.id, null, proxy.status)}
                        >
                          {proxy.status}
                        </Button>
                      </td>
                      <td>{proxy.avg_response_time ? `${proxy.avg_response_time}ms` : '-'}</td>
                      <td>
                        {proxy.total_requests > 0
                          ? `${Math.round(((proxy.total_requests - proxy.failed_requests) / proxy.total_requests) * 100)}%`
                          : '-'}
                      </td>
                      <td>{formatDate(proxy.last_success)}</td>
                      <td className="proxy-manager__error-cell">
                        {proxy.last_error || '-'}
                      </td>
                      <td>
                        <div className="proxy-manager__actions">
                          <Button
                            variant="primary"
                            size="small"
                            onClick={() => handleShowErrorLog(proxy.id)}
                          >
                            Error Log
                          </Button>
                          <Button
                            variant="danger"
                            size="small"
                            onClick={() => handleConfirmRemove(proxy)}
                          >
                            Remove
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {/* Add Proxy-Session Modal */}
      <Modal
        title="Add Proxy-Session Pair"
        isOpen={showAddDialog}
        onClose={() => {
          setShowAddDialog(false);
          setErrors({});
          setProxyInput('');
          setSessionInput('');
        }}
      >
        {/* ... (existing add dialog content) */}
      </Modal>

      {/* Confirmation Modal */}
      <Modal
        title="Confirm Removal"
        isOpen={showConfirmation}
        onClose={() => setShowConfirmation(false)}
      >
        {/* ... (existing confirmation modal content) */}
      </Modal>

      {/* Rotation Settings Modal */}
      <Modal
        title="Proxy Rotation Settings"
        isOpen={showRotationSettings}
        onClose={() => setShowRotationSettings(false)}
      >
        {/* ... (existing rotation settings modal content) */}
      </Modal>

      {/* Error Log Modal */}
      <ProxyErrorLogModal
        proxyId={selectedProxyId}
        isOpen={showErrorLog}
        onClose={handleCloseErrorLog}
      />
    </div>
  );
};

export default ProxyManager;
