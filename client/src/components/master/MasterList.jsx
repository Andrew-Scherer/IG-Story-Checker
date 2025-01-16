import React, { useState, useMemo } from 'react';
import useProfileStore from '../../stores/profileStore';
import './MasterList.scss';

function MasterList() {
  const { profiles } = useProfileStore();
  const [currentPage, setCurrentPage] = useState(1);
  const PAGE_SIZE = 500;

  const { paginatedUsernames, totalPages } = useMemo(() => {
    const sortedUsernames = [...profiles]
      .sort((a, b) => a.username.localeCompare(b.username))
      .map(profile => profile.username);

    const startIndex = (currentPage - 1) * PAGE_SIZE;
    const endIndex = startIndex + PAGE_SIZE;
    
    return {
      paginatedUsernames: sortedUsernames.slice(startIndex, endIndex),
      totalPages: Math.ceil(sortedUsernames.length / PAGE_SIZE)
    };
  }, [profiles, currentPage]);

  return (
    <div className="master-list">
      <div className="master-list__list">
        {paginatedUsernames.map(username => (
          <div key={username} className="master-list__item">
            {username}
          </div>
        ))}
      </div>
      {totalPages > 1 && (
        <div className="master-list__pagination">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="master-list__pagination-button"
          >
            Previous
          </button>
          <span className="master-list__pagination-info">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="master-list__pagination-button"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default MasterList;
