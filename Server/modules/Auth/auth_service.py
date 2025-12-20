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
    Verify OTP and log user in.
    
    Args:
        email: User email address
        otp: OTP code to verify
    
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
        
        # Create JWT token
        token = create_token({"user_id": user.id})
        
        return {
            "status": True,
            "message": "OTP verified successfully",
            "data": {
                "token": token,
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "department": user.department,
                "designation": user.designation
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


async def mpin_login_service(email: str, mpin: str) -> dict:
    """
    Login user with MPIN.
    
    Args:
        email: User email address
        mpin: 6-digit MPIN
    
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
                "message": "User not found. Please sign up first.",
                "data": None
            }
        
        # Check if MPIN is set
        if not user.mpin:
            return {
                "status": False,
                "message": "MPIN not set. Please use OTP login or set your MPIN first.",
                "data": None
            }
        
        # Check if MPIN matches
        if user.mpin != mpin:
            return {
                "status": False,
                "message": "Invalid MPIN. Please try again.",
                "data": None
            }
        
        # MPIN is valid - create JWT token
        token = create_token({"user_id": user.id})
        
        return {
            "status": True,
            "message": "Login successful",
            "data": {
                "token": token,
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "department": user.department,
                "designation": user.designation
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


async def set_mpin_service(user_id: str) -> dict:
    """
    Generate and set MPIN for user, then email it.
    
    Args:
        user_id: User ID
    
    Returns:
        dict: Response status
    """
    db: Session = SessionLocal()
    try:
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            return {"status": False, "message": "User not found", "data": None}
            
        # Generate patterned MPIN
        from utills.auth_utils import generate_patterned_mpin
        mpin = generate_patterned_mpin()
        
        # Set MPIN
        user.mpin = mpin
        user.updated_at = datetime.utcnow()
        db.commit()
        
        # Send email
        email_sent = await send_otp_email(user.email, mpin)
        
        if not email_sent:
             return {
                "status": False,
                "message": "MPIN set but failed to send email.",
                "data": None
            }
            
        return {
            "status": True,
            "message": "MPIN generated and sent to your email.",
            "data": None
        }
    except Exception as e:
        db.rollback()
        return {"status": False, "message": str(e), "data": None}
    finally:
        db.close()


def update_profile_service(user_id: str, name: Optional[str] = None, 
                         department: Optional[str] = None, designation: Optional[str] = None) -> dict:
    """
    Update user profile.
    
    Args:
        user_id: User ID
        name: New name
        department: New department
        designation: New designation
    
    Returns:
        dict: Response status
    """
    db: Session = SessionLocal()
    try:
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            return {"status": False, "message": "User not found", "data": None}
            
        if name is not None:
            user.name = name
        if department is not None:
            user.department = department
        if designation is not None:
            user.designation = designation
            
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": True,
            "message": "Profile updated successfully",
            "data": {
                "id": user.id,
                "name": user.name,
                "department": user.department,
                "designation": user.designation
            }
        }
    except Exception as e:
        db.rollback()
        return {"status": False, "message": str(e), "data": None}
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
