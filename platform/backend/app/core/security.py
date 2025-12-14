from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import get_settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class TokenData:
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role


def create_access_token(username: str, role: str) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: Optional[str] = payload.get("sub")
        role: str = payload.get("role", "viewer")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return TokenData(username=username, role=role)
