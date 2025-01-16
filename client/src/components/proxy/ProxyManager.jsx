import React, { useState, useCallback } from 'react';
import classNames from 'classnames';
import Button from '../common/Button';
import Modal from '../common/Modal';
import useProxyStore from '../../stores/proxyStore';
import './ProxyManager.scss';

const ProxyManager = () => {
  const { 
    proxies,
    addProxy,
    removeProxy,
    testProxy,
    addSession,
    updateSession
  } = useProxyStore();

  const [proxyInput, setProxyInput] = useState('');
  const [sessionInput, setSessionInput] = useState('');
  const [errors, setErrors] = useState({});
  const [selectedProxies, setSelectedProxies] = useState([]);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [proxyToRemove, setProxyToRemove] = useState(null);
  const [testResults, setTestResults] = useState({});

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

  const handleAdd = () => {
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

    proxyLines.forEach((proxyLine, index) => {
      const [host, port, username, password] = proxyLine.split(':');
      const proxy = {
        host,
        port: parseInt(port, 10),
        username,
        password
      };

      const proxyId = Date.now() + index;
      addProxy({ ...proxy, id: proxyId });
      addSession(proxyId, { session: sessionLines[index], status: 'active' });
    });

    setProxyInput('');
    setSessionInput('');
    setErrors({});
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
      removeProxy(selectedProxies);
      setSelectedProxies([]);
    }
  };

  const handleTest = async (proxy) => {
    try {
      const result = await testProxy(proxy.id);
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

  const handleToggleSessionStatus = (proxyId, sessionId, currentStatus) => {
    updateSession(proxyId, sessionId, {
      status: currentStatus === 'active' ? 'disabled' : 'active'
    });
  };

  return (
    <div className="proxy-manager">
      <div className="proxy-manager__inputs">
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

        <Button onClick={handleAdd} className="proxy-manager__add-button">
          Add Proxy-Session Pairs
        </Button>
      </div>

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
                      <td>{`${proxy.host}:${proxy.port}:${proxy.username}:${proxy.password}`}</td>
                      <td>
                        {proxy.sessions?.map(session => (
                          <div key={session.id} className="proxy-manager__session-data">
                            {session.session}
                          </div>
                        ))}
                      </td>
                      <td>
                        {proxy.sessions?.map(session => (
                          <Button
                            key={session.id}
                            variant={session.status === 'active' ? 'success' : 'secondary'}
                            size="small"
                            onClick={() => handleToggleSessionStatus(proxy.id, session.id, session.status)}
                          >
                            {session.status}
                          </Button>
                        ))}
                      </td>
                      <td>
                        <div className="proxy-manager__actions">
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
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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

export default ProxyManager;
