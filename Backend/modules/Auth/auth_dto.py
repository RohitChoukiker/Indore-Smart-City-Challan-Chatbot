"""
Authentication DTOs (Data Transfer Objects).

Pydantic models for request/response validation in auth endpoints.
"""

# Standard library imports
from typing import Optional

# Third-party imports
from pydantic import BaseModel, EmailStr, Field


class OtpRequest(BaseModel):
    """Request model for OTP generation."""
    email: EmailStr = Field(..., description="User email address")


class OtpVerifyRequest(BaseModel):
    """Request model for OTP verification."""
    email: EmailStr = Field(..., description="User email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class MPINLoginRequest(BaseModel):
    """Request model for MPIN login."""
    email: EmailStr = Field(..., description="User email address")
    mpin: str = Field(..., min_length=6, max_length=6, description="6-digit MPIN")


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""
    name: Optional[str] = Field(None, description="User full name")
    department: Optional[str] = Field(None, description="User department")
    designation: Optional[str] = Field(None, description="User designation")





class TokenResponse(BaseModel):
    """Response model for token-based endpoints."""
    token: str = Field(..., description="JWT Bearer token")
    user_id: str = Field(..., description="User ID")


class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    id: str
    email: Optional[str]
    name: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    created_at: Optional[str]

