"""
Email utility functions for sending OTP emails.

Uses FastAPIMail for email delivery.
"""

# Standard library imports
import random
import string
from typing import Optional

# Third-party imports
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

# Email configuration from environment variables
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "noreply@example.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "default_password")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Indore Smart City")
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"
MAIL_USE_CREDENTIALS = os.getenv("MAIL_USE_CREDENTIALS", "True").lower() == "true"
MAIL_VALIDATE_CERTS = os.getenv("MAIL_VALIDATE_CERTS", "True").lower() == "true"

# FastAPIMail configuration
mail_config = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_STARTTLS=MAIL_STARTTLS,
    MAIL_SSL_TLS=MAIL_SSL_TLS,
    USE_CREDENTIALS=MAIL_USE_CREDENTIALS,
    VALIDATE_CERTS=MAIL_VALIDATE_CERTS,
    TEMPLATE_FOLDER=None
)

# FastMail instance
fastmail = FastMail(mail_config)

# Thread pool for non-blocking email sending
email_executor = ThreadPoolExecutor(max_workers=5)


def generate_otp(length: int = 6) -> str:
    """
    Generate a random OTP.
    
    Args:
        length: Length of OTP (default: 6)
    
    Returns:
        str: Generated OTP string
    """
    return ''.join(random.choices(string.digits, k=length))


async def send_otp_email(email: str, otp: str) -> bool:
    """
    Send OTP email to user asynchronously (non-blocking).
    
    Args:
        email: Recipient email address
        otp: OTP code to send
    
    Returns:
        bool: True if email sending started successfully, False otherwise
    """
    # Development mode: Log OTP to console if email credentials not configured
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("=" * 60)
        print("⚠️  EMAIL NOT CONFIGURED - DEVELOPMENT MODE")
        print("=" * 60)
        print(f"OTP for {email}: {otp}")
        print(f"This OTP expires in 5 minutes")
        print("=" * 60)
        print("\nTo enable email sending, configure MAIL_USERNAME and MAIL_PASSWORD in .env")
        print("See EMAIL_SETUP_GUIDE.md for detailed instructions\n")
        return True  # Return True to allow testing without email
    
    # Create email sending task without awaiting (fire and forget)
    asyncio.create_task(_send_email_task(email, otp))
    return True  # Return immediately


async def _send_email_task(email: str, otp: str):
    """
    Internal task to send email in background.
    """
    try:
        message = MessageSchema(
            subject="Your OTP Code",
            recipients=[email],
            body=f"""
            <html>
            <body>
                <h2>Your OTP Code</h2>
                <p>Your OTP code is: <strong>{otp}</strong></p>
                <p>This code will expire in 5 minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <br>
                <p>Best regards,<br>{MAIL_FROM_NAME}</p>
            </body>
            </html>
            """,
            subtype="html"
        )
        
        await fastmail.send_message(message)
        print(f"✅ Email sent successfully to {email}")
    except Exception as e:
        error_msg = str(e)
        print("=" * 60)
        print("❌ ERROR SENDING EMAIL")
        print("=" * 60)
        print(f"Error: {error_msg}")
        print(f"Email: {email}")
        
        # Provide helpful error messages
        if "535" in error_msg or "BadCredentials" in error_msg or "Username and Password not accepted" in error_msg:
            print("\n🔧 GMAIL CREDENTIALS ISSUE:")
            print("1. Ensure you're using Gmail App Password (not regular password)")
            print("2. Enable 2-Step Verification in Google Account")
            print("3. Generate App Password: https://myaccount.google.com/apppasswords")
            print("4. Use the 16-character App Password in MAIL_PASSWORD")
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            print("\n🔧 CONNECTION ISSUE:")
            print("1. Check your internet connection")
            print("2. Verify firewall allows SMTP (port 587)")
            print("3. Check MAIL_SERVER and MAIL_PORT in .env")
        
        print("\n📝 OTP for development/testing:")
        print(f"   Email: {email}")
        print(f"   OTP: {otp}")
        print("=" * 60)
        return False

