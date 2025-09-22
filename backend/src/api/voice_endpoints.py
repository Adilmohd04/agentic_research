"""
Voice Processing API Endpoints
Handles TTS, STT, and voice-related functionality
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from ..voice.voice_service import get_voice_service
from ..core.service_manager import get_service_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "alloy"
    speed: Optional[float] = 1.0
    use_openai: Optional[bool] = True

class STTRequest(BaseModel):
    language: Optional[str] = "en"

def get_user_id(x_user_id: str = Header(None, alias="X-User-ID")):
    """Extract user ID from header"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return x_user_id

@router.post("/text-to-speech")
async def text_to_speech(
    request: TTSRequest,
    user_id: str = Depends(get_user_id)
):
    """Convert text to speech"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 4000:
            raise HTTPException(status_code=400, detail="Text too long (max 4000 characters)")
        
        voice_service = get_voice_service()
        
        # Get user's API keys for OpenAI TTS
        service_manager = get_service_manager()
        user_api_keys = await service_manager.get_user_api_keys(user_id)
        
        # Use user's OpenAI key if available
        if user_api_keys.get('openai_api_key') and request.use_openai:
            # Temporarily set user's API key
            original_key = os.getenv('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = user_api_keys['openai_api_key']
            
            try:
                result = await voice_service.text_to_speech(
                    text=request.text,
                    voice=request.voice,
                    speed=request.speed,
                    use_openai=True
                )
            finally:
                # Restore original key
                if original_key:
                    os.environ['OPENAI_API_KEY'] = original_key
                else:
                    os.environ.pop('OPENAI_API_KEY', None)
        else:
            # Use free gTTS
            result = await voice_service.text_to_speech(
                text=request.text,
                voice=request.voice,
                speed=request.speed,
                use_openai=False
            )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail="Text-to-speech failed")

@router.post("/speech-to-text")
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = "en",
    user_id: str = Depends(get_user_id)
):
    """Convert speech to text"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (25MB limit)
        content = await file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 25MB)")
        
        # Check file format
        allowed_formats = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in allowed_formats:
            raise HTTPException(status_code=400, detail=f"Unsupported format. Allowed: {', '.join(allowed_formats)}")
        
        voice_service = get_voice_service()
        
        # Get user's API keys for OpenAI Whisper
        service_manager = get_service_manager()
        user_api_keys = await service_manager.get_user_api_keys(user_id)
        
        # Create file-like object from content
        from io import BytesIO
        audio_file = BytesIO(content)
        audio_file.name = file.filename
        
        # Use user's OpenAI key if available
        if user_api_keys.get('openai_api_key'):
            # Temporarily set user's API key
            original_key = os.getenv('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = user_api_keys['openai_api_key']
            
            try:
                result = await voice_service.speech_to_text(audio_file, language)
            finally:
                # Restore original key
                if original_key:
                    os.environ['OPENAI_API_KEY'] = original_key
                else:
                    os.environ.pop('OPENAI_API_KEY', None)
        else:
            # Use free speech recognition
            result = await voice_service.speech_to_text(audio_file, language)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT error: {str(e)}")
        raise HTTPException(status_code=500, detail="Speech-to-text failed")

@router.get("/audio/{audio_id}")
async def get_audio_file(audio_id: str):
    """Get generated audio file"""
    try:
        voice_service = get_voice_service()
        audio_path = await voice_service.get_audio_file(audio_id)
        
        if not audio_path or not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=str(audio_path),
            media_type="audio/mpeg",
            filename=f"audio_{audio_id}.mp3"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio file error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audio file")

@router.get("/capabilities")
async def get_voice_capabilities():
    """Get voice processing capabilities"""
    try:
        voice_service = get_voice_service()
        capabilities = voice_service.get_voice_capabilities()
        return capabilities
        
    except Exception as e:
        logger.error(f"Capabilities error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get capabilities")

@router.get("/health")
async def voice_health_check():
    """Check voice service health"""
    try:
        voice_service = get_voice_service()
        health = await voice_service.health_check()
        return health
        
    except Exception as e:
        logger.error(f"Voice health check error: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

@router.post("/voice-chat")
async def voice_chat(
    file: UploadFile = File(...),
    language: str = "en",
    voice: str = "alloy",
    user_id: str = Depends(get_user_id)
):
    """Complete voice chat: STT -> AI -> TTS"""
    try:
        # Step 1: Convert speech to text
        content = await file.read()
        from io import BytesIO
        audio_file = BytesIO(content)
        audio_file.name = file.filename
        
        voice_service = get_voice_service()
        service_manager = get_service_manager()
        user_api_keys = await service_manager.get_user_api_keys(user_id)
        
        # STT
        stt_result = await voice_service.speech_to_text(audio_file, language)
        if "error" in stt_result:
            raise HTTPException(status_code=500, detail=f"STT failed: {stt_result['error']}")
        
        user_text = stt_result["text"]
        
        # Step 2: Get AI response
        ai_service = service_manager.ai_service
        
        messages = [{"role": "user", "content": user_text}]
        ai_response = await ai_service.generate_response(
            messages=messages,
            user_api_keys=user_api_keys
        )
        
        if ai_response.get("status") != "success":
            raise HTTPException(status_code=500, detail="AI response failed")
        
        ai_text = ai_response["response"]
        
        # Step 3: Convert AI response to speech
        tts_result = await voice_service.text_to_speech(
            text=ai_text,
            voice=voice,
            use_openai=bool(user_api_keys.get('openai_api_key'))
        )
        
        if "error" in tts_result:
            raise HTTPException(status_code=500, detail=f"TTS failed: {tts_result['error']}")
        
        return {
            "user_text": user_text,
            "ai_response": ai_text,
            "audio_id": tts_result["audio_id"],
            "audio_url": tts_result["audio_url"],
            "model_used": ai_response.get("model_used"),
            "tokens_used": ai_response.get("tokens_used", 0),
            "processing_time": {
                "stt": "~1s",
                "ai": "~2s", 
                "tts": "~1s"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Voice chat failed")