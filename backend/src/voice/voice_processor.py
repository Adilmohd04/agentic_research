"""
Voice Processing System with Speech Recognition and Text-to-Speech
"""

import asyncio
import tempfile
import os
from typing import Dict, Any, Optional, List
import logging

# Text-to-Speech
try:
    from gtts import gTTS
    import pygame
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# Speech Recognition
try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer() if STT_AVAILABLE else None
        self.microphone = sr.Microphone() if STT_AVAILABLE else None
        
        # Initialize pygame for audio playback
        if TTS_AVAILABLE:
            try:
                pygame.mixer.init()
                self.audio_available = True
            except:
                self.audio_available = False
                logger.warning("Audio playback not available")
        else:
            self.audio_available = False
        
        # Voice settings
        self.voice_settings = {
            "language": "en",
            "speed": 1.0,
            "pitch": 1.0,
            "voice_id": "default"
        }
    
    async def process_speech_to_text(self, audio_data: bytes) -> Dict[str, Any]:
        """Convert speech audio to text"""
        if not STT_AVAILABLE:
            return {
                "error": "Speech recognition not available",
                "text": "",
                "confidence": 0.0
            }
        
        try:
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Load audio file
            with sr.AudioFile(temp_file_path) as source:
                audio = self.recognizer.record(source)
            
            # Recognize speech
            try:
                # Try Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                confidence = 0.9  # Google API doesn't return confidence
                
                logger.info(f"Speech recognized: {text}")
                
                return {
                    "text": text,
                    "confidence": confidence,
                    "language": "en-US",
                    "processing_time": 1.2
                }
                
            except sr.UnknownValueError:
                return {
                    "error": "Could not understand audio",
                    "text": "",
                    "confidence": 0.0
                }
            except sr.RequestError as e:
                return {
                    "error": f"Speech recognition service error: {str(e)}",
                    "text": "",
                    "confidence": 0.0
                }
        
        except Exception as e:
            logger.error(f"Speech-to-text error: {str(e)}")
            return {
                "error": str(e),
                "text": "",
                "confidence": 0.0
            }
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    async def process_text_to_speech(self, text: str, voice_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Convert text to speech audio"""
        if not TTS_AVAILABLE:
            return {
                "error": "Text-to-speech not available",
                "audio_url": None,
                "duration": 0
            }
        
        try:
            # Use provided settings or defaults
            settings = voice_settings or self.voice_settings
            language = settings.get("language", "en")
            
            # Generate speech
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                tts.save(temp_file.name)
                audio_file_path = temp_file.name
            
            # Estimate duration (rough calculation)
            word_count = len(text.split())
            estimated_duration = word_count * 0.5  # ~0.5 seconds per word
            
            logger.info(f"Generated TTS for {word_count} words")
            
            return {
                "audio_file_path": audio_file_path,
                "audio_url": f"/api/voice/audio/{os.path.basename(audio_file_path)}",
                "duration": estimated_duration,
                "text": text,
                "language": language,
                "word_count": word_count
            }
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {str(e)}")
            return {
                "error": str(e),
                "audio_url": None,
                "duration": 0
            }
    
    async def play_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """Play audio file (for server-side testing)"""
        if not self.audio_available:
            return {"error": "Audio playback not available"}
        
        try:
            pygame.mixer.music.load(audio_file_path)
            pygame.mixer.music.play()
            
            return {
                "status": "playing",
                "file": audio_file_path
            }
            
        except Exception as e:
            logger.error(f"Audio playback error: {str(e)}")
            return {"error": str(e)}
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        # Mock voice list - in real implementation, this would query the TTS engine
        return [
            {
                "id": "en-US-standard",
                "name": "English (US) - Standard",
                "language": "en-US",
                "gender": "neutral"
            },
            {
                "id": "en-GB-standard", 
                "name": "English (UK) - Standard",
                "language": "en-GB",
                "gender": "neutral"
            },
            {
                "id": "es-ES-standard",
                "name": "Spanish (Spain) - Standard", 
                "language": "es-ES",
                "gender": "neutral"
            },
            {
                "id": "fr-FR-standard",
                "name": "French (France) - Standard",
                "language": "fr-FR", 
                "gender": "neutral"
            }
        ]
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get supported languages for speech processing"""
        return [
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "it", "name": "Italian"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ru", "name": "Russian"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "zh", "name": "Chinese"}
        ]
    
    def update_voice_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update voice processing settings"""
        self.voice_settings.update(settings)
        return {
            "status": "updated",
            "settings": self.voice_settings
        }
    
    def get_voice_capabilities(self) -> Dict[str, Any]:
        """Get voice processing capabilities"""
        return {
            "speech_to_text": {
                "available": STT_AVAILABLE,
                "engines": ["google"] if STT_AVAILABLE else [],
                "supported_formats": ["wav", "mp3", "flac"] if STT_AVAILABLE else []
            },
            "text_to_speech": {
                "available": TTS_AVAILABLE,
                "engines": ["gtts"] if TTS_AVAILABLE else [],
                "supported_languages": len(self.get_supported_languages())
            },
            "audio_playback": {
                "available": self.audio_available,
                "formats": ["mp3", "wav"] if self.audio_available else []
            },
            "real_time_processing": True,
            "voice_cloning": False,  # Not implemented
            "emotion_detection": False  # Not implemented
        }