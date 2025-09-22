"""
Researcher Agent - Gathers information using RAG system
"""

import asyncio
from typing import Dict, Any, List
from .base_agent import BaseAgent

class ResearcherAgent(BaseAgent):
    def __init__(self, rag_system=None):
        super().__init__(
            agent_id="researcher-001",
            role="researcher",
            capabilities=[
                "information_retrieval",
                "knowledge_base_search",
                "source_gathering",
                "context_analysis"
            ]
        )
        self.rag_system = rag_system
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Research information using RAG system"""
        query = task.get("query", task.get("request", ""))
        max_sources = task.get("max_sources", 5)
        
        # Simulate RAG search with realistic delay
        await asyncio.sleep(2)
        
        # Get information from RAG system
        if self.rag_system:
            search_results = await self.rag_system.search(query, max_sources)
        else:
            search_results = await self._mock_rag_search(query, max_sources)
        
        return {
            "action": "information_gathered",
            "query": query,
            "sources_found": len(search_results.get("documents", [])),
            "search_results": search_results,
            "confidence_score": search_results.get("confidence", 0.85),
            "processing_time": 2.1
        }
    
    async def _mock_rag_search(self, query: str, max_sources: int) -> Dict[str, Any]:
        """Mock RAG search for demonstration"""
        query_lower = query.lower()
        
        # Generate relevant mock results based on query
        if "machine learning" in query_lower or "ml" in query_lower:
            documents = [
                {
                    "id": "ml_001",
                    "title": "Introduction to Machine Learning",
                    "content": "Machine learning is a subset of AI that enables computers to learn without explicit programming...",
                    "source": "ML Research Database",
                    "confidence": 0.95,
                    "relevance": 0.92
                },
                {
                    "id": "ml_002", 
                    "title": "Deep Learning Fundamentals",
                    "content": "Deep learning uses neural networks with multiple layers to model complex patterns...",
                    "source": "AI Knowledge Base",
                    "confidence": 0.89,
                    "relevance": 0.87
                }
            ]
        elif "quantum" in query_lower:
            documents = [
                {
                    "id": "quantum_001",
                    "title": "Quantum Computing Principles",
                    "content": "Quantum computing leverages quantum mechanics to process information...",
                    "source": "Quantum Research Papers",
                    "confidence": 0.93,
                    "relevance": 0.91
                }
            ]
        elif "blockchain" in query_lower:
            documents = [
                {
                    "id": "blockchain_001",
                    "title": "Blockchain Technology Overview",
                    "content": "Blockchain is a distributed ledger technology that maintains records...",
                    "source": "Crypto Technology Database",
                    "confidence": 0.88,
                    "relevance": 0.85
                }
            ]
        else:
            documents = [
                {
                    "id": "general_001",
                    "title": f"Information about {query}",
                    "content": f"Comprehensive information related to {query} from our knowledge base...",
                    "source": "General Knowledge Database",
                    "confidence": 0.82,
                    "relevance": 0.78
                }
            ]
        
        return {
            "documents": documents[:max_sources],
            "total_found": len(documents),
            "confidence": sum(doc["confidence"] for doc in documents) / len(documents),
            "search_time": 1.8
        }