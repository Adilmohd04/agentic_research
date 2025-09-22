'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import { 
  ArrowLeft,
  Save, 
  Key,  
  Eye,
  EyeOff, 
  CheckCircle,
  Mic,
  MessageSquare,
  Volume2,
  Download,
  Trash2,
  AlertCircle,
  Brain
} from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Slider } from './ui/slider';
import { Switch } from './ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

interface SettingsInterfaceProps {
  onBack: () => void;
}

interface APIKeySettings {
  openrouter_api_key: string;
  openai_api_key: string;
  anthropic_api_key: string;
}

export default function SettingsInterface({ onBack }: SettingsInterfaceProps) {
  const { user } = useUser();
  
  // Voice Settings
  const [voiceSettings, setVoiceSettings] = useState({
    enabled: true,
    autoSpeak: true,
    speechRate: 0.9,
    speechVolume: 0.8,
    language: 'en-US'
  });
  
  // Chat Settings
  const [chatSettings, setChatSettings] = useState({
    fontSize: 'medium',
    autoScroll: true,
    showTimestamps: true
  });

  // Memory Settings
  const [memorySettings, setMemorySettings] = useState({
    enabled: true,
    retentionDays: 30,
    autoSave: true,
    includeVoice: true,
  });

  // API Keys
  const [apiKeys, setApiKeys] = useState<APIKeySettings>({
    openrouter_api_key: '',
    openai_api_key: '',
    anthropic_api_key: '',
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
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/user/settings`, {
        headers: {
          'X-User-ID': user.id,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setApiKeys({
          openrouter_api_key: data.openrouter_api_key || '',
          openai_api_key: data.openai_api_key || '',
          anthropic_api_key: data.anthropic_api_key || '',
        });
        setChatSettings({
          ...chatSettings,
          model: data.preferred_model || 'sonoma-sky-alpha',
          temperature: data.temperature || 0.7,
          maxTokens: data.max_tokens || 2000,
        });
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
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/user/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': user.id,
        },
        body: JSON.stringify({
          openrouter_api_key: apiKeys.openrouter_api_key,
          openai_api_key: apiKeys.openai_api_key,
          anthropic_api_key: apiKeys.anthropic_api_key,
          preferred_model: 'sonoma-sky-alpha',
          temperature: 0.7,
          max_tokens: 2000,
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Settings saved successfully!' });
        setTimeout(() => setMessage(null), 3000);
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

  const updateApiKey = (key: keyof APIKeySettings, value: string) => {
    setApiKeys(prev => ({ ...prev, [key]: value }));
  };

  const apiKeyFields = [
    {
      key: 'openrouter_api_key' as keyof APIKeySettings,
      label: 'OpenRouter API Key',
      description: 'Access multiple LLM providers through OpenRouter',
      placeholder: 'sk-or-v1-...',
      required: true
    },
    {
      key: 'openai_api_key' as keyof APIKeySettings,
      label: 'OpenAI API Key',
      description: 'Direct OpenAI API access (optional)',
      placeholder: 'sk-...',
      required: false
    },
    {
      key: 'anthropic_api_key' as keyof APIKeySettings,
      label: 'Anthropic API Key',
      description: 'Direct Anthropic API access (optional)',
      placeholder: 'sk-ant-...',
      required: false
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={onBack}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
                <p className="text-gray-600 dark:text-gray-400">Customize your AI assistant experience</p>
              </div>
            </div>
            <Button 
              onClick={saveSettings} 
              disabled={saving}
              className="flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className="max-w-4xl mx-auto px-6 pt-4">
          <div className={`p-4 rounded-lg flex items-center gap-2 ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200 dark:bg-green-900/20 dark:text-green-200 dark:border-green-800' 
              : 'bg-red-50 text-red-800 border border-red-200 dark:bg-red-900/20 dark:text-red-200 dark:border-red-800'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
            <span>{message.text}</span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        
        {/* API Keys Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              API Keys
            </CardTitle>
            <CardDescription>
              Configure your AI service API keys for enhanced functionality
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {apiKeyFields.map((field) => (
              <div key={field.key} className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                </div>
                <p className="text-xs text-muted-foreground">{field.description}</p>
                <div className="relative">
                  <Input
                    type={showKeys[field.key] ? 'text' : 'password'}
                    value={apiKeys[field.key]}
                    onChange={(e) => updateApiKey(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    className="pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => toggleKeyVisibility(field.key)}
                    className="absolute right-0 top-0 h-9 w-9 hover:bg-transparent"
                  >
                    {showKeys[field.key] ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Voice Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="h-5 w-5" />
              Voice & Speech
            </CardTitle>
            <CardDescription>
              Configure voice recognition and text-to-speech settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium">Enable Voice Features</div>
                <div className="text-xs text-muted-foreground">Allow speech-to-text and text-to-speech</div>
              </div>
              <Switch
                checked={voiceSettings.enabled}
                onCheckedChange={(checked) => setVoiceSettings({...voiceSettings, enabled: checked})}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium">Auto-speak Responses</div>
                <div className="text-xs text-muted-foreground">Automatically speak AI responses</div>
              </div>
              <Switch
                checked={voiceSettings.autoSpeak}
                onCheckedChange={(checked) => setVoiceSettings({...voiceSettings, autoSpeak: checked})}
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Speech Rate</div>
                <div className="text-xs text-muted-foreground">{voiceSettings.speechRate}x</div>
              </div>
              <Slider
                value={[voiceSettings.speechRate]}
                onValueChange={([value]) => setVoiceSettings({...voiceSettings, speechRate: value})}
                min={0.5}
                max={2}
                step={0.1}
                className="w-full"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium flex items-center gap-2">
                  <Volume2 className="h-4 w-4" />
                  Speech Volume
                </div>
                <div className="text-xs text-muted-foreground">{Math.round(voiceSettings.speechVolume * 100)}%</div>
              </div>
              <Slider
                value={[voiceSettings.speechVolume]}
                onValueChange={([value]) => setVoiceSettings({...voiceSettings, speechVolume: value})}
                min={0}
                max={1}
                step={0.1}
                className="w-full"
              />
            </div>
          </CardContent>
        </Card>

        {/* Chat Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Chat Interface
            </CardTitle>
            <CardDescription>
              Customize your chat experience and display preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium">Font Size</div>
                <div className="text-xs text-muted-foreground">Adjust text size for better readability</div>
              </div>
              <select
                value={chatSettings.fontSize}
                onChange={(e) => setChatSettings({...chatSettings, fontSize: e.target.value})}
                className="px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-ring focus:border-transparent"
              >
                <option value="small">Small</option>
                <option value="medium">Medium</option>
                <option value="large">Large</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium">Auto Scroll</div>
                <div className="text-xs text-muted-foreground">Automatically scroll to new messages</div>
              </div>
              <Switch
                checked={chatSettings.autoScroll}
                onCheckedChange={(checked) => setChatSettings({...chatSettings, autoScroll: checked})}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium">Show Timestamps</div>
                <div className="text-xs text-muted-foreground">Display message timestamps</div>
              </div>
              <Switch
                checked={chatSettings.showTimestamps}
                onCheckedChange={(checked) => setChatSettings({...chatSettings, showTimestamps: checked})}
              />
            </div>
          </CardContent>
        </Card>

        {/* Memory Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Memory & Context
            </CardTitle>
            <CardDescription>
              Control how the AI remembers and uses conversation history
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium">Enable Memory System</div>
                <div className="text-xs text-muted-foreground">Allow AI to remember conversations and context</div>
              </div>
              <Switch
                checked={memorySettings.enabled}
                onCheckedChange={(checked) => setMemorySettings({...memorySettings, enabled: checked})}
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Memory Retention</div>
                <div className="text-xs text-muted-foreground">{memorySettings.retentionDays} days</div>
              </div>
              <Slider
                value={[memorySettings.retentionDays]}
                onValueChange={([value]) => setMemorySettings({...memorySettings, retentionDays: value})}
                min={1}
                max={365}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>1 day</span>
                <span>1 year</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium">Auto-save Conversations</div>
                <div className="text-xs text-muted-foreground">Automatically save conversation history</div>
              </div>
              <Switch
                checked={memorySettings.autoSave}
                onCheckedChange={(checked) => setMemorySettings({...memorySettings, autoSave: checked})}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium">Include Voice Interactions</div>
                <div className="text-xs text-muted-foreground">Save voice conversations to memory</div>
              </div>
              <Switch
                checked={memorySettings.includeVoice}
                onCheckedChange={(checked) => setMemorySettings({...memorySettings, includeVoice: checked})}
              />
            </div>
          </CardContent>
        </Card>

        {/* Data Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Data Management
            </CardTitle>
            <CardDescription>
              Export or clear your conversation data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <div className="space-y-0.5">
                <div className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Export Data</div>
                <div className="text-xs text-yellow-700 dark:text-yellow-300">Download all your conversations and memories</div>
              </div>
              <Button variant="outline" size="sm" className="gap-2">
                <Download className="h-4 w-4" />
                Export
              </Button>
            </div>

            <div className="flex items-center justify-between p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="space-y-0.5">
                <div className="text-sm font-medium text-red-800 dark:text-red-200">Clear All Data</div>
                <div className="text-xs text-red-700 dark:text-red-300">Permanently delete all conversations and memories</div>
              </div>
              <Button variant="destructive" size="sm" className="gap-2">
                <Trash2 className="h-4 w-4" />
                Clear All
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}