/**
 * Agent status indicator component
 */

'use client';

import { useState, useEffect } from 'react';

interface AgentStatus {
  total_agents: number;
  active_agents: number;
  active_tasks: number;
  agents: Array<{
    id: string;
    role: string;
    active: boolean;
    current_tasks: number;
    capabilities: string[];
  }>;
}

export default function AgentStatusIndicator() {
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

  useEffect(() => {
    const connectToAgentStatus = () => {
      const ws = new WebSocket(`${WS_BASE}/ws/agent-status`);

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'agent_status_update') {
            setAgentStatus(data.data);
          }
        } catch (error) {
          console.error('Error parsing agent status:', error);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Reconnect after 5 seconds
        setTimeout(connectToAgentStatus, 5000);
      };

      ws.onerror = (error) => {
        console.error('Agent status WebSocket error:', error);
      };

      return ws;
    };

    const ws = connectToAgentStatus();

    return () => {
      ws.close();
    };
  }, []);

  // Get agent role info
  const getAgentInfo = (role: string) => {
    switch (role) {
      case 'coordinator':
        return { emoji: '📋', color: 'text-blue-600', name: 'Coordinator' };
      case 'researcher':
        return { emoji: '🔍', color: 'text-green-600', name: 'Researcher' };
      case 'analyzer':
        return { emoji: '🔬', color: 'text-purple-600', name: 'Analyzer' };
      case 'executor':
        return { emoji: '⚡', color: 'text-orange-600', name: 'Executor' };
      default:
        return { emoji: '🤖', color: 'text-gray-600', name: 'Agent' };
    }
  };

  if (!agentStatus) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
        <span className="text-sm">Loading agents...</span>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Status Indicator */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center space-x-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
      >
        <div className="flex items-center space-x-1">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm font-medium text-gray-700">
            {agentStatus.active_agents}/{agentStatus.total_agents} Agents
          </span>
        </div>
        
        {agentStatus.active_tasks > 0 && (
          <div className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
            {agentStatus.active_tasks} tasks
          </div>
        )}

        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded Status Panel */}
      {isExpanded && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Agent Status</h3>
            <p className="text-sm text-gray-600">
              Multi-agent system coordination
            </p>
          </div>

          <div className="p-4">
            {/* Overall Stats */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {agentStatus.total_agents}
                </div>
                <div className="text-xs text-gray-600">Total Agents</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {agentStatus.active_agents}
                </div>
                <div className="text-xs text-gray-600">Active</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {agentStatus.active_tasks}
                </div>
                <div className="text-xs text-gray-600">Tasks</div>
              </div>
            </div>

            {/* Individual Agents */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-gray-900">Individual Agents</h4>
              {agentStatus.agents.map((agent) => {
                const agentInfo = getAgentInfo(agent.role);
                
                return (
                  <div
                    key={agent.id}
                    className={`p-3 rounded-lg border ${
                      agent.active ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{agentInfo.emoji}</span>
                        <div>
                          <div className={`text-sm font-medium ${agentInfo.color}`}>
                            {agentInfo.name}
                          </div>
                          <div className="text-xs text-gray-500">
                            {agent.id}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${
                          agent.active ? 'bg-green-500' : 'bg-gray-400'
                        }`} />
                        <span className="text-xs text-gray-600">
                          {agent.active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>

                    {agent.current_tasks > 0 && (
                      <div className="text-xs text-gray-600 mb-2">
                        Current tasks: {agent.current_tasks}
                      </div>
                    )}

                    <div className="flex flex-wrap gap-1">
                      {agent.capabilities.slice(0, 3).map((capability) => (
                        <span
                          key={capability}
                          className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                        >
                          {capability.replace('_', ' ')}
                        </span>
                      ))}
                      {agent.capabilities.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          +{agent.capabilities.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Footer */}
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
              <div className="flex items-center space-x-1">
                <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isExpanded && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsExpanded(false)}
        />
      )}
    </div>
  );
}