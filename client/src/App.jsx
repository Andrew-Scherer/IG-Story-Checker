import React, { useState } from 'react';
import AppLayout from './components/layout/AppLayout';
import NicheFeed from './components/niche/NicheFeed';
import BatchTable from './components/batch/BatchTable';
import MasterList from './components/master/MasterList';
import Settings from './components/settings/Settings';
import ProxyManager from './components/proxy/ProxyManager';
import './App.scss';

const App = () => {
  const [activeTab, setActiveTab] = useState('niche');

  const renderContent = () => {
    switch (activeTab) {
      case 'niche':
        return <NicheFeed />;
      case 'batch':
        return <BatchTable />;
      case 'master':
        return <MasterList />;
      case 'proxies':
        return <ProxyManager />;
      case 'settings':
        return <Settings />;
      default:
        return null;
    }
  };

  return (
    <AppLayout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      tabs={[
        { id: 'niche', label: 'Niche Feed' },
        { id: 'batch', label: 'Batch' },
        { id: 'master', label: 'Master List' },
        { id: 'proxies', label: 'Proxy Management' },
        { id: 'settings', label: 'Settings' }
      ]}
    >
      {renderContent()}
    </AppLayout>
  );
};

export default App;
