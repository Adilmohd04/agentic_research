"""
Unit tests for Text-to-Speech Service

Tests the TTS service functionality including voice synthesis,
voice selection, and speech rate configuration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from backend.src.voice.tts_service import (
    TTSService,
    TTSProvider,
    VoiceConfig,
    VoiceGender,
    SpeechRequest,
    SpeechResult,
    SpeechSession,
    SpeechStatus,
    WebSpeechTTSEngine,
    EdgeTTSEngine,
    OpenAITTSEngine
)


class TestVoiceConfig:
    """Test VoiceConfig dataclass."""
    
    def test_default_config(self):
        """Test default voice configuration."""
        config = VoiceConfig()
        
        assert config.voice_id == "default"
        assert config.language == "en-US"
        assert config.gender == VoiceGender.FEMALE
        assert config.speed == 1.0
        assert config.pitch == 1.0
        assert config.volume == 1.0
        assert config.sample_rate == 22050
        assert config.format == "wav"
        assert config.quality == "standard"


class TestWebSpeechTTSEngine:
    """Test WebSpeechTTSEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create WebSpeechTTSEngine instance for testing."""
        return WebSpeechTTSEngine()
    
    @pytest.mark.asyncio
    async def test_initialize(self, engine):
        """Test engine initialization."""
        config = VoiceConfig()
        result = await engine.initialize(config)
        
        assert result is True
        assert engine.is_initialized is True
        assert engine.config == config
    
    @pytest.mark.asyncio
    async def test_synthesize(self, engine):
        """Test speech synthesis."""
        config = VoiceConfig()
        await engine.initialize(config)
        
        result = await engine.synthesize("Hello world", config)
        
        assert isinstance(result, SpeechResult)
        assert result.success is True
        assert result.voice_config == config
        assert result.format == "client-side"
        assert result.duration > 0


class TestTTSService:
    """Test TTSService class."""
    
    @pytest.fixture
    def service(self):
        """Create TTSService instance for testing."""
        return TTSService(default_provider=TTSProvider.WEB_SPEECH_API)
    
    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.default_provider == TTSProvider.WEB_SPEECH_API
        assert isinstance(service.voice_config, VoiceConfig)
        assert len(service.engines) > 0
        assert TTSProvider.WEB_SPEECH_API in service.engines
        assert len(service.sessions) == 0
        assert service.is_playing is False
    
    @pytest.mark.asyncio
    async def test_initialize_service(self, service):
        """Test service initialization."""
        result = await service.initialize()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_start_stop_session(self, service):
        """Test session management."""
        # Start session
        session_id = await service.start_session(conversation_id="conv-123")
        
        assert session_id in service.sessions
        session = service.sessions[session_id]
        assert session.conversation_id == "conv-123"
        assert session.provider == TTSProvider.WEB_SPEECH_API
        assert session.status == SpeechStatus.IDLE
        
        # Stop session
        stopped_session = await service.stop_session(session_id)
        
        assert session_id not in service.sessions
        assert stopped_session is not None
        assert stopped_session.status == SpeechStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__])