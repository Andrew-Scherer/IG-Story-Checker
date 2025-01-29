import React, { useEffect } from 'react';
import useProfileStore from '../../stores/profileStore';
import Table from '../common/Table';
import Pagination from '../common/Pagination';
import './ProfileList.scss';

const ProfileList = ({ nicheId }) => {
  const {
    profiles,
    totalProfiles,
    currentPage,
    pageSize,
    sortColumn,
    sortDirection,
    loading,
    error,
    selectedProfileIds,
    setFilters,
    setSelectedProfiles,
    fetchProfiles,
    updateProfile
  } = useProfileStore();

  useEffect(() => {
    setFilters({ nicheId });
    fetchProfiles();
  }, [nicheId, setFilters, fetchProfiles]);

  useEffect(() => {
    console.log('ProfileList - Current profiles:', profiles);
    console.log('ProfileList - Current sort column:', sortColumn);
    console.log('ProfileList - Current sort direction:', sortDirection);
  }, [profiles, sortColumn, sortDirection]);

  const handlePageChange = (page) => {
    console.log('ProfileList - Changing page to:', page);
    fetchProfiles({ page });
  };

  const handleSort = (column) => {
    console.log('ProfileList - Sorting by column:', column);
    const direction = column === sortColumn && sortDirection === 'asc' ? 'desc' : 'asc';
    console.log('ProfileList - New sort direction:', direction);
    console.log('ProfileList - Current sortColumn:', sortColumn);
    console.log('ProfileList - Current sortDirection:', sortDirection);
    
    // Ensure 'niche.name' is correctly handled
    const adjustedColumn = column === 'niche.name' ? 'niche__name' : column;
    
    console.log('ProfileList - Fetching profiles with:', { sortColumn: adjustedColumn, sortDirection: direction });
    fetchProfiles({ sortColumn: adjustedColumn, sortDirection: direction });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const columns = [
    {
      key: 'username',
      title: 'Username',
      sortable: true,
      render: (profile) => (
        <div className="profile-list__username">
          <a 
            href={`https://instagram.com/${profile.username}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            {profile.username}
          </a>
        </div>
      )
    },
    {
      key: 'niche.name',
      title: 'Niche',
      sortable: true,
      render: (profile) => {
        console.log('Rendering niche for profile:', profile);
        return profile.niche ? profile.niche.name : '-';
      }
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      render: (profile) => (
        <div className="profile-list__status">
          <span 
            className={`profile-list__status-badge profile-list__status-badge--${profile.status}`}
            onClick={async (e) => {
              e.stopPropagation();
              await updateProfile(profile.id, {
                status: profile.status === 'active' ? 'inactive' : 'active'
              });
            }}
          >
            {profile.status}
          </span>
        </div>
      )
    },
    {
      key: 'active_story',
      title: 'Active Story',
      sortable: true,
      render: (profile) => (
        <div className={`profile-list__story-status ${profile.active_story ? 'profile-list__story-status--active' : ''}`}>
          {profile.active_story ? 'Yes' : 'No'}
        </div>
      )
    },
    {
      key: 'last_story_detected',
      title: 'Last Story Detected',
      sortable: true,
      render: (profile) => formatDate(profile.last_story_detected)
    },
    {
      key: 'total_checks',
      title: 'Total Checks',
      sortable: true,
      render: (profile) => profile.total_checks
    },
    {
      key: 'total_detections',
      title: 'Total Detections',
      sortable: true,
      render: (profile) => profile.total_detections
    }
  ];

  const totalPages = Math.ceil(totalProfiles / pageSize);

  return (
    <div className="profile-list">
      {loading && <div className="profile-list__loading">Loading...</div>}
      {error && <div className="profile-list__error">{error}</div>}

      <div className="profile-list__info">
        Total Profiles: {totalProfiles}
      </div>

      {selectedProfileIds.length > 0 && (
        <div className="profile-list__selection-info">
          {selectedProfileIds.length} profiles selected
        </div>
      )}

      {profiles.length > 0 ? (
        <>
          <Table
            data={profiles}
            columns={columns}
            selectable={true}
            selectedRows={selectedProfileIds}
            onSelectionChange={setSelectedProfiles}
            onSort={handleSort}
            sortColumn={sortColumn}
            sortDirection={sortDirection}
          />
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />
        </>
      ) : (
        <div className="profile-list__empty">
          <p>No profiles found</p>
          <p>Import profiles using the file importer above</p>
        </div>
      )}
    </div>
  );
};

export default ProfileList;
