'use client';

import { useState, useEffect } from 'react';
import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from '@clerk/nextjs';
import ChatInterface from '../components/ChatInterface';
import RealTimeVoiceChat from '../components/RealTimeVoiceChat';
import VoiceInterface from '../components/VoiceInterface';
import MemoryInterface from '../components/MemoryInterface';
import AgentDashboard from '../components/AgentDashboard';
import UnifiedKnowledgeBase from '../components/UnifiedKnowledgeBase';
import SettingsInterface from '../components/SettingsInterface';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'voice' | 'realtime' | 'memory' | 'dashboard' | 'rag' | 'settings'>('chat');
  const [sessionId, setSessionId] = useState<string>('');

  useEffect(() => {
    setSessionId(`session-${Date.now()}`);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Main Header with Clerk Integration */}
      <header className="glass border-b border-white/20 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center animate-glow">
                  <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">AI Agenting Research</h1>
                <p className="text-sm text-slate-600 font-medium">Advanced Multi-Agent Research Platform</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-slate-600 bg-white/50 px-3 py-1.5 rounded-full">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="font-medium">Online</span>
              </div>
              
              <SignedOut>
                <SignInButton>
                  <button className="px-4 py-2 text-sm font-medium text-slate-700 bg-white/70 hover:bg-white/90 rounded-lg transition-all duration-200 border border-white/50">
                    Sign In
                  </button>
                </SignInButton>
                <SignUpButton>
                  <button className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl">
                    Sign Up
                  </button>
                </SignUpButton>
              </SignedOut>
              
              <SignedIn>
                <button
                  onClick={() => setActiveTab('settings')}
                  className={`p-2.5 rounded-lg transition-all duration-200 ${
                    activeTab === 'settings' 
                      ? 'bg-blue-100 text-blue-600 shadow-md' 
                      : 'text-slate-500 hover:text-slate-700 hover:bg-white/50'
                  }`}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
                <UserButton 
                  appearance={{
                    elements: {
                      avatarBox: "w-10 h-10 rounded-lg shadow-md hover:shadow-lg transition-shadow"
                    }
                  }}
                />
              </SignedIn>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      {activeTab !== 'settings' && (
        <nav className="glass-dark border-b border-white/10">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex space-x-1 overflow-x-auto">
              <button
                onClick={() => setActiveTab('chat')}
                className={`py-4 px-6 font-medium text-sm transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                  activeTab === 'chat'
                    ? 'bg-white/20 text-blue-600 border-b-2 border-blue-500 shadow-lg'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-white/10'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <span>💬</span>
                  <span>Text Chat</span>
                </span>
              </button>
              <button
                onClick={() => setActiveTab('voice')}
                className={`py-4 px-6 font-medium text-sm transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                  activeTab === 'voice'
                    ? 'bg-white/20 text-blue-600 border-b-2 border-blue-500 shadow-lg'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-white/10'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <span>🎤</span>
                  <span>Voice Chat</span>
                </span>
              </button>
              <button
                onClick={() => setActiveTab('realtime')}
                className={`py-4 px-6 font-medium text-sm transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                  activeTab === 'realtime'
                    ? 'bg-white/20 text-blue-600 border-b-2 border-blue-500 shadow-lg'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-white/10'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <span>🗣️</span>
                  <span>Real-time Speech</span>
                </span>
              </button>
              <button
                onClick={() => setActiveTab('memory')}
                className={`py-4 px-6 font-medium text-sm transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                  activeTab === 'memory'
                    ? 'bg-white/20 text-blue-600 border-b-2 border-blue-500 shadow-lg'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-white/10'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <span>🧠</span>
                  <span>Memory</span>
                </span>
              </button>
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`py-4 px-6 font-medium text-sm transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                  activeTab === 'dashboard'
                    ? 'bg-white/20 text-blue-600 border-b-2 border-blue-500 shadow-lg'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-white/10'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <span>📊</span>
                  <span>Agent Dashboard</span>
                </span>
              </button>
              <button
                onClick={() => setActiveTab('rag')}
                className={`py-4 px-6 font-medium text-sm transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                  activeTab === 'rag'
                    ? 'bg-white/20 text-blue-600 border-b-2 border-blue-500 shadow-lg'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-white/10'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <span>🧠</span>
                  <span>Knowledge Base</span>
                </span>
              </button>
            </div>
          </div>
        </nav>
      )}

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="glass rounded-2xl shadow-2xl min-h-[calc(100vh-200px)] overflow-hidden">
          {activeTab === 'chat' && sessionId && (
            <div className="h-full">
              <ChatInterface sessionId={sessionId} />
            </div>
          )}
          {activeTab === 'voice' && sessionId && (
            <div className="h-full">
              <VoiceInterface sessionId={sessionId} />
            </div>
          )}
          {activeTab === 'realtime' && sessionId && (
            <div className="bg-gradient-to-br from-blue-50/50 to-indigo-100/50 h-full">
              <RealTimeVoiceChat sessionId={sessionId} />
            </div>
          )}
          {activeTab === 'memory' && sessionId && (
            <div className="h-full">
              <MemoryInterface sessionId={sessionId} />
            </div>
          )}
          {activeTab === 'dashboard' && sessionId && (
            <div className="h-full">
              <AgentDashboard sessionId={sessionId} />
            </div>
          )}
          {activeTab === 'rag' && (
            <div className="h-full">
              <UnifiedKnowledgeBase />
            </div>
          )}
          {activeTab === 'settings' && (
            <div className="h-full">
              <SettingsInterface onBack={() => setActiveTab('chat')} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}