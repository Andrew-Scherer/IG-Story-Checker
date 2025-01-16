import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import './Table.scss';

const Table = ({
  data,
  columns,
  pageSize = 100,
  selectable,
  selectedRows,
  onSelectionChange,
  onSort: externalOnSort,
  sortColumn: externalSortColumn,
  sortDirection: externalSortDirection
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [internalSortColumn, setInternalSortColumn] = useState(null);
  const [internalSortDirection, setInternalSortDirection] = useState('asc');

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

  const tableColumns = useMemo(() => {
    if (!selectable) return columns;

    const handleCheckboxClick = (id) => {
      const newSelected = new Set(selectedRows);
      if (newSelected.has(id)) {
        newSelected.delete(id);
      } else {
        newSelected.add(id);
      }
      onSelectionChange(Array.from(newSelected));
    };

    const handleSelectAll = () => {
      const allSelected = paginatedData.every(item => selectedRows.includes(item.id));
      if (allSelected) {
        onSelectionChange([]);
      } else {
        const newSelected = [...new Set([...selectedRows, ...paginatedData.map(item => item.id)])];
        onSelectionChange(newSelected);
      }
    };

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
          onChange={() => handleCheckboxClick(item.id)}
        />
      )
    };

    return [selectColumn, ...columns];
  }, [selectable, columns, paginatedData, selectedRows, onSelectionChange]);

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
              >
                {title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paginatedData.map((item, index) => (
            <tr key={item.id} className="table__row">
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

Table.defaultProps = {
  pageSize: 100,
  selectable: false,
  selectedRows: [],
  onSelectionChange: () => {}
};

export default Table;
