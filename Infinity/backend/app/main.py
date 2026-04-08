from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.jobs.scheduler_jobs import shutdown_scheduler, start_scheduler
from app.middleware.error_handlers import (
    validation_exception_handler,
    python_exception_handler,
    value_error_handler,
)
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.cors_middleware import get_cors_middleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import (
    auth,
    auth,
    business_opportunities,
    calculators,
    campaigns,
    client_products,
    clients,
    dashboard,
    data_io,
    devices,
    documents,
    goals,
    health,
    leads,
    notifications,
    ocr,
    pdfs,
    profile,
    scheduler,
    search,
    sheets,
    tasks,
    templates,
    touchpoints,
    voice,
    voice_ppt,
    webhooks,
    whatsapp_forms,
    whatsapp_inputs,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: startup and shutdown."""
    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(title="MFD Digital Diary API", lifespan=lifespan)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, python_exception_handler)

# Add middleware (order matters - last added runs first!)
# Execution order: Security Headers → Rate Limiter → Logging → CORS → Route
cors_config = get_cors_middleware()
app.add_middleware(cors_config["middleware_class"], **{k: v for k, v in cors_config.items() if k != "middleware_class"})
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60, auth_requests_per_minute=10)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(clients.router, prefix="/api/v1", tags=["Clients"])
app.include_router(leads.router, prefix="/api/v1", tags=["Leads"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(touchpoints.router, prefix="/api/v1", tags=["Touchpoints"])
app.include_router(business_opportunities.router, prefix="/api/v1", tags=["Business Opportunities"])
app.include_router(goals.router, prefix="/api/v1", tags=["Goals"])
app.include_router(calculators.router, prefix="/api/v1", tags=["Calculators"])
app.include_router(profile.router, prefix="/api/v1", tags=["Profile"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
app.include_router(devices.router, prefix="/api/v1", tags=["Devices"])
app.include_router(campaigns.router, prefix="/api/v1", tags=["Campaigns"])
app.include_router(client_products.router, prefix="/api/v1", tags=["Client Products"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(scheduler.router, prefix="/api/v1", tags=["Scheduler"])
app.include_router(templates.router, prefix="/api/v1", tags=["Templates"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(whatsapp_forms.router, prefix="/api/v1", tags=["WhatsApp Forms"])
app.include_router(whatsapp_inputs.router, prefix="/api/v1", tags=["WhatsApp Inputs"])
app.include_router(pdfs.router, prefix="/api/v1", tags=["PDFs"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(data_io.router, prefix="/api/v1", tags=["Data Import/Export"])
app.include_router(sheets.router, prefix="/api/v1", tags=["Sheets Sync"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice Notes"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR Scan"])
app.include_router(voice_ppt.router, prefix="/api/v1", tags=["Voice PPT"])

@app.get("/")
async def root() -> dict:
    return {"status": "running"}


__all__ = ["app"]

