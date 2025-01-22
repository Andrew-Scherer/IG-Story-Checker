import React, { useState, useCallback, useEffect } from 'react';
import classNames from 'classnames';
import Button from '../common/Button';
import Modal from '../common/Modal';
import Input from '../common/Input';
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
  }, []); // Empty dependency array since loadProxies is from zustand store

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
    console.log('Starting proxy-session pair addition');
    const proxyLines = proxyInput.trim().split('\n').filter(line => line.trim());
    const sessionLines = sessionInput.trim().split('\n').filter(line => line.trim());

    const cleanProxyLines = proxyLines.filter(line => line.trim());
    const cleanSessionLines = sessionLines.filter(line => line.trim());

    if (cleanProxyLines.length === 0) {
      setErrors({ proxy: 'Please enter at least one proxy' });
      return;
    }

    if (cleanSessionLines.length !== cleanProxyLines.length) {
      setErrors({ session: 'Number of sessions must match number of proxies' });
      return;
    }

    const proxyErrors = validateProxies(proxyLines);
    if (Object.keys(proxyErrors).length > 0) {
      setErrors({ proxy: 'Invalid proxy format found', ...proxyErrors });
      return;
    }

    clearError();
    setErrors({});

    try {
      for (let i = 0; i < proxyLines.length; i++) {
        console.log(`Processing proxy-session pair ${i + 1}/${proxyLines.length}`);
        const [ip, port, username, password] = proxyLines[i].split(':');
        const proxyData = {
          ip,
          port: parseInt(port, 10),
          username,
          password,
          session: sessionLines[i]
        };

        console.log('Sending request to create proxy-session pair', { ...proxyData, session: '[REDACTED]' });
        await addProxy(proxyData);
        console.log(`Successfully added proxy-session pair ${i + 1}`);
      }

      setProxyInput('');
      setSessionInput('');
      setShowAddDialog(false);
      console.log('Successfully added all proxy-session pairs');
    } catch (error) {
      console.error('Failed to add proxy-session pair:', error);
      let errorMessage;
      
      // Handle specific error types
      switch (error.error) {
        case 'duplicate_session':
          errorMessage = 'This session is already in use';
          break;
        case 'duplicate_proxy':
          errorMessage = 'A proxy with this IP and port already exists';
          break;
        default:
          errorMessage = error.message || 'Failed to add proxy-session pair';
      }
      
      setErrors({ proxy: errorMessage });
    }
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
                      <td>
                        <div className="proxy-manager__actions">
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
        <div className="proxy-manager__add-dialog">
          <div className="proxy-manager__input-group">
            <label>Proxies (ip:port:username:password)</label>
            <textarea
              value={proxyInput}
              onChange={(e) => setProxyInput(e.target.value)}
              placeholder="165.231.24.193:4444:andres:Andres2025&#10;154.16.20.193:4444:andres:Andres2025&#10;107.175.90.211:4444:andres:Andres2025"
              className={classNames('proxy-manager__textarea', {
                'proxy-manager__textarea--error': errors.proxy
              })}
            />
            {errors.proxy && <div className="proxy-manager__error">{errors.proxy}</div>}
          </div>

          <div className="proxy-manager__input-group">
            <label>Sessions (one per line)</label>
            <textarea
              value={sessionInput}
              onChange={(e) => setSessionInput(e.target.value)}
              placeholder="session_data_1&#10;session_data_2&#10;session_data_3"
              className={classNames('proxy-manager__textarea', {
                'proxy-manager__textarea--error': errors.session
              })}
            />
            {errors.session && <div className="proxy-manager__error">{errors.session}</div>}
          </div>

          <div className="proxy-manager__dialog-actions">
            <Button 
              onClick={handleAdd} 
              disabled={loading}
              variant="primary"
            >
              {loading ? 'Adding...' : 'Add Proxy-Session Pairs'}
            </Button>
            <Button 
              onClick={() => {
                setShowAddDialog(false);
                setErrors({});
                setProxyInput('');
                setSessionInput('');
              }}
              variant="secondary"
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>

      {/* Confirmation Modal */}
      <Modal
        title="Confirm Removal"
        isOpen={showConfirmation}
        onClose={() => setShowConfirmation(false)}
      >
        <div className="proxy-manager__confirmation">
          <h3>Are you sure?</h3>
          <p>This action cannot be undone.</p>
          <div className="proxy-manager__confirmation-actions">
            <Button variant="danger" onClick={confirmRemove}>
              Confirm
            </Button>
            <Button onClick={() => setShowConfirmation(false)}>
              Cancel
            </Button>
          </div>
        </div>
      </Modal>

      {/* Rotation Settings Modal */}
      <Modal
        title="Proxy Rotation Settings"
        isOpen={showRotationSettings}
        onClose={() => setShowRotationSettings(false)}
      >
        <div className="proxy-manager__rotation-settings">
          <div className="proxy-manager__setting">
            <label>Auto-Rotation</label>
            <Button
              variant={rotationSettings.enabled ? 'primary' : 'secondary'}
              onClick={handleToggleRotation}
            >
              {rotationSettings.enabled ? 'Enabled' : 'Disabled'}
            </Button>
          </div>
          <div className="proxy-manager__setting">
            <label>Rotation Interval (minutes)</label>
            <Input
              type="number"
              min="1"
              value={rotationSettings.interval}
              onChange={(e) => handleUpdateRotationInterval(e.target.value)}
            />
          </div>
          {rotationSettings.lastRotation && (
            <div className="proxy-manager__setting">
              <label>Last Rotation</label>
              <span>{formatDate(rotationSettings.lastRotation)}</span>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default ProxyManager;
