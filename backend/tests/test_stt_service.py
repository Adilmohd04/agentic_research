"""
Unit tests for Speech-to-Text Service

Tests the STT service functionality including voice activity detection,
noise reduction, and transcript logging.
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from typing import AsyncGenerator

from backend.src.voice.stt_service import (
    STTService,
    STTProvider,
    AudioConfig,
    TranscriptionResult,
    TranscriptionSession,
    TranscriptionStatus,
    VoiceActivityDetector,
    VoiceActivityResult,
    NoiseReducer,
    WebSpeechEngine,
    WhisperEngine
)


class TestAudioConfig:
    """Test AudioConfig dataclass."""
    
    def test_default_config(self):
        """Test default audio configuration."""
        config = AudioConfig()
        
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.chunk_size == 1024
        assert config.format == "float32"
        assert config.noise_reduction is True
        assert config.voice_activity_detection is True
        assert config.silence_threshold == 0.01
        assert config.silence_duration == 2.0
    
    def test_custom_config(self):
        """Test custom audio configuration."""
        config = AudioConfig(
            sample_rate=44100,
            channels=2,
            chunk_size=2048,
            noise_reduction=False
        )
        
        assert config.sample_rate == 44100
        assert config.channels == 2
        assert config.chunk_size == 2048
        assert config.noise_reduction is False


class TestTranscriptionResult:
    """Test TranscriptionResult dataclass."""
    
    def test_transcription_result_creation(self):
        """Test transcription result creation."""
        result = TranscriptionResult(
            transcript_id="test-123",
            text="Hello world",
            confidence=0.95,
            is_final=True,
            timestamp=1234567890.0,
            duration=2.5,
            language="en"
        )
        
        assert result.transcript_id == "test-123"
        assert result.text == "Hello world"
        assert result.confidence == 0.95
        assert result.is_final is True
        assert result.timestamp == 1234567890.0
        assert result.duration == 2.5
        assert result.language == "en"


class TestVoiceActivityDetector:
    """Test VoiceActivityDetector class."""
    
    @pytest.fixture
    def vad(self):
        """Create VAD instance for testing."""
        return VoiceActivityDetector(threshold=0.01, window_size=1024)
    
    def test_vad_initialization(self, vad):
        """Test VAD initialization."""
        assert vad.threshold == 0.01
        assert vad.window_size == 1024
        assert vad.sample_rate == 16000
        assert len(vad.energy_history) == 0
    
    def test_detect_voice_activity_silence(self, vad):
        """Test VAD with silence."""
        # Generate silent audio (low energy)
        silent_audio = np.zeros(1024, dtype=np.float32)
        audio_bytes = silent_audio.tobytes()
        
        result = vad.detect_voice_activity(audio_bytes)
        
        assert isinstance(result, VoiceActivityResult)
        assert result.is_speech is False
        assert result.energy_level < 0.01
        assert result.confidence >= 0.0
    
    def test_detect_voice_activity_speech(self, vad):
        """Test VAD with speech-like audio."""
        # Generate audio with higher energy
        speech_audio = np.random.normal(0, 0.1, 1024).astype(np.float32)
        audio_bytes = speech_audio.tobytes()
        
        result = vad.detect_voice_activity(audio_bytes)
        
        assert isinstance(result, VoiceActivityResult)
        assert result.energy_level > 0.0
        # Speech detection depends on energy level
    
    def test_adaptive_threshold(self, vad):
        """Test adaptive threshold calculation."""
        # Feed several audio chunks to build history
        for _ in range(5):
            audio = np.random.normal(0, 0.05, 1024).astype(np.float32)
            vad.detect_voice_activity(audio.tobytes())
        
        assert len(vad.energy_history) == 5
        
        # Test with higher energy audio
        high_energy_audio = np.random.normal(0, 0.2, 1024).astype(np.float32)
        result = vad.detect_voice_activity(high_energy_audio.tobytes())
        
        assert len(vad.energy_history) == 6


class TestNoiseReducer:
    """Test NoiseReducer class."""
    
    @pytest.fixture
    def noise_reducer(self):
        """Create NoiseReducer instance for testing."""
        return NoiseReducer(alpha=2.0, beta=0.01)
    
    def test_noise_reducer_initialization(self, noise_reducer):
        """Test noise reducer initialization."""
        assert noise_reducer.alpha == 2.0
        assert noise_reducer.beta == 0.01
        assert noise_reducer.noise_profile is None
        assert noise_reducer.noise_frames == 0
    
    @patch('backend.src.voice.stt_service.scipy.fft')
    def test_reduce_noise_without_scipy(self, mock_scipy, noise_reducer):
        """Test noise reduction without scipy."""
        # Mock scipy import error
        mock_scipy.side_effect = ImportError("scipy not available")
        
        audio_data = np.random.normal(0, 0.1, 1024).astype(np.float32)
        audio_bytes = audio_data.tobytes()
        
        # Should return original audio when scipy not available
        result = noise_reducer.reduce_noise(audio_bytes)
        assert result == audio_bytes
    
    def test_noise_profiling_phase(self, noise_reducer):
        """Test noise profiling phase."""
        audio_data = np.random.normal(0, 0.1, 1024).astype(np.float32)
        audio_bytes = audio_data.tobytes()
        
        # During noise profiling, should return original audio
        for i in range(5):
            result = noise_reducer.reduce_noise(audio_bytes)
            assert result == audio_bytes
            assert noise_reducer.noise_frames == i + 1


class TestWebSpeechEngine:
    """Test WebSpeechEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create WebSpeechEngine instance for testing."""
        return WebSpeechEngine()
    
    @pytest.mark.asyncio
    async def test_initialize(self, engine):
        """Test engine initialization."""
        config = AudioConfig()
        result = await engine.initialize(config)
        
        assert result is True
        assert engine.is_initialized is True
        assert engine.config == config
    
    @pytest.mark.asyncio
    async def test_transcribe_stream(self, engine):
        """Test stream transcription."""
        config = AudioConfig()
        await engine.initialize(config)
        
        # Mock audio stream
        async def mock_audio_stream():
            yield b"audio_chunk_1"
            yield b"audio_chunk_2"
        
        # Mock callback
        callback = Mock()
        
        await engine.transcribe_stream(mock_audio_stream(), callback)
        
        # Should call callback with result
        callback.assert_called_once()
        result = callback.call_args[0][0]
        assert isinstance(result, TranscriptionResult)
        assert result.text == "Web Speech API transcription result"
        assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_transcribe_file_not_supported(self, engine):
        """Test file transcription not supported."""
        config = AudioConfig()
        await engine.initialize(config)
        
        with pytest.raises(NotImplementedError):
            await engine.transcribe_file("test.wav")
    
    @pytest.mark.asyncio
    async def test_cleanup(self, engine):
        """Test engine cleanup."""
        config = AudioConfig()
        await engine.initialize(config)
        
        await engine.cleanup()
        assert engine.is_initialized is False


class TestWhisperEngine:
    """Test WhisperEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create WhisperEngine instance for testing."""
        return WhisperEngine(model_size="base")
    
    @pytest.mark.asyncio
    async def test_initialize_without_whisper(self, engine):
        """Test initialization without whisper installed."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'whisper'")):
            result = await engine.initialize(AudioConfig())
            assert result is False
            assert engine.is_initialized is False
    
    @pytest.mark.asyncio
    @patch('whisper.load_model')
    async def test_initialize_success(self, mock_load_model, engine):
        """Test successful initialization."""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        config = AudioConfig()
        result = await engine.initialize(config)
        
        assert result is True
        assert engine.is_initialized is True
        assert engine.model == mock_model
        assert engine.config == config
        mock_load_model.assert_called_once_with("base")
    
    @pytest.mark.asyncio
    @patch('whisper.load_model')
    async def test_transcribe_stream(self, mock_load_model, engine):
        """Test stream transcription."""
        # Mock whisper model
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "Hello world",
            "language": "en"
        }
        mock_load_model.return_value = mock_model
        
        config = AudioConfig()
        await engine.initialize(config)
        
        # Mock audio stream
        async def mock_audio_stream():
            audio_data = np.random.normal(0, 0.1, 1024).astype(np.float32)
            yield audio_data.tobytes()
        
        # Mock callback
        callback = Mock()
        
        await engine.transcribe_stream(mock_audio_stream(), callback)
        
        # Should call callback with result
        callback.assert_called_once()
        result = callback.call_args[0][0]
        assert isinstance(result, TranscriptionResult)
        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.confidence == 1.0
    
    @pytest.mark.asyncio
    @patch('whisper.load_model')
    async def test_transcribe_file(self, mock_load_model, engine):
        """Test file transcription."""
        # Mock whisper model
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "File transcription result",
            "language": "en",
            "duration": 5.0
        }
        mock_load_model.return_value = mock_model
        
        config = AudioConfig()
        await engine.initialize(config)
        
        result = await engine.transcribe_file("test.wav")
        
        assert isinstance(result, TranscriptionResult)
        assert result.text == "File transcription result"
        assert result.language == "en"
        assert result.duration == 5.0
        assert result.confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_transcribe_without_initialization(self, engine):
        """Test transcription without initialization."""
        async def mock_audio_stream():
            yield b"audio_chunk"
        
        with pytest.raises(RuntimeError, match="Whisper engine not initialized"):
            await engine.transcribe_stream(mock_audio_stream(), Mock())
        
        with pytest.raises(RuntimeError, match="Whisper engine not initialized"):
            await engine.transcribe_file("test.wav")


