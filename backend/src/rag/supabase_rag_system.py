"""
Enhanced RAG System with Supabase Vector Integration
Multi-user support with proper isolation and optimized performance
"""

import os
import asyncio
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Document processing
import PyPDF2
from docx import Document
import markdown
from bs4 import BeautifulSoup

# Service Manager for centralized service access
from ..core.service_manager import get_service_manager
from ..core.supabase_vector import Document as VectorDocument, SearchResult

logger = logging.getLogger(__name__)

class SupabaseRAGSystem:
    """Advanced RAG system with Supabase Vector storage and user isolation"""
    
    def __init__(self):
        # Get service manager for centralized service access
        self.service_manager = get_service_manager()
        self.vector_service = self.service_manager.supabase_service
        
        logger.info("Supabase RAG System initialized")
    
    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str, 
        clerk_user_id: str
    ) -> Dict[str, Any]:
        """Upload and process a document for a specific user"""
        try:
            # Extract text based on file type
            text_content = await self._extract_text(file_content, filename)
            
            if not text_content:
                return {"error": "Could not extract text from document"}
            
            # Store document in Supabase
            document = await self.vector_service.store_document(
                clerk_user_id=clerk_user_id,
                filename=filename,
                content=text_content,
                file_type=self._get_file_type(filename),
                file_size=len(file_content)
            )
            
            # Chunk the document
            chunks = await self._chunk_document(text_content)
            
            # Store chunks with embeddings
            stored_chunks = await self.vector_service.store_chunks(
                document=document,
                chunks=chunks,
                clerk_user_id=clerk_user_id
            )
            
            logger.info(f"Uploaded document {filename} for user {clerk_user_id}: {len(stored_chunks)} chunks")
            
            return {
                "document_id": document.id,
                "filename": filename,
                "chunks_created": len(stored_chunks),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error uploading document {filename}: {str(e)}")
            return {"error": str(e)}
    
    async def search(
        self, 
        query: str, 
        clerk_user_id: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Search documents for a specific user"""
        try:
            # Perform vector search
            search_results = await self.vector_service.search_similar(
                query=query,
                clerk_user_id=clerk_user_id,
                max_results=max_results
            )
            
            # Format results
            documents = []
            for result in search_results:
                documents.append({
                    "id": result.id,
                    "title": result.metadata.get('filename', 'Untitled') if result.metadata else 'Untitled',
                    "content": result.content,
                    "source": result.source or "Uploaded Document",
                    "confidence": result.similarity,
                    "relevance": result.similarity
                })
            
            return {
                "documents": documents,
                "total_found": len(documents),
                "confidence": sum(doc["confidence"] for doc in documents) / len(documents) if documents else 0,
                "search_time": 1.2
            }
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return {"documents": [], "error": str(e)}
    
    async def ask_question(
        self, 
        question: str, 
        clerk_user_id: str,
        model: Optional[str] = None,
        max_context_docs: int = 5,
        user_api_keys: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Ask a question using RAG with AI generation for a specific user"""
        try:
            # First, search for relevant documents
            search_results = await self.search(question, clerk_user_id, max_context_docs)
            
            if not search_results.get("documents"):
                return {
                    "answer": "I don't have any relevant documents to answer your question. Please upload some documents first.",
                    "sources": [],
                    "confidence": 0.0,
                    "search_results": search_results
                }
            
            # Get AI service from service manager
            ai_service = self.service_manager.ai_service
            
            # Prepare conversation messages
            messages = [
                {
                    "role": "user",
                    "content": question
                }
            ]
            
            # Generate AI response with RAG context
            ai_response = await ai_service.generate_response(
                messages=messages,
                model=model,
                context_documents=search_results["documents"],
                user_api_keys=user_api_keys
            )
            
            # Format response
            return {
                "answer": ai_response.get("response", "I couldn't generate a response."),
                "sources": [
                    {
                        "title": doc["title"],
                        "content_preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                        "confidence": doc["confidence"],
                        "source": doc["source"]
                    }
                    for doc in search_results["documents"]
                ],
                "confidence": search_results.get("confidence", 0.0),
                "model_used": ai_response.get("model_used"),
                "tokens_used": ai_response.get("tokens_used", 0),
                "search_results_count": len(search_results["documents"]),
                "timestamp": datetime.utcnow().isoformat(),
                "status": ai_response.get("status", "success")
            }
            
        except Exception as e:
            logger.error(f"RAG question answering error: {str(e)}")
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "error": str(e),
                "sources": [],
                "confidence": 0.0,
                "status": "error"
            }
    
    async def get_documents(self, clerk_user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a specific user"""
        try:
            documents = await self.vector_service.get_user_documents(clerk_user_id)
            
            # Get chunk counts for each document
            result = []
            for doc in documents:
                # Get chunk count from Supabase
                chunk_count_result = self.vector_service.client.table('document_chunks').select('id', count='exact').eq('document_id', doc.id).execute()
                chunk_count = chunk_count_result.count if chunk_count_result.count is not None else 0
                
                result.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
                    "file_size": doc.file_size,
                    "status": doc.status,
                    "chunks": chunk_count
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return []
    
    async def delete_document(self, document_id: str, clerk_user_id: str) -> bool:
        """Delete a document and all its chunks for a specific user"""
        try:
            return await self.vector_service.delete_document(document_id, clerk_user_id)
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    async def get_stats(self, clerk_user_id: str) -> Dict[str, Any]:
        """Get RAG system statistics for a specific user"""
        try:
            user_stats = await self.vector_service.get_user_stats(clerk_user_id)
            system_health = await self.vector_service.health_check()
            
            return {
                **user_stats,
                "supported_formats": ["PDF", "DOCX", "TXT", "MD", "HTML"],
                "system_status": system_health["status"],
                "vector_db_available": system_health["database_connected"],
                "embedding_service_available": system_health["embedding_service_available"]
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "total_size": 0,
                "ready_documents": 0,
                "processing_documents": 0,
                "supported_formats": ["PDF", "DOCX", "TXT", "MD", "HTML"],
                "system_status": "error",
                "vector_db_available": False,
                "embedding_service_available": False
            }
    
    # Document processing methods (same as original)
    async def _extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from various file formats"""
        file_ext = filename.lower().split('.')[-1]
        
        try:
            if file_ext == 'pdf':
                return await self._extract_pdf_text(file_content)
            elif file_ext in ['docx', 'doc']:
                return await self._extract_docx_text(file_content)
            elif file_ext in ['md', 'markdown']:
                return await self._extract_markdown_text(file_content)
            elif file_ext in ['txt', 'text']:
                return file_content.decode('utf-8')
            elif file_ext in ['html', 'htm']:
                return await self._extract_html_text(file_content)
            else:
                # Try to decode as text
                return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return ""
    
    async def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF"""
        try:
            import io
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            return ""
    
    async def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            import io
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"DOCX extraction error: {str(e)}")
            return ""
    
    async def _extract_markdown_text(self, file_content: bytes) -> str:
        """Extract text from Markdown"""
        try:
            md_content = file_content.decode('utf-8')
            html = markdown.markdown(md_content)
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()
        except Exception as e:
            logger.error(f"Markdown extraction error: {str(e)}")
            return ""
    
    async def _extract_html_text(self, file_content: bytes) -> str:
        """Extract text from HTML"""
        try:
            html_content = file_content.decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text()
        except Exception as e:
            logger.error(f"HTML extraction error: {str(e)}")
            return ""
    
    async def _chunk_document(self, text: str) -> List[str]:
        """Chunk document into smaller pieces"""
        chunk_size = 1000
        overlap = 200
        
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text.strip()) > 50:  # Only keep meaningful chunks
                chunks.append(chunk_text)
        
        return chunks
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type from filename"""
        ext = filename.lower().split('.')[-1]
        type_mapping = {
            'pdf': 'PDF Document',
            'docx': 'Word Document',
            'doc': 'Word Document',
            'txt': 'Text File',
            'md': 'Markdown',
            'html': 'HTML Document',
            'htm': 'HTML Document'
        }
        return type_mapping.get(ext, 'Unknown')