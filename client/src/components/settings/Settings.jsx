import React from 'react';
import useSettingsStore from '../../stores/settingsStore';
import Input from '../common/Input';
import './Settings.scss';

function Settings() {
  const { 
    settings,
    updateSettings
  } = useSettingsStore();

  const handleChange = (field, value) => {
    updateSettings({ [field]: value });
  };

  return (
    <div className="settings">
      <div className="settings__section">
        <h2>Daily Story Targets</h2>
        <div className="settings__field">
          <label>Stories Needed Per Day (per niche)</label>
          <Input
            type="number"
            value={settings.storiesPerDay}
            onChange={(e) => handleChange('storiesPerDay', parseInt(e.target.value))}
            min={1}
          />
        </div>
      </div>

      <div className="settings__section">
        <h2>Rate Limiting</h2>
        <div className="settings__field">
          <label>Profiles Per Minute</label>
          <Input
            type="number"
            value={settings.profilesPerMinute}
            onChange={(e) => handleChange('profilesPerMinute', parseInt(e.target.value))}
            min={1}
          />
        </div>
        <div className="settings__field">
          <label>Thread Count</label>
          <Input
            type="number"
            value={settings.threadCount}
            onChange={(e) => handleChange('threadCount', parseInt(e.target.value))}
            min={1}
          />
        </div>
        <div className="settings__field">
          <label>Proxy-Session Hourly Limit</label>
          <Input
            type="number"
            value={settings.proxyHourlyLimit}
            onChange={(e) => handleChange('proxyHourlyLimit', parseInt(e.target.value))}
            min={1}
            placeholder="Default: 150"
          />
          <div className="settings__help-text">
            Maximum requests per hour for each proxy-session pair
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;
