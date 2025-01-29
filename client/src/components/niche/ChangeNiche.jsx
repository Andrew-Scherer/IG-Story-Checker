import React, { useState } from 'react';
import useNicheStore from '../../stores/nicheStore';
import useProfileStore from '../../stores/profileStore';
import Modal from '../common/Modal';
import Button from '../common/Button';
import './ChangeNiche.scss';

const ChangeNiche = ({ isOpen, onClose }) => {
  const { niches } = useNicheStore();
  const { updateProfile, getFilteredProfiles } = useProfileStore();
  const [selectedNicheId, setSelectedNicheId] = useState('');

  const handleSave = async () => {
    if (!selectedNicheId) return;

    const profiles = getFilteredProfiles();
    for (const profile of profiles) {
      await updateProfile(profile.id, { niche_id: selectedNicheId });
    }

    onClose();
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
        <div className="change-niche__actions">
          <Button onClick={handleSave} disabled={!selectedNicheId}>
            Save
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ChangeNiche;