/**
 * Agent Orchestrator - Live Multi-Agent Visualization
 * Shows real-time agent coordination and task execution
 */

'use client';

import { useState, useEffect, useRef } from 'react';

interface AgentOrchestratorProps {
  sessionId: string;
}

interface Agent {
  id: string;
  name: string;
  role: string;
  status: 'idle' | 'thinking' | 'working' | 'completed' | 'error';
  currentTask?: string;
  progress: number;
  avatar: string;
  color: string;
}

interface Task {
  id: string;
  description: string;
  assignedAgent: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  result?: string;
  timestamp: Date;
}

export default function AgentOrchestrator({ sessionId }: AgentOrchestratorProps) {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'coordinator',
      name: 'Coordinator',
      role: 'Task Manager & Orchestrator',
      status: 'idle',
      progress: 0,
      avatar: '🎯',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      id: 'researcher',
      name: 'Researcher',
      role: 'Information Gathering & Analysis',
      status: 'idle',
      progress: 0,
      avatar: '🔍',
      color: 'from-green-500 to-emerald-500'
    },
    {
      id: 'analyzer',
      name: 'Analyzer',
      role: 'Data Processing & Insights',
      status: 'idle',
      progress: 0,
      avatar: '📊',
      color: 'from-purple-500 to-violet-500'
    },
    {
      id: 'executor',
      name: 'Executor',
      role: 'Code Generation & Implementation',
      status: 'idle',
      progress: 0,
      avatar: '⚡',
      color: 'from-orange-500 to-red-500'
    }
  ]);

  const [tasks, setTasks] = useState<Task[]>([]);
  const [currentWorkflow, setCurrentWorkflow] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [workflowResults, setWorkflowResults] = useState<string>('');
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        wsRef.current = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
        
        wsRef.current.onopen = () => {
          console.log('WebSocket connected');
        };

        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'agent_status_update') {
            updateAgentStatus(data.data);
          } else if (data.type === 'task_update') {
            updateTaskStatus(data.data);
          } else if (data.type === 'workflow_complete') {
            setWorkflowResults(data.data.results);
            setIsProcessing(false);
          }
        };

        wsRef.current.onclose = () => {
          console.log('WebSocket disconnected');
          // Reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId]);

  const updateAgentStatus = (agentData: any) => {
    setAgents(prev => prev.map(agent => {
      if (agentData[agent.id]) {
        return {
          ...agent,
          status: agentData[agent.id].status,
          currentTask: agentData[agent.id].current_task,
          progress: agentData[agent.id].progress || 0
        };
      }
      return agent;
    }));
  };

  const updateTaskStatus = (taskData: any) => {
    setTasks(prev => {
      const existingTask = prev.find(t => t.id === taskData.id);
      if (existingTask) {
        return prev.map(t => t.id === taskData.id ? { ...t, ...taskData } : t);
      } else {
        return [...prev, { ...taskData, timestamp: new Date() }];
      }
    });
  };

  const executeWorkflow = async () => {
    if (!userInput.trim() || isProcessing) return;

    setIsProcessing(true);
    setCurrentWorkflow(userInput);
    setWorkflowResults('');
    setTasks([]);

    // Simulate agent coordination
    simulateAgentWorkflow(userInput);

    try {
      const response = await fetch('http://localhost:8000/api/agents/coordinate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task: userInput,
          context: { 
            session_id: sessionId,
            real_time_updates: true
          },
          agents: ['coordinator', 'researcher', 'analyzer', 'executor']
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();
      setWorkflowResults(result.results?.summary || result.summary || 'Workflow completed successfully!');

    } catch (error) {
      setWorkflowResults(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
      // Reset agents to idle after completion
      setTimeout(() => {
        setAgents(prev => prev.map(agent => ({ ...agent, status: 'idle', progress: 0, currentTask: undefined })));
      }, 2000);
    }
  };

  const simulateAgentWorkflow = (task: string) => {
    const workflow = [
      { agent: 'coordinator', task: 'Analyzing task and creating execution plan', delay: 1000 },
      { agent: 'researcher', task: 'Gathering relevant information and data', delay: 2000 },
      { agent: 'analyzer', task: 'Processing data and generating insights', delay: 1500 },
      { agent: 'executor', task: 'Implementing solution and generating output', delay: 2500 }
    ];

    workflow.forEach((step, index) => {
      setTimeout(() => {
        setAgents(prev => prev.map(agent => {
          if (agent.id === step.agent) {
            return { ...agent, status: 'working', currentTask: step.task, progress: 0 };
          }
          return agent;
        }));

        // Simulate progress
        const progressInterval = setInterval(() => {
          setAgents(prev => prev.map(agent => {
            if (agent.id === step.agent && agent.status === 'working') {
              const newProgress = Math.min(agent.progress + 10, 100);
              if (newProgress === 100) {
                clearInterval(progressInterval);
                return { ...agent, status: 'completed', progress: 100 };
              }
              return { ...agent, progress: newProgress };
            }
            return agent;
          }));
        }, step.delay / 10);

      }, index * 1000);
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'text-gray-400';
      case 'thinking': return 'text-yellow-400';
      case 'working': return 'text-blue-400';
      case 'completed': return 'text-green-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'idle':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        );
      case 'thinking':
        return (
          <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case 'working':
        return (
          <svg className="w-4 h-4 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'completed':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
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
          AI Agent Orchestrator
        </h2>
        <p className="text-white/70">
          Watch multiple AI agents collaborate in real-time
        </p>
      </div>

      {/* Task Input */}
      <div className="mb-8">
        <div className="flex space-x-4">
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Enter a complex task for the agents to handle..."
            className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && executeWorkflow()}
          />
          <button
            onClick={executeWorkflow}
            disabled={!userInput.trim() || isProcessing}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isProcessing ? 'Processing...' : 'Execute'}
          </button>
        </div>
      </div>

      {/* Current Workflow */}
      {currentWorkflow && (
        <div className="mb-8 p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
          <h3 className="text-blue-300 font-medium mb-2">Current Workflow:</h3>
          <p className="text-white">{currentWorkflow}</p>
        </div>
      )}

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className={`p-6 bg-white/10 border border-white/20 rounded-xl transition-all duration-300 ${
              agent.status === 'working' ? 'ring-2 ring-blue-400 shadow-lg shadow-blue-400/20' : ''
            }`}
          >
            {/* Agent Avatar */}
            <div className={`w-16 h-16 mx-auto mb-4 bg-gradient-to-r ${agent.color} rounded-full flex items-center justify-center text-2xl shadow-lg`}>
              {agent.avatar}
            </div>

            {/* Agent Info */}
            <div className="text-center mb-4">
              <h3 className="text-white font-semibold text-lg">{agent.name}</h3>
              <p className="text-white/60 text-sm">{agent.role}</p>
            </div>

            {/* Status */}
            <div className={`flex items-center justify-center space-x-2 mb-3 ${getStatusColor(agent.status)}`}>
              {getStatusIcon(agent.status)}
              <span className="text-sm font-medium capitalize">{agent.status}</span>
            </div>

            {/* Progress Bar */}
            {agent.status === 'working' && (
              <div className="mb-3">
                <div className="w-full bg-white/20 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-400 to-purple-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${agent.progress}%` }}
                  ></div>
                </div>
                <p className="text-xs text-white/60 mt-1 text-center">{agent.progress}%</p>
              </div>
            )}

            {/* Current Task */}
            {agent.currentTask && (
              <div className="text-xs text-white/70 text-center">
                <p className="italic">"{agent.currentTask}"</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Workflow Results */}
      {workflowResults && (
        <div className="mb-8 p-6 bg-green-500/20 border border-green-500/30 rounded-lg">
          <h3 className="text-green-300 font-medium mb-3 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Workflow Results:
          </h3>
          <div className="text-white whitespace-pre-wrap">{workflowResults}</div>
        </div>
      )}

      {/* Task History */}
      {tasks.length > 0 && (
        <div className="bg-white/5 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4">Task Execution History</h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {tasks.map((task) => (
              <div
                key={task.id}
                className={`p-3 rounded-lg border-l-4 ${
                  task.status === 'completed' ? 'bg-green-500/20 border-green-400' :
                  task.status === 'in_progress' ? 'bg-blue-500/20 border-blue-400' :
                  task.status === 'failed' ? 'bg-red-500/20 border-red-400' :
                  'bg-gray-500/20 border-gray-400'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-white/70 text-xs font-medium">
                    {agents.find(a => a.id === task.assignedAgent)?.name || task.assignedAgent}
                  </span>
                  <span className="text-white/50 text-xs">
                    {task.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-white text-sm">{task.description}</p>
                {task.result && (
                  <p className="text-white/70 text-xs mt-2 italic">{task.result}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-8 p-4 bg-white/5 rounded-lg">
        <h4 className="text-white font-medium mb-2">How Agent Orchestration Works:</h4>
        <ul className="text-white/70 text-sm space-y-1">
          <li>• <strong>Coordinator:</strong> Breaks down complex tasks and manages workflow</li>
          <li>• <strong>Researcher:</strong> Gathers information and conducts analysis</li>
          <li>• <strong>Analyzer:</strong> Processes data and generates insights</li>
          <li>• <strong>Executor:</strong> Implements solutions and generates code</li>
        </ul>
      </div>
    </div>
  );
}