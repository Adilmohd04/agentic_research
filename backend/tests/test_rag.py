"""
Tests for RAG system components
"""

import pytest
import asyncio
from datetime import datetime

from src.rag.document_processor import DocumentProcessor
from src.rag.vector_store import VectorStore
from src.rag.bm25_index import BM25Index
from src.rag.hybrid_retriever import HybridRetriever


class TestDocumentProcessor:
    """Test document processing functionality"""
    
    @pytest.fixture
    def processor(self):
        return DocumentProcessor()
    
    @pytest.mark.asyncio
    async def test_document_processing(self, processor):
        """Test basic document processing"""
        
        content = """
        This is a test document about artificial intelligence.
        AI has many applications in healthcare, finance, and technology.
        Machine learning is a subset of AI that focuses on learning from data.
        """
        
        document = await processor.process_document(
            content=content,
            title="Test AI Document",
            source="test_source"
        )
        
        assert document.title == "Test AI Document"
        assert len(document.chunks) > 0
        assert document.metadata.wordCount > 0
        
        # Check that chunks have embeddings
        for chunk in document.chunks:
            assert chunk.embeddings is not None
            assert len(chunk.embeddings) > 0
    
    @pytest.mark.asyncio
    async def test_chunk_creation(self, processor):
        """Test chunk creation with overlap"""
        
        # Long content to ensure multiple chunks
        content = " ".join([f"This is sentence number {i} about AI and machine learning." for i in range(50)])
        
        document = await processor.process_document(
            content=content,
            title="Long Test Document",
            source="test_source"
        )
        
        assert len(document.chunks) > 1
        
        # Check chunk metadata
        for i, chunk in enumerate(document.chunks):
            assert chunk.metadata.chunkIndex == i
            assert chunk.metadata.tokenCount > 0


