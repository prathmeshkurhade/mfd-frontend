"""
Enhanced CORS Configuration
Configures Cross-Origin Resource Sharing for production.
"""

from fastapi.middleware.cors import CORSMiddleware
from app.config import settings


def get_cors_middleware():
    """
    Returns CORS middleware with production-safe settings.
    In production, should specify allowed origins instead of "*".
    """
    
    # In production, replace ["*"] with actual frontend URLs:
    # allowed_origins = ["https://yourapp.com", "https://www.yourapp.com"]
    allowed_origins = ["*"]  # Change this in production!
    
    return {
        "middleware_class": CORSMiddleware,
        "allow_origins": allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": ["X-Process-Time"]  # Expose custom headers
    }
