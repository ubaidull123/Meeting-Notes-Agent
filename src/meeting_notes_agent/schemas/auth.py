"""Authentication schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
            }
        }
    )


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
            }
        }
    )


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newsecurepassword456",
            }
        }
    )


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    """Verify email request."""
    token: str