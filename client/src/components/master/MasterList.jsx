import React, { useState, useEffect } from 'react';
import useProfileStore from '../../stores/profileStore';
import useNicheStore from '../../stores/nicheStore';
import { useFilterStore } from '../../stores/filterStore';
import { usePaginationStore } from '../../stores/paginationStore';
import { useSortStore } from '../../stores/sortStore';
import Table from '../common/Table';
import Button from '../common/Button';
import Modal from '../common/Modal';
import Input from '../common/Input';
import ChangeNiche from '../niche/ChangeNiche';
import Pagination from '../common/Pagination';
import './MasterList.scss';

function MasterList() {
  const {
    profiles,
    loading,
    error,
    updateProfile,
    deleteProfiles,
    refreshStories,
    fetchProfiles
  } = useProfileStore();

  const { filters, setFilter } = useFilterStore();
  const { niches } = useNicheStore();
  const { currentPage, pageSize, setPage } = usePaginationStore();
  const { sortColumn, sortDirection } = useSortStore();

  const [selectedIds, setSelectedIds] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [showChangeNiche, setShowChangeNiche] = useState(false);

  // Fetch profiles when filters, pagination, or sorting changes
  useEffect(() => {
    fetchProfiles();
  }, [filters, currentPage, pageSize, sortColumn, sortDirection, fetchProfiles]);

  const handleBulkAction = async (action) => {
    if (!selectedIds.length) return;

    switch (action) {
      case 'delete':
        await deleteProfiles(selectedIds);
        break;
      case 'activate':
        await Promise.all(
          selectedIds.map(id => updateProfile(id, { status: 'active' }))
        );
        break;
      case 'deactivate':
        await Promise.all(
          selectedIds.map(id => updateProfile(id, { status: 'inactive' }))
        );
        break;
      default:
        break;
    }

    setSelectedIds([]);
    setShowBulkActions(false);
  };

  const handleStatusChange = async (id, newStatus) => {
    await updateProfile(id, { status: newStatus });
  };

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
        <div className="master-list__username">
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
      key: 'niche',
      title: 'Niche',
      sortable: true,
      render: (profile) => {
        const niche = niches.find(n => n.id === profile.niche_id);
        return niche?.name || '-';
      }
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      render: (profile) => (
        <select
          value={profile.status}
          onChange={(e) => handleStatusChange(profile.id, e.target.value)}
          className="master-list__status-select"
        >
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
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

  return (
    <div className="master-list">
      <div className="master-list__header">
        <div className="master-list__filters">
          <Input
            type="text"
            placeholder="Search profiles..."
            value={filters.search}
            onChange={(e) => setFilter('search', e.target.value)}
            style={{ width: '200px' }}
          />
          <select
            value={filters.nicheId || ''}
            onChange={(e) => {
              const nicheId = e.target.value || null;
              setFilter('nicheId', nicheId);
              setPage(1); // Reset to first page when changing niche
            }}
          >
            <option value="">All Niches</option>
            {niches.map(niche => (
              <option key={niche.id} value={niche.id}>
                {niche.name}
              </option>
            ))}
          </select>
          <select
            value={filters.status || ''}
            onChange={(e) => {
              setFilter('status', e.target.value || null);
              setPage(1); // Reset to first page when changing status
            }}
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <Button onClick={() => setShowChangeNiche(true)}>
            Change Niche
          </Button>
        </div>

        <div className="master-list__actions">
          <Button
            onClick={async () => {
              try {
                await fetchProfiles();
                await refreshStories();
              } catch (error) {
                console.error('Failed to refresh stories:', error);
              }
            }}
          >
            Refresh Active Stories
          </Button>
          <Button
            onClick={() => {
              const activeProfiles = profiles.filter(p => p.active_story);
              setSelectedIds(activeProfiles.map(p => p.id));
            }}
          >
            Select Active Stories
          </Button>

          {selectedIds.length > 0 && (
            <Button onClick={() => setShowBulkActions(true)}>
              Bulk Actions ({selectedIds.length})
            </Button>
          )}
        </div>
      </div>

      {loading && <div className="master-list__loading">Loading...</div>}
      {error && <div className="master-list__error">{error}</div>}

      <Table
        data={profiles}
        columns={columns}
        selectable={true}
        selectedRows={selectedIds}
        onSelectionChange={setSelectedIds}
      />

      <Pagination />

      {/* Bulk Actions Modal */}
      {showBulkActions && (
        <Modal
          title="Bulk Actions"
          isOpen={showBulkActions}
          onClose={() => setShowBulkActions(false)}
        >
          <div className="master-list__bulk-actions">
            <Button onClick={() => handleBulkAction('activate')}>
              Activate Selected
            </Button>
            <Button onClick={() => handleBulkAction('deactivate')}>
              Deactivate Selected
            </Button>
            <Button
              variant="danger"
              onClick={() => handleBulkAction('delete')}
            >
              Delete Selected
            </Button>
          </div>
        </Modal>
      )}

      {/* Change Niche Modal */}
      <ChangeNiche
        isOpen={showChangeNiche}
        onClose={() => setShowChangeNiche(false)}
      />
    </div>
  );
}

export default MasterList;
