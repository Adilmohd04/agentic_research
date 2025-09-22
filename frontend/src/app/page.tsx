'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import dynamic from 'next/dynamic';

// Lazy load components for better performance
const ChatInterface = dynamic(() => import('../components/ChatInterface'), { ssr: false });
const VoiceInterface = dynamic(() => import('../components/VoiceInterface'), { ssr: false });
const MemoryInterface = dynamic(() => import('../components/MemoryInterface'), { ssr: false });
const AgentDashboard = dynamic(() => import('../components/AgentDashboard'), { ssr: false });
const UnifiedKnowledgeBase = dynamic(() => import('../components/UnifiedKnowledgeBase'), { ssr: false });
const SettingsInterface = dynamic(() => import('../components/SettingsInterface'), { ssr: false });

type TabType = 'chat' | 'voice' | 'memory' | 'dashboard' | 'rag' | 'settings';

// Force dynamic rendering
export const dynamic = 'force-dynamic'
export const revalidate = 0

export default function Home() {
  const { user, isLoaded } = useUser();
  const [activeTab, setActiveTab] = useState<TabType>('chat');
  const [sessionId, setSessionId] = useState<string>('');

  useEffect(() => {
    setSessionId(`session-${Date.now()}`);
  }, []);

  // Show loading while Clerk is initializing
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center animate-pulse mx-auto mb-4">
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <p className="text-slate-600">Loading AI Research Platform...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-white/20 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">AI Research Platform</h1>
                <p className="text-sm text-gray-600">Multi-Agent Research System</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {user ? (
                <>
                  <button
                    onClick={() => setActiveTab('settings')}
                    className={`p-2 rounded-lg transition-colors ${
                      activeTab === 'settings' 
                        ? 'bg-blue-100 text-blue-600' 
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </button>
                  <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-gray-700">
                      {user.firstName?.[0] || user.emailAddresses[0]?.emailAddress[0] || 'U'}
                    </span>
                  </div>
                </>
              ) : (
                <div className="flex space-x-2">
                  <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 rounded-lg border">
                    Sign In
                  </button>
                  <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg">
                    Sign Up
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      {activeTab !== 'settings' && (
        <nav className="bg-white/60 backdrop-blur-xl border-b border-white/20">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex space-x-1 overflow-x-auto">
              {[
                { id: 'chat', label: 'Chat', icon: '💬' },
                { id: 'voice', label: 'Voice', icon: '🎤' },
                { id: 'memory', label: 'Memory', icon: '🧠' },
                { id: 'dashboard', label: 'Dashboard', icon: '📊' },
                { id: 'rag', label: 'Knowledge', icon: '📚' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`py-3 px-4 font-medium text-sm transition-all duration-200 rounded-t-lg whitespace-nowrap flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'bg-white text-blue-600 border-b-2 border-blue-500 shadow-sm'
                      : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
          </div>
        </nav>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 min-h-[600px]">
          {activeTab === 'chat' && (
            <div className="h-full">
              <ChatInterface sessionId={sessionId} />
            </div>
          )}
          {activeTab === 'voice' && (
            <div className="h-full">
              <VoiceInterface sessionId={sessionId} />
            </div>
          )}
          {activeTab === 'memory' && (
            <div className="h-full">
              <MemoryInterface />
            </div>
          )}
          {activeTab === 'dashboard' && (
            <div className="h-full">
              <AgentDashboard />
            </div>
          )}
          {activeTab === 'rag' && (
            <div className="h-full">
              <UnifiedKnowledgeBase />
            </div>
          )}
          {activeTab === 'settings' && user && (
            <div className="h-full">
              <SettingsInterface onBack={() => setActiveTab('chat')} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}