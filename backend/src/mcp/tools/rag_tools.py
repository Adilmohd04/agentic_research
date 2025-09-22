"""
MCP tools for RAG system integration
"""

from typing import Any, Dict, List
from ..base_tool import BaseMCPTool
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from shared.schemas.mcp import JSONSchema
from ...rag.hybrid_retriever import hybrid_retriever
from ...rag.document_processor import document_processor
from ...rag.vector_store import vector_store
from ...rag.bm25_index import bm25_index


class DocumentSearchTool(BaseMCPTool):
    """MCP tool for searching documents using RAG"""
    
    def __init__(self):
        super().__init__(
            name="document_search",
            description="Search documents using hybrid RAG retrieval with citations",
            category="search"
        )
    
    def _define_schema(self) -> JSONSchema:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "k": {"type": "integer", "description": "Number of results to return", "default": 10},
                "include_citations": {"type": "boolean", "description": "Include citations in results", "default": True},
                "min_confidence": {"type": "number", "description": "Minimum confidence threshold", "default": 0.1},
                "rerank": {"type": "boolean", "description": "Apply reranking", "default": True}
            },
            "required": ["query"]
        }
    
    async def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params["query"]
        k = params.get("k", 10)
        include_citations = params.get("include_citations", True)
        min_confidence = params.get("min_confidence", 0.1)
        rerank = params.get("rerank", True)
        
        if include_citations:
            results, citations = await hybrid_retriever.retrieve_with_citations(
                query=query,
                k=k,
                min_confidence=min_confidence,
                rerank=rerank
            )
            
            return {
                "query": query,
                "results": results,
                "citations": [citation.__dict__ for citation in citations],
                "total_results": len(results),
                "search_method": "hybrid_rag"
            }
        else:
            results = await hybrid_retriever.retrieve(
                query=query,
                k=k,
                min_confidence=min_confidence,
                rerank=rerank
            )
            
            return {
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_method": "hybrid_rag"
            }


class DocumentUploadTool(BaseMCPTool):
    """MCP tool for uploading and processing documents"""
    
    def __init__(self):
        super().__init__(
            name="document_upload",
            description="Upload and process documents for RAG system",
            category="data_processing"
        )
    
    def _define_schema(self) -> JSONSchema:
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Document content"},
                "title": {"type": "string", "description": "Document title"},
                "source": {"type": "string", "description": "Document source"},
                "metadata": {"type": "object", "description": "Additional metadata", "default": {}}
            },
            "required": ["content", "title", "source"]
        }
    
    async def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        content = params["content"]
        title = params["title"]
        source = params["source"]
        metadata = params.get("metadata", {})
        
        # Process document
        document = await document_processor.process_document(
            content=content,
            title=title,
            source=source,
            metadata=metadata
        )
        
        # Add to indexes
        await vector_store.add_chunks(document.chunks)
        await bm25_index.add_chunks(document.chunks)
        
        return {
            "success": True,
            "document_id": document.id,
            "title": document.title,
            "chunks_created": len(document.chunks),
            "word_count": document.metadata.wordCount,
            "source": source
        }


class RAGStatsTool(BaseMCPTool):
    """MCP tool for getting RAG system statistics"""
    
    def __init__(self):
        super().__init__(
            name="rag_stats",
            description="Get RAG system statistics and health information",
            category="data_processing"
        )
    
    def _define_schema(self) -> JSONSchema:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        stats = hybrid_retriever.get_statistics()
        
        return {
            "rag_statistics": stats,
            "system_status": "operational",
            "timestamp": "now"
        }


class ExplainRetrievalTool(BaseMCPTool):
    """MCP tool for explaining retrieval results"""
    
    def __init__(self):
        super().__init__(
            name="explain_retrieval",
            description="Explain why specific chunks were retrieved for a query",
            category="search"
        )
    
    def _define_schema(self) -> JSONSchema:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "chunk_id": {"type": "string", "description": "Chunk ID to explain"}
            },
            "required": ["query", "chunk_id"]
        }
    
    async def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params["query"]
        chunk_id = params["chunk_id"]
        
        explanation = await hybrid_retriever.explain_retrieval(query, chunk_id)
        
        return {
            "explanation": explanation,
            "query": query,
            "chunk_id": chunk_id
        }