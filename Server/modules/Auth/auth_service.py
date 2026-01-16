import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.models import SessionLocal, Users
from utills.auth_utils import create_token
from utills.email_utils import generate_otp, send_otp_email
from .auth_dto import UserProfileResponse


OTP_EXPIRATION_MINUTES = 5


async def request_otp_service(email: str) -> dict:
    db: Session = SessionLocal()
    try:
        otp = generate_otp()

        user = db.query(Users).filter(Users.email == email).first()

        if user:
            user.otp = otp
            user.otp_created_at = datetime.utcnow()
        else:
            user = Users(
                email=email,
                otp=otp,
                otp_created_at=datetime.utcnow()
            )
            db.add(user)

        db.commit()

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
    db: Session = SessionLocal()
    try:
        user = db.query(Users).filter(Users.email == email).first()

        if not user:
            return {
                "status": False,
                "message": "User not found. Please request OTP first.",
                "data": None
            }

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

        user.otp = None
        user.otp_created_at = None
        db.commit()

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
    db: Session = SessionLocal()
    try:
        user = db.query(Users).filter(Users.email == email).first()

        if not user:
            return {
                "status": False,
                "message": "User not found. Please sign up first.",
                "data": None
            }

        if not user.mpin:
            return {
                "status": False,
                "message": "MPIN not set. Please use OTP login or set your MPIN first.",
                "data": None
            }

        if user.mpin != mpin:
            return {
                "status": False,
                "message": "Invalid MPIN. Please try again.",
                "data": None
            }

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
    db: Session = SessionLocal()
    try:
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            return {"status": False, "message": "User not found", "data": None}

        from utills.auth_utils import generate_patterned_mpin
        mpin = generate_patterned_mpin()

        user.mpin = mpin
        user.updated_at = datetime.utcnow()
        db.commit()

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


def update_profile_service(
    user_id: str,
    name: Optional[str] = None,
    department: Optional[str] = None,
    designation: Optional[str] = None
) -> dict:
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
    db: Session = SessionLocal()
    try:
        user = db.query(Users).filter(Users.id == user_id).first()

        if not user:
            return {
                "status": False,
                "message": "User not found",
                "data": None
            }

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
