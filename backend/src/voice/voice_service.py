"""
Voice Processing Service
Handles Text-to-Speech (TTS) and Speech-to-Text (STT) functionality
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, BinaryIO
from pathlib import Path
import tempfile
import uuid

try:
    import speech_recognition as sr
    from gtts import gTTS
    import pygame
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceService:
    """Voice processing service with TTS and STT capabilities"""
    
    def __init__(self):
        self.voice_enabled = os.getenv('VOICE_ENABLED', 'true').lower() == 'true'
        self.storage_path = Path(os.getenv('VOICE_STORAGE_PATH', './data/voice'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize speech recognition
        if VOICE_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Initialize pygame for audio playback
            try:
                pygame.mixer.init()
            except Exception as e:
                logger.warning(f"Could not initialize pygame mixer: {e}")
        
        # OpenAI settings for advanced voice processing
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.tts_model = os.getenv('TTS_MODEL', 'tts-1')
        self.stt_model = os.getenv('STT_MODEL', 'whisper-1')
        
        logger.info(f"Voice Service initialized - Enabled: {self.voice_enabled}")
    
    async def text_to_speech(
        self, 
        text: str, 
        voice: str = "alloy",
        speed: float = 1.0,
        use_openai: bool = True
    ) -> Dict[str, Any]:
        """Convert text to speech"""
        try:
            if not self.voice_enabled:
                return {"error": "Voice processing is disabled"}
            
            if use_openai and self.openai_api_key and OPENAI_AVAILABLE:
                return await self._openai_tts(text, voice, speed)
            elif VOICE_AVAILABLE:
                return await self._gtts_tts(text)
            else:
                return {"error": "Voice processing not available"}
                
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            return {"error": str(e)}
    
    async def speech_to_text(
        self, 
        audio_file: BinaryIO,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Convert speech to text"""
        try:
            if not self.voice_enabled:
                return {"error": "Voice processing is disabled"}
            
            if self.openai_api_key and OPENAI_AVAILABLE:
                return await self._openai_stt(audio_file, language)
            elif VOICE_AVAILABLE:
                return await self._speech_recognition_stt(audio_file, language)
            else:
                return {"error": "Speech recognition not available"}
                
        except Exception as e:
            logger.error(f"STT error: {str(e)}")
            return {"error": str(e)}
    
    async def _openai_tts(self, text: str, voice: str, speed: float) -> Dict[str, Any]:
        """OpenAI Text-to-Speech"""
        try:
            client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            
            response = await client.audio.speech.create(
                model=self.tts_model,
                voice=voice,
                input=text,
                speed=speed
            )
            
            # Save audio file
            audio_id = str(uuid.uuid4())
            audio_path = self.storage_path / f"tts_{audio_id}.mp3"
            
            with open(audio_path, 'wb') as f:
                async for chunk in response.iter_bytes():
                    f.write(chunk)
            
            return {
                "audio_id": audio_id,
                "audio_path": str(audio_path),
                "audio_url": f"/api/voice/audio/{audio_id}",
                "duration": len(text.split()) * 0.5,  # Rough estimate
                "model": self.tts_model,
                "voice": voice,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {str(e)}")
            return {"error": str(e)}
    
    async def _gtts_tts(self, text: str) -> Dict[str, Any]:
        """Google Text-to-Speech (Free)"""
        try:
            # Generate TTS
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save audio file
            audio_id = str(uuid.uuid4())
            audio_path = self.storage_path / f"tts_{audio_id}.mp3"
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, tts.save, str(audio_path))
            
            return {
                "audio_id": audio_id,
                "audio_path": str(audio_path),
                "audio_url": f"/api/voice/audio/{audio_id}",
                "duration": len(text.split()) * 0.6,  # Rough estimate
                "model": "gtts",
                "voice": "default",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"gTTS error: {str(e)}")
            return {"error": str(e)}
    
    async def _openai_stt(self, audio_file: BinaryIO, language: str) -> Dict[str, Any]:
        """OpenAI Speech-to-Text (Whisper)"""
        try:
            client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            
            transcript = await client.audio.transcriptions.create(
                model=self.stt_model,
                file=audio_file,
                language=language
            )
            
            return {
                "text": transcript.text,
                "language": language,
                "model": self.stt_model,
                "confidence": 0.95,  # Whisper doesn't provide confidence scores
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"OpenAI STT error: {str(e)}")
            return {"error": str(e)}
    
    async def _speech_recognition_stt(self, audio_file: BinaryIO, language: str) -> Dict[str, Any]:
        """Speech Recognition STT (Free)"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_file.read())
                temp_path = temp_file.name
            
            # Process audio
            with sr.AudioFile(temp_path) as source:
                audio = self.recognizer.record(source)
            
            # Recognize speech
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None, 
                self.recognizer.recognize_google, 
                audio, 
                None, 
                language
            )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return {
                "text": text,
                "language": language,
                "model": "google_speech_recognition",
                "confidence": 0.8,  # Estimated
                "status": "success"
            }
            
        except sr.UnknownValueError:
            return {"error": "Could not understand audio"}
        except sr.RequestError as e:
            return {"error": f"Speech recognition service error: {e}"}
        except Exception as e:
            logger.error(f"Speech recognition error: {str(e)}")
            return {"error": str(e)}
    
    async def get_audio_file(self, audio_id: str) -> Optional[Path]:
        """Get audio file by ID"""
        try:
            audio_path = self.storage_path / f"tts_{audio_id}.mp3"
            if audio_path.exists():
                return audio_path
            return None
        except Exception as e:
            logger.error(f"Error getting audio file: {str(e)}")
            return None
    
    def get_voice_capabilities(self) -> Dict[str, Any]:
        """Get voice processing capabilities"""
        return {
            "voice_enabled": self.voice_enabled,
            "tts_available": {
                "openai": bool(self.openai_api_key and OPENAI_AVAILABLE),
                "gtts": VOICE_AVAILABLE,
                "models": ["tts-1", "tts-1-hd"] if self.openai_api_key else ["gtts"]
            },
            "stt_available": {
                "openai_whisper": bool(self.openai_api_key and OPENAI_AVAILABLE),
                "google_speech": VOICE_AVAILABLE,
                "models": ["whisper-1"] if self.openai_api_key else ["google"]
            },
            "supported_voices": [
                "alloy", "echo", "fable", "onyx", "nova", "shimmer"
            ] if self.openai_api_key else ["default"],
            "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
            "max_audio_length": "25MB",
            "supported_formats": ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check voice service health"""
        try:
            capabilities = self.get_voice_capabilities()
            
            return {
                "status": "healthy" if self.voice_enabled else "disabled",
                "voice_enabled": self.voice_enabled,
                "tts_ready": capabilities["tts_available"]["openai"] or capabilities["tts_available"]["gtts"],
                "stt_ready": capabilities["stt_available"]["openai_whisper"] or capabilities["stt_available"]["google_speech"],
                "storage_path": str(self.storage_path),
                "storage_writable": os.access(self.storage_path, os.W_OK),
                "dependencies": {
                    "speech_recognition": VOICE_AVAILABLE,
                    "openai": OPENAI_AVAILABLE,
                    "pygame": VOICE_AVAILABLE
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "voice_enabled": False
            }

# Global voice service instance
_voice_service: Optional[VoiceService] = None

def get_voice_service() -> VoiceService:
    """Get global voice service instance"""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service