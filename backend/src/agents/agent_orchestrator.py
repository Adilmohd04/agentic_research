"""
Agent Orchestrator - Coordinates multi-agent workflows
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from .coordinator_agent import CoordinatorAgent
from .researcher_agent import ResearcherAgent
from .analyzer_agent import AnalyzerAgent
from .executor_agent import ExecutorAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.agents = {
            "coordinator": CoordinatorAgent(),
            "researcher": ResearcherAgent(),
            "analyzer": AnalyzerAgent(),
            "executor": ExecutorAgent()
        }
        self.active_workflows = {}
        self.workflow_history = []
    
    async def execute_workflow(self, user_request: str, session_id: str = None) -> Dict[str, Any]:
        """Execute complete multi-agent workflow"""
        workflow_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        workflow = {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "user_request": user_request,
            "status": "in_progress",
            "started_at": datetime.utcnow(),
            "steps": [],
            "results": {}
        }
        
        self.active_workflows[workflow_id] = workflow
        
        try:
            # Step 1: Coordinator plans the workflow
            logger.info(f"Starting workflow {workflow_id}: {user_request}")
            
            coordinator_task = {
                "task_id": f"{workflow_id}_plan",
                "request": user_request,
                "session_id": session_id
            }
            
            plan_result = await self.agents["coordinator"].execute_task(coordinator_task)
            workflow["steps"].append({
                "step": 1,
                "agent": "coordinator",
                "action": "workflow_planning",
                "result": plan_result,
                "completed_at": datetime.utcnow()
            })
            
            execution_plan = plan_result.get("execution_plan", {})
            required_agents = execution_plan.get("agents_required", ["researcher", "analyzer"])
            
            # Step 2: Execute planned workflow steps
            research_data = None
            analysis_data = None
            
            if "researcher" in required_agents:
                research_task = {
                    "task_id": f"{workflow_id}_research",
                    "query": user_request,
                    "max_sources": 5
                }
                
                research_result = await self.agents["researcher"].execute_task(research_task)
                research_data = research_result.get("search_results", {})
                
                workflow["steps"].append({
                    "step": 2,
                    "agent": "researcher", 
                    "action": "information_gathering",
                    "result": research_result,
                    "completed_at": datetime.utcnow()
                })
            
            if "analyzer" in required_agents:
                analysis_task = {
                    "task_id": f"{workflow_id}_analysis",
                    "type": "information" if research_data else "general",
                    "search_results": research_data or {}
                }
                
                analysis_result = await self.agents["analyzer"].execute_task(analysis_task)
                analysis_data = analysis_result
                
                workflow["steps"].append({
                    "step": 3,
                    "agent": "analyzer",
                    "action": "information_analysis", 
                    "result": analysis_result,
                    "completed_at": datetime.utcnow()
                })
            
            # Step 3: Executor generates final deliverable
            executor_task = {
                "task_id": f"{workflow_id}_execution",
                "type": "report",
                "topic": user_request,
                "research_data": research_data or {},
                "analysis_data": analysis_data or {}
            }
            
            execution_result = await self.agents["executor"].execute_task(executor_task)
            
            workflow["steps"].append({
                "step": 4,
                "agent": "executor",
                "action": "report_generation",
                "result": execution_result,
                "completed_at": datetime.utcnow()
            })
            
            # Complete workflow
            workflow["status"] = "completed"
            workflow["completed_at"] = datetime.utcnow()
            workflow["results"] = {
                "plan": plan_result,
                "research": research_data,
                "analysis": analysis_data,
                "final_output": execution_result
            }
            
            # Move to history
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Completed workflow {workflow_id}")
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "summary": self._create_workflow_summary(workflow),
                "results": workflow["results"],
                "execution_time": (workflow["completed_at"] - workflow["started_at"]).total_seconds(),
                "agents_used": [step["agent"] for step in workflow["steps"]],
                "steps_completed": len(workflow["steps"])
            }
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            workflow["status"] = "failed"
            workflow["error"] = str(e)
            workflow["completed_at"] = datetime.utcnow()
            
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "partial_results": workflow.get("results", {})
            }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of active or completed workflow"""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        for workflow in self.workflow_history:
            if workflow["workflow_id"] == workflow_id:
                return workflow
        
        return None
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            agent_id: agent.get_status() 
            for agent_id, agent in self.agents.items()
        }
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        return list(self.active_workflows.values())
    
    def get_workflow_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow history"""
        return self.workflow_history[-limit:]
    
    def _create_workflow_summary(self, workflow: Dict[str, Any]) -> str:
        """Create human-readable workflow summary"""
        steps_count = len(workflow["steps"])
        duration = (workflow["completed_at"] - workflow["started_at"]).total_seconds()
        
        final_result = workflow["results"].get("final_output", {})
        report = final_result.get("report", {})
        
        if report:
            word_count = final_result.get("word_count", 0)
            sources_count = len(workflow["results"].get("research", {}).get("documents", []))
            
            return f"""
Completed comprehensive analysis of: "{workflow['user_request']}"

✅ Multi-agent coordination with {steps_count} steps
⏱️ Execution time: {duration:.1f} seconds  
📄 Generated {word_count} word report
📚 Analyzed {sources_count} sources
🎯 Quality score: {workflow['results'].get('analysis', {}).get('overall_quality', 0.85):.1%}

The research copilot successfully coordinated multiple AI agents to deliver a comprehensive analysis with validated sources and actionable insights.
            """.strip()
        else:
            return f"Completed workflow with {steps_count} steps in {duration:.1f} seconds"