"""
Request/Response Logging Middleware
Logs all API requests and responses for debugging and monitoring.
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request and response with timing information.
    Helps track API usage and debug issues in production.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"➡️  {request.method} {request.url.path} "
            f"- Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            status_emoji = "✅" if response.status_code < 400 else "❌"
            logger.info(
                f"{status_emoji} {request.method} {request.url.path} "
                f"- Status: {response.status_code} "
                f"- Duration: {duration:.2f}s"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = f"{duration:.3f}"
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"💥 {request.method} {request.url.path} "
                f"- Error: {str(e)} "
                f"- Duration: {duration:.2f}s"
            )
            raise
