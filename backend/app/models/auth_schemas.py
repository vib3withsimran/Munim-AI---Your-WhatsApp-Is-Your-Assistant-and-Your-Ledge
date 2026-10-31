import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_and_validate_email(v: str) -> str:
    clean = v.strip().lower()
    if not EMAIL_REGEX.match(clean):
        raise ValueError("Invalid email format")
    return clean


class SignupRequest(BaseModel):
    email: str = Field(description="Seller email address")
    password: str = Field(min_length=6, description="Password must be at least 6 characters")
    business_name: str = Field(min_length=1, max_length=150, description="Business or store name")
    phone: Optional[str] = Field(default=None, max_length=20, description="Contact phone number")
    business_type: Optional[str] = Field(default=None, max_length=100, description="Category/type of business")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _clean_and_validate_email(v)


class SignupResponse(BaseModel):
    success: bool = True
    message: str
    email_verification_required: bool
    seller_id: Optional[str] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _clean_and_validate_email(v)


class SellerInfo(BaseModel):
    id: str
    email: Optional[str] = None
    business_name: Optional[str] = None
    phone: Optional[str] = None
    business_type: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    expires_at: Optional[int] = None
    seller: SellerInfo


class LogoutResponse(BaseModel):
    success: bool = True
    message: str
    note: str = (
        "Server-side session cleared where applicable. "
        "Frontend clients must delete their stored JWT access token and refresh token."
    )


class ProfileResponse(BaseModel):
    id: str
    email: Optional[str] = None
    business_name: Optional[str] = None
    phone: Optional[str] = None
    business_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    business_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=20)
    business_type: Optional[str] = Field(default=None, max_length=100)


class ResetPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _clean_and_validate_email(v)


class ResetPasswordResponse(BaseModel):
    success: bool = True
    message: str = "If this email is registered in our system, a password reset link has been dispatched."
