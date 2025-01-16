import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import Input from '../common/Input';
import Button from '../common/Button';
import Modal from '../common/Modal';
import './ProxyManager.scss';

/**
 * @typedef {Object} Proxy
 * @property {number} id - Unique identifier
 * @property {string} host - IP address or hostname
 * @property {number} port - Port number
 * @property {string} [username] - Optional username for authentication
 * @property {string} [password] - Optional password for authentication
 */

const ProxyManager = ({ proxies, onAdd, onRemove, onUpdate, onTest }) => {
  const [newProxy, setNewProxy] = useState({
    host: '',
    port: '',
    username: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [selectedProxies, setSelectedProxies] = useState([]);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [proxyToRemove, setProxyToRemove] = useState(null);
  const [testResults, setTestResults] = useState({});

  const validateProxy = useCallback((proxy) => {
    const newErrors = {};
    
    // Validate IP address format
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(proxy.host)) {
      newErrors.host = 'Invalid IP address';
    }
    
    // Validate port number
    const port = parseInt(proxy.port, 10);
    if (isNaN(port) || port < 1 || port > 65535) {
      newErrors.port = 'Port must be between 1 and 65535';
    }
    
    // Validate username format if provided
    if (proxy.username && !/^[a-zA-Z0-9_-]+$/.test(proxy.username)) {
      newErrors.username = 'Invalid username format';
    }
    
    // Check for duplicate proxy
    const isDuplicate = proxies.some(
      p => p.host === proxy.host && p.port === parseInt(proxy.port, 10)
    );
    if (isDuplicate) {
      newErrors.host = 'Proxy already exists';
    }
    
    return newErrors;
  }, [proxies]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewProxy(prev => ({ ...prev, [name]: value }));
    setErrors(prev => ({ ...prev, [name]: '' }));
  };

  const handleAdd = () => {
    const validationErrors = validateProxy(newProxy);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    const payload = {
      host: newProxy.host,
      port: parseInt(newProxy.port, 10)
    };

    if (newProxy.username) {
      payload.username = newProxy.username;
    }
    if (newProxy.password) {
      payload.password = newProxy.password;
    }

    onAdd(payload);

    setNewProxy({
      host: '',
      port: '',
      username: '',
      password: ''
    });
  };

  const handleRemove = (proxy) => {
    onRemove(proxy.id);
  };

  const handleConfirmRemove = (proxy) => {
    setProxyToRemove(proxy);
    setShowConfirmation(true);
  };

  const confirmRemove = () => {
    if (proxyToRemove) {
      onRemove(proxyToRemove.id);
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
      onRemove(selectedProxies);
      setSelectedProxies([]);
    }
  };

  const handleTest = async (proxy) => {
    try {
      const result = await onTest(proxy);
      setTestResults(prev => ({
        ...prev,
        [proxy.id]: result
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [proxy.id]: { success: false, error: error.message }
      }));
    }
  };

  return (
    <div className="proxy-manager">
      <div className="proxy-manager__add-form">
        <Input
          name="host"
          label="Host"
          value={newProxy.host}
          onChange={handleInputChange}
          error={errors.host}
          placeholder="192.168.1.1"
        />
        <Input
          name="port"
          label="Port"
          type="number"
          value={newProxy.port}
          onChange={handleInputChange}
          error={errors.port}
          placeholder="8080"
        />
        <Input
          name="username"
          label="Username (Optional)"
          value={newProxy.username}
          onChange={handleInputChange}
          error={errors.username}
        />
        <Input
          name="password"
          label="Password (Optional)"
          type="password"
          value={newProxy.password}
          onChange={handleInputChange}
          error={errors.password}
        />
        <Button onClick={handleAdd}>Add</Button>
      </div>

      <div className="proxy-manager__list">
        {proxies.length === 0 ? (
          <div className="proxy-manager__empty">No proxies configured</div>
        ) : (
          <>
            <div className="proxy-manager__controls">
              {selectedProxies.length > 0 && (
                <Button variant="danger" onClick={handleRemoveSelected}>
                  Remove Selected
                </Button>
              )}
            </div>
            <div className="proxy-manager__items">
              {proxies.map(proxy => (
                <div
                  key={proxy.id}
                  className={classNames('proxy-manager__item', {
                    'proxy-manager__item--selected': selectedProxies.includes(proxy.id)
                  })}
                >
                  <input
                    type="checkbox"
                    checked={selectedProxies.includes(proxy.id)}
                    onChange={() => handleSelectProxy(proxy.id)}
                  />
                  <span className="proxy-manager__item-details">
                    {proxy.host}:{proxy.port}
                    {proxy.username && ` (${proxy.username})`}
                  </span>
                  <div className="proxy-manager__item-actions">
                    {testResults[proxy.id] && (
                      <span className={`proxy-manager__test-result proxy-manager__test-result--${testResults[proxy.id].success ? 'success' : 'error'}`}>
                        {testResults[proxy.id].success 
                          ? `${testResults[proxy.id].latency}ms`
                          : testResults[proxy.id].error}
                      </span>
                    )}
                    <Button
                      size="small"
                      onClick={() => handleTest(proxy)}
                    >
                      Test
                    </Button>
                    <Button
                      variant="danger"
                      size="small"
                      onClick={() => handleConfirmRemove(proxy)}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

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
    </div>
  );
};

ProxyManager.propTypes = {
  proxies: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.number.isRequired,
    host: PropTypes.string.isRequired,
    port: PropTypes.number.isRequired,
    username: PropTypes.string,
    password: PropTypes.string
  })).isRequired,
  onAdd: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  onUpdate: PropTypes.func.isRequired,
  onTest: PropTypes.func
};

export default ProxyManager;
