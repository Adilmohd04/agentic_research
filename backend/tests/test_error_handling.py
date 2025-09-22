"""
Unit tests for comprehensive error handling and recovery system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.error_handler import (
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
    TimeoutError,
    ErrorCategory,
    ErrorSeverity,
    RetryConfig,
    CircuitBreakerConfig,
    CircuitBreakerState,
    error_handler
)
from src.api.error_handling import (
    ErrorHandlingMiddleware,
    setup_error_handlers,
    get_http_status_code,
    router as error_router
)


class TestApplicationErrors:
    """Test custom application error classes."""
    
    def test_application_error_creation(self):
        """Test creating application error with all parameters."""
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
        assert isinstance(error.timestamp, datetime)
    
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
    """Test retry mechanism with exponential backoff."""
    
    def test_calculate_delay_exponential(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=False
        )
        retry = RetryMechanism(config)
        
        assert retry.calculate_delay(1) == 1.0
        assert retry.calculate_delay(2) == 2.0
        assert retry.calculate_delay(3) == 4.0
        assert retry.calculate_delay(4) == 8.0
    
    def test_calculate_delay_linear(self):
        """Test linear backoff delay calculation."""
        config = RetryConfig(
            base_delay=1.0,
            backoff_strategy="linear",
            jitter=False
        )
        retry = RetryMechanism(config)
        
        assert retry.calculate_delay(1) == 1.0
        assert retry.calculate_delay(2) == 2.0
        assert retry.calculate_delay(3) == 3.0
    
    def test_calculate_delay_fixed(self):
        """Test fixed delay calculation."""
        config = RetryConfig(
            base_delay=2.0,
            backoff_strategy="fixed",
            jitter=False
        )
        retry = RetryMechanism(config)
        
        assert retry.calculate_delay(1) == 2.0
        assert retry.calculate_delay(2) == 2.0
        assert retry.calculate_delay(3) == 2.0
    
    def test_calculate_delay_max_limit(self):
        """Test maximum delay limit."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=5.0,
            jitter=False
        )
        retry = RetryMechanism(config)
        
        # Should be capped at max_delay
        assert retry.calculate_delay(10) == 5.0
    
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            jitter=True
        )
        retry = RetryMechanism(config)
        
        # With jitter, delay should be different each time
        delay1 = retry.calculate_delay(2)
        delay2 = retry.calculate_delay(2)
        
        # Both should be around 2.0 but with jitter
        assert 2.0 <= delay1 <= 2.6  # 2.0 + 30% jitter
        assert 2.0 <= delay2 <= 2.6
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test successful execution without retry."""
        config = RetryConfig(max_attempts=3)
        retry = RetryMechanism(config)
        
        mock_func = AsyncMock(return_value="success")
        
        result = await retry.execute_with_retry(mock_func, "arg1", key="value")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", key="value")
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_eventual_success(self):
        """Test retry mechanism with eventual success."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)  # Fast retry for testing
        retry = RetryMechanism(config)
        
        # Mock function that fails twice then succeeds
        mock_func = AsyncMock(side_effect=[
            NetworkError("Connection failed"),
            NetworkError("Connection failed"),
            "success"
        ])
        
        result = await retry.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_max_attempts_exceeded(self):
        """Test retry mechanism when max attempts exceeded."""
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        retry = RetryMechanism(config)
        
        mock_func = AsyncMock(side_effect=NetworkError("Connection failed"))
        
        with pytest.raises(NetworkError):
            await retry.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_no_retry_on_auth_error(self):
        """Test that authentication errors are not retried."""
        config = RetryConfig(max_attempts=3)
        retry = RetryMechanism(config)
        
        mock_func = AsyncMock(side_effect=AuthenticationError("Invalid token"))
        
        with pytest.raises(AuthenticationError):
            await retry.execute_with_retry(mock_func)
        
        # Should not retry authentication errors
        mock_func.assert_called_once()


