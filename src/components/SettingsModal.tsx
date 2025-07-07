import React, { useState } from 'react';
import { X, Save, RefreshCw, Globe, Database, Zap } from 'lucide-react';

interface SettingsModalProps {
  settings: any;
  onClose: () => void;
  onSave: (settings: any) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ settings, onClose, onSave }) => {
  const [localSettings, setLocalSettings] = useState(settings);
  const [activeTab, setActiveTab] = useState('general');

  const handleSave = () => {
    onSave(localSettings);
    onClose();
  };

  const tabs = [
    { id: 'general', label: 'General', icon: Globe },
    { id: 'api', label: 'API Settings', icon: Database },
    { id: 'performance', label: 'Performance', icon: Zap }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Settings</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon size={16} />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-96">
          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Theme
                </label>
                <select
                  value={localSettings.theme}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, theme: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Language
                </label>
                <select
                  value={localSettings.language}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, language: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                >
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                  <option value="ta">Tamil</option>
                  <option value="te">Telugu</option>
                </select>
              </div>

              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={localSettings.enableNotifications}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, enableNotifications: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Enable notifications</span>
                </label>
              </div>

              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={localSettings.enableVoice}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, enableVoice: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Enable voice input</span>
                </label>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Endpoint
                </label>
                <input
                  type="url"
                  value={localSettings.apiEndpoint}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, apiEndpoint: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="http://localhost:8000/api/v1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key (Optional)
                </label>
                <input
                  type="password"
                  value={localSettings.apiKey}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, apiKey: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="Enter API key if required"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Request Timeout (seconds)
                </label>
                <input
                  type="number"
                  min="5"
                  max="60"
                  value={localSettings.requestTimeout}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, requestTimeout: parseInt(e.target.value) }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={localSettings.enableRealTimeUpdates}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, enableRealTimeUpdates: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Enable real-time data updates</span>
                </label>
              </div>
            </div>
          )}

          {activeTab === 'performance' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Messages per Session
                </label>
                <input
                  type="number"
                  min="10"
                  max="1000"
                  value={localSettings.maxMessages}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, maxMessages: parseInt(e.target.value) }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Auto-save Interval (minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={localSettings.autoSaveInterval}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, autoSaveInterval: parseInt(e.target.value) }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={localSettings.enableCaching}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, enableCaching: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Enable response caching</span>
                </label>
              </div>

              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={localSettings.enableAnalytics}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, enableAnalytics: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Enable usage analytics</span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <button
            onClick={() => setLocalSettings(settings)}
            className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            <RefreshCw size={16} />
            <span>Reset</span>
          </button>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              <Save size={16} />
              <span>Save Changes</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};