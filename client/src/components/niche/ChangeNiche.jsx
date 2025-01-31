import React, { useState } from 'react';
import useNicheStore from '../../stores/nicheStore';
import useProfileStore from '../../stores/profileStore';
import Modal from '../common/Modal';
import Button from '../common/Button';
import './ChangeNiche.scss';

const ChangeNiche = ({ isOpen, onClose }) => {
  const { niches } = useNicheStore();
  const { updateProfile, getFilteredProfiles, fetchProfiles } = useProfileStore();
  const [selectedNicheId, setSelectedNicheId] = useState('');
  const [progress, setProgress] = useState(0);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleSave = async () => {
    if (!selectedNicheId) return;

    const profiles = getFilteredProfiles();
    setIsUpdating(true);
    setProgress(0);

    try {
      for (let i = 0; i < profiles.length; i++) {
        await updateProfile(profiles[i].id, { niche_id: selectedNicheId });
        setProgress(Math.round(((i + 1) / profiles.length) * 100));
      }

      // Refresh the profile list to show updated niches
      await fetchProfiles();
      setIsUpdating(false);
      onClose();
    } catch (error) {
      console.error('Error updating niches:', error);
      setIsUpdating(false);
    }
  };

  return (
    <Modal title="Change Niche" isOpen={isOpen} onClose={onClose}>
      <div className="change-niche">
        <ul className="change-niche__list">
          {niches.map((niche) => (
            <li key={niche.id} className="change-niche__item">
              <label className="change-niche__label">
                <input
                  type="radio"
                  name="niche"
                  value={niche.id}
                  checked={selectedNicheId === niche.id}
                  onChange={() => setSelectedNicheId(niche.id)}
                  className="change-niche__radio"
                />
                {niche.name}
              </label>
            </li>
          ))}
        </ul>
        {isUpdating && (
          <div className="change-niche__progress">
            <div className="change-niche__progress-bar" style={{ width: `${progress}%` }}>
              {progress}%
            </div>
          </div>
        )}
        <div className="change-niche__actions">
          <Button onClick={handleSave} disabled={!selectedNicheId || isUpdating}>
            {isUpdating ? 'Updating...' : 'Save'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ChangeNiche;