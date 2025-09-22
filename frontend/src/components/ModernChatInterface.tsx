/**
 * Modern Chat Interface with 2025 Design Trends
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Message } from '../types/chat';

interface ChatInterfaceProps {
  sessionId: string;
  userId?: string;
}

export default function ModernChatInterface({ sessionId, userId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/health`);
        setApiStatus(response.ok ? 'connected' : 'disconnected');
      } catch (error) {
        console.error('API health check failed:', error);
        setApiStatus('disconnected');
      }
    };
    checkApiStatus();
  }, []);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const messageContent = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: messageContent,
      timestamp: new Date(),
      metadata: { source: 'chat_interface' },
      citations: []
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/agents/coordinate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: messageContent,
          context: { session_id: sessionId },
          agents: ['researcher', 'analyzer']
        }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const result = await response.json();
      
      const aiMessage: Message = {
        id: `ai_${Date.now()}`,
        role: 'assistant',
        content: result.results?.summary || 'Task completed successfully!',
        timestamp: new Date(),
        metadata: { 
          task_id: result.task_id,
          agents_used: result.agents_used || ['researcher', 'analyzer']
        },
        citations: result.results?.citations || []
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        metadata: { error: true },
        citations: []
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const quickPrompts = [
    { icon: '🔍', text: 'Research latest AI trends', gradient: 'from-blue-500 to-cyan-500' },
    { icon: '📊', text: 'Analyze market data', gradient: 'from-green-500 to-emerald-500' },
    { icon: '💡', text: 'Generate creative ideas', gradient: 'from-purple-500 to-pink-500' },
    { icon: '📝', text: 'Write a summary', gradient: 'from-orange-500 to-red-500' }
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-white/10">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center animate-glow">
            <span className="text-xl">🤖</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">AI Assistant</h2>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                apiStatus === 'connected' ? 'bg-green-400 animate-pulse' : 
                apiStatus === 'checking' ? 'bg-yellow-400 animate-pulse' : 'bg-red-400'
              }`}></div>
              <span className="text-sm text-gray-300 capitalize">{apiStatus}</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
            <span className="text-lg">⚙️</span>
          </button>
          <button className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
            <span className="text-lg">📎</span>
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-6 animate-float">
              <span className="text-3xl">🚀</span>
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">Welcome to AI Chat</h3>
            <p className="text-gray-300 mb-8 max-w-md">
              Start a conversation with our advanced AI assistant. Ask questions, get insights, or explore ideas.
            </p>
            
            {/* Quick Prompts */}
            <div className="grid grid-cols-2 gap-3 w-full max-w-2xl">
              {quickPrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => setInputMessage(prompt.text)}
                  className={`p-4 rounded-xl bg-gradient-to-r ${prompt.gradient} bg-opacity-20 border border-white/20 hover:bg-opacity-30 transition-all duration-300 group`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl group-hover:scale-110 transition-transform">{prompt.icon}</span>
                    <span className="text-white font-medium">{prompt.text}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                  {message.role === 'assistant' && (
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <span className="text-sm">🤖</span>
                      </div>
                      <span className="text-sm text-gray-300">AI Assistant</span>
                    </div>
                  )}
                  
                  <div className={`p-4 rounded-2xl ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white ml-4'
                      : 'bg-white/10 text-white mr-4 backdrop-blur-xl border border-white/20'
                  }`}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    
                    {message.citations && message.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-white/20">
                        <p className="text-xs text-gray-300 mb-2">Sources:</p>
                        <div className="space-y-1">
                          {message.citations.map((citation, idx) => (
                            <div key={idx} className="text-xs text-blue-300 hover:text-blue-200 cursor-pointer">
                              📄 {citation.title}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className={`text-xs text-gray-400 mt-1 ${
                    message.role === 'user' ? 'text-right' : 'text-left'
                  }`}>
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-sm">🤖</span>
                  </div>
                  <span className="text-sm text-gray-300">AI Assistant</span>
                </div>
                <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-4 mr-4">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-white/10">
        <div className="flex items-end space-x-4">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message... (Press Enter to send)"
              className="w-full p-4 pr-12 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300"
              rows={1}
              style={{ minHeight: '56px', maxHeight: '120px' }}
            />
            
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="absolute right-3 bottom-3 w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-all duration-300 animate-glow"
            >
              <span className="text-white text-lg">
                {isLoading ? '⏳' : '🚀'}
              </span>
            </button>
          </div>
        </div>
        
        <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
          <span>Session: {sessionId.slice(-8)}</span>
          <span>{messages.length} messages</span>
        </div>
      </div>
    </div>
  );
}