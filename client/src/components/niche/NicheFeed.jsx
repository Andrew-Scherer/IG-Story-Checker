import React, { useState } from 'react';
import useNicheStore from '../../stores/nicheStore';
import useProfileStore from '../../stores/profileStore';
import Button from '../common/Button';
import './NicheFeed.scss';

function NicheFeed() {
  const {
    selectedNicheId,
    setSelectedNicheId,
    deleteNiche,
    updateNiche,
    addNiche,
    reorderNiches,
    getSortedNiches
  } = useNicheStore();

  const { getProfilesByNiche } = useProfileStore();

  const [isAdding, setIsAdding] = useState(false);
  const [newNicheName, setNewNicheName] = useState('');
  const [draggedItem, setDraggedItem] = useState(null);

  const handleNicheClick = (id) => {
    setSelectedNicheId(id === selectedNicheId ? null : id);
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
      addNiche({ name: newNicheName.trim() });
      setNewNicheName('');
      setIsAdding(false);
    }
  };

  const handleDragStart = (e, index) => {
    setDraggedItem(index);
    e.dataTransfer.effectAllowed = 'move';
    e.target.classList.add('niche-feed__item--dragging');
  };

  const handleDragEnd = (e) => {
    e.target.classList.remove('niche-feed__item--dragging');
    setDraggedItem(null);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedItem === null) return;
    if (draggedItem === index) return;

    reorderNiches(draggedItem, index);
    setDraggedItem(index);
  };

  const sortedNiches = getSortedNiches();

  return (
    <div className="niche-feed">
      <div className="niche-feed__header">
        <Button onClick={handleAddClick} data-testid="add-niche-button">
          Add Niche
        </Button>
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
        {sortedNiches.map((niche, index) => {
          const profiles = getProfilesByNiche(niche.id);
          return (
            <div
              key={niche.id}
              className={`niche-feed__item ${
                selectedNicheId === niche.id ? 'niche-feed__item--selected' : ''
              }`}
              onClick={() => handleNicheClick(niche.id)}
              draggable
              onDragStart={(e) => handleDragStart(e, index)}
              onDragEnd={handleDragEnd}
              onDragOver={(e) => handleDragOver(e, index)}
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
                  {profiles.length} profiles
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
          );
        })}
      </div>
    </div>
  );
}

export default NicheFeed;
