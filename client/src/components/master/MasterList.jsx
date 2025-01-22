import React, { useState, useMemo, useEffect } from 'react';
import useProfileStore from '../../stores/profileStore';
import useNicheStore from '../../stores/nicheStore';
import Table from '../common/Table';
import Button from '../common/Button';
import Modal from '../common/Modal';
import Input from '../common/Input';
import './MasterList.scss';

function MasterList() {
  const {
    profiles,
    updateProfile,
    deleteProfiles,
    getFilteredProfiles,
    setFilters,
    filters,
    loading,
    error,
    refreshStories,
    fetchProfiles
  } = useProfileStore();

  const { niches } = useNicheStore();

  const [selectedIds, setSelectedIds] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [showProfileStats, setShowProfileStats] = useState(null);
  const [showHistory, setShowHistory] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Apply initial filters
  useEffect(() => {
    setFilters({ search: searchTerm });
  }, [searchTerm, setFilters]);

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

  const formatDuration = (minutes) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
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
      key: 'stats',
      title: 'Story Detection Rate',
      render: (profile) => {
        const rate = profile.total_checks 
          ? ((profile.total_detections / profile.total_checks) * 100).toFixed(1)
          : 0;
        return `${rate}%`;
      }
    }
  ];

  const filteredProfiles = useMemo(() => {
    return getFilteredProfiles();
  }, [getFilteredProfiles]);

  return (
    <div className="master-list">
      <div className="master-list__header">
        <div className="master-list__filters">
          <Input
            type="text"
            placeholder="Search profiles..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select
            value={filters.nicheId || ''}
            onChange={(e) => setFilters({ nicheId: e.target.value ? Number(e.target.value) : null })}
          >
            <option value="">All Niches</option>
            {niches.map(niche => (
              <option key={niche.id} value={niche.id}>
                {niche.name}
              </option>
            ))}
          </select>
          <select
            value={filters.status}
            onChange={(e) => setFilters({ status: e.target.value })}
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
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
              const activeProfiles = filteredProfiles.filter(p => p.active_story);
              setSelectedIds(activeProfiles.map(p => p.id));
            }}
          >
            Select Active Stories
          </Button>

          {selectedIds.length > 0 && (
            <Button
              onClick={() => setShowBulkActions(true)}
            >
              Bulk Actions ({selectedIds.length})
            </Button>
          )}
        </div>
      </div>

      {loading && <div className="master-list__loading">Loading...</div>}
      {error && <div className="master-list__error">{error}</div>}

      <Table
        data={filteredProfiles}
        columns={columns}
        pageSize={50}
        selectable={true}
        selectedRows={selectedIds}
        onSelectionChange={setSelectedIds}
      />

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

      {/* Profile Stats Modal */}
      {showProfileStats && (
        <Modal
          title={`Statistics for ${showProfileStats.username}`}
          isOpen={!!showProfileStats}
          onClose={() => setShowProfileStats(null)}
        >
          <div className="master-list__stats">
            <div className="master-list__stat">
              <label>Total Checks:</label>
              <span>{showProfileStats.total_checks || 0}</span>
            </div>
            <div className="master-list__stat">
              <label>Stories Found:</label>
              <span>{showProfileStats.total_detections || 0}</span>
            </div>
            <div className="master-list__stat">
              <label>Story Detection Rate:</label>
              <span>
                {showProfileStats.total_checks
                  ? ((showProfileStats.total_detections / showProfileStats.total_checks) * 100).toFixed(1)
                  : 0}%
              </span>
            </div>
            <div className="master-list__stat">
              <label>Last Check:</label>
              <span>{formatDate(showProfileStats.last_checked)}</span>
            </div>
            <div className="master-list__stat">
              <label>Last Story:</label>
              <span>{formatDate(showProfileStats.last_detected)}</span>
            </div>
            <div className="master-list__stat">
              <label>Status:</label>
              <span>{showProfileStats.status}</span>
            </div>
          </div>
        </Modal>
      )}

      {/* Profile History Modal */}
      {showHistory && (
        <Modal
          title={`Check History for ${showHistory.username}`}
          isOpen={!!showHistory}
          onClose={() => setShowHistory(null)}
        >
          <div className="master-list__history">
            {showHistory.checkHistory?.length ? (
              showHistory.checkHistory.map((check, index) => (
                <div key={index} className="master-list__history-item">
                  <div className="master-list__history-time">
                    {formatDate(check.timestamp)}
                  </div>
                  <div className={`master-list__history-status master-list__history-status--${check.success ? 'success' : 'failure'}`}>
                    {check.success ? 'Story Found' : 'No Story'}
                  </div>
                  <div className="master-list__history-duration">
                    {formatDuration(check.duration)}
                  </div>
                </div>
              ))
            ) : (
              <div className="master-list__empty">
                No check history available
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}

export default MasterList;
