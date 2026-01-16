
from typing import Optional


from pydantic import BaseModel, EmailStr, Field


class OtpRequest(BaseModel):
  
    email: EmailStr = Field(..., description="User email address")


class OtpVerifyRequest(BaseModel):

    email: EmailStr = Field(..., description="User email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class MPINLoginRequest(BaseModel):
  
    email: EmailStr = Field(..., description="User email address")
    mpin: str = Field(..., min_length=6, max_length=6, description="6-digit MPIN")


class UpdateProfileRequest(BaseModel):
   
    name: Optional[str] = Field(None, description="User full name")
    department: Optional[str] = Field(None, description="User department")
    designation: Optional[str] = Field(None, description="User designation")





class TokenResponse(BaseModel):

    token: str = Field(..., description="JWT Bearer token")
    user_id: str = Field(..., description="User ID")


class UserProfileResponse(BaseModel):
 
    id: str
    email: Optional[str]
    name: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    created_at: Optional[str]


