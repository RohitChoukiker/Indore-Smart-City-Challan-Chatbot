"""
Authentication controller.

HTTP routes for authentication endpoints (login, signup, profile).
"""

# Standard library imports
import sys
from pathlib import Path
from typing import Optional

# Third-party imports
from fastapi import APIRouter, Depends, Header, HTTPException

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local application imports
from utills.auth_utils import get_user_id_from_token
from .auth_dto import (
    OtpRequest,
    OtpVerifyRequest,
    SignupRequest,
    LoginRequest
)
from .auth_service import (
    request_otp_service,
    verify_otp_service,
    signup_service,
    login_service,
    get_profile_service
)

# Create router
authRouter = APIRouter(tags=["Authentication"])


def _user_id_dep(authorization: Optional[str] = Header(default=None, alias="Authorization")):
    """
    Dependency function to extract and validate user ID from JWT token.
    
    Args:
        authorization: Authorization header value (Bearer token)
    
    Returns:
        str: User ID if token is valid
    
    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


@authRouter.post("/request-otp")
async def request_otp(req: OtpRequest):
    """
    Request OTP for login or signup.
    
    Sends OTP to user's email address.
    """
    return await request_otp_service(req.email)


@authRouter.post("/verify-otp")
async def verify_otp(req: OtpVerifyRequest):
    """
    Verify OTP code.
    
    Validates the OTP sent to user's email.
    """
    return await verify_otp_service(req.email, req.otp)


@authRouter.post("/signup")
async def signup(req: SignupRequest):
    """
    User signup.
    
    Creates new user account after OTP verification.
    Returns JWT token upon successful signup.
    """
    return await signup_service(
        email=req.email,
        otp=req.otp,
        name=req.name,
        department=req.department,
        designation=req.designation,
        mpin=req.mpin
    )


@authRouter.post("/login")
async def login(req: LoginRequest):
    """
    User login.
    
    Authenticates user after OTP verification.
    Returns JWT token upon successful login.
    """
    return await login_service(req.email, req.otp)


@authRouter.get("/profile")
def get_profile(user_id: str = Depends(_user_id_dep)):
    """
    Get user profile.
    
    Requires valid JWT Bearer token in Authorization header.
    Returns user profile information.
    """
    return get_profile_service(user_id)

