/**
 * Smart Knowledge Base - Interactive Document Management and RAG System
 */

'use client';

import { useState, useRef } from 'react';

interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadDate: Date;
  chunks: number;
  status: 'processing' | 'ready' | 'error';
}

interface SearchResult {
  id: string;
  title: string;
  content: string;
  source: string;
  confidence: number;
  relevance: number;
}

export default function SmartKnowledgeBase() {
  const [documents, setDocuments] = useState<Document[]>([
    {
      id: '1',
      name: 'AI Research Paper.pdf',
      type: 'PDF',
      size: '2.4 MB',
      uploadDate: new Date('2024-01-15'),
      chunks: 45,
      status: 'ready'
    },
    {
      id: '2',
      name: 'Technical Documentation.docx',
      type: 'DOCX',
      size: '1.8 MB',
      uploadDate: new Date('2024-01-14'),
      chunks: 32,
      status: 'ready'
    },
    {
      id: '3',
      name: 'Project Guidelines.md',
      type: 'Markdown',
      size: '156 KB',
      uploadDate: new Date('2024-01-13'),
      chunks: 12,
      status: 'ready'
    }
  ]);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedTab, setSelectedTab] = useState<'documents' | 'search' | 'upload'>('search');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setSearchResults([]);

    try {
      const response = await fetch('http://localhost:8000/api/rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          max_results: 5
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();
      
      // Transform API response to SearchResult format
      const results: SearchResult[] = result.citations?.map((citation: any, index: number) => ({
        id: `result-${index}`,
        title: citation.title || `Result ${index + 1}`,
        content: citation.excerpt || citation.content || 'No content available',
        source: citation.source || 'Unknown source',
        confidence: citation.confidence || 0.8,
        relevance: Math.max(0.6, 1 - (index * 0.1))
      })) || [];

      // Add main answer as first result if available
      if (result.answer) {
        results.unshift({
          id: 'main-answer',
          title: 'AI Generated Answer',
          content: result.answer,
          source: 'AI Analysis',
          confidence: result.confidence_score || 0.9,
          relevance: 1.0
        });
      }

      setSearchResults(results);

    } catch (error) {
      console.error('Search error:', error);
      // Add error result
      setSearchResults([{
        id: 'error',
        title: 'Search Error',
        content: `Failed to search: ${error instanceof Error ? error.message : 'Unknown error'}`,
        source: 'System',
        confidence: 0,
        relevance: 0
      }]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    setIsUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await fetch('http://localhost:8000/api/rag/upload', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const result = await response.json();

      // Add new document to list
      const newDoc: Document = {
        id: result.document_id || Date.now().toString(),
        name: file.name,
        type: file.name.split('.').pop()?.toUpperCase() || 'Unknown',
        size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
        uploadDate: new Date(),
        chunks: result.chunks_created || 0,
        status: 'ready'
      };

      setDocuments(prev => [newDoc, ...prev]);
      setSelectedTab('documents');

    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'text-green-400';
      case 'processing': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'processing':
        return (
          <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">
          Smart Knowledge Base
        </h2>
        <p className="text-white/70">
          Upload, search, and analyze documents with AI-powered insights
        </p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-8 bg-white/10 rounded-lg p-1">
        {[
          { id: 'search', label: 'Search & Query', icon: '🔍' },
          { id: 'documents', label: 'Documents', icon: '📚' },
          { id: 'upload', label: 'Upload', icon: '📤' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id as any)}
            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium text-sm transition-all ${
              selectedTab === tab.id
                ? 'bg-white/20 text-white shadow-lg'
                : 'text-white/70 hover:text-white hover:bg-white/10'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Search Tab */}
      {selectedTab === 'search' && (
        <div className="space-y-6">
          {/* Search Input */}
          <div className="flex space-x-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ask questions about your documents..."
              className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button
              onClick={handleSearch}
              disabled={!searchQuery.trim() || isSearching}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-white font-semibold text-lg">Search Results</h3>
              {searchResults.map((result) => (
                <div
                  key={result.id}
                  className="bg-white/10 border border-white/20 rounded-lg p-6 hover:bg-white/15 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <h4 className="text-white font-medium text-lg">{result.title}</h4>
                    <div className="flex items-center space-x-4 text-sm">
                      <div className="flex items-center space-x-1">
                        <span className="text-white/60">Confidence:</span>
                        <span className={`font-medium ${
                          result.confidence > 0.8 ? 'text-green-400' :
                          result.confidence > 0.6 ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                          {(result.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="text-white/60">Relevance:</span>
                        <div className="w-16 bg-white/20 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-blue-400 to-purple-400 h-2 rounded-full"
                            style={{ width: `${result.relevance * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-white/80 mb-3 leading-relaxed">{result.content}</p>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-white/60 text-sm">Source: {result.source}</span>
                    <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                      View Source →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Search Suggestions */}
          {searchResults.length === 0 && !isSearching && (
            <div className="bg-white/5 rounded-lg p-6">
              <h4 className="text-white font-medium mb-3">Try asking:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  "What are the main findings in the research papers?",
                  "Summarize the technical documentation",
                  "What are the project requirements?",
                  "Explain the methodology used",
                  "What are the key recommendations?",
                  "Compare different approaches mentioned"
                ].map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => setSearchQuery(suggestion)}
                    className="text-left p-3 bg-white/10 hover:bg-white/20 rounded-lg text-white/80 text-sm transition-colors"
                  >
                    "{suggestion}"
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Documents Tab */}
      {selectedTab === 'documents' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-semibold text-lg">Document Library</h3>
            <div className="text-white/60 text-sm">
              {documents.length} documents • {documents.reduce((sum, doc) => sum + doc.chunks, 0)} chunks total
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="bg-white/10 border border-white/20 rounded-lg p-6 hover:bg-white/15 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className={`flex items-center space-x-1 ${getStatusColor(doc.status)}`}>
                      {getStatusIcon(doc.status)}
                      <span className="text-xs font-medium capitalize">{doc.status}</span>
                    </div>
                  </div>
                </div>

                <h4 className="text-white font-medium mb-2 truncate" title={doc.name}>
                  {doc.name}
                </h4>

                <div className="space-y-2 text-sm text-white/60">
                  <div className="flex justify-between">
                    <span>Type:</span>
                    <span className="text-white">{doc.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Size:</span>
                    <span className="text-white">{doc.size}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Chunks:</span>
                    <span className="text-white">{doc.chunks}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Uploaded:</span>
                    <span className="text-white">{doc.uploadDate.toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="mt-4 flex space-x-2">
                  <button className="flex-1 px-3 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-lg text-sm font-medium transition-colors">
                    View
                  </button>
                  <button className="flex-1 px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm font-medium transition-colors">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Tab */}
      {selectedTab === 'upload' && (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-white font-semibold text-lg mb-2">Upload Documents</h3>
            <p className="text-white/60">
              Supported formats: PDF, DOCX, TXT, MD, HTML
            </p>
          </div>

          {/* Upload Area */}
          <div
            className="border-2 border-dashed border-white/30 rounded-lg p-12 text-center hover:border-white/50 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.md,.html"
              onChange={(e) => handleFileUpload(e.target.files)}
              className="hidden"
            />
            
            {isUploading ? (
              <div className="space-y-4">
                <svg className="w-16 h-16 mx-auto text-blue-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <div>
                  <p className="text-white font-medium mb-2">Uploading...</p>
                  <div className="w-64 mx-auto bg-white/20 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-400 to-purple-400 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-white/60 text-sm mt-2">{uploadProgress}%</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <svg className="w-16 h-16 mx-auto text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <div>
                  <p className="text-white font-medium mb-2">
                    Drop files here or click to browse
                  </p>
                  <p className="text-white/60 text-sm">
                    Maximum file size: 50MB
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Upload Instructions */}
          <div className="bg-white/5 rounded-lg p-6">
            <h4 className="text-white font-medium mb-3">Processing Information:</h4>
            <ul className="text-white/70 text-sm space-y-2">
              <li>• Documents are automatically processed and indexed</li>
              <li>• Text is extracted and split into searchable chunks</li>
              <li>• Vector embeddings are generated for semantic search</li>
              <li>• Processing time depends on document size and complexity</li>
              <li>• All data is processed securely and privately</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}