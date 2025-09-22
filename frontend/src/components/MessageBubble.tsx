/**
 * Individual message bubble component
 */

'use client';

import { Message } from '../types/chat';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAgent = message.role === 'agent';

  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(timestamp);
  };

  const getAgentIcon = (agentId?: string) => {
    if (!agentId) return '🤖';
    
    if (agentId.includes('coordinator')) return '📋';
    if (agentId.includes('researcher')) return '🔍';
    if (agentId.includes('analyzer')) return '🔬';
    if (agentId.includes('executor')) return '⚡';
    
    return '🤖';
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-500';
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3xl ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Message Header */}
        <div className={`flex items-center mb-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          {!isUser && (
            <span className="text-lg mr-2">
              {getAgentIcon(message.metadata.agent_id)}
            </span>
          )}
          <span className="text-xs text-gray-500">
            {isUser ? 'You' : (message.metadata.agent_id || 'Assistant')}
          </span>
          <span className="text-xs text-gray-400 ml-2">
            {formatTimestamp(message.timestamp)}
          </span>
          {message.metadata.confidence && (
            <span className={`text-xs ml-2 ${getConfidenceColor(message.metadata.confidence)}`}>
              {(message.metadata.confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>

        {/* Message Content */}
        <div
          className={`px-4 py-3 rounded-lg ${
            isUser
              ? 'bg-blue-600 text-white'
              : isAgent
              ? 'bg-gray-100 text-gray-900 border border-gray-200'
              : 'bg-white text-gray-900 border border-gray-200'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-xs text-gray-500 font-medium">Sources:</p>
            {message.citations.map((citation, index) => (
              <div
                key={citation.id}
                className="p-2 text-xs bg-blue-50 rounded border border-blue-200"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-blue-800">
                    [{index + 1}] {citation.title}
                  </span>
                  <span className="text-blue-600">
                    {(citation.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-blue-700 mt-1">
                  {citation.excerpt}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Metadata (for debugging/development) */}
        {process.env.NODE_ENV === 'development' && message.metadata && (
          <details className="mt-2">
            <summary className="text-xs text-gray-400 cursor-pointer">
              Debug Info
            </summary>
            <pre className="text-xs text-gray-500 mt-1 bg-gray-50 p-2 rounded overflow-x-auto">
              {JSON.stringify(message.metadata, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}