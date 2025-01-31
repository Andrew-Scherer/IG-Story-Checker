import React, { useState } from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import { useSortStore } from '../../stores/sortStore';
import './Table.scss';

const Table = ({
  data,
  columns,
  selectable = false,
  selectedRows = [],
  onSelectionChange = () => {}
}) => {
  const { sortColumn, sortDirection, setSort } = useSortStore();
  const [lastSelectedId, setLastSelectedId] = useState(null);

  const handleSort = (key) => {
    if (!key) return;
    
    // If clicking the same column, toggle direction
    if (sortColumn === key) {
      setSort(key, sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New column, start with ascending
      setSort(key, 'asc');
    }
  };

  const handleCheckboxClick = (id, event) => {
    event.stopPropagation(); // Prevent row click handler from firing
    const newSelected = new Set(selectedRows);
    
    if (event.shiftKey && lastSelectedId) {
      // Get all visible rows between last selected and current
      const lastIndex = data.findIndex(item => item.id === lastSelectedId);
      const currentIndex = data.findIndex(item => item.id === id);
      const start = Math.min(lastIndex, currentIndex);
      const end = Math.max(lastIndex, currentIndex);
      
      // Select/deselect the range
      const isSelecting = !selectedRows.includes(id);
      for (let i = start; i <= end; i++) {
        if (isSelecting) {
          newSelected.add(data[i].id);
        } else {
          newSelected.delete(data[i].id);
        }
      }
    } else {
      // Normal toggle
      if (newSelected.has(id)) {
        newSelected.delete(id);
      } else {
        newSelected.add(id);
      }
      setLastSelectedId(id);
    }
    
    onSelectionChange(Array.from(newSelected));
  };

  const handleSelectAll = (event) => {
    event.stopPropagation(); // Prevent row click handler from firing
    const allSelected = data.every(item => selectedRows.includes(item.id));
    if (allSelected) {
      onSelectionChange([]);
    } else {
      const newSelected = [...new Set([...selectedRows, ...data.map(item => item.id)])];
      onSelectionChange(newSelected);
    }
  };

  const tableColumns = React.useMemo(() => {
    if (!selectable) return columns;

    const selectColumn = {
      key: 'select',
      title: (
        <input
          type="checkbox"
          onChange={handleSelectAll}
          checked={data.length > 0 && data.every(item => selectedRows.includes(item.id))}
        />
      ),
      render: (item) => (
        <input
          type="checkbox"
          checked={selectedRows.includes(item.id)}
          onChange={(e) => handleCheckboxClick(item.id, e)}
        />
      )
    };

    return [selectColumn, ...columns];
  }, [selectable, columns, data, selectedRows, onSelectionChange]);

  return (
    <div className="table-wrapper">
      <table className="table">
        <thead>
          <tr>
            {tableColumns.map(({ key, title, sortable }) => (
              <th
                key={key}
                className={classNames('table__header', {
                  'table__header--checkbox': key === 'select',
                  'table__header--sortable': sortable,
                  'table__header--sorted': sortColumn === key
                })}
                onClick={sortable ? () => handleSort(key) : undefined}
                data-direction={sortColumn === key ? sortDirection : undefined}
              >
                {title}
                {sortable && sortColumn === key && (
                  <span className="table__header-sort-indicator">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => (
            <tr 
              key={item.id} 
              className={classNames('table__row', {
                'table__row--selected': selectedRows.includes(item.id)
              })}
              onClick={(e) => {
                // Don't handle row click if clicking checkbox
                if (e.target.type === 'checkbox') return;
                
                const newSelected = new Set(selectedRows);
                
                if (e.shiftKey && lastSelectedId) {
                  // Range selection
                  const lastIndex = data.findIndex(row => row.id === lastSelectedId);
                  const currentIndex = data.findIndex(row => row.id === item.id);
                  const start = Math.min(lastIndex, currentIndex);
                  const end = Math.max(lastIndex, currentIndex);
                  
                  for (let i = start; i <= end; i++) {
                    newSelected.add(data[i].id);
                  }
                } else if (e.ctrlKey || e.metaKey) {
                  // Toggle selection
                  if (newSelected.has(item.id)) {
                    newSelected.delete(item.id);
                  } else {
                    newSelected.add(item.id);
                  }
                } else {
                  // Single selection
                  newSelected.clear();
                  newSelected.add(item.id);
                }
                
                setLastSelectedId(item.id);
                onSelectionChange(Array.from(newSelected));
              }}
            >
              {tableColumns.map(({ key, render }) => (
                <td 
                  key={key} 
                  className={classNames('table__cell', {
                    'table__cell--checkbox': key === 'select'
                  })}
                >
                  {render ? render(item, index) : item[key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

Table.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  columns: PropTypes.arrayOf(PropTypes.shape({
    key: PropTypes.string.isRequired,
    title: PropTypes.node.isRequired,
    sortable: PropTypes.bool,
    render: PropTypes.func
  })).isRequired,
  selectable: PropTypes.bool,
  selectedRows: PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.string, PropTypes.number])),
  onSelectionChange: PropTypes.func
};

export default Table;
