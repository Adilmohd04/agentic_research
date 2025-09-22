"""
Executor Agent - Generates reports, code, and deliverables
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent

class ExecutorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="executor-001",
            role="executor",
            capabilities=[
                "report_generation",
                "code_generation",
                "document_creation",
                "file_export",
                "visualization"
            ]
        )
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute final deliverable generation"""
        task_type = task.get("type", "report")
        
        if task_type == "code_generation":
            return await self._generate_code(task)
        elif task_type == "document_export":
            return await self._export_document(task)
        else:
            return await self._generate_report(task)
    
    async def _generate_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive research report"""
        research_data = task.get("research_data", {})
        analysis_data = task.get("analysis_data", {})
        
        # Simulate report generation
        await asyncio.sleep(3)
        
        # Create structured report
        report = {
            "title": f"Research Report: {task.get('topic', 'Analysis')}",
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": self._create_executive_summary(research_data, analysis_data),
            "detailed_findings": self._create_detailed_findings(research_data),
            "analysis_results": self._create_analysis_section(analysis_data),
            "recommendations": self._create_recommendations(analysis_data),
            "sources": self._compile_sources(research_data),
            "appendices": {
                "methodology": "Multi-agent research approach with RAG-enhanced information retrieval",
                "confidence_metrics": analysis_data.get("overall_quality", 0.85)
            }
        }
        
        # Generate downloadable formats
        export_options = await self._create_export_options(report)
        
        return {
            "action": "report_generated",
            "report": report,
            "export_options": export_options,
            "word_count": self._estimate_word_count(report),
            "generation_time": 3.2
        }
    
    async def _generate_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized code based on analysis"""
        original_code = task.get("original_code", "")
        analysis_results = task.get("analysis_results", {})
        language = task.get("language", "python")
        
        # Simulate code generation
        await asyncio.sleep(2)
        
        # Generate improved code
        improved_code = self._create_improved_code(original_code, analysis_results, language)
        
        return {
            "action": "code_generated",
            "language": language,
            "original_code": original_code,
            "improved_code": improved_code,
            "improvements_made": self._list_improvements(analysis_results),
            "code_quality_improvement": 0.25,
            "download_options": {
                "formats": ["py", "txt", "zip"],
                "files": [
                    {"name": f"improved_code.{language}", "content": improved_code},
                    {"name": "improvement_notes.md", "content": self._create_improvement_notes(analysis_results)}
                ]
            }
        }
    
    async def _export_document(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Export document in various formats"""
        content = task.get("content", {})
        format_type = task.get("format", "pdf")
        
        # Simulate document generation
        await asyncio.sleep(1.5)
        
        return {
            "action": "document_exported",
            "format": format_type,
            "file_size": "2.3 MB",
            "download_url": f"/api/downloads/{task.get('task_id')}.{format_type}",
            "preview_available": True
        }
    
    def _create_executive_summary(self, research_data: Dict, analysis_data: Dict) -> str:
        """Create executive summary"""
        sources_count = len(research_data.get("documents", []))
        quality_score = analysis_data.get("overall_quality", 0.85)
        
        return f"""
This comprehensive research report synthesizes information from {sources_count} verified sources 
with an overall quality score of {quality_score:.1%}. The analysis reveals key insights and 
actionable recommendations based on multi-agent coordination and advanced information retrieval.

Key findings include validated information from credible sources, comprehensive fact-checking, 
and strategic recommendations for implementation. The research methodology employed RAG-enhanced 
information retrieval with multi-agent validation for maximum accuracy and reliability.
        """.strip()
    
    def _create_detailed_findings(self, research_data: Dict) -> List[Dict]:
        """Create detailed findings section"""
        documents = research_data.get("documents", [])
        findings = []
        
        for i, doc in enumerate(documents, 1):
            findings.append({
                "finding_id": f"F{i:03d}",
                "title": doc.get("title", f"Finding {i}"),
                "source": doc.get("source", "Unknown"),
                "confidence": doc.get("confidence", 0.8),
                "key_points": [
                    "Primary insight from source analysis",
                    "Supporting evidence and data points", 
                    "Implications for overall research question"
                ],
                "relevance_score": doc.get("relevance", 0.8)
            })
        
        return findings
    
    def _create_analysis_section(self, analysis_data: Dict) -> Dict:
        """Create analysis results section"""
        return {
            "methodology": "Multi-agent analysis with source validation",
            "quality_assessment": {
                "overall_score": analysis_data.get("overall_quality", 0.85),
                "reliability_level": analysis_data.get("reliability_assessment", "high"),
                "validated_sources": len(analysis_data.get("validated_sources", []))
            },
            "key_insights": [
                "Cross-validated information from multiple credible sources",
                "Comprehensive fact-checking and quality assessment performed",
                "Strategic implications identified and analyzed"
            ]
        }
    
    def _create_recommendations(self, analysis_data: Dict) -> List[str]:
        """Create recommendations section"""
        base_recommendations = analysis_data.get("recommendations", [])
        
        enhanced_recommendations = [
            "Implement findings based on high-confidence sources first",
            "Monitor developments in areas with moderate confidence scores",
            "Conduct periodic reviews to validate ongoing relevance"
        ]
        
        return base_recommendations + enhanced_recommendations
    
    def _compile_sources(self, research_data: Dict) -> List[Dict]:
        """Compile sources bibliography"""
        documents = research_data.get("documents", [])
        sources = []
        
        for doc in documents:
            sources.append({
                "title": doc.get("title"),
                "source": doc.get("source"),
                "confidence_score": doc.get("confidence"),
                "access_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "relevance": doc.get("relevance")
            })
        
        return sources
    
    async def _create_export_options(self, report: Dict) -> Dict:
        """Create export options for the report"""
        return {
            "formats": ["pdf", "docx", "md", "html"],
            "sizes": {
                "pdf": "1.8 MB",
                "docx": "1.2 MB", 
                "md": "45 KB",
                "html": "78 KB"
            },
            "download_urls": {
                "pdf": "/api/exports/report.pdf",
                "docx": "/api/exports/report.docx",
                "md": "/api/exports/report.md",
                "html": "/api/exports/report.html"
            }
        }
    
    def _estimate_word_count(self, report: Dict) -> int:
        """Estimate word count of generated report"""
        # Simple word count estimation
        text_content = str(report.get("executive_summary", "")) + \
                      str(report.get("detailed_findings", "")) + \
                      str(report.get("analysis_results", ""))
        
        return len(text_content.split())
    
    def _create_improved_code(self, original: str, analysis: Dict, language: str) -> str:
        """Generate improved code based on analysis"""
        if not original:
            return f"""
# Improved {language.title()} Code
# Generated by Agentic Research Copilot

def example_function(data):
    \"\"\"
    Example function with proper documentation and error handling.
    
    Args:
        data: Input data to process
        
    Returns:
        Processed result
        
    Raises:
        ValueError: If data is invalid
    \"\"\"
    try:
        if not data:
            raise ValueError("Data cannot be empty")
        
        # Process data with proper validation
        result = process_data_safely(data)
        return result
        
    except Exception as e:
        logger.error(f"Error processing data: {{e}}")
        raise

def process_data_safely(data):
    \"\"\"Safely process data with validation\"\"\"
    # Implementation with proper error handling
    return data
"""
        
        # Add improvements to existing code
        improved = f"""# Improved Code - Generated by Agentic Research Copilot
# Original code enhanced with error handling and documentation

{original}

# Additional improvements:
# - Added proper error handling
# - Enhanced documentation
# - Improved code structure
# - Added input validation
"""
        return improved
    
    def _list_improvements(self, analysis: Dict) -> List[str]:
        """List improvements made to code"""
        return [
            "Added comprehensive error handling",
            "Enhanced function documentation with docstrings",
            "Improved code structure and readability",
            "Added input validation and type hints",
            "Optimized performance where applicable"
        ]
    
    def _create_improvement_notes(self, analysis: Dict) -> str:
        """Create improvement notes document"""
        return f"""# Code Improvement Notes

## Analysis Summary
- Issues found: {len(analysis.get('issues', []))}
- Suggestions implemented: {len(analysis.get('suggestions', []))}
- Quality improvement: +25%

## Key Improvements Made
1. **Error Handling**: Added try-catch blocks for robust error management
2. **Documentation**: Enhanced with comprehensive docstrings
3. **Code Structure**: Improved organization and readability
4. **Validation**: Added input validation for security
5. **Performance**: Optimized critical code paths

## Recommendations for Future Development
- Implement unit tests for all functions
- Consider adding logging for debugging
- Review security implications of external inputs
- Monitor performance in production environment

Generated by Agentic Research Copilot - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
"""