"""
Comprehensive Error Handling and Recovery System

This module provides categorized error types, retry mechanisms with exponential backoff,
graceful degradation strategies, and comprehensive error recovery mechanisms.
"""

import asyncio
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Type, Union
from dataclasses import dataclass, asdict
from enum import Enum
import random
from functools import wraps

logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    """Categories of errors for different handling strategies."""
    SYSTEM = "system"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    FAIL_FAST = "fail_fast"
    IGNORE = "ignore"

@dataclass
class ErrorContext:
    """Context information for error handling."""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_strategy: str = "exponential"  # exponential, linear, fixed

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = Exception
    name: str = "default"

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    state: CircuitBreakerState
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    last_success_time: Optional[datetime]
    total_requests: int

class ApplicationError(Exception):
    """Base application error with categorization."""
    
    def __init__(self, 
                 message: str,
                 category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 details: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()

class SystemError(ApplicationError):
    """System-level errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.SYSTEM, ErrorSeverity.HIGH, **kwargs)

class NetworkError(ApplicationError):
    """Network-related errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.NETWORK, ErrorSeverity.MEDIUM, **kwargs)

class AuthenticationError(ApplicationError):
    """Authentication errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH, **kwargs)

class AuthorizationError(ApplicationError):
    """Authorization errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.AUTHORIZATION, ErrorSeverity.HIGH, **kwargs)

class ValidationError(ApplicationError):
    """Input validation errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.LOW, **kwargs)

class BusinessLogicError(ApplicationError):
    """Business logic errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.MEDIUM, **kwargs)

class ExternalServiceError(ApplicationError):
    """External service errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.MEDIUM, **kwargs)

class ResourceError(ApplicationError):
    """Resource-related errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.RESOURCE, ErrorSeverity.HIGH, **kwargs)

class TimeoutError(ApplicationError):
    """Timeout errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM, **kwargs)

class RateLimitError(ApplicationError):
    """Rate limiting errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.RATE_LIMIT, ErrorSeverity.LOW, **kwargs)

