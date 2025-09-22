'use client';

import { useState, useEffect } from 'react';
import DocumentUpload from './DocumentUpload';

interface MemoryItem {
  id: string;
  type: 'conversation' | 'fact' | 'preference' | 'context';
  content: string;
  timestamp: string;
  importance: 'low' | 'medium' | 'high';
  tags: string[];
}

interface MemoryInterfaceProps {
  sessionId: string;
}

export default function MemoryInterface({ sessionId }: MemoryInterfaceProps) {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMemories();
  }, [sessionId]);

  const loadMemories = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/memory?session_id=${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setMemories(data.memories || []);
      }
    } catch (error) {
      console.error('Failed to load memories:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredMemories = memories.filter(memory => {
    const matchesSearch = memory.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         memory.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = selectedType === 'all' || memory.type === selectedType;
    return matchesSearch && matchesType;
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'conversation': return '💬';
      case 'fact': return '📝';
      case 'preference': return '⚙️';
      case 'context': return '🔗';
      default: return '📄';
    }
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Knowledge Base: Upload Documents */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Knowledge Base</h2>
        <p className="text-gray-600 mb-4">Add documents to enrich retrieval and context</p>
        <DocumentUpload onUploadComplete={() => { /* no-op refresh hook for now */ }} />
      </div>

      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Memory Bank</h2>
        <p className="text-gray-600">View and manage AI conversation memories and learned context</p>
      </div>

      {/* Search and Filter */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search memories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All Types</option>
          <option value="conversation">Conversations</option>
          <option value="fact">Facts</option>
          <option value="preference">Preferences</option>
          <option value="context">Context</option>
        </select>
      </div>

      {/* Memory Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{memories.length}</div>
          <div className="text-sm text-blue-800">Total Memories</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {memories.filter(m => m.importance === 'high').length}
          </div>
          <div className="text-sm text-green-800">High Priority</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">
            {memories.filter(m => m.type === 'conversation').length}
          </div>
          <div className="text-sm text-purple-800">Conversations</div>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">
            {memories.filter(m => m.type === 'preference').length}
          </div>
          <div className="text-sm text-orange-800">Preferences</div>
        </div>
      </div>

      {/* Memory List */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading memories...</p>
          </div>
        ) : filteredMemories.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🧠</div>
            <p className="text-gray-600">No memories found</p>
            <p className="text-sm text-gray-500 mt-2">
              {searchTerm || selectedType !== 'all' 
                ? 'Try adjusting your search or filter'
                : 'Start chatting to build memory context'
              }
            </p>
          </div>
        ) : (
          filteredMemories.map((memory) => (
            <div key={memory.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{getTypeIcon(memory.type)}</span>
                  <span className="font-medium text-gray-900 capitalize">{memory.type}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImportanceColor(memory.importance)}`}>
                    {memory.importance}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(memory.timestamp).toLocaleDateString()}
                </span>
              </div>
              
              <p className="text-gray-700 mb-3">{memory.content}</p>
              
              {memory.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {memory.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}