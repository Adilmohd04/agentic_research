"""
Coordinator Agent - Plans and orchestrates multi-agent workflows
"""

import asyncio
from typing import Dict, Any, List
from .base_agent import BaseAgent

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="coordinator-001",
            role="coordinator",
            capabilities=[
                "task_planning",
                "workflow_orchestration", 
                "agent_coordination",
                "resource_allocation"
            ]
        )
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Plan and coordinate multi-agent workflow"""
        user_request = task.get("request", "")
        
        # Analyze request and create execution plan
        plan = await self._create_execution_plan(user_request)
        
        return {
            "action": "workflow_planned",
            "execution_plan": plan,
            "estimated_duration": plan.get("estimated_duration", 30),
            "agents_required": plan.get("agents_required", []),
            "workflow_steps": plan.get("steps", [])
        }
    
    async def _create_execution_plan(self, request: str) -> Dict[str, Any]:
        """Create detailed execution plan based on user request"""
        request_lower = request.lower()
        
        # Determine task type and required agents
        if any(keyword in request_lower for keyword in ["research", "analyze", "study", "investigate"]):
            return {
                "task_type": "research",
                "agents_required": ["researcher", "analyzer"],
                "estimated_duration": 45,
                "steps": [
                    {
                        "step": 1,
                        "agent": "researcher",
                        "action": "gather_information",
                        "description": "Search knowledge base and external sources"
                    },
                    {
                        "step": 2,
                        "agent": "analyzer", 
                        "action": "validate_sources",
                        "description": "Fact-check and validate information quality"
                    },
                    {
                        "step": 3,
                        "agent": "executor",
                        "action": "generate_report",
                        "description": "Create comprehensive research report"
                    }
                ]
            }
        
        elif any(keyword in request_lower for keyword in ["code", "programming", "debug", "optimize"]):
            return {
                "task_type": "code_analysis",
                "agents_required": ["analyzer", "executor"],
                "estimated_duration": 30,
                "steps": [
                    {
                        "step": 1,
                        "agent": "analyzer",
                        "action": "analyze_code",
                        "description": "Review code structure and identify issues"
                    },
                    {
                        "step": 2,
                        "agent": "executor",
                        "action": "generate_improvements",
                        "description": "Create optimized code suggestions"
                    }
                ]
            }
        
        else:
            return {
                "task_type": "general",
                "agents_required": ["researcher", "analyzer"],
                "estimated_duration": 25,
                "steps": [
                    {
                        "step": 1,
                        "agent": "researcher",
                        "action": "information_gathering",
                        "description": "Collect relevant information"
                    },
                    {
                        "step": 2,
                        "agent": "analyzer",
                        "action": "process_information",
                        "description": "Analyze and synthesize findings"
                    }
                ]
            }