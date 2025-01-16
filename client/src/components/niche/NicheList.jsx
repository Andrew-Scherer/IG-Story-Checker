import React from 'react';
import NicheFeed from './NicheFeed';
import ProfileList from './ProfileList';
import FileImporter from './FileImporter';
import useProfileStore from '../../stores/profileStore';
import './NicheList.scss';

function NicheList() {
  const { addProfiles } = useProfileStore();

  const handleImport = async (file) => {
    const text = await file.text();
    const profiles = text.split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
      .map(username => ({ username }));
    
    addProfiles(profiles);
  };

  return (
    <div className="niche-list">
      <div className="niche-list__feed">
        <FileImporter
          onImport={handleImport}
          allowedTypes={['.txt', '.csv']}
          maxSize={5 * 1024 * 1024} // 5MB
        />
        <NicheFeed />
      </div>
      <div className="niche-list__profiles">
        <ProfileList />
      </div>
    </div>
  );
}

export default NicheList;
