import React, { useEffect } from 'react';
import useProfileStore from '../../stores/profileStore';
import Table from '../common/Table';
import './ProfileList.scss';

const ProfileList = ({ nicheId }) => {
  const {
    setFilters,
    getFilteredProfiles,
    updateProfile,
    loading,
    error,
      selectedProfileIds,
      setSelectedProfiles,
      fetchProfiles
    } = useProfileStore();

  useEffect(() => {
    setFilters({ nicheId });
    fetchProfiles();
  }, [nicheId, setFilters, fetchProfiles]);

  const profiles = getFilteredProfiles();

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const columns = [
    {
      key: 'username',
      title: 'Username',
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
      key: 'status',
      title: 'Status',
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

  return (
    <div className="profile-list">
      {loading && <div className="profile-list__loading">Loading...</div>}
      {error && <div className="profile-list__error">{error}</div>}

      {selectedProfileIds.length > 0 && (
        <div className="profile-list__selection-info">
          {selectedProfileIds.length} profiles selected
        </div>
      )}

      {!profiles.length ? (
        <div className="profile-list__empty">
          <p>No profiles found</p>
          <p>Import profiles using the file importer above</p>
        </div>
      ) : (
        <Table
          data={profiles}
          columns={columns}
          pageSize={100}
          selectable={true}
          selectedRows={selectedProfileIds}
          onSelectionChange={setSelectedProfiles}
        />
      )}
    </div>
  );
};

export default ProfileList;