class TestCircuitBreaker:
    """Test circuit breaker pattern."""
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)
        
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self):
        """Test circuit breaker with successful calls."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)
        
        mock_func = AsyncMock(return_value="success")
        
        result = await cb.call(mock_func, "arg1")
        
        assert result == "success"
        assert cb.success_count == 1
        assert cb.failure_count == 0
        assert cb.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(config)
        
        mock_func = AsyncMock(side_effect=Exception("Service error"))
        
        # First failure
        with pytest.raises(Exception):
            await cb.call(mock_func)
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 1
        
        # Second failure - should open circuit
        with pytest.raises(Exception):
            await cb.call(mock_func)
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 2
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_fails_fast_when_open(self):
        """Test circuit breaker fails fast when open."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker(config)
        
        # Force circuit to open
        cb.state = CircuitBreakerState.OPEN
        cb.failure_count = 1
        
        mock_func = AsyncMock()
        
        with pytest.raises(ExternalServiceError) as exc_info:
            await cb.call(mock_func)
        
        assert "Circuit breaker" in str(exc_info.value)
        assert "OPEN" in str(exc_info.value)
        mock_func.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01)
        cb = CircuitBreaker(config)
        
        # Force circuit to open
        cb.state = CircuitBreakerState.OPEN
        cb.failure_count = 1
        cb.last_failure_time = datetime.utcnow() - timedelta(seconds=1)
        
        mock_func = AsyncMock(return_value="success")
        
        # Should attempt reset and succeed
        result = await cb.call(mock_func)
        
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
    
    def test_circuit_breaker_stats(self):
        """Test circuit breaker statistics."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)
        
        cb.success_count = 5
        cb.failure_count = 2
        cb.total_requests = 7
        
        stats = cb.get_stats()
        
        assert stats.state == CircuitBreakerState.CLOSED
        assert stats.success_count == 5
        assert stats.failure_count == 2
        assert stats.total_requests == 7


class TestGracefulDegradation:
    """Test graceful degradation strategies."""
    
    def test_register_fallback(self):
        """Test registering fallback handler."""
        gd = GracefulDegradation()
        
        def fallback_handler():
            return "fallback"
        
        gd.register_fallback("test_service", fallback_handler)
        
        assert "test_service" in gd.fallback_handlers
        assert gd.fallback_handlers["test_service"] == fallback_handler
    
    def test_degrade_and_restore_service(self):
        """Test degrading and restoring services."""
        gd = GracefulDegradation()
        
        # Initially no degraded services
        assert len(gd.degraded_services) == 0
        
        # Degrade service
        gd.degrade_service("test_service")
        assert "test_service" in gd.degraded_services
        
        # Restore service
        gd.restore_service("test_service")
        assert "test_service" not in gd.degraded_services
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_normal_operation(self):
        """Test normal operation without fallback."""
        gd = GracefulDegradation()
        
        mock_func = AsyncMock(return_value="primary")
        
        result = await gd.execute_with_fallback("test_service", mock_func, "arg1")
        
        assert result == "primary"
        mock_func.assert_called_once_with("arg1")
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_degraded_service(self):
        """Test fallback execution for degraded service."""
        gd = GracefulDegradation()
        
        # Register fallback
        fallback_func = AsyncMock(return_value="fallback")
        gd.register_fallback("test_service", fallback_func)
        
        # Degrade service
        gd.degrade_service("test_service")
        
        primary_func = AsyncMock(return_value="primary")
        
        result = await gd.execute_with_fallback("test_service", primary_func, "arg1")
        
        assert result == "fallback"
        fallback_func.assert_called_once_with("arg1")
        primary_func.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_no_fallback_available(self):
        """Test error when no fallback available for degraded service."""
        gd = GracefulDegradation()
        
        # Degrade service without registering fallback
        gd.degrade_service("test_service")
        
        primary_func = AsyncMock()
        
        with pytest.raises(ExternalServiceError) as exc_info:
            await gd.execute_with_fallback("test_service", primary_func)
        
        assert "no fallback available" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_auto_degrade_on_failure(self):
        """Test automatic service degradation on failure."""
        gd = GracefulDegradation()
        
        primary_func = AsyncMock(side_effect=Exception("Service failed"))
        
        with pytest.raises(Exception):
            await gd.execute_with_fallback("test_service", primary_func)
        
        # Service should be auto-degraded
        assert "test_service" in gd.degraded_services


class TestErrorHandler:
    """Test main error handler functionality."""
    
    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        eh = ErrorHandler()
        
        assert len(eh.error_log) == 0
        assert isinstance(eh.retry_mechanism, RetryMechanism)
        assert isinstance(eh.graceful_degradation, GracefulDegradation)
        assert len(eh.circuit_breakers) == 0
    
    def test_register_error_handler(self):
        """Test registering custom error handler."""
        eh = ErrorHandler()
        
        def custom_handler(error_context):
            pass
        
        eh.register_error_handler(ErrorCategory.SYSTEM, custom_handler)
        
        assert ErrorCategory.SYSTEM in eh.error_handlers
        assert eh.error_handlers[ErrorCategory.SYSTEM] == custom_handler
    
    def test_register_circuit_breaker(self):
        """Test registering circuit breaker."""
        eh = ErrorHandler()
        
        config = CircuitBreakerConfig(name="test_service")
        eh.register_circuit_breaker("test_service", config)
        
        assert "test_service" in eh.circuit_breakers
        assert isinstance(eh.circuit_breakers["test_service"], CircuitBreaker)
    
    @pytest.mark.asyncio
    async def test_handle_error_application_error(self):
        """Test handling application error."""
        eh = ErrorHandler()
        
        error = SystemError("Test system error", details={"key": "value"})
        
        error_context = await eh.handle_error(
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
        assert len(eh.error_log) == 1
    
    @pytest.mark.asyncio
    async def test_handle_error_generic_exception(self):
        """Test handling generic exception."""
        eh = ErrorHandler()
        
        error = ValueError("Generic error")
        
        error_context = await eh.handle_error(error)
        
        assert error_context.category == ErrorCategory.SYSTEM
        assert error_context.severity == ErrorSeverity.MEDIUM
        assert error_context.message == "Generic error"
        assert "ValueError" in error_context.details["exception_type"]
    
    @pytest.mark.asyncio
    async def test_handle_error_with_custom_handler(self):
        """Test error handling with custom handler."""
        eh = ErrorHandler()
        
        # Register custom handler
        custom_handler_called = False
        
        def custom_handler(error_context):
            nonlocal custom_handler_called
            custom_handler_called = True
        
        eh.register_error_handler(ErrorCategory.SYSTEM, custom_handler)
        
        error = SystemError("Test error")
        await eh.handle_error(error)
        
        assert custom_handler_called
    
    def test_get_error_statistics_empty(self):
        """Test error statistics with no errors."""
        eh = ErrorHandler()
        
        stats = eh.get_error_statistics()
        
        assert stats["total_errors"] == 0
    
    def test_get_error_statistics_with_errors(self):
        """Test error statistics with errors."""
        eh = ErrorHandler()
        
        # Add some errors manually
        from src.core.error_handler import ErrorContext
        import uuid
        
        error1 = ErrorContext(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            message="Error 1",
            details={}
        )
        
        error2 = ErrorContext(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Error 2",
            details={}
        )
        
        eh.error_log.extend([error1, error2])
        
        stats = eh.get_error_statistics()
        
        assert stats["total_errors"] == 2
        assert stats["errors_by_category"]["system"] == 1
        assert stats["errors_by_category"]["network"] == 1
        assert stats["errors_by_severity"]["high"] == 1
        assert stats["errors_by_severity"]["medium"] == 1
    
    def test_clear_error_log(self):
        """Test clearing error log."""
        eh = ErrorHandler()
        
        # Add an error
        from src.core.error_handler import ErrorContext
        import uuid
        
        error = ErrorContext(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            message="Test error",
            details={}
        )
        
        eh.error_log.append(error)
        assert len(eh.error_log) == 1
        
        eh.clear_error_log()
        assert len(eh.error_log) == 0


class TestErrorHandlingAPI:
    """Test FastAPI error handling integration."""
    
    def test_get_http_status_code(self):
        """Test HTTP status code mapping."""
        assert get_http_status_code(ErrorCategory.AUTHENTICATION) == 401
        assert get_http_status_code(ErrorCategory.AUTHORIZATION) == 403
        assert get_http_status_code(ErrorCategory.VALIDATION) == 400
        assert get_http_status_code(ErrorCategory.RESOURCE) == 404
        assert get_http_status_code(ErrorCategory.RATE_LIMIT) == 429
        assert get_http_status_code(ErrorCategory.TIMEOUT) == 408
        assert get_http_status_code(ErrorCategory.SYSTEM) == 500
    
    def test_setup_error_handlers(self):
        """Test setting up error handlers for FastAPI."""
        app = FastAPI()
        
        # Should not raise any exceptions
        setup_error_handlers(app)
        
        # Check that middleware was added
        assert len(app.user_middleware) > 0
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app with error handling."""
        app = FastAPI()
        setup_error_handlers(app)
        app.include_router(error_router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_error_statistics_endpoint(self, client):
        """Test error statistics endpoint."""
        # This would require authentication, so we'll test the basic structure
        response = client.get("/api/errors/statistics")
        
        # Should return 403 (forbidden) due to missing authentication
        assert response.status_code == 403
    
    def test_health_check_endpoint(self, client):
        """Test error handling health check."""
        response = client.get("/api/errors/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert data["service"] == "error_handling"


class TestErrorHandlingDecorators:
    """Test error handling decorators."""
    
    @pytest.mark.asyncio
    async def test_with_retry_decorator(self):
        """Test retry decorator."""
        eh = ErrorHandler()
        
        call_count = 0
        
        @eh.with_retry(RetryConfig(max_attempts=3, base_delay=0.01))
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary failure")
            return "success"
        
        result = await test_function()
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_with_circuit_breaker_decorator(self):
        """Test circuit breaker decorator."""
        eh = ErrorHandler()
        
        config = CircuitBreakerConfig(name="test_service", failure_threshold=2)
        
        @eh.with_circuit_breaker("test_service", config)
        async def test_function():
            return "success"
        
        result = await test_function()
        
        assert result == "success"
        assert "test_service" in eh.circuit_breakers
    
    @pytest.mark.asyncio
    async def test_with_fallback_decorator(self):
        """Test fallback decorator."""
        eh = ErrorHandler()
        
        async def fallback_handler():
            return "fallback_result"
        
        @eh.with_fallback("test_service", fallback_handler)
        async def test_function():
            return "primary_result"
        
        result = await test_function()
        
        assert result == "primary_result"
        assert "test_service" in eh.graceful_degradation.fallback_handlers


if __name__ == "__main__":
    pytest.main([__file__])