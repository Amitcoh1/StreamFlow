import React, { useState } from 'react';
import { Save, Database, Bell, Shield } from 'lucide-react';

const Settings = () => {
  const [settings, setSettings] = useState({
    alertThreshold: 5,
    retentionDays: 30,
    enableNotifications: true,
    logLevel: 'info'
  });

  const handleSave = () => {
    // Save settings logic here
    console.log('Saving settings:', settings);
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure system settings and preferences</p>
      </div>

      <div className="max-w-2xl space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Bell className="h-5 w-5 text-blue-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Alert Settings</h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Error Rate Threshold (%)</label>
              <input
                type="number"
                value={settings.alertThreshold}
                onChange={(e) => setSettings({...settings, alertThreshold: e.target.value})}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={settings.enableNotifications}
                onChange={(e) => setSettings({...settings, enableNotifications: e.target.checked})}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-900">Enable email notifications</label>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Database className="h-5 w-5 text-green-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Data Settings</h3>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Data Retention (days)</label>
            <input
              type="number"
              value={settings.retentionDays}
              onChange={(e) => setSettings({...settings, retentionDays: e.target.value})}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Shield className="h-5 w-5 text-purple-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">System Settings</h3>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Log Level</label>
            <select
              value={settings.logLevel}
              onChange={(e) => setSettings({...settings, logLevel: e.target.value})}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Save className="h-4 w-4 mr-2" />
          Save Settings
        </button>
      </div>
    </div>
  );
};

export default Settings; 