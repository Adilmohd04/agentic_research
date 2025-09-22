"""
Analyzer Agent - Validates sources and analyzes information
"""

import asyncio
from typing import Dict, Any, List
from .base_agent import BaseAgent

class AnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="analyzer-001",
            role="analyzer",
            capabilities=[
                "source_validation",
                "fact_checking",
                "data_analysis",
                "quality_assessment",
                "code_review"
            ]
        )
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and validate information or code"""
        task_type = task.get("type", "information")
        
        if task_type == "code_analysis":
            return await self._analyze_code(task)
        else:
            return await self._analyze_information(task)
    
    async def _analyze_information(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze research information for quality and accuracy"""
        search_results = task.get("search_results", {})
        documents = search_results.get("documents", [])
        
        # Simulate analysis time
        await asyncio.sleep(1.5)
        
        # Validate sources
        validated_sources = []
        quality_scores = []
        
        for doc in documents:
            validation = await self._validate_source(doc)
            validated_sources.append(validation)
            quality_scores.append(validation["quality_score"])
        
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "action": "information_analyzed",
            "validated_sources": validated_sources,
            "overall_quality": overall_quality,
            "reliability_assessment": self._get_reliability_level(overall_quality),
            "recommendations": self._generate_recommendations(validated_sources),
            "analysis_confidence": 0.91
        }
    
    async def _analyze_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code for quality, security, and optimization"""
        code = task.get("code", "")
        language = task.get("language", "python")
        
        # Simulate code analysis
        await asyncio.sleep(2)
        
        issues = []
        suggestions = []
        
        # Mock code analysis results
        if "def " in code or "function " in code:
            issues.append({
                "type": "documentation",
                "severity": "medium",
                "message": "Function lacks proper documentation",
                "line": 1
            })
            suggestions.append({
                "type": "improvement",
                "message": "Add docstrings to functions for better maintainability"
            })
        
        if "try:" not in code and "except:" not in code:
            issues.append({
                "type": "error_handling",
                "severity": "high", 
                "message": "Missing error handling",
                "line": None
            })
            suggestions.append({
                "type": "security",
                "message": "Add proper error handling and input validation"
            })
        
        return {
            "action": "code_analyzed",
            "language": language,
            "issues_found": len(issues),
            "issues": issues,
            "suggestions": suggestions,
            "code_quality_score": 0.75,
            "security_score": 0.68,
            "maintainability_score": 0.82
        }
    
    async def _validate_source(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual source quality"""
        confidence = document.get("confidence", 0.5)
        source = document.get("source", "Unknown")
        
        # Mock validation logic
        quality_factors = {
            "source_credibility": 0.8 if "Research" in source or "Database" in source else 0.6,
            "content_relevance": document.get("relevance", 0.7),
            "information_freshness": 0.9,  # Mock freshness score
            "citation_quality": confidence
        }
        
        quality_score = sum(quality_factors.values()) / len(quality_factors)
        
        return {
            "document_id": document.get("id"),
            "title": document.get("title"),
            "source": source,
            "quality_score": quality_score,
            "quality_factors": quality_factors,
            "validation_status": "verified" if quality_score > 0.7 else "needs_review"
        }
    
    def _get_reliability_level(self, score: float) -> str:
        """Get reliability level based on quality score"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "high"
        elif score >= 0.7:
            return "good"
        elif score >= 0.6:
            return "moderate"
        else:
            return "low"
    
    def _generate_recommendations(self, validated_sources: List[Dict]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        low_quality_sources = [s for s in validated_sources if s["quality_score"] < 0.7]
        if low_quality_sources:
            recommendations.append(f"Consider additional verification for {len(low_quality_sources)} sources with lower quality scores")
        
        excellent_sources = [s for s in validated_sources if s["quality_score"] >= 0.9]
        if excellent_sources:
            recommendations.append(f"Prioritize information from {len(excellent_sources)} high-quality sources")
        
        recommendations.append("Cross-reference findings with additional sources for comprehensive analysis")
        
        return recommendations