class TestVectorStore:
    """Test vector store functionality"""
    
    @pytest.fixture
    async def vector_store_with_data(self):
        vs = VectorStore(dimension=384)
        
        # Create test chunks with embeddings
        from src.rag.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        test_content = [
            "Artificial intelligence is transforming healthcare.",
            "Machine learning algorithms can predict diseases.",
            "Natural language processing helps analyze medical records."
        ]
        
        chunks = []
        for i, content in enumerate(test_content):
            doc = await processor.process_document(
                content=content,
                title=f"Test Doc {i}",
                source="test"
            )
            chunks.extend(doc.chunks)
        
        await vs.add_chunks(chunks)
        return vs, chunks
    
    @pytest.mark.asyncio
    async def test_vector_search(self, vector_store_with_data):
        """Test vector similarity search"""
        
        vs, chunks = vector_store_with_data
        
        # Search for similar content
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode("AI in medicine").tolist()
        
        results = await vs.search(query_embedding, k=3)
        
        assert len(results) > 0
        assert all("similarity_score" in result for result in results)
        assert all("chunk_id" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_vector_store_statistics(self, vector_store_with_data):
        """Test vector store statistics"""
        
        vs, chunks = vector_store_with_data
        
        stats = vs.get_statistics()
        
        assert stats["total_vectors"] == len(chunks)
        assert stats["dimension"] == 384
        assert stats["metadata_entries"] == len(chunks)


class TestBM25Index:
    """Test BM25 indexing functionality"""
    
    @pytest.fixture
    async def bm25_with_data(self):
        bm25 = BM25Index()
        
        test_documents = [
            ("doc1", "Artificial intelligence is revolutionizing healthcare and medical diagnosis."),
            ("doc2", "Machine learning algorithms can analyze large datasets efficiently."),
            ("doc3", "Natural language processing enables computers to understand human language.")
        ]
        
        for doc_id, content in test_documents:
            await bm25.add_document(doc_id, content)
        
        return bm25
    
    @pytest.mark.asyncio
    async def test_bm25_search(self, bm25_with_data):
        """Test BM25 search functionality"""
        
        bm25 = bm25_with_data
        
        results = await bm25.search("artificial intelligence healthcare", k=3)
        
        assert len(results) > 0
        assert all("bm25_score" in result for result in results)
        assert all("chunk_id" in result for result in results)
        
        # Results should be sorted by score
        scores = [result["bm25_score"] for result in results]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_term_statistics(self, bm25_with_data):
        """Test term statistics"""
        
        bm25 = bm25_with_data
        
        stats = await bm25.get_term_statistics("artificial")
        
        assert "document_frequency" in stats
        assert "total_frequency" in stats
        assert stats["document_frequency"] > 0
    
    @pytest.mark.asyncio
    async def test_score_explanation(self, bm25_with_data):
        """Test BM25 score explanation"""
        
        bm25 = bm25_with_data
        
        explanation = await bm25.explain_score("artificial intelligence", "doc1")
        
        assert "total_score" in explanation
        assert "term_scores" in explanation
        assert len(explanation["term_scores"]) > 0


class TestHybridRetriever:
    """Test hybrid retrieval functionality"""
    
    @pytest.fixture
    async def retriever_with_data(self):
        retriever = HybridRetriever()
        
        # Add test documents
        from src.rag.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        test_docs = [
            {
                "content": "Artificial intelligence is transforming healthcare by enabling faster diagnosis and personalized treatment plans.",
                "title": "AI in Healthcare",
                "source": "medical_journal"
            },
            {
                "content": "Machine learning algorithms can process vast amounts of medical data to identify patterns and predict outcomes.",
                "title": "ML in Medicine",
                "source": "tech_review"
            },
            {
                "content": "Natural language processing helps doctors analyze patient records and extract meaningful insights.",
                "title": "NLP for Medical Records",
                "source": "research_paper"
            }
        ]
        
        processed_docs = await processor.process_multiple_documents(test_docs)
        
        # Add to indexes
        all_chunks = []
        for doc in processed_docs:
            all_chunks.extend(doc.chunks)
        
        from src.rag.vector_store import vector_store
        from src.rag.bm25_index import bm25_index
        
        await vector_store.add_chunks(all_chunks)
        await bm25_index.add_chunks(all_chunks)
        
        return retriever
    
    @pytest.mark.asyncio
    async def test_hybrid_retrieval(self, retriever_with_data):
        """Test hybrid retrieval combining vector and BM25"""
        
        retriever = retriever_with_data
        
        results = await retriever.retrieve(
            query="AI applications in medical diagnosis",
            k=5,
            rerank=True
        )
        
        assert len(results) > 0
        
        # Check result structure
        for result in results:
            assert "chunk_id" in result
            assert "content" in result
            assert "confidence" in result
            assert "hybrid_score" in result
            assert "retrieval_method" in result
    
    @pytest.mark.asyncio
    async def test_retrieval_with_citations(self, retriever_with_data):
        """Test retrieval with citation generation"""
        
        retriever = retriever_with_data
        
        results, citations = await retriever.retrieve_with_citations(
            query="machine learning in healthcare",
            k=3
        )
        
        assert len(results) > 0
        assert len(citations) == len(results)
        
        # Check citation structure
        for citation in citations:
            assert hasattr(citation, 'id')
            assert hasattr(citation, 'source')
            assert hasattr(citation, 'confidence')
            assert hasattr(citation, 'relevance')
    
    @pytest.mark.asyncio
    async def test_retrieval_explanation(self, retriever_with_data):
        """Test retrieval explanation"""
        
        retriever = retriever_with_data
        
        # First get some results
        results = await retriever.retrieve("AI healthcare", k=1)
        
        if results:
            chunk_id = results[0]["chunk_id"]
            explanation = await retriever.explain_retrieval("AI healthcare", chunk_id)
            
            assert "query" in explanation
            assert "chunk_id" in explanation
            assert "vector_search" in explanation
            assert "bm25_search" in explanation


class TestRAGIntegration:
    """Test RAG system integration"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_rag_workflow(self):
        """Test complete RAG workflow from document upload to retrieval"""
        
        # Initialize components
        processor = DocumentProcessor()
        
        # Process document
        document = await processor.process_document(
            content="Artificial intelligence and machine learning are revolutionizing healthcare by enabling predictive analytics and personalized medicine.",
            title="AI Revolution in Healthcare",
            source="healthcare_tech_review"
        )
        
        # Add to indexes
        from src.rag.vector_store import vector_store
        from src.rag.bm25_index import bm25_index
        from src.rag.hybrid_retriever import hybrid_retriever
        
        await vector_store.add_chunks(document.chunks)
        await bm25_index.add_chunks(document.chunks)
        
        # Perform retrieval
        results, citations = await hybrid_retriever.retrieve_with_citations(
            query="AI in healthcare",
            k=3
        )
        
        # Verify results
        assert len(results) > 0
        assert len(citations) > 0
        assert all(result["confidence"] > 0 for result in results)
        
        # Check that citations are properly formatted
        for citation in citations:
            assert citation.confidence > 0
            assert citation.relevance > 0
            assert len(citation.excerpt) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])