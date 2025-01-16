import React from 'react';
import PropTypes from 'prop-types';
import TabNav from './TabNav';
import './AppLayout.scss';

const AppLayout = ({ activeTab, onTabChange, tabs, children }) => {
  return (
    <div className="app-layout">
      <header className="app-layout__header">
        <h1 className="app-layout__title">Instagram Story Checker</h1>
        <TabNav
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={onTabChange}
        />
      </header>
      <main className="app-layout__content">
        {children}
      </main>
    </div>
  );
};

AppLayout.propTypes = {
  /** Currently active tab ID */
  activeTab: PropTypes.string.isRequired,
  /** Tab change handler */
  onTabChange: PropTypes.func.isRequired,
  /** Array of tab objects */
  tabs: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired
  })).isRequired,
  /** Tab content */
  children: PropTypes.node.isRequired
};

export default AppLayout;
