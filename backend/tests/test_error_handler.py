"""
Unit tests for Error Handler

Tests the comprehensive error handling and recovery functionality including
retry mechanisms, circuit breakers, and graceful degradation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from backend.src.core.error_handler import (
    ErrorHandler,
    RetryMechanism,
    CircuitBreaker,
    GracefulDegradation,
    ApplicationError,
    SystemError,
    NetworkError,
    AuthenticationError,
    ValidationError,
    ExternalServiceError,
    ErrorCategory,
    ErrorSeverity,
    RecoveryStrategy,
    RetryConfig,
    CircuitBreakerConfig,
    CircuitBreakerState,
    ErrorContext
)


class TestApplicationErrors:
    """Test custom application error classes."""
    
    def test_application_error_creation(self):
        """Test basic application error creation."""
        error = ApplicationError(
            "Test error",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            details={"key": "value"}
        )
        
        assert error.message == "Test error"
        assert error.category == ErrorCategory.SYSTEM
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == {"key": "value"}
        assert error.timestamp is not None
    
    def test_system_error(self):
        """Test SystemError class."""
        error = SystemError("System failure")
        
        assert error.category == ErrorCategory.SYSTEM
        assert error.severity == ErrorSeverity.HIGH
        assert str(error) == "System failure"
    
    def test_network_error(self):
        """Test NetworkError class."""
        error = NetworkError("Connection failed")
        
        assert error.category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.MEDIUM
        assert str(error) == "Connection failed"
    
    def test_authentication_error(self):
        """Test AuthenticationError class."""
        error = AuthenticationError("Invalid credentials")
        
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.severity == ErrorSeverity.HIGH
        assert str(error) == "Invalid credentials"
    
    def test_validation_error(self):
        """Test ValidationError class."""
        error = ValidationError("Invalid input")
        
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.LOW
        assert str(error) == "Invalid input"


class TestRetryMechanism:
    """Test RetryMechanism class."""
    
    @pytest.fixture
    def retry_config(self):
        """Create retry configuration for testing."""
        return RetryConfig(
            max_attempts=3,
            base_delay=0.1,  # Short delay for testing
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False  # Disable jitter for predictable testing
        )
    
    @pytest.fixture
    def retry_mechanism(self, retry_config):
        """Create RetryMechanism instance for testing."""
        return RetryMechanism(retry_config)
    
    def test_calculate_delay_exponential(self, retry_mechanism):
        """Test exponential backoff delay calculation."""
        # First attempt
        delay1 = retry_mechanism.calculate_delay(1)
        assert delay1 == 0.1
        
        # Second attempt
        delay2 = retry_mechanism.calculate_delay(2)
        assert delay2 == 0.2
        
        # Third attempt
        delay3 = retry_mechanism.calculate_delay(3)
        assert delay3 == 0.4
    
    def test_calculate_delay_with_max_limit(self):
        """Test delay calculation with maximum limit."""
        config = RetryConfig(
            base_delay=10.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False
        )
        retry_mechanism = RetryMechanism(config)
        
        # Should be capped at max_delay
        delay = retry_mechanism.calculate_delay(5)
        assert delay == 5.0
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, retry_mechanism):
        """Test successful execution without retries."""
        mock_func = AsyncMock(return_value="success")
        
        result = await retry_mechanism.execute_with_retry(mock_func, "arg1", key="value")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", key="value")
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_eventual_success(self, retry_mechanism):
        """Test eventual success after retries."""
        mock_func = AsyncMock(side_effect=[
            NetworkError("Network error"),
            NetworkError("Network error"),
            "success"
        ])
        
        result = await retry_mechanism.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_max_attempts_exceeded(self, retry_mechanism):
        """Test failure after max attempts exceeded."""
        mock_func = AsyncMock(side_effect=NetworkError("Persistent error"))
        
        with pytest.raises(NetworkError, match="Persistent error"):
            await retry_mechanism.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 3  # max_attempts
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_no_retry_on_auth_error(self, retry_mechanism):
        """Test that authentication errors are not retried."""
        mock_func = AsyncMock(side_effect=AuthenticationError("Invalid token"))
        
        with pytest.raises(AuthenticationError, match="Invalid token"):
            await retry_mechanism.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 1  # No retries
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_sync_function(self, retry_mechanism):
        """Test retry mechanism with synchronous function."""
        call_count = 0
        
        def sync_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Network error")
            return "success"
        
        result = await retry_mechanism.execute_with_retry(sync_func)
        
        assert result == "success"
        assert call_count == 3


class TestCircuitBreaker:
    """Test CircuitBreaker class."""
    
    @pytest.fixture
    def circuit_breaker_config(self):
        """Create circuit breaker configuration for testing."""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1.0,  # Short timeout for testing
            name="test_breaker"
        )
    
    @pytest.fixture
    def circuit_breaker(self, circuit_breaker_config):
        """Create CircuitBreaker instance for testing."""
        return CircuitBreaker(circuit_breaker_config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self, circuit_breaker):
        """Test successful operation through circuit breaker."""
        mock_func = AsyncMock(return_value="success")
        
        result = await circuit_breaker.call(mock_func, "arg1")
        
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.success_count == 1
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures."""
        mock_func = AsyncMock(side_effect=ExternalServiceError("Service error"))
        
        # First two failures should not open circuit
        for _ in range(2):
            with pytest.raises(ExternalServiceError):
                await circuit_breaker.call(mock_func)
            assert circuit_breaker.state == CircuitBreakerState.CLOSED
        
        # Third failure should open circuit
        with pytest.raises(ExternalServiceError):
            await circuit_breaker.call(mock_func)
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_fails_fast_when_open(self, circuit_breaker):
        """Test circuit breaker fails fast when open."""
        # Force circuit breaker to open state
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.failure_count = 5
        
        mock_func = AsyncMock()
        
        with pytest.raises(ExternalServiceError, match="Circuit breaker.*is OPEN"):
            await circuit_breaker.call(mock_func)
        
        # Function should not be called
        mock_func.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self, circuit_breaker):
        """Test circuit breaker recovery through half-open state."""
        # Set up circuit breaker in open state with old failure time
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.failure_count = 3
        circuit_breaker.last_failure_time = datetime.utcnow() - timedelta(seconds=2)
        
        mock_func = AsyncMock(return_value="success")
        
        # Should attempt reset and succeed
        result = await circuit_breaker.call(mock_func)
        
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.success_count == 1
    
    def test_circuit_breaker_stats(self, circuit_breaker):
        """Test circuit breaker statistics."""
        circuit_breaker.success_count = 5
        circuit_breaker.failure_count = 2
        circuit_breaker.total_requests = 7
        
        stats = circuit_breaker.get_stats()
        
        assert stats.state == CircuitBreakerState.CLOSED
        assert stats.success_count == 5
        assert stats.failure_count == 2
        assert stats.total_requests == 7


