import React, { useState, useEffect } from 'react';
import useNicheStore from '../../stores/nicheStore';
import useProfileStore from '../../stores/profileStore';
import useBatchStore from '../../stores/batchStore';
import Button from '../common/Button';
import FileImporter from './FileImporter';
import ProfileList from './ProfileList';
import './NicheFeed.scss';

function NicheFeed() {
  const {
    selectedNicheId,
    setSelectedNicheId,
    deleteNiche,
    updateNiche,
    createNiche,
    getNiches,
    fetchNiches
  } = useNicheStore();

  const { 
    getProfilesByNiche, 
    fetchProfiles, 
    importFromFile, 
    setFilters,
    selectedProfileIds,
    setSelectedProfiles,
    refreshStories
  } = useProfileStore();

  const { createBatch } = useBatchStore();

  useEffect(() => {
    fetchNiches();
    fetchProfiles();
  }, [fetchNiches, fetchProfiles]);

  const [isAdding, setIsAdding] = useState(false);
  const [newNicheName, setNewNicheName] = useState('');

  const handleNicheClick = (id) => {
    const newId = id === selectedNicheId ? null : id;
    setSelectedNicheId(newId);
    setFilters({ nicheId: newId });
  };

  const handleDelete = (e, id) => {
    e.stopPropagation();
    deleteNiche(id);
  };

  const handleNameChange = (e, id) => {
    e.stopPropagation();
    updateNiche(id, { name: e.target.value });
  };

  const handleAddClick = () => {
    setIsAdding(true);
  };

  const handleAddSubmit = (e) => {
    e.preventDefault();
    if (newNicheName.trim()) {
      createNiche({ name: newNicheName.trim() });
      setNewNicheName('');
      setIsAdding(false);
    }
  };

  const niches = getNiches() || [];

  return (
    <div className="niche-feed">
      <div className="niche-feed__sidebar">
        <div className="niche-feed__header">
          <div className="niche-feed__header-controls">
            <Button onClick={handleAddClick} data-testid="add-niche-button">
              Add Niche
            </Button>
          </div>
        </div>

        {isAdding && (
          <form onSubmit={handleAddSubmit} className="niche-feed__add-form">
            <input
              type="text"
              value={newNicheName}
              onChange={(e) => setNewNicheName(e.target.value)}
              placeholder="Enter niche name"
              autoFocus
              className="niche-feed__input"
            />
            <Button type="submit">Save</Button>
            <Button variant="secondary" onClick={() => setIsAdding(false)}>
              Cancel
            </Button>
          </form>
        )}

        <div className="niche-feed__list">
          {niches.map((niche) => (
            <div
              key={niche.id}
              className={`niche-feed__item ${
                selectedNicheId === niche.id ? 'niche-feed__item--selected' : ''
              }`}
              onClick={() => handleNicheClick(niche.id)}
              data-testid="niche-item"
            >
              <div className="niche-feed__content">
                <input
                  type="text"
                  value={niche.name}
                  onChange={(e) => handleNameChange(e, niche.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="niche-feed__name"
                  data-testid="niche-name-input"
                />
                <span className="niche-feed__counter">
                  {getProfilesByNiche(niche.id).length} profiles
                </span>
              </div>
              <Button
                variant="danger"
                size="small"
                onClick={(e) => handleDelete(e, niche.id)}
                data-testid="delete-button"
              >
                X
              </Button>
            </div>
          ))}
        </div>
      </div>

      <div className="niche-feed__main">
        <div className="niche-feed__header">
          <div className="niche-feed__header-controls">
            <div className="niche-feed__header-group">
              <FileImporter
                onImport={async (file) => {
                  try {
                    const result = await importFromFile(file);
                    if (result?.errors?.length > 0) {
                      throw new Error(
                        `Import completed with ${result.errors.length} errors:\n` +
                        result.errors.map(err => `${err.line}: ${err.error}`).join('\n')
                      );
                    }
                    await fetchProfiles();
                  } catch (error) {
                    console.error('Import failed:', error);
                    throw error;
                  }
                }}
                disabled={!selectedNicheId}
                disabledMessage="Please select a niche before importing profiles"
              />
              <div className="niche-feed__button-group">
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
                    const activeProfiles = getProfilesByNiche(selectedNicheId).filter(p => p.active_story);
                    setSelectedProfiles(activeProfiles.map(p => p.id));
                  }}
                  disabled={!selectedNicheId}
                >
                  Select Active Stories
                </Button>
                <Button
                  disabled={!selectedNicheId || selectedProfileIds.length === 0}
                  onClick={async () => {
                    try {
                      await createBatch(selectedProfileIds, selectedNicheId);
                      setSelectedProfiles([]); // Clear selection after batch creation
                    } catch (error) {
                      console.error('Failed to create batch:', error);
                    }
                  }}
                >
                  Check Selected Profiles for Stories ({selectedProfileIds.length})
                </Button>
              </div>
            </div>
          </div>
        </div>
        <div className="niche-feed__profiles">
          {selectedNicheId && <ProfileList nicheId={selectedNicheId} />}
        </div>
      </div>
    </div>
  );
}

export default NicheFeed;
