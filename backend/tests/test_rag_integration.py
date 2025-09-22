"""
Tests for RAG integration with CrewAI agents and MCP tools
"""

import pytest
import asyncio
from datetime import datetime

from src.mcp.registry import MCPToolRegistryImpl
from src.mcp.tools.rag_tools import DocumentSearchTool, DocumentUploadTool, RAGStatsTool
from src.agents.researcher import ResearcherAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.crew_setup import AgentCrew
from src.core.memory import TaskRecord


class TestRAGMCPIntegration:
    """Test RAG tools integration with MCP"""
    
    @pytest.fixture
    async def mcp_with_rag_tools(self):
        registry = MCPToolRegistryImpl()
        
        # Register RAG tools
        await registry.registerTool(DocumentSearchTool())
        await registry.registerTool(DocumentUploadTool())
        await registry.registerTool(RAGStatsTool())
        
        return registry
    
    @pytest.mark.asyncio
    async def test_document_upload_tool(self, mcp_with_rag_tools):
        """Test document upload MCP tool"""
        
        registry = mcp_with_rag_tools
        
        # Test document upload
        result = await registry.executeTool("document_upload", {
            "content": "Artificial intelligence is transforming healthcare through predictive analytics and personalized medicine.",
            "title": "AI in Healthcare",
            "source": "test_integration"
        })
        
        assert result.success is True
        assert "document_id" in result.data
        assert result.data["chunks_created"] > 0
    
    @pytest.mark.asyncio
    async def test_document_search_tool(self, mcp_with_rag_tools):
        """Test document search MCP tool"""
        
        registry = mcp_with_rag_tools
        
        # First upload a document
        await registry.executeTool("document_upload", {
            "content": "Machine learning algorithms can analyze medical data to predict patient outcomes and optimize treatment plans.",
            "title": "ML in Medicine",
            "source": "test_integration"
        })
        
        # Then search for it
        result = await registry.executeTool("document_search", {
            "query": "machine learning medical data",
            "k": 5,
            "include_citations": True
        })
        
        assert result.success is True
        assert "results" in result.data
        assert "citations" in result.data
    
    @pytest.mark.asyncio
    async def test_rag_stats_tool(self, mcp_with_rag_tools):
        """Test RAG statistics MCP tool"""
        
        registry = mcp_with_rag_tools
        
        result = await registry.executeTool("rag_stats", {})
        
        assert result.success is True
        assert "rag_statistics" in result.data
        assert "system_status" in result.data