class TestGracefulDegradation:
    """Test GracefulDegradation class."""
    
    @pytest.fixture
    def graceful_degradation(self):
        """Create GracefulDegradation instance for testing."""
        return GracefulDegradation()
    
    def test_register_fallback(self, graceful_degradation):
        """Test registering fallback handler."""
        def fallback_handler():
            return "fallback_result"
        
        graceful_degradation.register_fallback("test_service", fallback_handler)
        
        assert "test_service" in graceful_degradation.fallback_handlers
        assert graceful_degradation.fallback_handlers["test_service"] == fallback_handler
    
    def test_degrade_and_restore_service(self, graceful_degradation):
        """Test service degradation and restoration."""
        service_name = "test_service"
        
        # Initially not degraded
        assert service_name not in graceful_degradation.degraded_services
        
        # Degrade service
        graceful_degradation.degrade_service(service_name)
        assert service_name in graceful_degradation.degraded_services
        
        # Restore service
        graceful_degradation.restore_service(service_name)
        assert service_name not in graceful_degradation.degraded_services
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_normal_operation(self, graceful_degradation):
        """Test normal operation without fallback."""
        mock_primary = AsyncMock(return_value="primary_result")
        mock_fallback = Mock(return_value="fallback_result")
        
        graceful_degradation.register_fallback("test_service", mock_fallback)
        
        result = await graceful_degradation.execute_with_fallback(
            "test_service", mock_primary, "arg1"
        )
        
        assert result == "primary_result"
        mock_primary.assert_called_once_with("arg1")
        mock_fallback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_degraded_service(self, graceful_degradation):
        """Test fallback execution for degraded service."""
        mock_primary = AsyncMock()
        mock_fallback = AsyncMock(return_value="fallback_result")
        
        graceful_degradation.register_fallback("test_service", mock_fallback)
        graceful_degradation.degrade_service("test_service")
        
        result = await graceful_degradation.execute_with_fallback(
            "test_service", mock_primary, "arg1"
        )
        
        assert result == "fallback_result"
        mock_primary.assert_not_called()
        mock_fallback.assert_called_once_with("arg1")
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_no_fallback_available(self, graceful_degradation):
        """Test error when no fallback is available for degraded service."""
        mock_primary = AsyncMock()
        
        graceful_degradation.degrade_service("test_service")
        
        with pytest.raises(ExternalServiceError, match="no fallback available"):
            await graceful_degradation.execute_with_fallback(
                "test_service", mock_primary
            )
    
    @pytest.mark.asyncio
    async def test_auto_degrade_on_failure(self, graceful_degradation):
        """Test automatic service degradation on failure."""
        mock_primary = AsyncMock(side_effect=ExternalServiceError("Service failed"))
        
        with pytest.raises(ExternalServiceError):
            await graceful_degradation.execute_with_fallback(
                "test_service", mock_primary
            )
        
        # Service should be automatically degraded
        assert "test_service" in graceful_degradation.degraded_services


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    @pytest.fixture
    def error_handler(self):
        """Create ErrorHandler instance for testing."""
        handler = ErrorHandler()
        handler.clear_error_log()  # Start with clean log
        return handler
    
    @pytest.mark.asyncio
    async def test_handle_error_basic(self, error_handler):
        """Test basic error handling."""
        error = SystemError("Test system error")
        
        error_context = await error_handler.handle_error(
            error, 
            component="test_component",
            user_id="user123",
            request_id="req456"
        )
        
        assert error_context.category == ErrorCategory.SYSTEM
        assert error_context.severity == ErrorSeverity.HIGH
        assert error_context.message == "Test system error"
        assert error_context.component == "test_component"
        assert error_context.user_id == "user123"
        assert error_context.request_id == "req456"
        assert len(error_handler.error_log) == 1
    
    @pytest.mark.asyncio
    async def test_handle_error_with_custom_handler(self, error_handler):
        """Test error handling with custom handler."""
        custom_handler_called = False
        
        async def custom_handler(error_context):
            nonlocal custom_handler_called
            custom_handler_called = True
            assert error_context.category == ErrorCategory.VALIDATION
        
        error_handler.register_error_handler(ErrorCategory.VALIDATION, custom_handler)
        
        error = ValidationError("Invalid input")
        await error_handler.handle_error(error)
        
        assert custom_handler_called
    
    def test_register_circuit_breaker(self, error_handler):
        """Test circuit breaker registration."""
        config = CircuitBreakerConfig(name="test_cb")
        
        error_handler.register_circuit_breaker("test_service", config)
        
        assert "test_service" in error_handler.circuit_breakers
        assert error_handler.circuit_breakers["test_service"].config.name == "test_cb"
    
    @pytest.mark.asyncio
    async def test_with_retry_decorator(self, error_handler):
        """Test retry decorator."""
        call_count = 0
        
        @error_handler.with_retry(RetryConfig(max_attempts=3, base_delay=0.01))
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Network error")
            return "success"
        
        result = await test_function()
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_with_circuit_breaker_decorator(self, error_handler):
        """Test circuit breaker decorator."""
        @error_handler.with_circuit_breaker("test_service")
        async def test_function():
            return "success"
        
        result = await test_function()
        
        assert result == "success"
        assert "test_service" in error_handler.circuit_breakers
    
    @pytest.mark.asyncio
    async def test_with_fallback_decorator(self, error_handler):
        """Test fallback decorator."""
        async def fallback_handler():
            return "fallback_result"
        
        @error_handler.with_fallback("test_service", fallback_handler)
        async def test_function():
            return "primary_result"
        
        result = await test_function()
        
        assert result == "primary_result"
        assert "test_service" in error_handler.graceful_degradation.fallback_handlers
    
    def test_get_error_statistics(self, error_handler):
        """Test error statistics generation."""
        # Add some test errors
        error_handler.error_log.extend([
            ErrorContext(
                error_id="1",
                timestamp=datetime.utcnow(),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message="System error",
                details={}
            ),
            ErrorContext(
                error_id="2",
                timestamp=datetime.utcnow(),
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message="Network error",
                details={}
            ),
            ErrorContext(
                error_id="3",
                timestamp=datetime.utcnow(),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.LOW,
                message="Another system error",
                details={}
            )
        ])
        
        stats = error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 3
        assert stats["errors_by_category"]["system"] == 2
        assert stats["errors_by_category"]["network"] == 1
        assert stats["errors_by_severity"]["high"] == 1
        assert stats["errors_by_severity"]["medium"] == 1
        assert stats["errors_by_severity"]["low"] == 1
    
    def test_clear_error_log(self, error_handler):
        """Test clearing error log."""
        # Add test error
        error_handler.error_log.append(
            ErrorContext(
                error_id="1",
                timestamp=datetime.utcnow(),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                message="Test error",
                details={}
            )
        )
        
        assert len(error_handler.error_log) == 1
        
        error_handler.clear_error_log()
        
        assert len(error_handler.error_log) == 0


if __name__ == "__main__":
    pytest.main([__file__])