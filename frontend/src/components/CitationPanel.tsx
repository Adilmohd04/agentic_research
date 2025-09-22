/**
 * Citations panel component
 */

'use client';

import { Citation } from '../types/chat';
import { useState } from 'react';

interface CitationPanelProps {
  citations: Citation[];
  onClose: () => void;
}

export default function CitationPanel({ citations, onClose }: CitationPanelProps) {
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter citations based on search term
  const filteredCitations = citations.filter(citation =>
    citation.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    citation.excerpt.toLowerCase().includes(searchTerm.toLowerCase()) ||
    citation.source.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group citations by source
  const citationsBySource = filteredCitations.reduce((acc, citation) => {
    const source = citation.source;
    if (!acc[source]) {
      acc[source] = [];
    }
    acc[source].push(citation);
    return acc;
  }, {} as Record<string, Citation[]>);

  const getSourceTypeIcon = (sourceType?: string) => {
    switch (sourceType) {
      case 'web': return '🌐';
      case 'document': return '📄';
      case 'database': return '🗄️';
      case 'api': return '🔌';
      default: return '📚';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const formatDate = (date?: Date) => {
    if (!date) return 'Unknown date';
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Citations</h3>
          <p className="text-sm text-gray-500">{citations.length} sources found</p>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded-md transition-colors"
        >
          <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200">
        <input
          type="text"
          placeholder="Search citations..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Citations List */}
      <div className="flex-1 overflow-y-auto">
        {Object.keys(citationsBySource).length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <div className="text-4xl mb-2">📚</div>
            <p>No citations found</p>
            {searchTerm && (
              <p className="text-sm mt-1">Try adjusting your search terms</p>
            )}
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {Object.entries(citationsBySource).map(([source, sourceCitations]) => (
              <div key={source} className="border border-gray-200 rounded-lg overflow-hidden">
                {/* Source Header */}
                <div className="bg-gray-50 px-3 py-2 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900 text-sm">{source}</h4>
                    <span className="text-xs text-gray-500">
                      {sourceCitations.length} citation{sourceCitations.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>

                {/* Citations from this source */}
                <div className="divide-y divide-gray-100">
                  {sourceCitations.map((citation) => (
                    <div
                      key={citation.id}
                      className={`p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedCitation?.id === citation.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                      }`}
                      onClick={() => setSelectedCitation(citation)}
                    >
                      {/* Citation Header */}
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm">
                            {getSourceTypeIcon(citation.metadata?.sourceType)}
                          </span>
                          <h5 className="font-medium text-sm text-gray-900 line-clamp-2">
                            {citation.title}
                          </h5>
                        </div>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(citation.confidence)}`}>
                          {(citation.confidence * 100).toFixed(0)}%
                        </div>
                      </div>

                      {/* Citation Excerpt */}
                      <p className="text-sm text-gray-600 line-clamp-3 mb-2">
                        {citation.excerpt}
                      </p>

                      {/* Citation Metadata */}
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center space-x-3">
                          {citation.metadata?.author && (
                            <span>By {citation.metadata.author}</span>
                          )}
                          {citation.metadata?.publishDate && (
                            <span>{formatDate(citation.metadata.publishDate)}</span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span>Relevance: {(citation.relevance * 100).toFixed(0)}%</span>
                          {citation.url && (
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800"
                              onClick={(e) => e.stopPropagation()}
                            >
                              🔗
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Citation Details */}
      {selectedCitation && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <h4 className="font-medium text-sm text-gray-900 mb-2">Citation Details</h4>
          <div className="space-y-2 text-xs">
            <div>
              <span className="font-medium">ID:</span> {selectedCitation.id}
            </div>
            <div>
              <span className="font-medium">Source:</span> {selectedCitation.source}
            </div>
            <div>
              <span className="font-medium">Confidence:</span> {(selectedCitation.confidence * 100).toFixed(1)}%
            </div>
            <div>
              <span className="font-medium">Relevance:</span> {(selectedCitation.relevance * 100).toFixed(1)}%
            </div>
            {selectedCitation.metadata?.credibilityScore && (
              <div>
                <span className="font-medium">Credibility:</span> {(selectedCitation.metadata.credibilityScore * 100).toFixed(1)}%
              </div>
            )}
            {selectedCitation.timestamp && (
              <div>
                <span className="font-medium">Retrieved:</span> {formatDate(selectedCitation.timestamp)}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}