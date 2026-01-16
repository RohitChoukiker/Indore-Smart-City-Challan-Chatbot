
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from dotenv import load_dotenv


load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_key_change_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "180"))


def create_token(payload: dict, days: Optional[int] = None) -> str:
  
    if days is None:
        days = JWT_EXPIRATION_DAYS
    
    to_encode = payload.copy()
    to_encode.update({
        "exp": datetime.utcnow() + timedelta(days=days),
        "iat": datetime.utcnow()
    })
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_id_from_token(authorization: Optional[str]) -> Optional[str]:
   
    if not authorization:
        return None
    
    try:
        
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            return None
        
        payload = decode_token(token)
        if payload:
            return payload.get("user_id")
        return None
    except (ValueError, AttributeError):
        return None


def generate_patterned_mpin() -> str:
   
    import random
    
   
    n = random.randint(0, 8)
    n_plus_1 = n + 1
    
   
    mpin = f"{n}{n_plus_1}{n}{n_plus_1}{n}{n_plus_1}"
    
    return mpin


