"""
Global Exception Handlers
Standardizes error responses and prevents sensitive info leakage in production.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles Pydantic validation errors (422).
    Makes validation errors more user-friendly.
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid input data",
            "details": errors
        }
    )


async def python_exception_handler(request: Request, exc: Exception):
    """
    Catches all unhandled Python exceptions (500).
    Logs the error and returns safe error message (no stack trace exposure).
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True  # Logs full stack trace
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": str(id(request))  # For support tracking
        }
    )


async def value_error_handler(request: Request, exc: ValueError):
    """
    Handles ValueError exceptions (business logic errors).
    Returns 400 Bad Request instead of 500.
    """
    logger.warning(f"ValueError on {request.url.path}: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "message": str(exc)
        }
    )
