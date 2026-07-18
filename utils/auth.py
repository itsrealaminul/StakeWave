"""Auth utilities"""
import jwt
import hashlib
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "stakewave-secret")
JWT_ALGORITHM = "HS256"


def create_token(telegram_id: int, username: str = None) -> str:
    payload = {
        "telegram_id": telegram_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=30),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except:
        return None


def generate_referral_code(telegram_id: int) -> str:
    secret = os.getenv("SECRET_KEY", "stakewave")
    return hashlib.md5(f"{secret}-{telegram_id}".encode()).hexdigest()[:8].upper()
