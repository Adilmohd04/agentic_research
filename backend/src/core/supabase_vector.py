"""
Supabase Vector Database Service
Handles vector storage, search, and user isolation using Supabase + pgvector
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import hashlib
import json

try:
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# AI Service import removed - now handled by service manager

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    id: str
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    chunk_index: int = 0

@dataclass
class Document:
    id: str
    user_id: str
    filename: str
    file_type: str
    file_size: int
    content_hash: str
    status: str = 'processing'
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

@dataclass
class SearchResult:
    id: str
    document_id: str
    content: str
    similarity: float
    metadata: Optional[Dict[str, Any]] = None
    source: Optional[str] = None

class SupabaseVectorService:
    """Supabase Vector Database Service with user isolation"""
    
    def __init__(self):
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")
        
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        # Initialize Supabase client
        self.client: Client = create_client(
            self.supabase_url, 
            self.supabase_key,
            options=ClientOptions(
                postgrest_client_timeout=10,
                storage_client_timeout=10
            )
        )
        
        # Initialize free embedding service
        from .free_embedding_service import get_embedding_service
        self.embedding_service = get_embedding_service()
        
        logger.info("Supabase Vector Service initialized")
    
    async def ensure_user_exists(self, clerk_user_id: str, user_data: Dict[str, Any] = None) -> str:
        """Ensure user exists in database and return user UUID"""
        try:
            # Check if user exists
            result = self.client.table('users').select('id').eq('clerk_user_id', clerk_user_id).execute()
            
            if result.data:
                return result.data[0]['id']
            
            # Create new user
            user_record = {
                'clerk_user_id': clerk_user_id,
                'email': user_data.get('email') if user_data else None,
                'first_name': user_data.get('first_name') if user_data else None,
                'last_name': user_data.get('last_name') if user_data else None,
                'image_url': user_data.get('image_url') if user_data else None,
            }
            
            result = self.client.table('users').insert(user_record).execute()
            
            if result.data:
                logger.info(f"Created new user: {clerk_user_id}")
                return result.data[0]['id']
            else:
                raise Exception("Failed to create user")
                
        except Exception as e:
            logger.error(f"Error ensuring user exists: {str(e)}")
            raise
    
    def _set_user_context(self, clerk_user_id: str):
        """Set user context for RLS policies"""
        # This would typically be done at the connection level
        # For now, we'll handle user filtering in queries
        pass
    
    async def store_document(
        self, 
        clerk_user_id: str,
        filename: str, 
        content: str, 
        file_type: str,
        file_size: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Store document and return document record"""
        try:
            # Ensure user exists
            user_id = await self.ensure_user_exists(clerk_user_id)
            
            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Create document record
            doc_data = {
                'user_id': user_id,
                'filename': filename,
                'file_type': file_type,
                'file_size': file_size,
                'content_hash': content_hash,
                'metadata': metadata or {},
                'status': 'processing'
            }
            
            result = self.client.table('documents').insert(doc_data).execute()
            
            if not result.data:
                raise Exception("Failed to create document record")
            
            doc_record = result.data[0]
            
            return Document(
                id=doc_record['id'],
                user_id=user_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                content_hash=content_hash,
                status='processing',
                metadata=metadata,
                created_at=datetime.fromisoformat(doc_record['created_at'].replace('Z', '+00:00'))
            )
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            raise
    
    async def store_chunks(
        self, 
        document: Document, 
        chunks: List[str],
        clerk_user_id: str
    ) -> List[DocumentChunk]:
        """Store document chunks with embeddings"""
        try:
            user_id = await self.ensure_user_exists(clerk_user_id)
            
            # Generate embeddings for all chunks using free service
            logger.info(f"Generating embeddings for {len(chunks)} chunks using {self.embedding_service.model_name}")
            embeddings = await self.embedding_service.generate_embeddings(chunks)
            
            # Prepare chunk records
            chunk_records = []
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_records.append({
                    'document_id': document.id,
                    'user_id': user_id,
                    'chunk_index': i,
                    'content': chunk_text,
                    'embedding': embedding,
                    'metadata': {'chunk_length': len(chunk_text)}
                })
            
            # Insert chunks in batches
            batch_size = 100
            stored_chunks = []
            
            for i in range(0, len(chunk_records), batch_size):
                batch = chunk_records[i:i + batch_size]
                result = self.client.table('document_chunks').insert(batch).execute()
                
                if result.data:
                    for record in result.data:
                        stored_chunks.append(DocumentChunk(
                            id=record['id'],
                            document_id=record['document_id'],
                            content=record['content'],
                            embedding=record['embedding'],
                            metadata=record['metadata'],
                            chunk_index=record['chunk_index']
                        ))
            
            # Update document status to ready
            self.client.table('documents').update({
                'status': 'ready',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', document.id).execute()
            
            logger.info(f"Stored {len(stored_chunks)} chunks for document {document.id}")
            return stored_chunks
            
        except Exception as e:
            logger.error(f"Error storing chunks: {str(e)}")
            # Update document status to error
            self.client.table('documents').update({
                'status': 'error',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', document.id).execute()
            raise
    
    async def search_similar(
        self, 
        query: str, 
        clerk_user_id: str,
        max_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[SearchResult]:
        """Search for similar document chunks"""
        try:
            user_id = await self.ensure_user_exists(clerk_user_id)
            
            # Generate query embedding using free service
            query_embedding = await self.embedding_service.generate_single_embedding(query)
            
            # Use the search function
            result = self.client.rpc('search_documents', {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': max_results,
                'filter_user_id': user_id
            }).execute()
            
            search_results = []
            if result.data:
                for row in result.data:
                    search_results.append(SearchResult(
                        id=row['id'],
                        document_id=row['document_id'],
                        content=row['content'],
                        similarity=row['similarity'],
                        metadata=row['metadata'],
                        source=row['metadata'].get('source', 'Unknown') if row['metadata'] else 'Unknown'
                    ))
            
            logger.info(f"Found {len(search_results)} similar chunks for user {clerk_user_id}")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            return []
    
    async def get_user_documents(self, clerk_user_id: str) -> List[Document]:
        """Get all documents for a user"""
        try:
            user_id = await self.ensure_user_exists(clerk_user_id)
            
            result = self.client.table('documents').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            
            documents = []
            if result.data:
                for record in result.data:
                    documents.append(Document(
                        id=record['id'],
                        user_id=record['user_id'],
                        filename=record['filename'],
                        file_type=record['file_type'],
                        file_size=record['file_size'],
                        content_hash=record['content_hash'],
                        status=record['status'],
                        metadata=record['metadata'],
                        created_at=datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                    ))
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting user documents: {str(e)}")
            return []
    
    async def delete_document(self, document_id: str, clerk_user_id: str) -> bool:
        """Delete document and all its chunks"""
        try:
            user_id = await self.ensure_user_exists(clerk_user_id)
            
            # Verify document belongs to user
            doc_result = self.client.table('documents').select('id').eq('id', document_id).eq('user_id', user_id).execute()
            
            if not doc_result.data:
                logger.warning(f"Document {document_id} not found for user {clerk_user_id}")
                return False
            
            # Delete document (chunks will be deleted by CASCADE)
            result = self.client.table('documents').delete().eq('id', document_id).eq('user_id', user_id).execute()
            
            success = len(result.data) > 0 if result.data else False
            if success:
                logger.info(f"Deleted document {document_id} for user {clerk_user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    async def get_user_stats(self, clerk_user_id: str) -> Dict[str, Any]:
        """Get user document statistics"""
        try:
            user_id = await self.ensure_user_exists(clerk_user_id)
            
            result = self.client.rpc('get_user_document_stats', {'user_uuid': user_id}).execute()
            
            if result.data and len(result.data) > 0:
                stats = result.data[0]
                return {
                    'total_documents': stats['total_documents'],
                    'total_chunks': stats['total_chunks'],
                    'total_size': stats['total_size'],
                    'ready_documents': stats['ready_documents'],
                    'processing_documents': stats['processing_documents']
                }
            
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'total_size': 0,
                'ready_documents': 0,
                'processing_documents': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'total_size': 0,
                'ready_documents': 0,
                'processing_documents': 0
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            # Test database connection
            result = self.client.table('users').select('count').execute()
            
            # Check embedding service health
            embedding_health = await self.embedding_service.health_check()
            
            return {
                'status': 'healthy',
                'database_connected': True,
                'vector_extension_available': True,
                'embedding_service_available': embedding_health['available'],
                'embedding_model': embedding_health.get('model', 'unknown'),
                'embedding_dimension': embedding_health.get('dimension', 0)
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_connected': False,
                'vector_extension_available': False,
                'embedding_service_available': False,
                'embedding_model': 'error',
                'embedding_dimension': 0
            }