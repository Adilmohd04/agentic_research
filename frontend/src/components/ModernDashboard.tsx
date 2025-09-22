/**
 * Modern Analytics Dashboard with 2025 Design
 */

'use client';

import { useState, useEffect } from 'react';
import { AgentStatus, TaskProgress } from '../types/chat';

export default function ModernDashboard() {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [tasks, setTasks] = useState<TaskProgress[]>([]);
  const [stats, setStats] = useState({
    totalTasks: 0,
    completedTasks: 0,
    activeAgents: 0,
    avgResponseTime: 0
  });

  // Mock data for demo
  useEffect(() => {
    const mockAgents: AgentStatus[] = [
      {
        id: 'researcher',
        role: 'Research Agent',
        active: true,
        current_tasks: 2,
        capabilities: ['web_search', 'document_analysis', 'data_extraction'],
        last_activity: new Date()
      },
      {
        id: 'analyzer',
        role: 'Data Analyzer',
        active: true,
        current_tasks: 1,
        capabilities: ['statistical_analysis', 'pattern_recognition', 'visualization'],
        last_activity: new Date()
      },
      {
        id: 'writer',
        role: 'Content Writer',
        active: false,
        current_tasks: 0,
        capabilities: ['content_generation', 'summarization', 'translation'],
        last_activity: new Date(Date.now() - 300000)
      }
    ];

    const mockTasks: TaskProgress[] = [
      {
        task_id: 'task_001',
        status: 'in_progress',
        progress: 75,
        agent_id: 'researcher',
        description: 'Analyzing market trends for Q4 2024',
        started_at: new Date(Date.now() - 120000)
      },
      {
        task_id: 'task_002',
        status: 'completed',
        progress: 100,
        agent_id: 'analyzer',
        description: 'Statistical analysis of user behavior',
        started_at: new Date(Date.now() - 300000),
        completed_at: new Date(Date.now() - 60000)
      },
      {
        task_id: 'task_003',
        status: 'pending',
        progress: 0,
        agent_id: 'writer',
        description: 'Generate executive summary report'
      }
    ];

    setAgents(mockAgents);
    setTasks(mockTasks);
    setStats({
      totalTasks: 15,
      completedTasks: 12,
      activeAgents: 2,
      avgResponseTime: 2.3
    });
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'from-green-500 to-emerald-500';
      case 'in_progress': return 'from-blue-500 to-cyan-500';
      case 'pending': return 'from-yellow-500 to-orange-500';
      case 'failed': return 'from-red-500 to-pink-500';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  const getAgentIcon = (role: string) => {
    switch (role.toLowerCase()) {
      case 'research agent': return '🔍';
      case 'data analyzer': return '📊';
      case 'content writer': return '✍️';
      default: return '🤖';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
          <p className="text-gray-300">Real-time monitoring of AI agents and tasks</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl text-white font-medium hover:scale-105 transition-transform">
            📊 Export Report
          </button>
          <button className="px-4 py-2 bg-white/10 backdrop-blur-xl border border-white/20 rounded-xl text-white font-medium hover:bg-white/20 transition-colors">
            ⚙️ Settings
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-sm">Total Tasks</p>
              <p className="text-3xl font-bold text-white">{stats.totalTasks}</p>
            </div>
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
              <span className="text-2xl">📋</span>
            </div>
          </div>
          <div className="mt-4 flex items-center text-green-400 text-sm">
            <span>↗️ +12% from last week</span>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-sm">Completed</p>
              <p className="text-3xl font-bold text-white">{stats.completedTasks}</p>
            </div>
            <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
              <span className="text-2xl">✅</span>
            </div>
          </div>
          <div className="mt-4 flex items-center text-green-400 text-sm">
            <span>↗️ 80% success rate</span>
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-sm">Active Agents</p>
              <p className="text-3xl font-bold text-white">{stats.activeAgents}</p>
            </div>
            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
          </div>
          <div className="mt-4 flex items-center text-green-400 text-sm">
            <span>🟢 All systems operational</span>
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-500/20 to-red-500/20 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-sm">Avg Response</p>
              <p className="text-3xl font-bold text-white">{stats.avgResponseTime}s</p>
            </div>
            <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
              <span className="text-2xl">⚡</span>
            </div>
          </div>
          <div className="mt-4 flex items-center text-green-400 text-sm">
            <span>↘️ -0.5s improvement</span>
          </div>
        </div>
      </div>

      {/* Agents and Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Agents */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center">
            <span className="mr-2">🤖</span>
            Active Agents
          </h2>
          <div className="space-y-4">
            {agents.map((agent) => (
              <div key={agent.id} className="bg-white/5 rounded-xl p-4 border border-white/10">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <span className="text-lg">{getAgentIcon(agent.role)}</span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">{agent.role}</h3>
                      <p className="text-sm text-gray-300">{agent.id}</p>
                    </div>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${agent.active ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`}></div>
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-300">Current Tasks: {agent.current_tasks}</span>
                  <span className="text-gray-400">
                    {agent.last_activity ? new Date(agent.last_activity).toLocaleTimeString() : 'Never'}
                  </span>
                </div>
                
                <div className="mt-3">
                  <p className="text-xs text-gray-400 mb-2">Capabilities:</p>
                  <div className="flex flex-wrap gap-1">
                    {agent.capabilities.map((cap, idx) => (
                      <span key={idx} className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded-lg">
                        {cap.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Tasks */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center">
            <span className="mr-2">📋</span>
            Recent Tasks
          </h2>
          <div className="space-y-4">
            {tasks.map((task) => (
              <div key={task.task_id} className="bg-white/5 rounded-xl p-4 border border-white/10">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-white text-sm">{task.description}</h3>
                  <span className={`px-2 py-1 rounded-lg text-xs font-medium bg-gradient-to-r ${getStatusColor(task.status)} text-white`}>
                    {task.status.replace('_', ' ')}
                  </span>
                </div>
                
                <div className="mb-3">
                  <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                    <span>Progress</span>
                    <span>{task.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full bg-gradient-to-r ${getStatusColor(task.status)} transition-all duration-500`}
                      style={{ width: `${task.progress}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Agent: {task.agent_id}</span>
                  <span>
                    {task.started_at ? new Date(task.started_at).toLocaleTimeString() : 'Not started'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Chart Placeholder */}
      <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center">
          <span className="mr-2">📈</span>
          Performance Metrics
        </h2>
        <div className="h-64 flex items-center justify-center bg-white/5 rounded-xl border border-white/10">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
              <span className="text-2xl">📊</span>
            </div>
            <p className="text-gray-300">Performance charts coming soon...</p>
            <p className="text-sm text-gray-400 mt-2">Real-time analytics and visualizations</p>
          </div>
        </div>
      </div>
    </div>
  );
}