class TestAgentRAGIntegration:
    """Test agents using RAG tools"""
    
    @pytest.fixture
    async def researcher_with_rag(self):
        # Setup MCP registry with RAG tools
        from src.mcp.registry import mcp_registry
        await mcp_registry.registerTool(DocumentSearchTool())
        await mcp_registry.registerTool(DocumentUploadTool())
        await mcp_registry.registerTool(RAGStatsTool())
        
        # Create researcher agent
        agent = ResearcherAgent()
        await agent.initialize()
        
        yield agent
        
        await agent.shutdown()
    
    @pytest.fixture
    async def analyzer_with_rag(self):
        # Setup MCP registry with RAG tools
        from src.mcp.registry import mcp_registry
        await mcp_registry.registerTool(DocumentSearchTool())
        await mcp_registry.registerTool(RAGStatsTool())
        
        # Create analyzer agent
        agent = AnalyzerAgent()
        await agent.initialize()
        
        yield agent
        
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_researcher_rag_integration(self, researcher_with_rag):
        """Test researcher agent using RAG tools"""
        
        agent = researcher_with_rag
        
        # First add some test data to RAG system
        await agent.use_tool("document_upload", {
            "content": "Recent studies show that AI-powered diagnostic tools can improve accuracy by 25% in medical imaging.",
            "title": "AI Diagnostic Accuracy Study",
            "source": "medical_journal_2024"
        })
        
        # Create research task
        task = TaskRecord(
            task_id="rag-research-test",
            type="research",
            description="Research AI applications in medical diagnostics",
            status="pending",
            assigned_agent=agent.agent_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute task
        result = await agent.process_task(task)
        
        # Verify RAG integration
        assert "research_results" in result
        assert result["research_results"].get("rag_integration") is True
        assert "rag_citations" in result
        assert result["research_results"]["rag_results_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_analyzer_rag_validation(self, analyzer_with_rag):
        """Test analyzer agent using RAG for validation"""
        
        agent = analyzer_with_rag
        
        # Create analysis task with claims to validate
        task = TaskRecord(
            task_id="rag-analysis-test",
            type="analysis",
            description="AI shows significant improvement in diagnostic accuracy. Machine learning algorithms are being widely adopted in healthcare.",
            status="pending",
            assigned_agent=agent.agent_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute task
        result = await agent.process_task(task)
        
        # Verify RAG validation integration
        assert "validation_results" in result
        assert "rag_validation" in result["validation_results"]
        assert "rag_cross_reference" in result


class TestCrewAIRAGWorkflow:
    """Test CrewAI workflow with RAG integration"""
    
    @pytest.mark.asyncio
    async def test_rag_enhanced_research_workflow(self):
        """Test complete research workflow with RAG enhancement"""
        
        # Setup RAG tools
        from src.mcp.registry import mcp_registry
        await mcp_registry.registerTool(DocumentSearchTool())
        await mcp_registry.registerTool(DocumentUploadTool())
        await mcp_registry.registerTool(RAGStatsTool())
        
        # Add test documents to RAG system
        await mcp_registry.executeTool("document_upload", {
            "content": "Artificial intelligence in healthcare has shown remarkable progress in 2024, with new applications in diagnostic imaging, drug discovery, and personalized treatment plans.",
            "title": "AI Healthcare Progress 2024",
            "source": "healthcare_tech_review"
        })
        
        # Initialize crew
        crew = AgentCrew()
        await crew.initialize_crew()
        
        try:
            # Execute RAG-enhanced research workflow
            result = await crew.execute_research_workflow(
                topic="AI applications in healthcare 2024",
                session_id="rag-workflow-test"
            )
            
            # Verify RAG enhancement
            assert result["rag_enhanced"] is True
            assert "rag_stats" in result["results"]
            assert result["status"] == "completed"
            assert "RAG-enhanced" in result["summary"]
            
        finally:
            await crew.shutdown_crew()


class TestRAGReranking:
    """Test RAG reranking functionality"""
    
    @pytest.mark.asyncio
    async def test_hybrid_retrieval_with_reranking(self):
        """Test that RAG system uses reranking properly"""
        
        from src.rag.hybrid_retriever import hybrid_retriever
        from src.rag.document_processor import document_processor
        from src.rag.vector_store import vector_store
        from src.rag.bm25_index import bm25_index
        
        # Add test documents
        test_docs = [
            {
                "content": "Machine learning algorithms are revolutionizing medical diagnosis by analyzing complex patterns in medical imaging data.",
                "title": "ML in Medical Diagnosis",
                "source": "medical_ai_journal"
            },
            {
                "content": "Artificial intelligence applications in healthcare include predictive analytics, drug discovery, and personalized treatment recommendations.",
                "title": "AI Healthcare Applications",
                "source": "healthcare_tech"
            }
        ]
        
        # Process and index documents
        processed_docs = await document_processor.process_multiple_documents(test_docs)
        all_chunks = []
        for doc in processed_docs:
            all_chunks.extend(doc.chunks)
        
        await vector_store.add_chunks(all_chunks)
        await bm25_index.add_chunks(all_chunks)
        
        # Test retrieval with reranking
        results = await hybrid_retriever.retrieve(
            query="machine learning medical diagnosis",
            k=5,
            rerank=True
        )
        
        # Verify reranking was applied
        assert len(results) > 0
        for result in results:
            assert "rerank_score" in result
            assert "confidence" in result
            assert "hybrid_score" in result
            assert result["retrieval_method"] in ["hybrid", "vector", "bm25"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])