class TestSTTService:
    """Test STTService class."""
    
    @pytest.fixture
    def service(self):
        """Create STTService instance for testing."""
        return STTService(default_provider=STTProvider.WEB_SPEECH_API)
    
    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.default_provider == STTProvider.WEB_SPEECH_API
        assert isinstance(service.config, AudioConfig)
        assert len(service.engines) > 0
        assert STTProvider.WEB_SPEECH_API in service.engines
        assert STTProvider.WHISPER_LOCAL in service.engines
        assert len(service.sessions) == 0
    
    @pytest.mark.asyncio
    async def test_initialize_service(self, service):
        """Test service initialization."""
        result = await service.initialize()
        assert result is True
    
    def test_transcript_callbacks(self, service):
        """Test transcript callback management."""
        callback1 = Mock()
        callback2 = Mock()
        
        # Add callbacks
        service.add_transcript_callback(callback1)
        service.add_transcript_callback(callback2)
        assert len(service.transcript_callbacks) == 2
        
        # Remove callback
        service.remove_transcript_callback(callback1)
        assert len(service.transcript_callbacks) == 1
        assert callback2 in service.transcript_callbacks
    
    def test_notify_transcript_callbacks(self, service):
        """Test transcript callback notification."""
        callback1 = Mock()
        callback2 = Mock()
        
        service.add_transcript_callback(callback1)
        service.add_transcript_callback(callback2)
        
        result = TranscriptionResult(
            transcript_id="test-123",
            text="Test transcript",
            confidence=0.95,
            is_final=True,
            timestamp=1234567890.0,
            duration=1.0
        )
        
        service._notify_transcript_callbacks(result)
        
        callback1.assert_called_once_with(result)
        callback2.assert_called_once_with(result)
    
    def test_callback_error_handling(self, service):
        """Test callback error handling."""
        # Add callback that raises exception
        error_callback = Mock(side_effect=Exception("Callback error"))
        good_callback = Mock()
        
        service.add_transcript_callback(error_callback)
        service.add_transcript_callback(good_callback)
        
        result = TranscriptionResult(
            transcript_id="test-123",
            text="Test transcript",
            confidence=0.95,
            is_final=True,
            timestamp=1234567890.0,
            duration=1.0
        )
        
        # Should not raise exception, but still call good callback
        service._notify_transcript_callbacks(result)
        
        error_callback.assert_called_once_with(result)
        good_callback.assert_called_once_with(result)
    
    @pytest.mark.asyncio
    async def test_start_stop_session(self, service):
        """Test session management."""
        # Start session
        session_id = await service.start_session(conversation_id="conv-123")
        
        assert session_id in service.sessions
        session = service.sessions[session_id]
        assert session.conversation_id == "conv-123"
        assert session.provider == STTProvider.WEB_SPEECH_API
        assert session.status == TranscriptionStatus.IDLE
        
        # Stop session
        stopped_session = await service.stop_session(session_id)
        
        assert session_id not in service.sessions
        assert stopped_session is not None
        assert stopped_session.status == TranscriptionStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_transcribe_stream(self, service):
        """Test stream transcription."""
        await service.initialize()
        
        # Start session
        session_id = await service.start_session()
        
        # Mock audio stream
        async def mock_audio_stream():
            audio_data = np.random.normal(0, 0.1, 1024).astype(np.float32)
            yield audio_data.tobytes()
        
        # Mock callback to capture results
        results = []
        service.add_transcript_callback(lambda r: results.append(r))
        
        await service.transcribe_stream(session_id, mock_audio_stream())
        
        # Should have transcription result
        assert len(results) > 0
        result = results[0]
        assert isinstance(result, TranscriptionResult)
        
        # Session should be updated
        session = service.get_session(session_id)
        assert len(session.transcripts) > 0
    
    @pytest.mark.asyncio
    async def test_transcribe_stream_invalid_session(self, service):
        """Test stream transcription with invalid session."""
        async def mock_audio_stream():
            yield b"audio_chunk"
        
        with pytest.raises(ValueError, match="Session not found"):
            await service.transcribe_stream("invalid-session", mock_audio_stream())
    
    @pytest.mark.asyncio
    async def test_transcribe_file(self, service):
        """Test file transcription."""
        await service.initialize()
        
        # Mock the engine's transcribe_file method
        mock_result = TranscriptionResult(
            transcript_id="file-123",
            text="File transcription result",
            confidence=1.0,
            is_final=True,
            timestamp=1234567890.0,
            duration=5.0
        )
        
        engine = service.engines[STTProvider.WEB_SPEECH_API]
        engine.transcribe_file = AsyncMock(return_value=mock_result)
        
        result = await service.transcribe_file("test.wav")
        
        assert result == mock_result
        engine.transcribe_file.assert_called_once_with("test.wav")
    
    def test_get_session(self, service):
        """Test getting session."""
        # Non-existent session
        assert service.get_session("invalid") is None
        
        # Create session manually
        session = TranscriptionSession(
            session_id="test-123",
            conversation_id=None,
            provider=STTProvider.WEB_SPEECH_API,
            config=AudioConfig(),
            status=TranscriptionStatus.IDLE,
            created_at=1234567890.0,
            last_activity=1234567890.0
        )
        service.sessions["test-123"] = session
        
        retrieved = service.get_session("test-123")
        assert retrieved == session
    
    def test_get_active_sessions(self, service):
        """Test getting active sessions."""
        # Create sessions with different statuses
        sessions = [
            TranscriptionSession("s1", None, STTProvider.WEB_SPEECH_API, AudioConfig(), 
                               TranscriptionStatus.LISTENING, 1234567890.0, 1234567890.0),
            TranscriptionSession("s2", None, STTProvider.WEB_SPEECH_API, AudioConfig(), 
                               TranscriptionStatus.COMPLETED, 1234567890.0, 1234567890.0),
            TranscriptionSession("s3", None, STTProvider.WEB_SPEECH_API, AudioConfig(), 
                               TranscriptionStatus.PROCESSING, 1234567890.0, 1234567890.0),
            TranscriptionSession("s4", None, STTProvider.WEB_SPEECH_API, AudioConfig(), 
                               TranscriptionStatus.ERROR, 1234567890.0, 1234567890.0)
        ]
        
        for session in sessions:
            service.sessions[session.session_id] = session
        
        active = service.get_active_sessions()
        
        # Should only return listening and processing sessions
        assert len(active) == 2
        active_ids = {s.session_id for s in active}
        assert "s1" in active_ids  # LISTENING
        assert "s3" in active_ids  # PROCESSING
    
    def test_get_supported_providers(self, service):
        """Test getting supported providers."""
        providers = service.get_supported_providers()
        
        assert STTProvider.WEB_SPEECH_API in providers
        assert STTProvider.WHISPER_LOCAL in providers
        assert len(providers) >= 2
    
    def test_export_session_data(self, service):
        """Test session data export."""
        # Non-existent session
        assert service.export_session_data("invalid") is None
        
        # Create session
        session = TranscriptionSession(
            session_id="test-123",
            conversation_id="conv-456",
            provider=STTProvider.WEB_SPEECH_API,
            config=AudioConfig(),
            status=TranscriptionStatus.COMPLETED,
            created_at=1234567890.0,
            last_activity=1234567891.0,
            total_duration=5.0
        )
        service.sessions["test-123"] = session
        
        data = service.export_session_data("test-123")
        
        assert data is not None
        assert data["session_id"] == "test-123"
        assert data["conversation_id"] == "conv-456"
        assert data["total_duration"] == 5.0
    
    @pytest.mark.asyncio
    async def test_cleanup(self, service):
        """Test service cleanup."""
        await service.initialize()
        
        # Create some sessions
        session_id1 = await service.start_session()
        session_id2 = await service.start_session()
        
        assert len(service.sessions) == 2
        
        await service.cleanup()
        
        # All sessions should be stopped
        assert len(service.sessions) == 0


if __name__ == "__main__":
    pytest.main([__file__])