/**
 * Agent status panel component
 */

'use client';

import { useState, useEffect } from 'react';
import { AgentStatus as AgentStatusType, TaskProgress } from '../types/chat';
import { useWebSocket } from '../hooks/useWebSocket';

export default function AgentStatus() {
  const [agents, setAgents] = useState<AgentStatusType[]>([]);
  const [tasks, setTasks] = useState<TaskProgress[]>([]);
  const [systemStats, setSystemStats] = useState({
    totalAgents: 0,
    activeAgents: 0,
    activeTasks: 0
  });

  // WebSocket for real-time agent status updates
  const { isConnected, lastMessage } = useWebSocket('ws://localhost:8000/ws/agent-status');

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage);
        
        if (data.type === 'agent_status_update') {
          const statusData = data.data;
          
          // Update system stats
          setSystemStats({
            totalAgents: statusData.total_agents || 0,
            activeAgents: statusData.active_agents || 0,
            activeTasks: statusData.active_tasks || 0
          });

          // Update agents list
          if (statusData.agents) {
            setAgents(statusData.agents.map((agent: any) => ({
              id: agent.id,
              role: agent.role,
              active: agent.active,
              current_tasks: agent.current_tasks,
              capabilities: agent.capabilities || [],
              last_activity: agent.last_activity ? new Date(agent.last_activity) : undefined
            })));
          }
        } else if (data.type === 'task_progress_update') {
          const taskData = data.data;
          
          setTasks(prev => {
            const existingIndex = prev.findIndex(t => t.task_id === taskData.task_id);
            const newTask: TaskProgress = {
              task_id: taskData.task_id,
              status: taskData.status,
              progress: taskData.progress || 0,
              agent_id: taskData.agent_id,
              description: taskData.description || '',
              started_at: taskData.started_at ? new Date(taskData.started_at) : undefined,
              completed_at: taskData.completed_at ? new Date(taskData.completed_at) : undefined
            };

            if (existingIndex >= 0) {
              const updated = [...prev];
              updated[existingIndex] = newTask;
              return updated;
            } else {
              return [...prev, newTask];
            }
          });
        }
      } catch (error) {
        console.error('Error parsing agent status message:', error);
      }
    }
  }, [lastMessage]);

  // Fetch initial status
  useEffect(() => {
    const fetchInitialStatus = async () => {
      try {
        const response = await fetch('/api/agents/status');
        if (response.ok) {
          const data = await response.json();
          
          setSystemStats({
            totalAgents: data.total_agents || 0,
            activeAgents: data.active_agents || 0,
            activeTasks: data.active_tasks || 0
          });

          if (data.agents) {
            setAgents(data.agents.map((agent: any) => ({
              id: agent.id,
              role: agent.role,
              active: agent.active,
              current_tasks: agent.current_tasks,
              capabilities: agent.capabilities || []
            })));
          }
        }
      } catch (error) {
        console.error('Error fetching initial agent status:', error);
      }
    };

    fetchInitialStatus();
  }, []);

  const getAgentIcon = (role: string) => {
    switch (role) {
      case 'coordinator': return '📋';
      case 'researcher': return '🔍';
      case 'analyzer': return '🔬';
      case 'executor': return '⚡';
      default: return '🤖';
    }
  };

  const getStatusColor = (active: boolean) => {
    return active ? 'text-green-600 bg-green-100' : 'text-gray-500 bg-gray-100';
  };

  const getTaskStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'in_progress': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-100">
      {/* Header */}
      <div className="p-4 bg-white border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
        <div className="flex items-center mt-1">
          <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-500">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* System Stats */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="grid grid-cols-1 gap-3">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{systemStats.activeAgents}</div>
            <div className="text-xs text-gray-500">Active Agents</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{systemStats.activeTasks}</div>
            <div className="text-xs text-gray-500">Active Tasks</div>
          </div>
        </div>
      </div>

      {/* Agents List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Agents</h4>
          
          {agents.length === 0 ? (
            <div className="text-center text-gray-500 py-4">
              <div className="text-2xl mb-2">🤖</div>
              <p className="text-sm">No agents available</p>
            </div>
          ) : (
            <div className="space-y-3">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="bg-white rounded-lg p-3 border border-gray-200 shadow-sm"
                >
                  {/* Agent Header */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getAgentIcon(agent.role)}</span>
                      <div>
                        <div className="font-medium text-sm text-gray-900 capitalize">
                          {agent.role}
                        </div>
                        <div className="text-xs text-gray-500">{agent.id}</div>
                      </div>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.active)}`}>
                      {agent.active ? 'Active' : 'Inactive'}
                    </div>
                  </div>

                  {/* Agent Stats */}
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                    <span>Tasks: {agent.current_tasks}</span>
                    <span>Capabilities: {agent.capabilities.length}</span>
                  </div>

                  {/* Capabilities */}
                  {agent.capabilities.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {agent.capabilities.slice(0, 3).map((capability, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                        >
                          {capability.replace(/_/g, ' ')}
                        </span>
                      ))}
                      {agent.capabilities.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          +{agent.capabilities.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active Tasks */}
        {tasks.length > 0 && (
          <div className="p-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Active Tasks</h4>
            <div className="space-y-2">
              {tasks.filter(task => task.status !== 'completed').map((task) => (
                <div
                  key={task.task_id}
                  className="bg-white rounded-lg p-3 border border-gray-200 shadow-sm"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {task.description || task.task_id}
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${getTaskStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ')}
                    </div>
                  </div>
                  
                  <div className="text-xs text-gray-500 mb-2">
                    Agent: {task.agent_id}
                  </div>

                  {task.status === 'in_progress' && task.progress > 0 && (
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${task.progress}%` }}
                      ></div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}