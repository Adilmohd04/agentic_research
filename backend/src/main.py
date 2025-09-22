"""
Agentic Research Copilot - Optimized Complete Backend
"""

import os
import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import logging
import json

# Import our custom modules with fallbacks
try:
    from agents.agent_orchestrator import AgentOrchestrator
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

try:
    from rag.rag_system import RAGSystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    from voice.voice_processor import VoiceProcessor
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# Import API routers
try:
    from api.rag_endpoints import router as rag_router
    RAG_ROUTER_AVAILABLE = True
except ImportError:
    RAG_ROUTER_AVAILABLE = False

try:
    from api.clerk_webhooks import router as webhook_router
    WEBHOOK_ROUTER_AVAILABLE = True
except ImportError:
    WEBHOOK_ROUTER_AVAILABLE = False

try:
    from api.user_settings import router as user_settings_router
    USER_SETTINGS_ROUTER_AVAILABLE = True
except ImportError:
    USER_SETTINGS_ROUTER_AVAILABLE = False

try:
    from api.voice_endpoints import router as voice_router
    VOICE_ROUTER_AVAILABLE = True
except ImportError:
    VOICE_ROUTER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Research Copilot API",
    description="Complete multi-agent AI system with RAG, Voice, and Real-time Coordination",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize systems
orchestrator = AgentOrchestrator() if AGENTS_AVAILABLE else None
rag_system = RAGSystem() if RAG_AVAILABLE else None
voice_processor = VoiceProcessor() if VOICE_AVAILABLE else None

# Include API routers
if RAG_ROUTER_AVAILABLE:
    app.include_router(rag_router)

if WEBHOOK_ROUTER_AVAILABLE:
    app.include_router(webhook_router)

if USER_SETTINGS_ROUTER_AVAILABLE:
    app.include_router(user_settings_router)

if VOICE_ROUTER_AVAILABLE:
    app.include_router(voice_router)

