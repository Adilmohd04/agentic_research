/**
 * Live Dashboard - Real-time System Metrics and Analytics
 */

'use client';

import { useState, useEffect } from 'react';

interface SystemMetrics {
  cpu: number;
  memory: number;
  activeAgents: number;
  totalRequests: number;
  responseTime: number;
  successRate: number;
}

interface ActivityLog {
  id: string;
  timestamp: Date;
  type: 'request' | 'response' | 'error' | 'agent_action';
  message: string;
  details?: string;
}

export default function LiveDashboard() {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: 0,
    memory: 0,
    activeAgents: 0,
    totalRequests: 0,
    responseTime: 0,
    successRate: 0
  });

  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  // Simulate real-time metrics
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        cpu: Math.max(10, Math.min(90, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.max(20, Math.min(80, prev.memory + (Math.random() - 0.5) * 5)),
        activeAgents: Math.floor(Math.random() * 4) + 1,
        totalRequests: prev.totalRequests + Math.floor(Math.random() * 3),
        responseTime: Math.max(50, Math.min(500, prev.responseTime + (Math.random() - 0.5) * 50)),
        successRate: Math.max(85, Math.min(100, prev.successRate + (Math.random() - 0.5) * 2))
      }));

      // Add random activity logs
      if (Math.random() > 0.7) {
        const activities = [
          'Voice request processed successfully',
          'Agent coordination initiated',
          'Knowledge base query executed',
          'Real-time analysis completed',
          'Speech synthesis generated',
          'User interaction logged'
        ];

        const newLog: ActivityLog = {
          id: Date.now().toString(),
          timestamp: new Date(),
          type: ['request', 'response', 'agent_action'][Math.floor(Math.random() * 3)] as any,
          message: activities[Math.floor(Math.random() * activities.length)]
        };

        setActivityLogs(prev => [newLog, ...prev.slice(0, 19)]);
      }
    }, 2000);

    setIsConnected(true);

    return () => {
      clearInterval(interval);
      setIsConnected(false);
    };
  }, []);

  const getMetricColor = (value: number, type: 'cpu' | 'memory' | 'responseTime' | 'successRate') => {
    switch (type) {
      case 'cpu':
      case 'memory':
        return value > 70 ? 'text-red-400' : value > 50 ? 'text-yellow-400' : 'text-green-400';
      case 'responseTime':
        return value > 300 ? 'text-red-400' : value > 150 ? 'text-yellow-400' : 'text-green-400';
      case 'successRate':
        return value > 95 ? 'text-green-400' : value > 90 ? 'text-yellow-400' : 'text-red-400';
      default:
        return 'text-white';
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'request':
        return (
          <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
          </svg>
        );
      case 'response':
        return (
          <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'agent_action':
        return (
          <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">
            Live System Dashboard
          </h2>
          <p className="text-white/70">
            Real-time monitoring and analytics
          </p>
        </div>
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
          isConnected ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
          }`}></div>
          <span className="text-sm font-medium">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6 mb-8">
        {/* CPU Usage */}
        <div className="bg-white/10 border border-white/20 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white/70 text-sm font-medium">CPU Usage</h3>
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
          </div>
          <div className={`text-2xl font-bold ${getMetricColor(metrics.cpu, 'cpu')}`}>
            {metrics.cpu.toFixed(1)}%
          </div>
          <div className="w-full bg-white/20 rounded-full h-2 mt-2">
            <div
              className="bg-gradient-to-r from-blue-400 to-cyan-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${metrics.cpu}%` }}
            ></div>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="bg-white/10 border border-white/20 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white/70 text-sm font-medium">Memory</h3>
            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
            </svg>
          </div>
          <div className={`text-2xl font-bold ${getMetricColor(metrics.memory, 'memory')}`}>
            {metrics.memory.toFixed(1)}%
          </div>
          <div className="w-full bg-white/20 rounded-full h-2 mt-2">
            <div
              className="bg-gradient-to-r from-green-400 to-emerald-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${metrics.memory}%` }}
            ></div>
          </div>
        </div>

        {/* Active Agents */}
        <div className="bg-white/10 border border-white/20 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white/70 text-sm font-medium">Active Agents</h3>
            <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <div className="text-2xl font-bold text-purple-400">
            {metrics.activeAgents}
          </div>
          <div className="text-white/60 text-sm mt-2">
            of 4 total
          </div>
        </div>

        {/* Total Requests */}
        <div className="bg-white/10 border border-white/20 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white/70 text-sm font-medium">Requests</h3>
            <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <div className="text-2xl font-bold text-orange-400">
            {metrics.totalRequests}
          </div>
          <div className="text-white/60 text-sm mt-2">
            total processed
          </div>
        </div>

        {/* Response Time */}
        <div className="bg-white/10 border border-white/20 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white/70 text-sm font-medium">Response Time</h3>
            <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className={`text-2xl font-bold ${getMetricColor(metrics.responseTime, 'responseTime')}`}>
            {metrics.responseTime.toFixed(0)}ms
          </div>
          <div className="text-white/60 text-sm mt-2">
            average
          </div>
        </div>

        {/* Success Rate */}
        <div className="bg-white/10 border border-white/20 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white/70 text-sm font-medium">Success Rate</h3>
            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className={`text-2xl font-bold ${getMetricColor(metrics.successRate, 'successRate')}`}>
            {metrics.successRate.toFixed(1)}%
          </div>
          <div className="w-full bg-white/20 rounded-full h-2 mt-2">
            <div
              className="bg-gradient-to-r from-green-400 to-emerald-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${metrics.successRate}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Activity Feed */}
      <div className="bg-white/10 border border-white/20 rounded-xl p-6">
        <h3 className="text-white font-semibold text-lg mb-4 flex items-center">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Live Activity Feed
        </h3>
        
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {activityLogs.length === 0 ? (
            <div className="text-center py-8 text-white/50">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              <p>Waiting for activity...</p>
            </div>
          ) : (
            activityLogs.map((log) => (
              <div
                key={log.id}
                className="flex items-start space-x-3 p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
              >
                <div className="flex-shrink-0 mt-1">
                  {getActivityIcon(log.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm">{log.message}</p>
                  {log.details && (
                    <p className="text-white/60 text-xs mt-1">{log.details}</p>
                  )}
                </div>
                <div className="flex-shrink-0">
                  <span className="text-white/50 text-xs">
                    {log.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* System Status */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/10 border border-white/20 rounded-xl p-6">
          <h4 className="text-white font-medium mb-3">System Health</h4>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">API Server</span>
              <span className="text-green-400 text-sm">Online</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Voice Processing</span>
              <span className="text-green-400 text-sm">Active</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Agent System</span>
              <span className="text-green-400 text-sm">Running</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Knowledge Base</span>
              <span className="text-green-400 text-sm">Ready</span>
            </div>
          </div>
        </div>

        <div className="bg-white/10 border border-white/20 rounded-xl p-6">
          <h4 className="text-white font-medium mb-3">Performance</h4>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Uptime</span>
              <span className="text-white text-sm">99.9%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Avg Response</span>
              <span className="text-white text-sm">{metrics.responseTime.toFixed(0)}ms</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Throughput</span>
              <span className="text-white text-sm">150 req/min</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Error Rate</span>
              <span className="text-white text-sm">0.1%</span>
            </div>
          </div>
        </div>

        <div className="bg-white/10 border border-white/20 rounded-xl p-6">
          <h4 className="text-white font-medium mb-3">Resources</h4>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">CPU Cores</span>
              <span className="text-white text-sm">8 cores</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Memory</span>
              <span className="text-white text-sm">16 GB</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Storage</span>
              <span className="text-white text-sm">500 GB</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-white/70 text-sm">Network</span>
              <span className="text-white text-sm">1 Gbps</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}