import React, { useState } from 'react';
import PropTypes from 'prop-types';
import Button from '../common/Button';
import Modal from '../common/Modal';
import './ProxyManager.scss';

const SettingsProxyManager = ({
  proxies = [],
  onAdd,
  onRemove,
  onUpdate,
  onTest,
  onAddSession,
  onRemoveSession,
  onUpdateSession
}) => {
  const [formData, setFormData] = useState({
    host: '',
    port: '',
    username: ''
  });
  const [errors, setErrors] = useState({});
  const [selectedProxies, setSelectedProxies] = useState([]);
  const [sessionData, setSessionData] = useState('');
  const [sessionError, setSessionError] = useState('');
  const [editingSession, setEditingSession] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [proxyToRemove, setProxyToRemove] = useState(null);
  
  const getHealthStatusClass = (status) => {
    switch (status) {
      case 'healthy':
        return 'status-healthy';
      case 'degraded':
        return 'status-degraded';
      case 'unhealthy':
        return 'status-unhealthy';
      default:
        return '';
    }
  };

  const getLatencyClass = (latency) => {
    if (latency < 200) return 'latency-good';
    if (latency < 500) return 'latency-medium';
    return 'latency-high';
  };

  const validateIP = (ip) => {
    const pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!pattern.test(ip)) return false;
    return ip.split('.').every(num => parseInt(num) >= 0 && parseInt(num) <= 255);
  };

  const validatePort = (port) => {
    const num = parseInt(port);
    return num >= 1 && num <= 65535;
  };

  const validateForm = () => {
    const newErrors = {};
    if (!validateIP(formData.host)) {
      newErrors.host = 'Invalid IP address';
    }
    if (!validatePort(formData.port)) {
      newErrors.port = 'Port must be between 1 and 65535';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      onAdd({
        ...formData,
        port: parseInt(formData.port)
      });
      setFormData({ host: '', port: '', username: '' });
    }
  };

  const handleConfirmRemove = (proxy) => {
    setProxyToRemove(proxy);
    setShowConfirmation(true);
  };

  const handleBulkRemove = () => {
    if (selectedProxies.length > 0) {
      setProxyToRemove(null);
      setShowConfirmation(true);
    }
  };

  const confirmRemove = () => {
    if (proxyToRemove) {
      onRemove(proxyToRemove.id);
    } else if (selectedProxies.length > 0) {
      onRemove(selectedProxies);
      setSelectedProxies([]);
    }
    setShowConfirmation(false);
    setProxyToRemove(null);
  };

  const handleAddSession = (proxyId) => {
    if (!sessionData) {
      setSessionError('Session data is required');
      return;
    }
    onAddSession(proxyId, { session: sessionData });
    setSessionData('');
    setSessionError('');
  };

  const handleUpdateSession = (proxyId, sessionId) => {
    if (!sessionData) {
      setSessionError('Session data is required');
      return;
    }
    onUpdateSession(proxyId, sessionId, { session: sessionData });
    setEditingSession(null);
    setSessionData('');
    setSessionError('');
  };

  const toggleSessionStatus = (proxyId, sessionId, currentStatus) => {
    onUpdateSession(proxyId, sessionId, {
      status: currentStatus === 'active' ? 'disabled' : 'active'
    });
  };

  return (
    <div className="settings-proxy-manager">
      <form onSubmit={handleSubmit} className="proxy-form">
        <div className="form-group">
          <label htmlFor="host">Host</label>
          <input
            id="host"
            type="text"
            value={formData.host}
            onChange={e => setFormData(prev => ({ ...prev, host: e.target.value }))}
          />
          {errors.host && <span className="error">{errors.host}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="port">Port</label>
          <input
            id="port"
            type="text"
            value={formData.port}
            onChange={e => setFormData(prev => ({ ...prev, port: e.target.value }))}
          />
          {errors.port && <span className="error">{errors.port}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="username">Username (Optional)</label>
          <input
            id="username"
            type="text"
            value={formData.username}
            onChange={e => setFormData(prev => ({ ...prev, username: e.target.value }))}
          />
        </div>

        <Button type="submit">Add</Button>
      </form>

      {proxies.length === 0 ? (
        <div className="empty-state">No proxies configured</div>
      ) : (
        <div className="proxy-list">
          {selectedProxies.length > 0 && (
            <div className="bulk-actions">
              <Button 
                variant="danger" 
                onClick={handleBulkRemove}
                data-testid="remove-selected-proxies"
              >
                Remove Selected ({selectedProxies.length})
              </Button>
            </div>
          )}

          {proxies.map(proxy => (
            <div key={proxy.id} className="proxy-item">
              <div className="proxy-header">
                <input
                  type="checkbox"
                  checked={selectedProxies.includes(proxy.id)}
                  onChange={() => {
                    setSelectedProxies(prev => 
                      prev.includes(proxy.id)
                        ? prev.filter(id => id !== proxy.id)
                        : [...prev, proxy.id]
                    );
                  }}
                />
                <span className="proxy-info">
                  {proxy.host}:{proxy.port}
                  {proxy.username && ` (${proxy.username})`}
                </span>
                <div className="proxy-actions">
                  <Button onClick={() => onTest(proxy)}>Test</Button>
                  <Button 
                    variant="danger" 
                    onClick={() => handleConfirmRemove(proxy)}
                    data-testid={`remove-proxy-${proxy.id}`}
                  >
                    Remove
                  </Button>
                </div>
              </div>

              {proxy.health && (
                <div className="proxy-status">
                  <>
                    <span className={`status ${getHealthStatusClass(proxy.health.status)}`} data-testid="health-status">
                      {proxy.health.status}
                    </span>
                    <span className={`latency ${getLatencyClass(proxy.health.latency)}`} data-testid="health-latency">
                      {proxy.health.latency}ms
                    </span>
                    <span className="uptime" data-testid="health-uptime">
                      {proxy.health.uptime}%
                    </span>
                    <span className="last-check" data-testid="health-last-check">
                      Last checked: {new Date(proxy.health.lastCheck).toLocaleString()}
                    </span>
                  </>
                </div>
              )}

              <div className="sessions">
                <div className="session-form">
                  <div className="form-group">
                    <label htmlFor={`session-input-${proxy.id}`}>Session Data</label>
                    <input
                      id={`session-input-${proxy.id}`}
                      type="text"
                      placeholder="Enter session data"
                      value={sessionData}
                      onChange={e => setSessionData(e.target.value)}
                    />
                  </div>
                  <Button onClick={() => handleAddSession(proxy.id)}>
                    Add Session
                  </Button>
                  {sessionError && <span className="error">{sessionError}</span>}
                </div>

                {proxy.sessions?.map(session => (
                  <div key={session.id} className="session-item">
                    {editingSession === session.id ? (
                      <>
                        <input
                          type="text"
                          value={sessionData || session.session}
                          onChange={e => setSessionData(e.target.value)}
                          data-testid={`session-edit-${session.id}`}
                        />
                        <Button onClick={() => handleUpdateSession(proxy.id, session.id)}>
                          Save
                        </Button>
                        <Button onClick={() => {
                          setEditingSession(null);
                          setSessionData('');
                        }}>
                          Cancel
                        </Button>
                      </>
                    ) : (
                      <>
                        <span className="session-data" data-testid={`session-${session.id}`}>{session.session}</span>
                        <Button
                          variant={session.status === 'active' ? 'primary' : 'secondary'}
                          onClick={() => toggleSessionStatus(proxy.id, session.id, session.status)}
                        >
                          {session.status}
                        </Button>
                        <Button onClick={() => {
                          setEditingSession(session.id);
                          setSessionData(session.session);
                        }}>
                          Edit
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() => onRemoveSession(proxy.id, session.id)}
                          data-testid={`remove-session-${proxy.id}-${session.id}`}
                        >
                          Remove
                        </Button>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        title="Confirm Removal"
        isOpen={showConfirmation}
        onClose={() => setShowConfirmation(false)}
      >
        <div className="confirmation-content">
          <p>
            {selectedProxies.length > 0 
              ? `Are you sure you want to remove ${selectedProxies.length} selected proxies?`
              : 'Are you sure you want to remove this proxy?'
            }
          </p>
          <div className="confirmation-actions">
            <Button variant="danger" onClick={confirmRemove}>
              Confirm
            </Button>
            <Button onClick={() => setShowConfirmation(false)}>
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

SettingsProxyManager.propTypes = {
  proxies: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    host: PropTypes.string.isRequired,
    port: PropTypes.number.isRequired,
    username: PropTypes.string,
    sessions: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      session: PropTypes.string.isRequired,
      status: PropTypes.string.isRequired
    })),
    health: PropTypes.shape({
      status: PropTypes.oneOf(['healthy', 'degraded', 'unhealthy']).isRequired,
      latency: PropTypes.number.isRequired,
      uptime: PropTypes.number.isRequired,
      lastCheck: PropTypes.string.isRequired
    })
  })),
  onAdd: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  onUpdate: PropTypes.func.isRequired,
  onTest: PropTypes.func.isRequired,
  onAddSession: PropTypes.func.isRequired,
  onRemoveSession: PropTypes.func.isRequired,
  onUpdateSession: PropTypes.func.isRequired
};

export default SettingsProxyManager;
