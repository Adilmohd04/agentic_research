'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import { Save, Key, Eye, EyeOff, CheckCircle, AlertCircle } from 'lucide-react';

interface APIKeySettings {
  openrouter_api_key: string;
  openai_api_key: string;
  anthropic_api_key: string;
}

export default function APIKeyManager() {
  const { user } = useUser();
  const [settings, setSettings] = useState<APIKeySettings>({
    openrouter_api_key: '',
    openai_api_key: '',
    anthropic_api_key: ''
  });
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadSettings();
  }, [user]);

  const loadSettings = async () => {
    if (!user) return;
    
    try {
      const response = await fetch(`/api/user/settings?user_id=${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setSettings(data.settings || settings);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    if (!user) return;
    
    setSaving(true);
    setMessage(null);

    try {
      const response = await fetch('/api/user/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user.id,
          settings
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Settings saved successfully!' });
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save settings. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  const toggleKeyVisibility = (key: string) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const updateSetting = (key: keyof APIKeySettings, value: string) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const apiKeyFields = [
    {
      key: 'openrouter_api_key' as keyof APIKeySettings,
      label: 'OpenRouter API Key',
      description: 'For accessing multiple LLM providers through OpenRouter',
      placeholder: 'sk-or-v1-...',
      required: true
    },
    {
      key: 'openai_api_key' as keyof APIKeySettings,
      label: 'OpenAI API Key',
      description: 'Direct OpenAI API access (optional if using OpenRouter)',
      placeholder: 'sk-...',
      required: false
    },
    {
      key: 'anthropic_api_key' as keyof APIKeySettings,
      label: 'Anthropic API Key',
      description: 'Direct Anthropic API access (optional if using OpenRouter)',
      placeholder: 'sk-ant-...',
      required: false
    }
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">API Key Management</h2>
        <p className="text-gray-600">
          Configure your API keys to enable AI-powered features. Your keys are encrypted and stored securely.
        </p>
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-lg flex items-center space-x-2 ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-800 border border-green-200' 
            : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <div className="space-y-6">
        {apiKeyFields.map((field) => (
          <div key={field.key} className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                  <Key className="w-5 h-5" />
                  <span>{field.label}</span>
                  {field.required && (
                    <span className="text-red-500 text-sm">*</span>
                  )}
                </h3>
                <p className="text-gray-600 text-sm mt-1">{field.description}</p>
              </div>
            </div>

            <div className="relative">
              <input
                type={showKeys[field.key] ? 'text' : 'password'}
                value={settings[field.key]}
                onChange={(e) => updateSetting(field.key, e.target.value)}
                placeholder={field.placeholder}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => toggleKeyVisibility(field.key)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showKeys[field.key] ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>

            {field.key === 'openrouter_api_key' && (
              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Getting OpenRouter API Key:</h4>
                <ol className="text-sm text-blue-800 space-y-1">
                  <li>1. Visit <a href="https://openrouter.ai" target="_blank" rel="noopener noreferrer" className="underline">openrouter.ai</a></li>
                  <li>2. Sign up or log in to your account</li>
                  <li>3. Go to your API keys section</li>
                  <li>4. Create a new API key</li>
                  <li>5. Copy and paste it here</li>
                </ol>
              </div>
            )}
          </div>
        ))}

        <div className="flex justify-end space-x-4">
          <button
            onClick={saveSettings}
            disabled={saving}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Save className="w-5 h-5" />
            <span>{saving ? 'Saving...' : 'Save Settings'}</span>
          </button>
        </div>
      </div>

      <div className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">Security & Privacy</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• All API keys are encrypted before storage</li>
          <li>• Keys are only used for your requests and never shared</li>
          <li>• You can revoke access by deleting your keys</li>
          <li>• OpenRouter provides access to multiple AI models with one key</li>
        </ul>
      </div>
    </div>
  );
}
