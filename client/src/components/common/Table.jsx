import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import './Table.scss';

const Table = ({
  data,
  columns,
  pageSize = 100,
  selectable = false,
  selectedRows = [],
  onSelectionChange = () => {},
  onSort: externalOnSort,
  sortColumn: externalSortColumn,
  sortDirection: externalSortDirection
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [internalSortColumn, setInternalSortColumn] = useState(null);
  const [internalSortDirection, setInternalSortDirection] = useState('asc');
  const [lastSelectedId, setLastSelectedId] = useState(null);

  const sortColumn = externalSortColumn || internalSortColumn;
  const sortDirection = externalSortDirection || internalSortDirection;

  const handleSort = (key) => {
    const newDirection = sortColumn === key && sortDirection === 'asc' ? 'desc' : 'asc';
    
    if (externalOnSort) {
      externalOnSort(key, newDirection);
    } else {
      setInternalSortColumn(key);
      setInternalSortDirection(newDirection);
    }
  };

  const sortedData = useMemo(() => {
    if (!sortColumn) return data;

    return [...data].sort((a, b) => {
      const aValue = a[sortColumn];
      const bValue = b[sortColumn];
      const modifier = sortDirection === 'asc' ? 1 : -1;

      if (aValue < bValue) return -1 * modifier;
      if (aValue > bValue) return 1 * modifier;
      return 0;
    });
  }, [data, sortColumn, sortDirection]);

  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return sortedData.slice(startIndex, startIndex + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  const handleCheckboxClick = (id, event) => {
    event.stopPropagation(); // Prevent row click handler from firing
    const newSelected = new Set(selectedRows);
    
    if (event.shiftKey && lastSelectedId) {
      // Get all visible rows between last selected and current
      const lastIndex = paginatedData.findIndex(item => item.id === lastSelectedId);
      const currentIndex = paginatedData.findIndex(item => item.id === id);
      const start = Math.min(lastIndex, currentIndex);
      const end = Math.max(lastIndex, currentIndex);
      
      // Select/deselect the range
      const isSelecting = !selectedRows.includes(id);
      for (let i = start; i <= end; i++) {
        if (isSelecting) {
          newSelected.add(paginatedData[i].id);
        } else {
          newSelected.delete(paginatedData[i].id);
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
    const allSelected = paginatedData.every(item => selectedRows.includes(item.id));
    if (allSelected) {
      onSelectionChange([]);
    } else {
      const newSelected = [...new Set([...selectedRows, ...paginatedData.map(item => item.id)])];
      onSelectionChange(newSelected);
    }
  };

  const tableColumns = useMemo(() => {
    if (!selectable) return columns;

    const selectColumn = {
      key: 'select',
      title: (
        <input
          type="checkbox"
          onChange={handleSelectAll}
          checked={paginatedData.length > 0 && paginatedData.every(item => selectedRows.includes(item.id))}
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
  }, [selectable, columns, paginatedData, selectedRows, onSelectionChange, handleCheckboxClick, handleSelectAll]);

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
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paginatedData.map((item, index) => (
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
                  const lastIndex = paginatedData.findIndex(row => row.id === lastSelectedId);
                  const currentIndex = paginatedData.findIndex(row => row.id === item.id);
                  const start = Math.min(lastIndex, currentIndex);
                  const end = Math.max(lastIndex, currentIndex);
                  
                  for (let i = start; i <= end; i++) {
                    newSelected.add(paginatedData[i].id);
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
      {totalPages > 1 && (
        <div className="table__pagination">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="table__pagination-button"
            aria-label="previous"
          >
            Previous
          </button>
          <span className="table__pagination-info">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="table__pagination-button"
            aria-label="next"
          >
            Next
          </button>
        </div>
      )}
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
  pageSize: PropTypes.number,
  selectable: PropTypes.bool,
  selectedRows: PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.string, PropTypes.number])),
  onSelectionChange: PropTypes.func,
  onSort: PropTypes.func,
  sortColumn: PropTypes.string,
  sortDirection: PropTypes.oneOf(['asc', 'desc'])
};

export default Table;
