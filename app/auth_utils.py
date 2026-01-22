from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    # Ensure password is not None
    if not password:
        raise ValueError("Password cannot be empty")

    # bcrypt max size = 72 bytes
    password = password[:72]
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise ValueError("Invalid token")
