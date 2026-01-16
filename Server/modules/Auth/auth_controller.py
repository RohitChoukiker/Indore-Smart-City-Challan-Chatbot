
import sys
from pathlib import Path
from typing import Optional


from fastapi import APIRouter, Depends, Header, HTTPException


sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from utills.auth_utils import get_user_id_from_token
from .auth_dto import (
    OtpRequest,
    OtpVerifyRequest,
    MPINLoginRequest,
    UpdateProfileRequest
)
from .auth_service import (
    request_otp_service,
    verify_otp_service,
    mpin_login_service,
    get_profile_service,
    set_mpin_service,
    update_profile_service
)


authRouter = APIRouter(tags=["Authentication"])


def _user_id_dep(authorization: Optional[str] = Header(default=None, alias="Authorization")):
   
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


@authRouter.post("/request-otp")
async def request_otp(req: OtpRequest):
  
    return await request_otp_service(req.email)


@authRouter.post("/verify-otp")
async def verify_otp(req: OtpVerifyRequest):
   
    return await verify_otp_service(req.email, req.otp)


@authRouter.post("/login-mpin")
async def login_mpin(req: MPINLoginRequest):
   
    return await mpin_login_service(req.email, req.mpin)


@authRouter.get("/profile")
def get_profile(user_id: str = Depends(_user_id_dep)):
   
    return get_profile_service(user_id)


@authRouter.put("/profile")
def update_profile(req: UpdateProfileRequest, user_id: str = Depends(_user_id_dep)):
   
    return update_profile_service(
        user_id=user_id,
        name=req.name,
        department=req.department,
        designation=req.designation
    )


@authRouter.post("/set-mpin")
async def set_mpin(user_id: str = Depends(_user_id_dep)):
   
    return await set_mpin_service(user_id)


