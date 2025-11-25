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
    UpdateProfileRequest
)
from .auth_service import (
    request_otp_service,
    verify_otp_service,
    get_profile_service,
    set_mpin_service,
    update_profile_service
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
    Verify OTP code and log in.
    
    Validates the OTP and returns a JWT token.
    """
    return await verify_otp_service(req.email, req.otp)


@authRouter.get("/profile")
def get_profile(user_id: str = Depends(_user_id_dep)):
    """
    Get user profile.
    
    Requires valid JWT Bearer token in Authorization header.
    Returns user profile information.
    """
    return get_profile_service(user_id)


@authRouter.put("/profile")
def update_profile(req: UpdateProfileRequest, user_id: str = Depends(_user_id_dep)):
    """
    Update user profile.
    
    Requires valid JWT Bearer token.
    Updates name, department, and designation.
    """
    return update_profile_service(
        user_id=user_id,
        name=req.name,
        department=req.department,
        designation=req.designation
    )


@authRouter.post("/set-mpin")
async def set_mpin(user_id: str = Depends(_user_id_dep)):
    """
    Generate and set MPIN.
    
    Requires valid JWT Bearer token.
    Generates a patterned MPIN and emails it to the user.
    """
    return await set_mpin_service(user_id)

