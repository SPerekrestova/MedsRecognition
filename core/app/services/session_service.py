"""Authentication dependencies for FastAPI routes."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.services.auth_service import get_auth_service

# Main OAuth2 scheme for required authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", scheme_name="JWT")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    service = get_auth_service()
    user_data = service.verify_token(token)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_data


def logout_user(token: str = Depends(oauth2_scheme)):
    service = get_auth_service()
    service.logout_user(token)
