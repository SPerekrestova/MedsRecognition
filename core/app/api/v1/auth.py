"""Authentication endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, constr

from app.core.logging_config import logger
from app.services import session_service
from app.services.auth_service import get_auth_service

router = APIRouter()


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(gt=0, description="Token expiration time in seconds")
    refresh_token: Optional[str] = None


class RefreshToken(BaseModel):
    """Refresh token request model."""

    refresh_token: str = Field(..., min_length=1, description="Valid refresh token")


class UserCreate(BaseModel):
    """User registration model."""

    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Password must be between 8 and 72 characters and contain at least one letter and one number",
        pattern="^[A-Za-z0-9@$!%*#?&]*[A-Za-z][A-Za-z0-9@$!%*#?&]*[0-9][A-Za-z0-9@$!%*#?&]*$|^[A-Za-z0-9@$!%*#?&]*[0-9][A-Za-z0-9@$!%*#?&]*[A-Za-z][A-Za-z0-9@$!%*#?&]*$",
    )
    password_confirm: str = Field(..., description="Must match password field")
    username: Optional[constr(min_length=3, max_length=50)] = Field(
        None, description="Username between 3 and 50 characters"
    )


class ProfileCreate(BaseModel):
    """Profile creation model."""

    username: constr(min_length=3, max_length=50) = Field(
        ..., description="Username between 3 and 50 characters"
    )


class PasswordReset(BaseModel):
    """Password reset model."""

    token: str = Field(..., min_length=1, description="Valid reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Password must be between 8 and 72 characters and contain at least one letter and one number",
        pattern="^[A-Za-z0-9@$!%*#?&]*[A-Za-z][A-Za-z0-9@$!%*#?&]*[0-9][A-Za-z0-9@$!%*#?&]*$|^[A-Za-z0-9@$!%*#?&]*[0-9][A-Za-z0-9@$!%*#?&]*[A-Za-z][A-Za-z0-9@$!%*#?&]*$",
    )
    new_password_confirm: str = Field(..., description="Must match new_password field")


class EmailRequest(BaseModel):
    """Email request model."""

    email: EmailStr


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    if user_data.password != user_data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    try:
        service = get_auth_service()
        result = service.create_user_with_profile(
            email=str(user_data.email), password=user_data.password, username=user_data.username
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed"
            )

        return {
            "message": "Registration successful. You can now login.",
            "user_id": str(result.id),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration",
        )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return access token."""
    try:
        service = get_auth_service()
        try:
            success, result = service.authenticate_user(
                email=form_data.username, password=form_data.password
            )

            if not success or not result:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return {
                "access_token": result["access_token"],
                "token_type": "bearer",
                "expires_in": 3600,  # 1 hour
                "refresh_token": result["refresh_token"],
            }
        except Exception as auth_error:
            logger.error(f"Login error: {auth_error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login",
        )


@router.post("/logout")
async def logout(response: Response):
    """Logout current user."""
    try:
        session_service.logout_user()
        response.delete_cookie("session")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error during logout"
        )


@router.post("/refresh-token", response_model=Token)
async def refresh_token(token_data: RefreshToken):
    """Refresh access token using refresh token."""
    try:
        service = get_auth_service()
        session_dict = service.refresh_session(token_data.token)
        return {
            "access_token": session_dict["access_token"],
            "token_type": "bearer",
            "expires_in": 3600,  # 1 hour
            "refresh_token": session_dict["refresh_token"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
