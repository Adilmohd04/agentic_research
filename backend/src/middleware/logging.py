"""
Request logging middleware
"""

import time
import uuid
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    def __init__(self, app, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            await self._log_response(request, response, request_id, process_time)
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            await self._log_error(request, e, request_id, process_time)
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request"""
        
        # Get client info
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get request body if configured
        body = None
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                # Reset body for downstream processing
                request._body = body
            except Exception:
                body = "Could not read body"
        
        logger.info(
            "HTTP request received",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            query_params=dict(request.query_params),
            headers=dict(request.headers),
            client_host=client_host,
            user_agent=user_agent,
            body=body.decode() if body and len(body) < 1000 else None,
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def _log_response(self, request: Request, response: Response, request_id: str, process_time: float):
        """Log outgoing response"""
        
        logger.info(
            "HTTP response sent",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            response_headers=dict(response.headers),
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def _log_error(self, request: Request, error: Exception, request_id: str, process_time: float):
        """Log request error"""
        
        logger.error(
            "HTTP request error",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            error_type=type(error).__name__,
            error_message=str(error),
            process_time=process_time,
            timestamp=datetime.utcnow().isoformat()
        )


class WebSocketLoggingMiddleware:
    """Logging for WebSocket connections"""
    
    @staticmethod
    def log_connection(session_id: str, user_id: str = None):
        """Log WebSocket connection"""
        logger.info(
            "WebSocket connection established",
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    @staticmethod
    def log_disconnection(session_id: str, user_id: str = None):
        """Log WebSocket disconnection"""
        logger.info(
            "WebSocket connection closed",
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    @staticmethod
    def log_message(session_id: str, message_type: str, user_id: str = None):
        """Log WebSocket message"""
        logger.info(
            "WebSocket message processed",
            session_id=session_id,
            user_id=user_id,
            message_type=message_type,
            timestamp=datetime.utcnow().isoformat()
        )
    
    @staticmethod
    def log_error(session_id: str, error: Exception, user_id: str = None):
        """Log WebSocket error"""
        logger.error(
            "WebSocket error",
            session_id=session_id,
            user_id=user_id,
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=datetime.utcnow().isoformat()
        )