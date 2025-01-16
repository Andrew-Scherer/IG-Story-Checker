import React, { useState, useRef } from 'react';
import useProxyStore from '../../stores/proxyStore';
import Button from '../common/Button';
import Table from '../common/Table';
import './ProxyManager.scss';

function ProxyManager() {
  const { 
    proxies,
    addProxy,
    removeProxy,
    testProxy,
    addProxies
  } = useProxyStore();

  const [proxyInput, setProxyInput] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const fileInputRef = useRef(null);

  const handleAddProxy = () => {
    if (!proxyInput.trim()) return;

    const [ip, port, user, pass] = proxyInput.split(':');
    if (!ip || !port || !user || !pass) {
      alert('Invalid proxy format. Use: ip:port:user:pass');
      return;
    }

    addProxy({
      host: ip,
      port,
      username: user,
      password: pass,
      status: 'untested'
    });
    setProxyInput('');
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      const lines = content.split('\n').filter(line => line.trim());
      
      const newProxies = lines.map(line => {
        const [ip, port, user, pass] = line.trim().split(':');
        return {
          host: ip,
          port,
          username: user,
          password: pass,
          status: 'untested'
        };
      }).filter(proxy => proxy.host && proxy.port && proxy.username && proxy.password);

      if (newProxies.length > 0) {
        addProxies(newProxies);
      } else {
        alert('No valid proxies found in file. Use format: ip:port:user:pass');
      }
    };
    reader.readAsText(file);
    event.target.value = null; // Reset file input
  };

  const handleTestSelected = async () => {
    for (const id of selectedIds) {
      await testProxy(id);
    }
  };

  const handleDeleteSelected = () => {
    removeProxy(selectedIds);
    setSelectedIds([]);
  };

  const columns = [
    {
      key: 'proxy',
      title: 'Proxy',
      sortable: true,
      render: (proxy) => `${proxy.host}:${proxy.port}:${proxy.username}:${proxy.password}`
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      render: (proxy) => (
        <span className={`proxy-manager__status proxy-manager__status--${proxy.status}`}>
          {proxy.status}
        </span>
      )
    }
  ];

  return (
    <div className="proxy-manager">
      <div className="proxy-manager__header">
        <h2>Proxy Management</h2>
        <div className="proxy-manager__actions">
          <input
            type="file"
            accept=".txt"
            onChange={handleFileUpload}
            ref={fileInputRef}
            style={{ display: 'none' }}
          />
          <Button onClick={() => fileInputRef.current.click()}>
            Import from File
          </Button>
          {selectedIds.length > 0 && (
            <>
              <Button onClick={handleTestSelected}>
                Test Selected ({selectedIds.length})
              </Button>
              <Button variant="danger" onClick={handleDeleteSelected}>
                Delete Selected ({selectedIds.length})
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="proxy-manager__add-form">
        <input
          type="text"
          value={proxyInput}
          onChange={(e) => setProxyInput(e.target.value)}
          placeholder="ip:port:user:pass"
          className="proxy-manager__input"
        />
        <Button onClick={handleAddProxy}>Add Proxy</Button>
      </div>

      <div className="proxy-manager__table">
        <Table
          data={proxies}
          columns={columns}
          pageSize={500}
          selectable={true}
          selectedRows={selectedIds}
          onSelectionChange={setSelectedIds}
        />
      </div>
    </div>
  );
}

export default ProxyManager;
