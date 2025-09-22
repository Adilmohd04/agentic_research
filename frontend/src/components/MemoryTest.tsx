/**
 * RAG & Memory System Component
 * Interface for testing RAG queries and memory functionality
 */

'use client';

import { useState, useEffect } from 'react';
import DocumentUpload from './DocumentUpload';

interface Message {
  id: string;
  role: string;
  content: string;
  timestamp: string;
  metadata: Record<string, any>;
}

interface MemoryStats {
  total_messages: number;
  active_agents: number;
  tasks_by_status: Record<string, number>;
  cache_sizes: Record<string, number>;
}

export default function MemoryTest() {
  const [activeTab, setActiveTab] = useState<'rag' | 'memory'>('rag');
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(false);
  
  // RAG specific state
  const [ragQuery, setRagQuery] = useState('');
  const [ragResults, setRagResults] = useState<any>(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [documents, setDocuments] = useState<any[]>([]);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Load conversation history
  const loadMessages = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/memory/messages/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages);
      }
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  // Load memory stats
  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/memory/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  // Send message
  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/memory/messages/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          role: 'user',
          content: newMessage,
          metadata: {
            source: 'web_ui',
            timestamp: new Date().toISOString()
          }
        }),
      });

      if (response.ok) {
        setNewMessage('');
        await loadMessages();
        await loadStats();
      } else {
        console.error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  // RAG Query function
  const performRagQuery = async () => {
    if (!ragQuery.trim()) return;

    setRagLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/rag/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: ragQuery,
          max_results: 10
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setRagResults(data);
      } else {
        console.error('Failed to perform RAG query');
      }
    } catch (error) {
      console.error('Error performing RAG query:', error);
    } finally {
      setRagLoading(false);
    }
  };

  // Load sample documents
  const loadDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/rag/documents`);
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadMessages();
    loadStats();
    loadDocuments();
  }, []);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">🧠 RAG & Memory System</h2>
        
        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('rag')}
            className={`px-4 py-2 rounded-md font-medium text-sm transition-colors ${
              activeTab === 'rag'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            🔍 RAG System
          </button>
          <button
            onClick={() => setActiveTab('memory')}
            className={`px-4 py-2 rounded-md font-medium text-sm transition-colors ${
              activeTab === 'memory'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            💾 Memory System
          </button>
        </div>
      </div>

      {activeTab === 'rag' && (
        <div className="space-y-6">
          {/* Document Upload Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">📄 Document Upload</h3>
            <DocumentUpload onUploadComplete={(results) => {
              console.log('Upload completed:', results);
              loadDocuments(); // Refresh document list
            }} />
          </div>

          {/* RAG Query Interface */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">🔍 Knowledge Base Search</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter your research query:
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={ragQuery}
                  onChange={(e) => setRagQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && performRagQuery()}
                  placeholder="Ask about any topic in the knowledge base..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={ragLoading}
                />
                <button
                  onClick={performRagQuery}
                  disabled={ragLoading || !ragQuery.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {ragLoading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>

            {/* Sample Queries */}
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Try these sample queries:</p>
              <div className="flex flex-wrap gap-2">
                {[
                  'What is machine learning?',
                  'Explain quantum computing',
                  'Best practices for API design',
                  'How does blockchain work?'
                ].map((query) => (
                  <button
                    key={query}
                    onClick={() => setRagQuery(query)}
                    className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>

            {/* RAG Results */}
            {ragResults && (
              <div className="border-t pt-4">
                <h4 className="font-medium mb-3">Search Results</h4>
                
                {/* Answer */}
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h5 className="font-medium text-green-800 mb-2">AI Answer:</h5>
                  <p className="text-green-900">{ragResults.answer}</p>
                  <div className="mt-2 text-sm text-green-700">
                    Confidence: {(ragResults.confidence_score * 100).toFixed(1)}% | 
                    Processing Time: {ragResults.processing_time}s
                  </div>
                </div>

                {/* Citations */}
                {ragResults.citations && ragResults.citations.length > 0 && (
                  <div>
                    <h5 className="font-medium mb-2">Sources & Citations:</h5>
                    <div className="space-y-2">
                      {ragResults.citations.map((citation: any, index: number) => (
                        <div key={index} className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                          <div className="flex justify-between items-start mb-1">
                            <span className="font-medium text-blue-800">{citation.title}</span>
                            <span className="text-sm text-blue-600">
                              {(citation.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="text-sm text-blue-700 mb-1">{citation.excerpt}</p>
                          <p className="text-xs text-blue-600">Source: {citation.source}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Document Index Status */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Knowledge Base Status</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{documents.length}</div>
                <div className="text-sm text-gray-600">Documents Indexed</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {documents.reduce((acc, doc) => acc + (doc.chunks || 0), 0)}
                </div>
                <div className="text-sm text-gray-600">Text Chunks</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {documents.reduce((acc, doc) => acc + (doc.embeddings || 0), 0)}
                </div>
                <div className="text-sm text-gray-600">Vector Embeddings</div>
              </div>
            </div>

            {documents.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Indexed Documents:</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {documents.map((doc, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">{doc.title || `Document ${index + 1}`}</span>
                      <span className="text-xs text-gray-500">{doc.type || 'Unknown'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'memory' && (
        <div className="space-y-6">
      
      {/* Session Info */}
      <div className="bg-blue-50 p-4 rounded-lg mb-6">
        <h3 className="font-semibold mb-2">Session Information</h3>
        <p className="text-sm text-gray-600">Session ID: {sessionId}</p>
      </div>

      {/* Memory Stats */}
      {stats && (
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <h3 className="font-semibold mb-3">Memory Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total_messages}</div>
              <div className="text-sm text-gray-600">Total Messages</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.active_agents}</div>
              <div className="text-sm text-gray-600">Active Agents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {Object.values(stats.tasks_by_status).reduce((a, b) => a + b, 0)}
              </div>
              <div className="text-sm text-gray-600">Total Tasks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Object.values(stats.cache_sizes).reduce((a, b) => a + b, 0)}
              </div>
              <div className="text-sm text-gray-600">Cache Entries</div>
            </div>
          </div>
        </div>
      )}

      {/* Message Input */}
      <div className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type a message to test memory system..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !newMessage.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>

      {/* Message History */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold">Conversation History ({messages.length} messages)</h3>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              No messages yet. Send a message to test the memory system.
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="p-4 border-b border-gray-100 last:border-b-0">
                <div className="flex justify-between items-start mb-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    message.role === 'user' 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {message.role}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-gray-800 mb-2">{message.content}</p>
                {Object.keys(message.metadata).length > 0 && (
                  <details className="text-xs text-gray-600">
                    <summary className="cursor-pointer">Metadata</summary>
                    <pre className="mt-1 bg-gray-50 p-2 rounded overflow-x-auto">
                      {JSON.stringify(message.metadata, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))
          )}
        </div>
      </div>

          {/* Refresh Button */}
          <div className="mt-4 text-center">
            <button
              onClick={() => {
                loadMessages();
                loadStats();
              }}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Refresh Data
            </button>
          </div>
        </div>
      )}
    </div>
  );
}