from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps.auth import get_current_user_context
from app.services.auth_service import AuthError, login_user, signup_user
from packages.contracts.python.auth_contracts import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    SignupRequest,
    SignupResponse,
)


router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, raw_request: Request):
    """Authenticate the user and return session context."""
    try:
        return login_user(
            email=request.email,
            password=request.password,
            ip_address=raw_request.client.host if raw_request.client else None,
            user_agent=raw_request.headers.get("user-agent"),
        )
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/auth/signup", response_model=SignupResponse)
def signup(request: SignupRequest, raw_request: Request):
    """Create a user, default company context and authenticated session."""
    try:
        return signup_user(
            first_name=request.first_name,
            last_name=request.last_name,
            email=str(request.email),
            password=request.password,
            company_name=request.company_name,
            ip_address=raw_request.client.host if raw_request.client else None,
            user_agent=raw_request.headers.get("user-agent"),
        )
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/auth/me", response_model=MeResponse)
def me(current_user: MeResponse = Depends(get_current_user_context)):
    """Me me for the service workflow."""
    return current_user
