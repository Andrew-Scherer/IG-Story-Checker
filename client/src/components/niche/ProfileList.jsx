import React, { useEffect } from 'react';
import useProfileStore from '../../stores/profileStore';
import { useFilterStore } from '../../stores/filterStore';
import { usePaginationStore } from '../../stores/paginationStore';
import { useSortStore } from '../../stores/sortStore';
import Table from '../common/Table';
import Pagination from '../common/Pagination';
import './ProfileList.scss';

function ProfileList({ nicheId }) {
  const {
    profiles,
    loading,
    error,
    selectedProfileIds,
    setSelectedProfiles,
    fetchProfiles
  } = useProfileStore();

  const { setFilter } = useFilterStore();
  const { currentPage, pageSize, reset: resetPagination } = usePaginationStore();
  const { sortColumn, sortDirection } = useSortStore();

  // Set niche filter and reset pagination when niche changes
  useEffect(() => {
    setFilter('nicheId', nicheId);
    resetPagination();
    fetchProfiles();
  }, [nicheId, setFilter, resetPagination, fetchProfiles]);

  // Fetch profiles when filters, pagination, or sorting changes
  useEffect(() => {
    fetchProfiles();
  }, [currentPage, pageSize, sortColumn, sortDirection, fetchProfiles]);

  const formatDate = (dateString) => {
    if (!dateString) return '-';
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
            href={profile.url || `https://instagram.com/${profile.username}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            {profile.username}
          </a>
        </div>
      )
    },
    {
      key: 'last_checked',
      title: 'Last Check',
      sortable: true,
      render: (profile) => formatDate(profile.last_checked)
    },
    {
      key: 'last_detected',
      title: 'Last Story',
      sortable: true,
      render: (profile) => formatDate(profile.last_detected)
    },
    {
      key: 'detection_rate',
      title: 'Story Detection Rate',
      sortable: true,
      render: (profile) => {
        const rate = profile.total_checks
          ? ((profile.total_detections / profile.total_checks) * 100).toFixed(1)
          : 0;
        return `${rate}%`;
      }
    }
  ];

  if (loading) {
    return <div className="profile-list__loading">Loading...</div>;
  }

  if (error) {
    return <div className="profile-list__error">{error}</div>;
  }

  return (
    <div className="profile-list">
      <Table
        data={profiles}
        columns={columns}
        selectable={true}
        selectedRows={selectedProfileIds}
        onSelectionChange={setSelectedProfiles}
      />
      <Pagination />
    </div>
  );
}

export default ProfileList;