class RetryMechanism:
    """Implements various retry strategies with exponential backoff."""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        if self.config.backoff_strategy == "exponential":
            delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        elif self.config.backoff_strategy == "linear":
            delay = self.config.base_delay * attempt
        else:  # fixed
            delay = self.config.base_delay
        
        # Apply maximum delay limit
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter
        
        return delay
    
    async def execute_with_retry(self, 
                                func: Callable,
                                *args,
                                **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                # Don't retry on certain error types
                if isinstance(e, (AuthenticationError, AuthorizationError, ValidationError)):
                    raise
                
                if attempt == self.config.max_attempts:
                    logger.error(f"Max retry attempts ({self.config.max_attempts}) exceeded")
                    raise
                
                delay = self.calculate_delay(attempt)
                logger.warning(f"Attempt {attempt} failed, retrying in {delay:.2f}s: {str(e)}")
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception

class CircuitBreaker:
    """Implements circuit breaker pattern for external service calls."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED
        self.total_requests = 0
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.state != CircuitBreakerState.OPEN:
            return False
        
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def _record_success(self):
        """Record successful operation."""
        self.success_count += 1
        self.last_success_time = datetime.utcnow()
        self.failure_count = 0  # Reset failure count on success
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            logger.info(f"Circuit breaker '{self.config.name}' reset to CLOSED")
    
    def _record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if (self.state == CircuitBreakerState.CLOSED and 
            self.failure_count >= self.config.failure_threshold):
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker '{self.config.name}' opened due to failures")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker '{self.config.name}' reopened after failed attempt")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        self.total_requests += 1
        
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self.state = CircuitBreakerState.HALF_OPEN
            logger.info(f"Circuit breaker '{self.config.name}' attempting reset")
        
        # Fail fast if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            raise ExternalServiceError(
                f"Circuit breaker '{self.config.name}' is OPEN",
                details={"failure_count": self.failure_count}
            )
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._record_success()
            return result
        
        except self.config.expected_exception as e:
            self._record_failure()
            raise
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return CircuitBreakerStats(
            state=self.state,
            failure_count=self.failure_count,
            success_count=self.success_count,
            last_failure_time=self.last_failure_time,
            last_success_time=self.last_success_time,
            total_requests=self.total_requests
        )

class GracefulDegradation:
    """Implements graceful degradation strategies."""
    
    def __init__(self):
        self.fallback_handlers: Dict[str, Callable] = {}
        self.degraded_services: Set[str] = set()
    
    def register_fallback(self, service_name: str, fallback_handler: Callable):
        """Register fallback handler for a service."""
        self.fallback_handlers[service_name] = fallback_handler
        logger.info(f"Registered fallback handler for service: {service_name}")
    
    def degrade_service(self, service_name: str):
        """Mark service as degraded."""
        self.degraded_services.add(service_name)
        logger.warning(f"Service degraded: {service_name}")
    
    def restore_service(self, service_name: str):
        """Restore service from degraded state."""
        self.degraded_services.discard(service_name)
        logger.info(f"Service restored: {service_name}")
    
    async def execute_with_fallback(self, 
                                   service_name: str,
                                   primary_func: Callable,
                                   *args,
                                   **kwargs) -> Any:
        """Execute function with fallback if service is degraded."""
        if service_name in self.degraded_services:
            fallback_handler = self.fallback_handlers.get(service_name)
            if fallback_handler:
                logger.info(f"Using fallback for degraded service: {service_name}")
                if asyncio.iscoroutinefunction(fallback_handler):
                    return await fallback_handler(*args, **kwargs)
                else:
                    return fallback_handler(*args, **kwargs)
            else:
                raise ExternalServiceError(
                    f"Service '{service_name}' is degraded and no fallback available"
                )
        
        try:
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func(*args, **kwargs)
            else:
                return primary_func(*args, **kwargs)
        except Exception as e:
            # Auto-degrade service on repeated failures
            self.degrade_service(service_name)
            raise

class ErrorHandler:
    """Main error handler with categorized error types and recovery strategies."""
    
    def __init__(self):
        self.error_log: List[ErrorContext] = []
        self.retry_mechanism = RetryMechanism(RetryConfig())
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.graceful_degradation = GracefulDegradation()
        self.error_handlers: Dict[ErrorCategory, Callable] = {}
        self.recovery_strategies: Dict[ErrorCategory, RecoveryStrategy] = {
            ErrorCategory.SYSTEM: RecoveryStrategy.RETRY,
            ErrorCategory.NETWORK: RecoveryStrategy.RETRY,
            ErrorCategory.AUTHENTICATION: RecoveryStrategy.FAIL_FAST,
            ErrorCategory.AUTHORIZATION: RecoveryStrategy.FAIL_FAST,
            ErrorCategory.VALIDATION: RecoveryStrategy.FAIL_FAST,
            ErrorCategory.BUSINESS_LOGIC: RecoveryStrategy.GRACEFUL_DEGRADATION,
            ErrorCategory.EXTERNAL_SERVICE: RecoveryStrategy.CIRCUIT_BREAKER,
            ErrorCategory.RESOURCE: RecoveryStrategy.GRACEFUL_DEGRADATION,
            ErrorCategory.TIMEOUT: RecoveryStrategy.RETRY,
            ErrorCategory.RATE_LIMIT: RecoveryStrategy.RETRY,
        }
    
    def register_error_handler(self, category: ErrorCategory, handler: Callable):
        """Register custom error handler for specific category."""
        self.error_handlers[category] = handler
        logger.info(f"Registered error handler for category: {category.value}")
    
    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig):
        """Register circuit breaker for external service."""
        self.circuit_breakers[name] = CircuitBreaker(config)
        logger.info(f"Registered circuit breaker: {name}")
    
    def _create_error_context(self, 
                             error: Exception,
                             component: Optional[str] = None,
                             user_id: Optional[str] = None,
                             request_id: Optional[str] = None) -> ErrorContext:
        """Create error context from exception."""
        import uuid
        
        if isinstance(error, ApplicationError):
            category = error.category
            severity = error.severity
            details = error.details
        else:
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.MEDIUM
            details = {"exception_type": type(error).__name__}
        
        return ErrorContext(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            category=category,
            severity=severity,
            message=str(error),
            details=details,
            stack_trace=traceback.format_exc(),
            user_id=user_id,
            request_id=request_id,
            component=component
        )
    
    async def handle_error(self, 
                          error: Exception,
                          component: Optional[str] = None,
                          user_id: Optional[str] = None,
                          request_id: Optional[str] = None) -> ErrorContext:
        """Handle error with appropriate recovery strategy."""
        error_context = self._create_error_context(error, component, user_id, request_id)
        
        # Log error
        self.error_log.append(error_context)
        
        # Log based on severity
        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error_context.message}", extra=asdict(error_context))
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {error_context.message}", extra=asdict(error_context))
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error_context.message}", extra=asdict(error_context))
        else:
            logger.info(f"Low severity error: {error_context.message}", extra=asdict(error_context))
        
        # Execute custom error handler if registered
        custom_handler = self.error_handlers.get(error_context.category)
        if custom_handler:
            try:
                if asyncio.iscoroutinefunction(custom_handler):
                    await custom_handler(error_context)
                else:
                    custom_handler(error_context)
            except Exception as handler_error:
                logger.error(f"Error handler failed: {handler_error}")
        
        return error_context
    
    def with_retry(self, config: Optional[RetryConfig] = None):
        """Decorator for adding retry logic to functions."""
        retry_config = config or RetryConfig()
        retry_mechanism = RetryMechanism(retry_config)
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await retry_mechanism.execute_with_retry(func, *args, **kwargs)
            return wrapper
        return decorator
    
    def with_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """Decorator for adding circuit breaker protection."""
        if name not in self.circuit_breakers:
            cb_config = config or CircuitBreakerConfig(name=name)
            self.register_circuit_breaker(name, cb_config)
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                circuit_breaker = self.circuit_breakers[name]
                return await circuit_breaker.call(func, *args, **kwargs)
            return wrapper
        return decorator
    
    def with_fallback(self, service_name: str, fallback_handler: Callable):
        """Decorator for adding fallback functionality."""
        self.graceful_degradation.register_fallback(service_name, fallback_handler)
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.graceful_degradation.execute_with_fallback(
                    service_name, func, *args, **kwargs
                )
            return wrapper
        return decorator
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and metrics."""
        if not self.error_log:
            return {"total_errors": 0}
        
        # Count errors by category
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_log:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        # Get circuit breaker stats
        circuit_breaker_stats = {}
        for name, cb in self.circuit_breakers.items():
            circuit_breaker_stats[name] = asdict(cb.get_stats())
        
        return {
            "total_errors": len(self.error_log),
            "errors_by_category": category_counts,
            "errors_by_severity": severity_counts,
            "circuit_breakers": circuit_breaker_stats,
            "degraded_services": list(self.graceful_degradation.degraded_services)
        }
    
    def clear_error_log(self):
        """Clear error log (useful for testing)."""
        self.error_log.clear()

# Global error handler instance
error_handler = ErrorHandler()