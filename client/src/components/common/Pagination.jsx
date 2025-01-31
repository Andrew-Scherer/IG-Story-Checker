import React, { useState } from 'react';
import { usePaginationStore } from '../../stores/paginationStore';
import './Pagination.scss';

const PAGE_SIZE_OPTIONS = [25, 50, 100];

const Pagination = () => {
  const {
    currentPage,
    pageSize,
    loading,
    getTotalPages,
    setPage,
    setPageSize
  } = usePaginationStore();

  const [inputPage, setInputPage] = useState('');
  const totalPages = getTotalPages();

  const handlePageClick = (page) => {
    if (page >= 1 && page <= totalPages) {
      setPage(page);
    }
  };

  const handleInputChange = (e) => {
    setInputPage(e.target.value);
  };

  const handleGoToPage = () => {
    const page = parseInt(inputPage);
    if (page >= 1 && page <= totalPages) {
      setPage(page);
      setInputPage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleGoToPage();
    }
  };

  const handlePageSizeChange = (e) => {
    setPageSize(Number(e.target.value));
  };

  const renderPageNumbers = () => {
    const pages = [];
    let start = Math.max(1, currentPage - 4);
    let end = Math.min(totalPages, start + 8);

    if (end - start < 8) {
      start = Math.max(1, end - 8);
    }

    for (let i = start; i <= end; i++) {
      pages.push(
        <button
          key={i}
          className={`pagination__number ${currentPage === i ? 'pagination__number--active' : ''}`}
          onClick={() => handlePageClick(i)}
          disabled={loading}
        >
          {i}
        </button>
      );
    }
    return pages;
  };

  if (totalPages <= 1) return null;

  return (
    <div className="pagination">
      <div className="pagination__controls">
        <button
          className="pagination__arrow"
          onClick={() => handlePageClick(currentPage - 1)}
          disabled={currentPage === 1 || loading}
        >
          &lt;
        </button>

        {renderPageNumbers()}

        <button
          className="pagination__arrow"
          onClick={() => handlePageClick(currentPage + 1)}
          disabled={currentPage === totalPages || loading}
        >
          &gt;
        </button>

        <div className="pagination__goto">
          <input
            type="number"
            min="1"
            max={totalPages}
            value={inputPage}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Page"
            className="pagination__input"
            disabled={loading}
          />
          <button
            className="pagination__go-button"
            onClick={handleGoToPage}
            disabled={!inputPage || loading}
          >
            Go
          </button>
        </div>
      </div>

      <div className="pagination__size-selector">
        <select
          value={pageSize}
          onChange={handlePageSizeChange}
          disabled={loading}
          className="pagination__size-select"
        >
          {PAGE_SIZE_OPTIONS.map(size => (
            <option key={size} value={size}>
              {size} per page
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default Pagination;