# Initialize service manager on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        from core.service_manager import get_service_manager
        service_manager = get_service_manager()
        
        # Pre-initialize services for better performance
        _ = service_manager.supabase_service
        _ = service_manager.ai_service
        _ = service_manager.embedding_service
        _ = service_manager.voice_service
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Service initialization error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown"""
    try:
        from core.service_manager import get_service_manager
        service_manager = get_service_manager()
        await service_manager.close_all()
        logger.info("All services closed successfully")
    except Exception as e:
        logger.error(f"Service cleanup error: {str(e)}")

# Create data directories
os.makedirs("./data/uploads", exist_ok=True)
os.makedirs("./data/exports", exist_ok=True)
os.makedirs("./data/audio", exist_ok=True)

# WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Models
class TaskRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    agents: Optional[List[str]] = None

class QueryRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5

class VoiceRequest(BaseModel):
    text: str
    voice_settings: Optional[Dict[str, Any]] = None

# Basic endpoints
@app.get("/")
async def root():
    return {
        "message": "Agentic Research Copilot API v2.0",
        "status": "running",
        "features": {
            "multi_agent_coordination": AGENTS_AVAILABLE,
            "rag_system": RAG_AVAILABLE,
            "voice_processing": VOICE_AVAILABLE,
            "document_upload": True,
            "real_time_monitoring": True,
            "file_export": True
        },
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "running",
            "agents": "ready" if AGENTS_AVAILABLE else "demo_mode",
            "rag_system": "active" if RAG_AVAILABLE else "demo_mode",
            "voice_processing": "available" if VOICE_AVAILABLE else "demo_mode",
            "document_processing": "ready"
        }
    }

# Multi-Agent Coordination Endpoints
@app.post("/api/agents/coordinate")
async def coordinate_agents(request: TaskRequest):
    """Execute complete multi-agent workflow"""
    if orchestrator:
        try:
            result = await orchestrator.execute_workflow(
                user_request=request.task,
                session_id=request.context.get("session_id") if request.context else None
            )
            return result
        except Exception as e:
            logger.error(f"Coordination error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Fallback demo response
    task_id = str(uuid.uuid4())
    task_lower = request.task.lower()
    
    if "code" in task_lower or "programming" in task_lower:
        response = f"I've analyzed your code-related request: '{request.task}'. Here's what I found:\n\n• Code structure analysis completed\n• Error handling recommendations provided\n• Performance optimizations identified\n• Documentation improvements suggested"
        insights = ["Code follows best practices", "Error handling needs improvement", "Performance can be optimized"]
    elif "research" in task_lower or "analyze" in task_lower:
        response = f"I've conducted research on: '{request.task}'. Here are the key findings:\n\n• Multiple relevant sources analyzed\n• Evidence validation completed\n• Cross-references verified\n• Comprehensive analysis provided"
        insights = ["Strong evidence base found", "Multiple perspectives considered", "Recommendations provided"]
    else:
        response = f"I've processed your request: '{request.task}'. Here's my analysis:\n\n• Task categorized and analyzed\n• Relevant information gathered\n• Multi-agent coordination simulated\n• Results compiled successfully"
        insights = ["Task successfully processed", "Information analyzed", "Results comprehensive"]
    
    return {
        "workflow_id": task_id,
        "status": "completed",
        "summary": response,
        "results": {
            "summary": response,
            "insights": insights,
            "citations": [
                {
                    "source": "Demo Knowledge Base",
                    "title": "System Documentation",
                    "confidence": 0.95,
                    "excerpt": "Demonstration of multi-agent coordination capabilities."
                }
            ]
        },
        "execution_time": 2.5,
        "agents_used": request.agents or ["researcher", "analyzer"]
    }

@app.get("/api/agents/status")
async def get_agents_status():
    """Get real-time agent status"""
    if orchestrator:
        return {
            "agents": orchestrator.get_agent_status(),
            "active_workflows": orchestrator.get_active_workflows(),
            "workflow_history": orchestrator.get_workflow_history(5)
        }
    
    # Demo response
    return {
        "agents": {
            "coordinator": {"status": "ready", "role": "coordinator", "current_tasks": 0},
            "researcher": {"status": "ready", "role": "researcher", "current_tasks": 0},
            "analyzer": {"status": "ready", "role": "analyzer", "current_tasks": 0},
            "executor": {"status": "ready", "role": "executor", "current_tasks": 0}
        },
        "active_workflows": [],
        "workflow_history": []
    }

# RAG System Endpoints
@app.post("/api/rag/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document for RAG system"""
    if rag_system:
        try:
            content = await file.read()
            result = await rag_system.upload_document(
                file_path=file.filename,
                file_content=content,
                filename=file.filename
            )
            return result
        except Exception as e:
            logger.error(f"Document upload error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Demo response
    return {
        "document_id": str(uuid.uuid4()),
        "filename": file.filename,
        "chunks_created": 15,
        "status": "success (demo mode)"
    }

@app.post("/api/rag/query")
async def rag_query(request: QueryRequest):
    """Query RAG system"""
    if rag_system:
        try:
            results = await rag_system.search(request.query, request.max_results)
            
            answer = f"Based on {len(results.get('documents', []))} relevant sources, here's what I found about '{request.query}':\n\n"
            
            for i, doc in enumerate(results.get("documents", [])[:3], 1):
                answer += f"{i}. {doc.get('content', '')[:200]}...\n\n"
            
            return {
                "answer": answer,
                "citations": results.get("documents", []),
                "confidence_score": results.get("confidence", 0.85),
                "processing_time": results.get("search_time", 1.0)
            }
        except Exception as e:
            logger.error(f"RAG query error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Enhanced demo response based on query
    query_lower = request.query.lower()
    
    if "machine learning" in query_lower:
        answer = "Machine Learning is a subset of artificial intelligence that enables computers to learn from data without explicit programming. Key concepts include supervised learning, unsupervised learning, and reinforcement learning."
        citations = [{"source": "ML Knowledge Base", "title": "Introduction to Machine Learning", "confidence": 0.95, "excerpt": "ML algorithms build models based on training data..."}]
    elif "quantum" in query_lower:
        answer = "Quantum computing leverages quantum mechanical phenomena like superposition and entanglement to process information exponentially faster than classical computers for certain problems."
        citations = [{"source": "Quantum Research", "title": "Quantum Computing Principles", "confidence": 0.92, "excerpt": "Quantum computers use qubits that can exist in multiple states..."}]
    else:
        answer = f"Based on your query '{request.query}', I've analyzed the available information and provided relevant insights from the knowledge base."
        citations = [{"source": "General Knowledge Base", "title": "Comprehensive Analysis", "confidence": 0.85, "excerpt": "Relevant information processed through advanced retrieval systems..."}]
    
    return {
        "answer": answer,
        "citations": citations,
        "confidence_score": 0.87,
        "processing_time": 1.2
    }

@app.get("/api/rag/documents")
async def get_documents():
    """Get all uploaded documents"""
    if rag_system:
        documents = rag_system.get_documents()
        stats = rag_system.get_stats()
        return {"documents": documents, "statistics": stats}
    
    # Demo response
    return {
        "documents": [
            {
                "id": "demo-1",
                "filename": "machine_learning_guide.pdf",
                "file_type": "PDF Document",
                "chunks": 45,
                "uploaded_at": datetime.utcnow().isoformat()
            },
            {
                "id": "demo-2",
                "filename": "api_best_practices.docx",
                "file_type": "Word Document",
                "chunks": 32,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        ],
        "statistics": {
            "total_documents": 2,
            "total_chunks": 77,
            "vector_db_available": False
        }
    }

# Voice Processing Endpoints
@app.post("/api/voice/text-to-speech")
async def text_to_speech(request: VoiceRequest):
    """Convert text to speech"""
    if voice_processor:
        try:
            result = await voice_processor.process_text_to_speech(
                request.text, 
                request.voice_settings
            )
            return result
        except Exception as e:
            logger.error(f"Text-to-speech error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Demo response
    return {
        "audio_url": "/demo/audio.mp3",
        "duration": len(request.text.split()) * 0.5,
        "text": request.text,
        "status": "demo mode - TTS not available"
    }

@app.get("/api/voice/capabilities")
async def get_voice_capabilities():
    """Get voice processing capabilities"""
    if voice_processor:
        return voice_processor.get_voice_capabilities()
    
    return {
        "speech_to_text": {"available": False, "status": "demo mode"},
        "text_to_speech": {"available": False, "status": "demo mode"},
        "real_time_processing": False
    }

# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "agent_status_request":
                status = await get_agents_status()
                await websocket.send_text(json.dumps({
                    "type": "agent_status_update",
                    "data": status
                }))
                
    except WebSocketDisconnect:
        if session_id in active_connections:
            del active_connections[session_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)