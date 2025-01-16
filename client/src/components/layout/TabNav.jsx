import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import './TabNav.scss';

const TabNav = ({ tabs, activeTab, onTabChange }) => {
  return (
    <nav className="tab-nav">
      {tabs.map(({ id, label }) => (
        <button
          key={id}
          className={classNames('tab-nav__item', {
            'tab-nav__item--active': activeTab === id
          })}
          onClick={() => onTabChange(id)}
          aria-selected={activeTab === id}
          role="tab"
        >
          {label}
        </button>
      ))}
    </nav>
  );
};

TabNav.propTypes = {
  /** Array of tab objects */
  tabs: PropTypes.arrayOf(PropTypes.shape({
    /** Tab identifier */
    id: PropTypes.string.isRequired,
    /** Tab label */
    label: PropTypes.string.isRequired
  })).isRequired,
  /** Currently active tab ID */
  activeTab: PropTypes.string.isRequired,
  /** Tab change handler */
  onTabChange: PropTypes.func.isRequired
};

export default TabNav;
