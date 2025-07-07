import { useState, useEffect } from 'react';

interface Settings {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  enableNotifications: boolean;
  enableVoice: boolean;
  apiEndpoint: string;
  apiKey: string;
  requestTimeout: number;
  enableRealTimeUpdates: boolean;
  maxMessages: number;
  autoSaveInterval: number;
  enableCaching: boolean;
  enableAnalytics: boolean;
}

const defaultSettings: Settings = {
  theme: 'light',
  language: 'en',
  enableNotifications: true,
  enableVoice: true,
  apiEndpoint: 'http://localhost:8000/api/v1',
  apiKey: '',
  requestTimeout: 30,
  enableRealTimeUpdates: true,
  maxMessages: 100,
  autoSaveInterval: 5,
  enableCaching: true,
  enableAnalytics: false
};

export const useSettings = () => {
  const [settings, setSettings] = useState<Settings>(defaultSettings);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('mosdac-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...defaultSettings, ...parsed });
      } catch (error) {
        console.error('Error loading settings:', error);
      }
    }
  }, []);

  const updateSettings = (newSettings: Partial<Settings>) => {
    const updatedSettings = { ...settings, ...newSettings };
    setSettings(updatedSettings);
    
    // Save to localStorage
    localStorage.setItem('mosdac-settings', JSON.stringify(updatedSettings));
  };

  const openSettings = () => setIsSettingsOpen(true);
  const closeSettings = () => setIsSettingsOpen(false);

  return {
    settings,
    isSettingsOpen,
    openSettings,
    closeSettings,
    updateSettings
  };
};