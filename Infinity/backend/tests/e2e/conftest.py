"""
E2E test configuration and shared fixtures.

Reads from .env (same file backend uses) + optional overrides:
    API_BASE_URL          - e.g. http://127.0.0.1:8000
    SUPABASE_URL          - your Supabase project URL
    SUPABASE_KEY          - anon/public key
    SUPABASE_TEST_EMAIL   - test user email
    SUPABASE_TEST_PASSWORD - test user password
"""

import os
import uuid
import pytest
import httpx
from dotenv import load_dotenv

# Load backend .env so we can reuse SUPABASE_URL / SUPABASE_KEY
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
TEST_EMAIL = os.getenv("SUPABASE_TEST_EMAIL", "")
TEST_PASSWORD = os.getenv("SUPABASE_TEST_PASSWORD", "")

# Prefix every created record so cleanup is safe and easy
TEST_RUN_ID = str(uuid.uuid4())[:8]
TEST_PREFIX = f"[e2e:{TEST_RUN_ID}]"


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def get_jwt_token() -> str:
    """Login via Supabase REST and return the access token."""
    assert SUPABASE_URL, "SUPABASE_URL not set"
    assert SUPABASE_KEY, "SUPABASE_KEY not set"
    assert TEST_EMAIL, "SUPABASE_TEST_EMAIL not set"
    assert TEST_PASSWORD, "SUPABASE_TEST_PASSWORD not set"

    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    resp = httpx.post(
        url,
        headers=headers,
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15,
    )
    assert resp.status_code == 200, (
        f"Failed to get JWT token. Status: {resp.status_code}. "
        f"Body: {resp.text}"
    )
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Session-scoped fixtures (created once, reused across all tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def token() -> str:
    return get_jwt_token()


@pytest.fixture(scope="session")
def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def client(auth_headers) -> httpx.Client:
    """Shared HTTP client with auth headers pre-set."""
    with httpx.Client(
        base_url=API_BASE_URL,
        headers=auth_headers,
        timeout=20,
    ) as c:
        yield c


@pytest.fixture(scope="session")
def anon_client() -> httpx.Client:
    """HTTP client with NO auth (for public endpoint tests)."""
    with httpx.Client(base_url=API_BASE_URL, timeout=20) as c:
        yield c


# ---------------------------------------------------------------------------
# Helper to assert common response shape
# ---------------------------------------------------------------------------

def assert_ok(resp: httpx.Response, expected_status: int = 200):
    assert resp.status_code == expected_status, (
        f"Expected {expected_status}, got {resp.status_code}. Body: {resp.text}"
    )
    return resp.json()
