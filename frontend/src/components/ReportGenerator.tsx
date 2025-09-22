/**
 * Report generator component for exporting research results
 */

'use client';

import { useState } from 'react';
import { Message, Citation } from '@/shared/types/core';

interface ReportGeneratorProps {
  messages: Message[];
  citations: Citation[];
  sessionId: string;
}

interface ReportConfig {
  title: string;
  includeMessages: boolean;
  includeCitations: boolean;
  includeMetadata: boolean;
  format: 'markdown' | 'pdf' | 'html';
  citationStyle: 'apa' | 'mla' | 'chicago' | 'ieee';
}

export default function ReportGenerator({ messages, citations, sessionId }: ReportGeneratorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [config, setConfig] = useState<ReportConfig>({
    title: 'Research Report',
    includeMessages: true,
    includeCitations: true,
    includeMetadata: false,
    format: 'markdown',
    citationStyle: 'apa'
  });

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Generate report
  const generateReport = async () => {
    setIsGenerating(true);
    
    try {
      // Filter messages (exclude user messages if needed)
      const filteredMessages = messages.filter(msg => 
        config.includeMessages ? true : msg.role !== 'user'
      );

      // Prepare report data
      const reportData = {
        title: config.title,
        sessionId,
        messages: filteredMessages.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp,
          metadata: config.includeMetadata ? msg.metadata : undefined,
          citations: msg.citations
        })),
        citations: config.includeCitations ? citations : [],
        generatedAt: new Date().toISOString(),
        config
      };

      // Call backend to generate report
      const response = await fetch(`${API_BASE}/api/reports/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData)
      });

      if (response.ok) {
        // Download the generated report
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${config.title.replace(/\s+/g, '_')}.${config.format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        setIsOpen(false);
      } else {
        throw new Error('Failed to generate report');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Failed to generate report. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Generate preview
  const generatePreview = () => {
    const agentMessages = messages.filter(msg => msg.role === 'agent' || msg.role === 'assistant');
    const userQuestions = messages.filter(msg => msg.role === 'user');
    
    let preview = `# ${config.title}\n\n`;
    preview += `Generated on: ${new Date().toLocaleDateString()}\n`;
    preview += `Session ID: ${sessionId}\n\n`;
    
    if (userQuestions.length > 0) {
      preview += `## Research Questions\n\n`;
      userQuestions.forEach((msg, index) => {
        preview += `${index + 1}. ${msg.content}\n`;
      });
      preview += '\n';
    }
    
    if (agentMessages.length > 0) {
      preview += `## Research Findings\n\n`;
      agentMessages.forEach((msg, index) => {
        const agentRole = msg.metadata?.agent_role || 'Assistant';
        preview += `### ${agentRole} Response ${index + 1}\n\n`;
        preview += `${msg.content}\n\n`;
        
        if (msg.citations && msg.citations.length > 0 && config.includeCitations) {
          preview += `**Sources:**\n`;
          msg.citations.forEach((citation, citIndex) => {
            preview += `- [${citIndex + 1}] ${citation.title || citation.source}\n`;
          });
          preview += '\n';
        }
      });
    }
    
    if (config.includeCitations && citations.length > 0) {
      preview += `## References\n\n`;
      citations.forEach((citation, index) => {
        preview += `[${index + 1}] ${formatCitation(citation, config.citationStyle)}\n`;
      });
    }
    
    return preview;
  };

  // Format citation based on style
  const formatCitation = (citation: Citation, style: string) => {
    const author = citation.metadata?.author || 'Unknown Author';
    const title = citation.title || citation.source;
    const url = citation.url;
    const date = citation.timestamp ? new Date(citation.timestamp).getFullYear() : 'n.d.';
    
    switch (style) {
      case 'apa':
        return `${author} (${date}). ${title}. ${url ? `Retrieved from ${url}` : ''}`;
      case 'mla':
        return `${author}. "${title}." ${date}. ${url ? `Web. ${new Date().toLocaleDateString()}.` : ''}`;
      case 'chicago':
        return `${author}. "${title}." Accessed ${new Date().toLocaleDateString()}. ${url || ''}.`;
      case 'ieee':
        return `${author}, "${title}," ${date}. [Online]. Available: ${url || 'N/A'}`;
      default:
        return `${author}. ${title}. ${date}. ${url || ''}`;
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        disabled={messages.length === 0}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span>Generate Report</span>
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Generate Report</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex h-[calc(90vh-80px)]">
          {/* Configuration Panel */}
          <div className="w-80 p-6 border-r border-gray-200 overflow-y-auto">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Report Configuration</h3>
            
            <div className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Report Title
                </label>
                <input
                  type="text"
                  value={config.title}
                  onChange={(e) => setConfig(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Format */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export Format
                </label>
                <select
                  value={config.format}
                  onChange={(e) => setConfig(prev => ({ ...prev, format: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="markdown">Markdown (.md)</option>
                  <option value="pdf">PDF (.pdf)</option>
                  <option value="html">HTML (.html)</option>
                </select>
              </div>

              {/* Citation Style */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Citation Style
                </label>
                <select
                  value={config.citationStyle}
                  onChange={(e) => setConfig(prev => ({ ...prev, citationStyle: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="apa">APA</option>
                  <option value="mla">MLA</option>
                  <option value="chicago">Chicago</option>
                  <option value="ieee">IEEE</option>
                </select>
              </div>

              {/* Include Options */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Include in Report
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.includeMessages}
                    onChange={(e) => setConfig(prev => ({ ...prev, includeMessages: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">All Messages</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.includeCitations}
                    onChange={(e) => setConfig(prev => ({ ...prev, includeCitations: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Citations & References</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.includeMetadata}
                    onChange={(e) => setConfig(prev => ({ ...prev, includeMetadata: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Technical Metadata</span>
                </label>
              </div>

              {/* Statistics */}
              <div className="pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Report Statistics</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Messages: {messages.length}</div>
                  <div>Citations: {citations.length}</div>
                  <div>Agents: {new Set(messages.map(m => m.metadata?.agent_role).filter(Boolean)).size}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Preview Panel */}
          <div className="flex-1 p-6 overflow-y-auto">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Preview</h3>
            <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap">
              {generatePreview()}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            Report will be downloaded as {config.format.toUpperCase()} file
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={generateReport}
              disabled={isGenerating || !config.title.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isGenerating ? 'Generating...' : 'Generate Report'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}