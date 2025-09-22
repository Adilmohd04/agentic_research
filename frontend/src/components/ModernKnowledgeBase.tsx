/**
 * Modern Knowledge Base with 2025 Design
 */

'use client';

import { useState, useEffect } from 'react';

interface Document {
  id: string;
  title: string;
  type: 'pdf' | 'text' | 'web' | 'image';
  size: string;
  uploadDate: Date;
  status: 'processing' | 'ready' | 'error';
  tags: string[];
}

export default function ModernKnowledgeBase() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [isUploading, setIsUploading] = useState(false);

  // Mock data
  useEffect(() => {
    const mockDocs: Document[] = [
      {
        id: '1',
        title: 'AI Research Paper - Transformer Architecture',
        type: 'pdf',
        size: '2.4 MB',
        uploadDate: new Date(Date.now() - 86400000),
        status: 'ready',
        tags: ['AI', 'Research', 'Transformers']
      },
      {
        id: '2',
        title: 'Market Analysis Q4 2024',
        type: 'text',
        size: '156 KB',
        uploadDate: new Date(Date.now() - 172800000),
        status: 'ready',
        tags: ['Business', 'Analysis', 'Market']
      },
      {
        id: '3',
        title: 'Product Documentation',
        type: 'web',
        size: '892 KB',
        uploadDate: new Date(Date.now() - 259200000),
        status: 'processing',
        tags: ['Documentation', 'Product']
      }
    ];
    setDocuments(mockDocs);
  }, []);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'pdf': return '📄';
      case 'text': return '📝';
      case 'web': return '🌐';
      case 'image': return '🖼️';
      default: return '📄';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'from-green-500 to-emerald-500';
      case 'processing': return 'from-yellow-500 to-orange-500';
      case 'error': return 'from-red-500 to-pink-500';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  const filteredDocs = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         doc.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesFilter = selectedFilter === 'all' || doc.type === selectedFilter;
    return matchesSearch && matchesFilter;
  });

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      setIsUploading(true);
      // Simulate upload process
      setTimeout(() => {
        setIsUploading(false);
        // Add new document to list
        const newDoc: Document = {
          id: Date.now().toString(),
          title: files[0].name,
          type: files[0].type.includes('pdf') ? 'pdf' : 'text',
          size: `${(files[0].size / 1024 / 1024).toFixed(1)} MB`,
          uploadDate: new Date(),
          status: 'processing',
          tags: ['New', 'Upload']
        };
        setDocuments(prev => [newDoc, ...prev]);
      }, 2000);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Knowledge Base</h1>
          <p className="text-gray-300">Manage and search your AI-powered document library</p>
        </div>
        <div className="flex space-x-3">
          <label className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl text-white font-medium hover:scale-105 transition-transform cursor-pointer">
            📤 Upload Document
            <input
              type="file"
              className="hidden"
              onChange={handleFileUpload}
              accept=".pdf,.txt,.doc,.docx"
            />
          </label>
          <button className="px-4 py-2 bg-white/10 backdrop-blur-xl border border-white/20 rounded-xl text-white font-medium hover:bg-white/20 transition-colors">
            🔄 Sync
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="Search documents, tags, or content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full p-4 pl-12 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300"
          />
          <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl">🔍</span>
        </div>
        
        <div className="flex space-x-2">
          {['all', 'pdf', 'text', 'web', 'image'].map((filter) => (
            <button
              key={filter}
              onClick={() => setSelectedFilter(filter)}
              className={`px-4 py-2 rounded-xl font-medium transition-all duration-300 ${
                selectedFilter === filter
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                  : 'bg-white/10 text-gray-300 hover:bg-white/20'
              }`}
            >
              {filter === 'all' ? '📋 All' : `${getTypeIcon(filter)} ${filter.toUpperCase()}`}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 backdrop-blur-xl border border-white/20 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-sm">Total Documents</p>
              <p className="text-2xl font-bold text-white">{documents.length}</p>
            </div>
            <span className="text-2xl">📚</span>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 backdrop-blur-xl border border-white/20 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-sm">Ready</p>
              <p className="text-2xl font-bold text-white">{documents.filter(d => d.status === 'ready').length}</p>
            </div>
            <span className="text-2xl">✅</span>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-yellow-500/20 to-orange-500/20 backdrop-blur-xl border border-white/20 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-sm">Processing</p>
              <p className="text-2xl font-bold text-white">{documents.filter(d => d.status === 'processing').length}</p>
            </div>
            <span className="text-2xl">⏳</span>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-xl border border-white/20 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-sm">Storage Used</p>
              <p className="text-2xl font-bold text-white">3.4 GB</p>
            </div>
            <span className="text-2xl">💾</span>
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {isUploading && (
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center animate-pulse">
              <span className="text-2xl">📤</span>
            </div>
            <div className="flex-1">
              <p className="text-white font-medium">Uploading document...</p>
              <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                <div className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 animate-pulse" style={{width: '60%'}}></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Documents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredDocs.map((doc) => (
          <div key={doc.id} className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all duration-300 group">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">{getTypeIcon(doc.type)}</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-white text-sm line-clamp-2 group-hover:text-blue-300 transition-colors">
                    {doc.title}
                  </h3>
                  <p className="text-xs text-gray-400 mt-1">{doc.size}</p>
                </div>
              </div>
              
              <span className={`px-2 py-1 rounded-lg text-xs font-medium bg-gradient-to-r ${getStatusColor(doc.status)} text-white`}>
                {doc.status}
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex flex-wrap gap-1">
                {doc.tags.map((tag, idx) => (
                  <span key={idx} className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded-lg">
                    {tag}
                  </span>
                ))}
              </div>
              
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>Uploaded {doc.uploadDate.toLocaleDateString()}</span>
                <div className="flex space-x-2">
                  <button className="hover:text-blue-300 transition-colors">👁️</button>
                  <button className="hover:text-green-300 transition-colors">📤</button>
                  <button className="hover:text-red-300 transition-colors">🗑️</button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredDocs.length === 0 && (
        <div className="text-center py-12">
          <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-float">
            <span className="text-3xl">📚</span>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">No documents found</h3>
          <p className="text-gray-300 mb-6">
            {searchQuery ? 'Try adjusting your search terms' : 'Upload your first document to get started'}
          </p>
          <label className="inline-block px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl text-white font-medium hover:scale-105 transition-transform cursor-pointer">
            📤 Upload Document
            <input
              type="file"
              className="hidden"
              onChange={handleFileUpload}
              accept=".pdf,.txt,.doc,.docx"
            />
          </label>
        </div>
      )}
    </div>
  );
}