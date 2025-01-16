import React, { useState, useMemo, useEffect } from 'react';
import useProfileStore from '../../stores/profileStore';
import useNicheStore from '../../stores/nicheStore';
import Table from '../common/Table';
import Button from '../common/Button';
import './ProfileList.scss';

function ProfileList() {
  const {
    deleteProfiles,
    setFilters,
    getFilteredProfiles,
    getProfilesByNiche
  } = useProfileStore();

  const { selectedNicheId } = useNicheStore();

  const [selectedIds, setSelectedIds] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState(null);

  // Update filters when niche selection changes
  useEffect(() => {
    setFilters({ nicheId: selectedNicheId });
  }, [selectedNicheId, setFilters]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const profiles = useMemo(() => {
    if (!selectedNicheId) return [];
    const nicheProfiles = getProfilesByNiche(selectedNicheId);
    if (statusFilter === 'all') return nicheProfiles;
    return nicheProfiles.filter(profile => profile.status === statusFilter);
  }, [selectedNicheId, getProfilesByNiche, statusFilter]);

  const handleSort = (key, direction) => {
    setSortColumn(key);
    setSortDirection(direction);
  };

  const handleDelete = (id) => {
    deleteProfiles([id]);
    setSelectedIds(selectedIds.filter(selectedId => selectedId !== id));
  };

  const handleBulkDelete = () => {
    if (selectedIds.length > 0) {
      deleteProfiles(selectedIds);
      setSelectedIds([]);
    }
  };

  const columns = [
    {
      key: 'url',
      title: 'URL',
      sortable: true,
      render: (profile) => (
        <a 
          href={`https://instagram.com/${profile.username}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          {profile.username}
        </a>
      )
    },
    {
      key: 'username',
      title: 'Username',
      sortable: true
    },
    {
      key: 'lastChecked',
      title: 'Last Check',
      sortable: true,
      render: (profile) => profile.lastChecked ? formatDate(profile.lastChecked) : '-'
    },
    {
      key: 'lastDetected',
      title: 'Last Story',
      sortable: true,
      render: (profile) => profile.lastDetected ? formatDate(profile.lastDetected) : '-'
    },
    {
      key: 'totalChecks',
      title: 'Checks',
      sortable: true,
      render: (profile) => profile.totalChecks || 0
    },
    {
      key: 'totalDetections',
      title: 'Stories',
      sortable: true,
      render: (profile) => profile.totalDetections || 0
    },
    {
      key: 'actions',
      title: '',
      render: (profile) => (
        <Button
          variant="danger"
          size="small"
          onClick={() => handleDelete(profile.id)}
          data-testid="delete-button"
        >
          X
        </Button>
      )
    }
  ];

  return (
    <div className="profile-list">
      <div className="profile-list__header">
        <select
          className="profile-list__filter"
          data-testid="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        {selectedIds.length > 0 && (
          <Button
            variant="danger"
            onClick={handleBulkDelete}
            data-testid="bulk-delete-button"
          >
            Delete ({selectedIds.length})
          </Button>
        )}
      </div>

      {!selectedNicheId ? (
        <div className="profile-list__empty">
          <p>Select a niche to view profiles</p>
        </div>
      ) : !profiles.length ? (
        <div className="profile-list__empty">
          <p>No profiles found</p>
        </div>
      ) : (
        <Table
          data={profiles}
          columns={columns}
          onSort={handleSort}
          sortColumn={sortColumn}
          sortDirection={sortDirection}
          pageSize={100}
          selectable={true}
          selectedRows={selectedIds}
          onSelectionChange={setSelectedIds}
        />
      )}
    </div>
  );
}

export default ProfileList;
