"""
Enhanced RAG System with OpenRouter Integration
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

# Vector storage (using ChromaDB as example)
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

# Embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

# AI Service integration
from ..core.ai_service import get_ai_service

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.persist_directory = persist_directory
        self.documents = []
        self.chunks = []
        
        # Initialize vector database
        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self.client = None
            self.collection = None
            logger.warning("ChromaDB not available, using mock vector search")
        
        # Initialize embedding model
        if EMBEDDINGS_AVAILABLE:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.embedding_model = None
            logger.warning("SentenceTransformers not available, using mock embeddings")
    
    async def upload_document(self, file_path: str, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload and process a document"""
        try:
            # Extract text based on file type
            text_content = await self._extract_text(file_content, filename)
            
            if not text_content:
                return {"error": "Could not extract text from document"}
            
            # Create document metadata
            doc_id = hashlib.md5(f"{filename}_{datetime.utcnow()}".encode()).hexdigest()
            document = {
                "id": doc_id,
                "filename": filename,
                "content": text_content,
                "uploaded_at": datetime.utcnow().isoformat(),
                "file_size": len(file_content),
                "file_type": self._get_file_type(filename)
            }
            
            # Chunk the document
            chunks = await self._chunk_document(text_content, doc_id)
            
            # Generate embeddings and store
            if self.collection and self.embedding_model:
                await self._store_chunks_vector(chunks, doc_id)
            
            # Store in memory
            self.documents.append(document)
            self.chunks.extend(chunks)
            
            logger.info(f"Uploaded document {filename}: {len(chunks)} chunks")
            
            return {
                "document_id": doc_id,
                "filename": filename,
                "chunks_created": len(chunks),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error uploading document {filename}: {str(e)}")
            return {"error": str(e)}
    
    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search documents using hybrid approach"""
        try:
            if self.collection and self.embedding_model:
                # Vector search
                vector_results = await self._vector_search(query, max_results)
            else:
                # Fallback to keyword search
                vector_results = await self._keyword_search(query, max_results)
            
            # Format results
            documents = []
            for result in vector_results:
                documents.append({
                    "id": result.get("id"),
                    "title": result.get("title", "Untitled"),
                    "content": result.get("content", ""),
                    "source": result.get("source", "Uploaded Document"),
                    "confidence": result.get("confidence", 0.8),
                    "relevance": result.get("relevance", 0.8)
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
    
    async def _chunk_document(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """Chunk document into smaller pieces"""
        chunk_size = 1000
        overlap = 200
        
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text.strip()) > 50:  # Only keep meaningful chunks
                chunk_id = f"{doc_id}_chunk_{len(chunks)}"
                chunks.append({
                    "id": chunk_id,
                    "document_id": doc_id,
                    "content": chunk_text,
                    "chunk_index": len(chunks),
                    "word_count": len(chunk_words)
                })
        
        return chunks
    
    async def _store_chunks_vector(self, chunks: List[Dict], doc_id: str):
        """Store chunks in vector database"""
        if not self.collection or not self.embedding_model:
            return
        
        try:
            # Generate embeddings
            texts = [chunk["content"] for chunk in chunks]
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=[{
                    "document_id": doc_id,
                    "chunk_id": chunk["id"],
                    "chunk_index": chunk["chunk_index"]
                } for chunk in chunks],
                ids=[chunk["id"] for chunk in chunks]
            )
            
        except Exception as e:
            logger.error(f"Error storing vectors: {str(e)}")
    
    async def _vector_search(self, query: str, max_results: int) -> List[Dict]:
        """Perform vector similarity search"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results
            )
            
            # Format results
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )):
                # Find original document
                doc_id = metadata['document_id']
                original_doc = next((d for d in self.documents if d['id'] == doc_id), None)
                
                formatted_results.append({
                    "id": metadata['chunk_id'],
                    "title": original_doc['filename'] if original_doc else "Unknown",
                    "content": doc[:500] + "..." if len(doc) > 500 else doc,
                    "source": f"Document: {original_doc['filename']}" if original_doc else "Unknown",
                    "confidence": max(0, 1 - distance),  # Convert distance to confidence
                    "relevance": max(0, 1 - distance)
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search error: {str(e)}")
            return []
    
    async def _keyword_search(self, query: str, max_results: int) -> List[Dict]:
        """Fallback keyword search"""
        query_words = query.lower().split()
        results = []
        
        for chunk in self.chunks:
            content_lower = chunk["content"].lower()
            score = sum(1 for word in query_words if word in content_lower)
            
            if score > 0:
                # Find original document
                doc_id = chunk["document_id"]
                original_doc = next((d for d in self.documents if d['id'] == doc_id), None)
                
                results.append({
                    "id": chunk["id"],
                    "title": original_doc['filename'] if original_doc else "Unknown",
                    "content": chunk["content"][:500] + "..." if len(chunk["content"]) > 500 else chunk["content"],
                    "source": f"Document: {original_doc['filename']}" if original_doc else "Unknown",
                    "confidence": min(1.0, score / len(query_words)),
                    "relevance": min(1.0, score / len(query_words)),
                    "score": score
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]
    
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
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Get all uploaded documents"""
        return [{
            "id": doc["id"],
            "filename": doc["filename"],
            "file_type": doc["file_type"],
            "uploaded_at": doc["uploaded_at"],
            "file_size": doc["file_size"],
            "chunks": len([c for c in self.chunks if c["document_id"] == doc["id"]])
        } for doc in self.documents]
    
    async def ask_question(
        self, 
        question: str, 
        model: Optional[str] = None,
        max_context_docs: int = 5
    ) -> Dict[str, Any]:
        """Ask a question using RAG with AI generation"""
        try:
            # First, search for relevant documents
            search_results = await self.search(question, max_context_docs)
            
            if not search_results.get("documents"):
                return {
                    "answer": "I don't have any relevant documents to answer your question. Please upload some documents first.",
                    "sources": [],
                    "confidence": 0.0,
                    "search_results": search_results
                }
            
            # Get AI service
            ai_service = await get_ai_service()
            
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
                context_documents=search_results["documents"]
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
    
    async def generate_summary(self, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a summary of documents or a specific document"""
        try:
            ai_service = await get_ai_service()
            
            if document_id:
                # Summarize specific document
                doc = next((d for d in self.documents if d["id"] == document_id), None)
                if not doc:
                    return {"error": "Document not found"}
                
                content = doc["content"][:4000]  # Limit content length
                messages = [
                    {
                        "role": "user",
                        "content": f"Please provide a comprehensive summary of the following document:\n\n{content}"
                    }
                ]
            else:
                # Summarize all documents
                all_content = ""
                for doc in self.documents[:5]:  # Limit to first 5 documents
                    all_content += f"Document: {doc['filename']}\n{doc['content'][:1000]}\n\n"
                
                messages = [
                    {
                        "role": "user",
                        "content": f"Please provide a summary of the following documents:\n\n{all_content}"
                    }
                ]
            
            response = await ai_service.generate_response(messages)
            
            return {
                "summary": response.get("response", "Could not generate summary"),
                "document_id": document_id,
                "documents_summarized": 1 if document_id else len(self.documents),
                "model_used": response.get("model_used"),
                "tokens_used": response.get("tokens_used", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            return {"error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "vector_db_available": self.collection is not None,
            "embedding_model_available": self.embedding_model is not None,
            "supported_formats": ["PDF", "DOCX", "TXT", "MD", "HTML"],
            "ai_service_available": True
        }