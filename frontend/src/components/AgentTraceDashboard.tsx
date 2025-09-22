/**
 * Agent trace dashboard showing coordination steps and task flow
 */

'use client';

import { useState, useEffect } from 'react';
import { AgentStatus, TaskProgress } from '../types/chat';
import { useWebSocket } from '../hooks/useWebSocket';

interface WorkflowStep {
  id: string;
  agent: string;
  action: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  timestamp: Date;
  duration?: number;
  result?: any;
}

interface ActiveWorkflow {
  id: string;
  type: string;
  description: string;
  status: string;
  steps: WorkflowStep[];
  startedAt: Date;
  completedAt?: Date;
}

export default function AgentTraceDashboard() {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [workflows, setWorkflows] = useState<ActiveWorkflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [systemMetrics, setSystemMetrics] = useState({
    totalTasks: 0,
    completedTasks: 0,
    failedTasks: 0,
    averageResponseTime: 0
  });

  // WebSocket connections for real-time updates
  const { lastMessage: agentMessage } = useWebSocket('ws://localhost:8000/ws/agent-status');
  const { lastMessage: taskMessage } = useWebSocket('ws://localhost:8000/ws/task-progress');

  // Handle agent status updates
  useEffect(() => {
    if (agentMessage) {
      try {
        const data = JSON.parse(agentMessage);
        if (data.type === 'agent_status_update' && data.data.agents) {
          setAgents(data.data.agents.map((agent: any) => ({
            id: agent.id,
            role: agent.role,
            active: agent.active,
            current_tasks: agent.current_tasks,
            capabilities: agent.capabilities || []
          })));
        }
      } catch (error) {
        console.error('Error parsing agent message:', error);
      }
    }
  }, [agentMessage]);

  // Handle task progress updates
  useEffect(() => {
    if (taskMessage) {
      try {
        const data = JSON.parse(taskMessage);
        if (data.type === 'task_progress_update') {
          const taskData = data.data;
          
          // Update or create workflow
          setWorkflows(prev => {
            const workflowId = taskData.workflow_id || taskData.task_id;
            const existingIndex = prev.findIndex(w => w.id === workflowId);
            
            const step: WorkflowStep = {
              id: `${taskData.task_id}_${Date.now()}`,
              agent: taskData.agent_id,
              action: taskData.description || taskData.action || 'Processing',
              status: taskData.status,
              timestamp: new Date(),
              duration: taskData.duration,
              result: taskData.result
            };

            if (existingIndex >= 0) {
              const updated = [...prev];
              updated[existingIndex].steps.push(step);
              updated[existingIndex].status = taskData.workflow_status || taskData.status;
              if (taskData.status === 'completed') {
                updated[existingIndex].completedAt = new Date();
              }
              return updated;
            } else {
              const newWorkflow: ActiveWorkflow = {
                id: workflowId,
                type: taskData.workflow_type || 'task',
                description: taskData.description || `Task ${taskData.task_id}`,
                status: taskData.status,
                steps: [step],
                startedAt: new Date()
              };
              return [...prev, newWorkflow];
            }
          });
        }
      } catch (error) {
        console.error('Error parsing task message:', error);
      }
    }
  }, [taskMessage]);

  // Fetch initial data
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // Fetch agent status
        const agentResponse = await fetch('/api/agents/status');
        if (agentResponse.ok) {
          const agentData = await agentResponse.json();
          if (agentData.agents) {
            setAgents(agentData.agents);
          }
        }

        // Fetch system metrics (mock data for now)
        setSystemMetrics({
          totalTasks: 156,
          completedTasks: 142,
          failedTasks: 3,
          averageResponseTime: 2.3
        });

        // Create sample workflow for demonstration
        const sampleWorkflow: ActiveWorkflow = {
          id: 'demo-workflow-1',
          type: 'research',
          description: 'Research AI trends in healthcare',
          status: 'completed',
          startedAt: new Date(Date.now() - 300000), // 5 minutes ago
          completedAt: new Date(Date.now() - 60000), // 1 minute ago
          steps: [
            {
              id: 'step-1',
              agent: 'coordinator-001',
              action: 'Planning research strategy',
              status: 'completed',
              timestamp: new Date(Date.now() - 300000),
              duration: 2.1
            },
            {
              id: 'step-2',
              agent: 'researcher-001',
              action: 'Gathering information from knowledge base',
              status: 'completed',
              timestamp: new Date(Date.now() - 240000),
              duration: 15.3
            },
            {
              id: 'step-3',
              agent: 'analyzer-001',
              action: 'Validating sources and fact-checking',
              status: 'completed',
              timestamp: new Date(Date.now() - 180000),
              duration: 8.7
            },
            {
              id: 'step-4',
              agent: 'executor-001',
              action: 'Generating comprehensive report',
              status: 'completed',
              timestamp: new Date(Date.now() - 120000),
              duration: 12.4
            }
          ]
        };

        setWorkflows([sampleWorkflow]);
      } catch (error) {
        console.error('Error fetching initial data:', error);
      }
    };

    fetchInitialData();
  }, []);

  const getAgentIcon = (agentId: string) => {
    if (agentId.includes('coordinator')) return '📋';
    if (agentId.includes('researcher')) return '🔍';
    if (agentId.includes('analyzer')) return '🔬';
    if (agentId.includes('executor')) return '⚡';
    return '🤖';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'in_progress': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    return `${seconds.toFixed(1)}s`;
  };

  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(timestamp);
  };

  const selectedWorkflowData = workflows.find(w => w.id === selectedWorkflow);

  return (
    <div className="h-full flex bg-gray-50">
      {/* Left Panel - Workflows List */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Agent Workflows</h2>
          <p className="text-sm text-gray-500 mt-1">Real-time multi-agent coordination</p>
        </div>

        {/* System Metrics */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-lg font-bold text-blue-600">{systemMetrics.totalTasks}</div>
              <div className="text-xs text-gray-500">Total Tasks</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-green-600">{systemMetrics.completedTasks}</div>
              <div className="text-xs text-gray-500">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-red-600">{systemMetrics.failedTasks}</div>
              <div className="text-xs text-gray-500">Failed</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-purple-600">{systemMetrics.averageResponseTime}s</div>
              <div className="text-xs text-gray-500">Avg Time</div>
            </div>
          </div>
        </div>

        {/* Workflows List */}
        <div className="flex-1 overflow-y-auto">
          {workflows.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <div className="text-4xl mb-2">🔄</div>
              <p>No active workflows</p>
              <p className="text-sm mt-1">Start a conversation to see agent coordination</p>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {workflows.map((workflow) => (
                <div
                  key={workflow.id}
                  onClick={() => setSelectedWorkflow(workflow.id)}
                  className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                    selectedWorkflow === workflow.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-sm text-gray-900">{workflow.description}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(workflow.status)}`}>
                      {workflow.status}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{workflow.type} workflow</span>
                    <span>{workflow.steps.length} steps</span>
                  </div>
                  
                  <div className="text-xs text-gray-400 mt-1">
                    Started: {formatTimestamp(workflow.startedAt)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel - Workflow Details */}
      <div className="flex-1 flex flex-col">
        {selectedWorkflowData ? (
          <>
            {/* Workflow Header */}
            <div className="p-6 border-b border-gray-200 bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {selectedWorkflowData.description}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {selectedWorkflowData.type} workflow • {selectedWorkflowData.steps.length} steps
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedWorkflowData.status)}`}>
                  {selectedWorkflowData.status}
                </span>
              </div>
              
              <div className="mt-4 flex items-center space-x-6 text-sm text-gray-500">
                <span>Started: {formatTimestamp(selectedWorkflowData.startedAt)}</span>
                {selectedWorkflowData.completedAt && (
                  <span>Completed: {formatTimestamp(selectedWorkflowData.completedAt)}</span>
                )}
                <span>
                  Duration: {selectedWorkflowData.completedAt 
                    ? `${((selectedWorkflowData.completedAt.getTime() - selectedWorkflowData.startedAt.getTime()) / 1000).toFixed(1)}s`
                    : 'In progress'
                  }
                </span>
              </div>
            </div>

            {/* Workflow Steps */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
                {selectedWorkflowData.steps.map((step, index) => (
                  <div key={step.id} className="flex items-start space-x-4">
                    {/* Timeline */}
                    <div className="flex flex-col items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                        step.status === 'completed' ? 'bg-green-100 text-green-600' :
                        step.status === 'in_progress' ? 'bg-blue-100 text-blue-600' :
                        step.status === 'failed' ? 'bg-red-100 text-red-600' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {getAgentIcon(step.agent)}
                      </div>
                      {index < selectedWorkflowData.steps.length - 1 && (
                        <div className="w-0.5 h-12 bg-gray-200 mt-2"></div>
                      )}
                    </div>

                    {/* Step Content */}
                    <div className="flex-1 min-w-0">
                      <div className="bg-white rounded-lg border border-gray-200 p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{step.action}</h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(step.status)}`}>
                            {step.status}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                          <span>Agent: {step.agent}</span>
                          <span>Time: {formatTimestamp(step.timestamp)}</span>
                          <span>Duration: {formatDuration(step.duration)}</span>
                        </div>

                        {step.result && (
                          <details className="mt-3">
                            <summary className="text-sm text-blue-600 cursor-pointer">
                              View Result
                            </summary>
                            <pre className="text-xs text-gray-600 mt-2 bg-gray-50 p-2 rounded overflow-x-auto">
                              {JSON.stringify(step.result, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-white">
            <div className="text-center text-gray-500">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-lg font-medium mb-2">Select a Workflow</h3>
              <p className="text-sm">Choose a workflow from the left panel to see detailed agent coordination steps</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}