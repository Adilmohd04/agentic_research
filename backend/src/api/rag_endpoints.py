"""
RAG System API Endpoints with Supabase Vector Integration
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Header, Depends
from typing import Dict, Any, List, Optional
import logging
from ..rag.supabase_rag_system import SupabaseRAGSystem
from ..core.service_manager import get_service_manager

logger = logging.getLogger(__name__)

# Initialize Supabase RAG system
rag_system = SupabaseRAGSystem()

router = APIRouter(prefix="/api/rag", tags=["RAG"])

def get_user_id(x_user_id: str = Header(None, alias="X-User-ID")):
    """Extract user ID from header"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return x_user_id

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id)
) -> Dict[str, Any]:
    """Upload and process a document for a specific user"""
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.htm'}
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Read file content
        content = await file.read()
        
        if len(content) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        
        # Process document
        result = await rag_system.upload_document(
            file_content=content,
            filename=file.filename,
            clerk_user_id=user_id
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def get_documents(user_id: str = Depends(get_user_id)) -> Dict[str, Any]:
    """Get list of uploaded documents for a specific user"""
    try:
        documents = await rag_system.get_documents(clerk_user_id=user_id)
        return {
            "documents": documents,
            "total": len(documents)
        }
    except Exception as e:
        logger.error(f"Get documents error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_documents(
    query: str,
    max_results: int = Query(5, ge=1, le=20),
    user_id: str = Depends(get_user_id)
) -> Dict[str, Any]:
    """Search documents using vector similarity for a specific user"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        results = await rag_system.search(
            query=query,
            clerk_user_id=user_id,
            max_results=max_results
        )
        return results
        
    except Exception as e:
        logger.error(f"Document search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask")
async def ask_question(
    question: str,
    model: Optional[str] = None,
    max_context_docs: int = Query(5, ge=1, le=10),
    user_id: str = Depends(get_user_id)
) -> Dict[str, Any]:
    """Ask a question using RAG with AI generation for a specific user"""
    try:
        if not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Get user's API keys from service manager
        service_manager = get_service_manager()
        user_api_keys = await service_manager.get_user_api_keys(user_id)
        
        result = await rag_system.ask_question(
            question=question,
            clerk_user_id=user_id,
            model=model,
            max_context_docs=max_context_docs,
            user_api_keys=user_api_keys
        )
        
        return result
        
    except Exception as e:
        logger.error(f"RAG question error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Removed duplicate function - now handled by service_manager.get_user_api_keys()

@router.post("/summarize")
async def generate_summary(document_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate summary of documents"""
    try:
        result = await rag_system.generate_summary(document_id)
        return result
        
    except Exception as e:
        logger.error(f"Summary generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_rag_stats(user_id: str = Depends(get_user_id)) -> Dict[str, Any]:
    """Get RAG system statistics for a specific user"""
    try:
        stats = await rag_system.get_stats(clerk_user_id=user_id)
        
        # Add service status from service manager
        service_manager = get_service_manager()
        ai_service = service_manager.ai_service
        ai_status = ai_service.get_service_status()
        
        return {
            **stats,
            "ai_service": ai_status,
            "available_models": ai_service.get_available_models()
        }
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_user_id)
) -> Dict[str, Any]:
    """Delete a document and its chunks for a specific user"""
    try:
        success = await rag_system.delete_document(
            document_id=document_id,
            clerk_user_id=user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found or access denied")
        
        return {
            "message": f"Document {document_id} deleted successfully",
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def rag_chat(
    message: str,
    conversation_history: List[Dict[str, str]] = [],
    model: Optional[str] = None,
    use_rag: bool = True,
    user_id: str = Depends(get_user_id)
) -> Dict[str, Any]:
    """Chat with AI using RAG context for a specific user"""
    try:
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get services from service manager
        service_manager = get_service_manager()
        ai_service = service_manager.ai_service
        user_api_keys = await service_manager.get_user_api_keys(user_id)
        
        # Prepare messages
        messages = conversation_history + [{"role": "user", "content": message}]
        
        if use_rag:
            # Search for relevant context
            search_results = await rag_system.search(
                query=message,
                clerk_user_id=user_id,
                max_results=3
            )
            context_docs = search_results.get("documents", [])
        else:
            context_docs = None
        
        # Generate response with user's API keys
        response = await ai_service.generate_response(
            messages=messages,
            model=model,
            context_documents=context_docs,
            user_api_keys=user_api_keys
        )
        
        return {
            "response": response.get("response", ""),
            "model_used": response.get("model_used"),
            "tokens_used": response.get("tokens_used", 0),
            "context_used": len(context_docs) if context_docs else 0,
            "sources": context_docs[:3] if context_docs else [],
            "timestamp": response.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"RAG chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Check RAG system health"""
    try:
        service_manager = get_service_manager()
        health = await service_manager.health_check()
        return health
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

@router.get("/embedding-info")
async def get_embedding_info():
    """Get embedding service information"""
    try:
        service_manager = get_service_manager()
        embedding_service = service_manager.embedding_service
        
        info = embedding_service.get_model_info()
        health = await embedding_service.health_check()
        
        return {
            **info,
            "health": health,
            "cost_per_1k_tokens": 0,  # Free!
            "recommended_for": "cost-effective RAG applications"
        }
        
    except Exception as e:
        logger.error(f"Embedding info error: {str(e)}")
        return {"error": str(e)}

@router.post("/test-ai")
async def test_ai_response():
    """Test AI response with OpenRouter Sonoma Sky Alpha"""
    try:
        service_manager = get_service_manager()
        ai_service = service_manager.ai_service
        
        # Test message
        test_messages = [
            {
                "role": "user", 
                "content": "Hello! Can you confirm that you're working properly? Please respond with a brief message about your capabilities."
            }
        ]
        
        # Generate response using Sonoma Sky Alpha
        response = await ai_service.generate_response(
            messages=test_messages,
            model="sonoma-sky-alpha",
            temperature=0.7,
            max_tokens=150
        )
        
        # Get service status
        service_status = ai_service.get_service_status()
        
        return {
            "test_successful": response.get("status") == "success",
            "ai_response": response.get("response", ""),
            "model_used": response.get("model_used", ""),
            "tokens_used": response.get("tokens_used", 0),
            "service_status": service_status,
            "openrouter_configured": service_status.get("openrouter_configured", False),
            "available_models": ai_service.get_available_models(),
            "timestamp": response.get("timestamp", "")
        }
        
    except Exception as e:
        logger.error(f"AI test error: {str(e)}")
        return {
            "test_successful": False,
            "error": str(e),
            "message": "AI test failed - check your OpenRouter API key"
        }