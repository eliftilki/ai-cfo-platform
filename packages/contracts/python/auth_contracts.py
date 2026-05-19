from __future__ import annotations

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    company_name: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    user_id: str
    email: EmailStr
    company_id: str
    company_name: str | None = None


class SignupResponse(LoginResponse):
    pass


class MeResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str | None = None
    company_id: str
    company_name: str | None = None
    role: str | None = None
