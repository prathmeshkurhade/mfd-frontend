"""
Authentication Routes
Signup, login, logout, token refresh via Supabase Auth.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.auth.dependencies import get_current_user
from app.database import supabase

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_auth_response(session, user) -> AuthResponse:
    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in or 3600,
        user={
            "id": str(user.id),
            "email": user.email,
            "phone": user.phone,
            "created_at": str(user.created_at),
        },
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: SignupRequest):
    """Register a new user and return JWT tokens."""
    try:
        options: dict = {}
        if data.full_name or data.phone:
            options["data"] = {}
            if data.full_name:
                options["data"]["full_name"] = data.full_name
            if data.phone:
                options["data"]["phone"] = data.phone

        resp = supabase.auth.sign_up(
            {"email": data.email, "password": data.password, "options": options}
        )

        if not resp.session:
            # email confirmation required
            raise HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail="Signup successful. Please confirm your email before logging in.",
            )

        return _build_auth_response(resp.session, resp.user)

    except HTTPException:
        raise
    except Exception as e:
        msg = str(e).lower()
        if "already registered" in msg or "already exists" in msg:
            raise HTTPException(status_code=400, detail="Email already registered.")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest):
    """Login and return JWT access + refresh tokens."""
    try:
        resp = supabase.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )
        if not resp.session:
            raise HTTPException(status_code=401, detail="Invalid credentials.")
        return _build_auth_response(resp.session, resp.user)
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e).lower()
        if "invalid" in msg or "credentials" in msg:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """Invalidate the current session."""
    try:
        supabase.auth.sign_out()
        return MessageResponse(message="Logged out successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh", response_model=AuthResponse)
async def refresh(data: RefreshRequest):
    """Exchange a refresh token for a new access token."""
    try:
        resp = supabase.auth.refresh_session(data.refresh_token)
        if not resp.session:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")
        return _build_auth_response(resp.session, resp.user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's info."""
    return current_user
