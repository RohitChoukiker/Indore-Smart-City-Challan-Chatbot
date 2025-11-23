"""
Authentication service layer.

Contains all business logic for authentication, OTP management, and user operations.
"""

# Standard library imports
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Third-party imports
from sqlalchemy.orm import Session

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local application imports
from database.models import SessionLocal, Users
from utills.auth_utils import create_token
from utills.email_utils import generate_otp, send_otp_email
from .auth_dto import UserProfileResponse


OTP_EXPIRATION_MINUTES = 5


async def request_otp_service(email: str) -> dict:
    """
    Request OTP for login/signup.
    
    Args:
        email: User email address
    
    Returns:
        dict: Standardized response with status, message, and data
    """
    db: Session = SessionLocal()
    try:
        # Generate OTP
        otp = generate_otp()
        
        # Check if user exists
        user = db.query(Users).filter(Users.email == email).first()
        
        if user:
            # Update existing user's OTP
            user.otp = otp
            user.otp_created_at = datetime.utcnow()
        else:
            # Create new user for signup flow
            user = Users(
                email=email,
                otp=otp,
                otp_created_at=datetime.utcnow()
            )
            db.add(user)
        
        db.commit()
        
        # Send OTP email
        email_sent = await send_otp_email(email, otp)
        
        if not email_sent:
            return {
                "status": False,
                "message": "Failed to send OTP email. Please try again.",
                "data": None
            }
        
        return {
            "status": True,
            "message": "OTP has been sent to your email address",
            "data": None
        }
    except Exception as e:
        db.rollback()
        return {
            "status": False,
            "message": str(e),
            "data": None
        }
    finally:
        db.close()


async def verify_otp_service(email: str, otp: str) -> dict:
    """
    Verify OTP for login/signup.
    
    Args:
        email: User email address
        otp: OTP code to verify
    
    Returns:
        dict: Standardized response with status, message, and data
    """
    db: Session = SessionLocal()
    try:
        # Find user
        user = db.query(Users).filter(Users.email == email).first()
        
        if not user:
            return {
                "status": False,
                "message": "User not found. Please request OTP first.",
                "data": None
            }
        
        # Check if OTP exists
        if not user.otp:
            return {
                "status": False,
                "message": "No OTP found. Please request a new OTP.",
                "data": None
            }
        
        # Check if OTP matches
        if user.otp != otp:
            return {
                "status": False,
                "message": "Invalid OTP. Please try again.",
                "data": None
            }
        
        # Check if OTP is expired
        if user.otp_created_at:
            expiration_time = user.otp_created_at + timedelta(minutes=OTP_EXPIRATION_MINUTES)
            if datetime.utcnow() > expiration_time:
                # Clear expired OTP
                user.otp = None
                user.otp_created_at = None
                db.commit()
                
                return {
                    "status": False,
                    "message": "OTP has expired. Please request a new OTP.",
                    "data": None
                }
        
        # OTP is valid
        # Clear OTP after successful verification
        user.otp = None
        user.otp_created_at = None
        db.commit()
        
        return {
            "status": True,
            "message": "OTP verified successfully",
            "data": None
        }
    except Exception as e:
        db.rollback()
        return {
            "status": False,
            "message": str(e),
            "data": None
        }
    finally:
        db.close()


async def signup_service(email: str, otp: str, name: Optional[str] = None, 
                   department: Optional[str] = None, designation: Optional[str] = None,
                   mpin: Optional[str] = None) -> dict:
    """
    User signup after OTP verification.
    
    Args:
        email: User email address
        otp: OTP code
        name: User full name
        department: User department
        designation: User designation
        mpin: User MPIN
    
    Returns:
        dict: Standardized response with token and user data
    """
    db: Session = SessionLocal()
    try:
        # Find user
        user = db.query(Users).filter(Users.email == email).first()
        
        if not user:
            return {
                "status": False,
                "message": "User not found. Please request OTP first.",
                "data": None
            }
        
        # Verify OTP
        if not user.otp:
            return {
                "status": False,
                "message": "No OTP found. Please request a new OTP.",
                "data": None
            }
        
        if user.otp != otp:
            return {
                "status": False,
                "message": "Invalid OTP. Please try again.",
                "data": None
            }
        
        # Check if OTP is expired
        if user.otp_created_at:
            expiration_time = user.otp_created_at + timedelta(minutes=OTP_EXPIRATION_MINUTES)
            if datetime.utcnow() > expiration_time:
                user.otp = None
                user.otp_created_at = None
                db.commit()
                return {
                    "status": False,
                    "message": "OTP has expired. Please request a new OTP.",
                    "data": None
                }
        
        # Clear OTP after successful verification
        user.otp = None
        user.otp_created_at = None
        
        # Update user information
        if name is not None:
            user.name = name
        if department is not None:
            user.department = department
        if designation is not None:
            user.designation = designation
        if mpin is not None:
            user.mpin = mpin
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        token = create_token({"user_id": user.id})
        
        return {
            "status": True,
            "message": "Signup successful",
            "data": {
                "token": token,
                "user_id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    except Exception as e:
        db.rollback()
        return {
            "status": False,
            "message": str(e),
            "data": None
        }
    finally:
        db.close()


async def login_service(email: str, otp: str) -> dict:
    """
    User login after OTP verification.
    
    Args:
        email: User email address
        otp: OTP code
    
    Returns:
        dict: Standardized response with token and user data
    """
    db: Session = SessionLocal()
    try:
        # Find user
        user = db.query(Users).filter(Users.email == email).first()
        
        if not user:
            return {
                "status": False,
                "message": "User not found. Please signup first.",
                "data": None
            }
        
        # Verify OTP
        if not user.otp:
            return {
                "status": False,
                "message": "No OTP found. Please request a new OTP.",
                "data": None
            }
        
        if user.otp != otp:
            return {
                "status": False,
                "message": "Invalid OTP. Please try again.",
                "data": None
            }
        
        # Check if OTP is expired
        if user.otp_created_at:
            expiration_time = user.otp_created_at + timedelta(minutes=OTP_EXPIRATION_MINUTES)
            if datetime.utcnow() > expiration_time:
                user.otp = None
                user.otp_created_at = None
                db.commit()
                return {
                    "status": False,
                    "message": "OTP has expired. Please request a new OTP.",
                    "data": None
                }
        
        # Check if user has completed signup (has name or other details)
        if not user.name and not user.department:
            return {
                "status": False,
                "message": "User profile incomplete. Please complete signup first.",
                "data": None
            }
        
        # Clear OTP after successful verification
        user.otp = None
        user.otp_created_at = None
        db.commit()
        
        # Create JWT token
        token = create_token({"user_id": user.id})
        
        return {
            "status": True,
            "message": "Login successful",
            "data": {
                "token": token,
                "user_id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    except Exception as e:
        db.rollback()
        return {
            "status": False,
            "message": str(e),
            "data": None
        }
    finally:
        db.close()


def get_profile_service(user_id: str) -> dict:
    """
    Get user profile by user ID.
    
    Args:
        user_id: User ID from JWT token
    
    Returns:
        dict: Standardized response with user profile data
    """
    db: Session = SessionLocal()
    try:
        # Find user
        user = db.query(Users).filter(Users.id == user_id).first()
        
        if not user:
            return {
                "status": False,
                "message": "User not found",
                "data": None
            }
        
        # Build response data
        profile_data = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "department": user.department,
            "designation": user.designation,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        
        return {
            "status": True,
            "message": "Profile retrieved successfully",
            "data": profile_data
        }
    except Exception as e:
        return {
            "status": False,
            "message": str(e),
            "data": None
        }
    finally:
        db.close()

