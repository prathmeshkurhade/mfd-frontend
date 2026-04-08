"""
Shared fixtures for E2E tests.

Uses httpx AsyncClient + FastAPI's ASGITransport to test the real app
with auth overridden to a fixed test user (no live Supabase JWT needed).
"""

import os
import sys
import uuid
from pathlib import Path

import pytest
import httpx

# ── Load .env BEFORE anything else ──────────────────────────────────
# The backend .env lives next to the tests/ folder
_backend_dir = Path(__file__).resolve().parent.parent
_env_file = _backend_dir / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file, override=False)

from app.auth.dependencies import get_current_user, get_current_user_id
from app.main import app


# ── Test user ────────────────────────────────────────────────────────
# Use a real user_id from the database so RLS / foreign-key checks pass.
# Override this via TEST_USER_ID env var if your DB uses a different user.
TEST_USER_ID = uuid.UUID(
    os.environ.get("TEST_USER_ID", "567950d9-7a44-476d-b344-c5e48b722bd1")
)
TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "aditya.codes123@gmail.com")


def _override_get_current_user() -> dict:
    return {"id": TEST_USER_ID, "email": TEST_USER_EMAIL, "phone": None}


def _override_get_current_user_id() -> uuid.UUID:
    return TEST_USER_ID


# Override auth dependencies globally
app.dependency_overrides[get_current_user] = _override_get_current_user
app.dependency_overrides[get_current_user_id] = _override_get_current_user_id


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client():
    """Async httpx client wired to the FastAPI app."""
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        timeout=30.0,
    ) as c:
        yield c
