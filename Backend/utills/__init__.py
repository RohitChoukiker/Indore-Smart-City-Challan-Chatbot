"""
Utility functions package.

Exports authentication and email utilities.
"""

from utills.auth_utils import create_token, decode_token, get_user_id_from_token
from utills.email_utils import generate_otp, send_otp_email, fastmail

__all__ = [
    "create_token",
    "decode_token",
    "get_user_id_from_token",
    "generate_otp",
    "send_otp_email",
    "fastmail"
]


