import React, { useEffect } from 'react';
import useSettingsStore from '../../stores/settingsStore';
import Input from '../common/Input';
import Button from '../common/Button';
import './Settings.scss';

function Settings() {
  const { 
    settings,
    updateSettings,
    updateStoryRetention,
    updateAutoTrigger,
    updateProxyDefaults,
    updateProxyLimits,
    updateSystemRateLimit,
    updateBatchDefaults,
    fetchSettings,
    loading,
    error
  } = useSettingsStore();

  // Fetch settings on mount
  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleStoryRetention = (hours) => {
    updateStoryRetention(parseInt(hours, 10));
  };

  const handleAutoTrigger = (updates) => {
    updateAutoTrigger({
      enabled: settings.autoTriggerEnabled,
      startHour: settings.autoTriggerStartHour,
      endHour: settings.autoTriggerEndHour,
      interval: settings.minTriggerInterval,
      ...updates
    });
  };

  const handleProxyDefaults = (updates) => {
    updateProxyDefaults({
      ...settings.proxyDefaultSettings,
      ...updates
    });
  };

  const handleProxyLimits = (updates) => {
    updateProxyLimits({
      testTimeout: settings.proxyTestTimeout,
      maxFailures: settings.proxyMaxFailures,
      hourlyLimit: settings.proxyHourlyLimit,
      ...updates
    });
  };

  return (
    <div className="settings">
      {loading && <div className="settings__loading">Loading...</div>}
      {error && <div className="settings__error">{error}</div>}

      <div className="settings__section">
        <h2>Story Management</h2>
        <div className="settings__field">
          <label>Stories Needed Per Day (per niche)</label>
          <Input
            type="number"
            value={settings.storiesPerDay}
            onChange={(e) => updateSettings({ storiesPerDay: parseInt(e.target.value) })}
            min={1}
          />
        </div>
        <div className="settings__field">
          <label>Story Retention Period (hours)</label>
          <Input
            type="number"
            value={settings.storyRetentionHours}
            onChange={(e) => handleStoryRetention(e.target.value)}
            min={1}
          />
          <div className="settings__help-text">
            How long to keep story detection history
          </div>
        </div>
      </div>

      <div className="settings__section">
        <h2>Auto-Trigger Configuration</h2>
        <div className="settings__field">
          <label>Enable Auto-Trigger</label>
          <div className="settings__toggle">
            <Button
              variant={settings.autoTriggerEnabled ? 'primary' : 'secondary'}
              onClick={() => handleAutoTrigger({ enabled: !settings.autoTriggerEnabled })}
            >
              {settings.autoTriggerEnabled ? 'Enabled' : 'Disabled'}
            </Button>
          </div>
        </div>
        <div className="settings__field">
          <label>Active Hours</label>
          <div className="settings__hours">
            <Input
              type="number"
              value={settings.autoTriggerStartHour}
              onChange={(e) => handleAutoTrigger({ startHour: parseInt(e.target.value) })}
              min={0}
              max={23}
            />
            <span>to</span>
            <Input
              type="number"
              value={settings.autoTriggerEndHour}
              onChange={(e) => handleAutoTrigger({ endHour: parseInt(e.target.value) })}
              min={0}
              max={24}
            />
          </div>
        </div>
        <div className="settings__field">
          <label>Minimum Trigger Interval (minutes)</label>
          <Input
            type="number"
            value={settings.minTriggerInterval}
            onChange={(e) => handleAutoTrigger({ interval: parseInt(e.target.value) })}
            min={1}
          />
        </div>
      </div>

      <div className="settings__section">
        <h2>Batch Configuration</h2>
        <div className="settings__field">
          <label>Default Batch Size</label>
          <Input
            type="number"
            value={settings.defaultBatchSize}
            onChange={(e) => updateBatchDefaults({ batchSize: parseInt(e.target.value) })}
            min={1}
          />
        </div>
      </div>

      <div className="settings__section">
        <h2>Rate Limiting</h2>
        <div className="settings__field">
          <label>System-wide Rate Limit (requests/hour)</label>
          <Input
            type="number"
            value={settings.systemRateLimit}
            onChange={(e) => updateSystemRateLimit(parseInt(e.target.value))}
            min={1}
          />
        </div>
        <div className="settings__field">
          <label>Profiles Per Minute</label>
          <Input
            type="number"
            value={settings.profilesPerMinute}
            onChange={(e) => updateSettings({ profilesPerMinute: parseInt(e.target.value) })}
            min={1}
          />
        </div>
        <div className="settings__field">
          <label>Thread Count</label>
          <Input
            type="number"
            value={settings.threadCount}
            onChange={(e) => updateSettings({ threadCount: parseInt(e.target.value) })}
            min={1}
          />
        </div>
      </div>

      <div className="settings__section">
        <h2>Proxy Configuration</h2>
        <div className="settings__field">
          <label>Test Timeout (ms)</label>
          <Input
            type="number"
            value={settings.proxyTestTimeout}
            onChange={(e) => handleProxyLimits({ testTimeout: parseInt(e.target.value) })}
            min={1000}
            step={1000}
          />
        </div>
        <div className="settings__field">
          <label>Maximum Failures Before Disable</label>
          <Input
            type="number"
            value={settings.proxyMaxFailures}
            onChange={(e) => handleProxyLimits({ maxFailures: parseInt(e.target.value) })}
            min={1}
          />
        </div>
        <div className="settings__field">
          <label>Default Hourly Limit</label>
          <Input
            type="number"
            value={settings.proxyHourlyLimit}
            onChange={(e) => handleProxyLimits({ hourlyLimit: parseInt(e.target.value) })}
            min={1}
          />
        </div>
        <div className="settings__subsection">
          <h3>Default Proxy Settings</h3>
          <div className="settings__field">
            <label>Retry Attempts</label>
            <Input
              type="number"
              value={settings.proxyDefaultSettings.retryAttempts}
              onChange={(e) => handleProxyDefaults({ retryAttempts: parseInt(e.target.value) })}
              min={0}
            />
          </div>
          <div className="settings__field">
            <label>Retry Delay (ms)</label>
            <Input
              type="number"
              value={settings.proxyDefaultSettings.retryDelay}
              onChange={(e) => handleProxyDefaults({ retryDelay: parseInt(e.target.value) })}
              min={0}
              step={100}
            />
          </div>
          <div className="settings__field">
            <label>Rotation Interval (minutes)</label>
            <Input
              type="number"
              value={settings.proxyDefaultSettings.rotationInterval}
              onChange={(e) => handleProxyDefaults({ rotationInterval: parseInt(e.target.value) })}
              min={1}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;
