import logging
from typing import Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client
from supabase_auth.errors import AuthApiError

from backend.app.core.config import settings
from backend.app.core.supabase_client import get_supabase_client
from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.models.auth_schemas import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    SellerInfo,
    ProfileResponse,
    ProfileUpdateRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


def _extract_single_record(raw_data: Any) -> dict[str, Any]:
    if isinstance(raw_data, list):
        return raw_data[0] if raw_data else {}
    if isinstance(raw_data, dict):
        return raw_data
    return {}


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest) -> SignupResponse:
    """
    Register a new seller using Supabase Auth.
    Business metadata is passed via signup options so that the profile-creation trigger can utilize it.
    Email confirmation is enabled: when no session is returned, returns a prompt to verify email.
    """
    auth_client = get_supabase_client()

    metadata: dict[str, Any] = {
        "business_name": req.business_name,
    }
    if req.phone:
        metadata["phone"] = req.phone
    if req.business_type:
        metadata["business_type"] = req.business_type

    credentials = {
        "email": str(req.email),
        "password": req.password,
        "options": {
            "data": metadata
        }
    }

    try:
        auth_response = auth_client.auth.sign_up(credentials)
        user = auth_response.user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed. Unable to create seller user."
            )

        # Detect email enumeration / duplicate user when email confirmation is enabled
        if hasattr(user, "identities") and user.identities == []:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )

        session = auth_response.session
        email_verification_required = session is None

        msg = (
            "Registration successful. Please verify your email to activate your account."
            if email_verification_required
            else "Registration successful."
        )

        return SignupResponse(
            success=True,
            message=msg,
            email_verification_required=email_verification_required,
            seller_id=str(user.id),
            email=user.email,
        )

    except AuthApiError as e:
        msg = e.message.lower() if e.message else ""
        if "already registered" in msg or "already exists" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message or "Invalid signup details."
        )

    except HTTPException:
        raise

    except Exception:
        logger.error("Unexpected error during seller signup", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration could not be completed. Please try again."
        )


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest) -> LoginResponse:
    """
    Authenticate a seller with email and password via Supabase Auth.
    Strictly handles email confirmation errors and returns tokens alongside seller profile details.
    """
    auth_client = get_supabase_client()

    try:
        auth_response = auth_client.auth.sign_in_with_password({
            "email": str(req.email),
            "password": req.password,
        })

        session = auth_response.session
        user = auth_response.user

        if not session or not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed. No active session returned."
            )

        # Fetch profile data with seller's own authenticated client
        seller_db = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
        seller_db.postgrest.auth(session.access_token)

        profile_data: dict[str, Any] = {}
        try:
            profile_res = (
                seller_db.table("profiles")
                .select("*")
                .eq("id", user.id)
                .maybe_single()
                .execute()
            )
            profile_data = _extract_single_record(profile_res.data)
        except Exception as e:
            logger.warning(f"Could not load seller profile during login: {e}")

        user_meta = user.user_metadata or {}
        business_name = profile_data.get("business_name") or user_meta.get("business_name")
        phone = profile_data.get("phone") or user_meta.get("phone")
        business_type = profile_data.get("business_type") or user_meta.get("business_type")

        return LoginResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            expires_in=session.expires_in,
            expires_at=session.expires_at,
            seller=SellerInfo(
                id=str(user.id),
                email=user.email,
                business_name=business_name,
                phone=phone,
                business_type=business_type,
            )
        )

    except AuthApiError as e:
        msg = e.message.lower() if e.message else ""
        if "not confirmed" in msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required. Please verify your email address before logging in."
            )
        if "invalid login credentials" in msg or "invalid credentials" in msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message or "Authentication failed."
        )

    except HTTPException:
        raise

    except Exception:
        logger.error("Unexpected error during seller login", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to an internal service error."
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    seller: Optional[AuthenticatedSeller] = Depends(get_current_seller)
) -> LogoutResponse:
    """
    Log out the authenticated seller.
    Notifies Supabase Auth to terminate the session if available.
    Note: Stateless JWT tokens must be removed client-side by clearing stored cookies/local storage.
    """
    if seller:
        try:
            seller.db.auth.sign_out()
        except Exception as e:
            logger.warning(f"Server-side signout failed or already invalidated: {e}")

    return LogoutResponse(
        success=True,
        message="Logged out successfully.",
        note=(
            "Session ended on server. Because JWT access tokens are stateless, "
            "the frontend client must purge its stored access and refresh tokens."
        )
    )


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    seller: AuthenticatedSeller = Depends(get_current_seller)
) -> ProfileResponse:
    """
    Retrieve authenticated seller profile details.
    Derives identity exclusively from the verified Bearer token, enforcing Row Level Security.
    """
    try:
        res = (
            seller.db.table("profiles")
            .select("*")
            .eq("id", seller.id)
            .maybe_single()
            .execute()
        )
        data = _extract_single_record(res.data)

        # Fetch email from Supabase Auth user record if available
        auth_client = get_supabase_client()
        user_email: Optional[str] = None
        try:
            auth_user = auth_client.auth.admin.get_user_by_id(seller.id) if hasattr(auth_client.auth, "admin") else None
            if auth_user and auth_user.user:
                user_email = auth_user.user.email
        except Exception:
            pass

        return ProfileResponse(
            id=seller.id,
            email=user_email,
            business_name=data.get("business_name"),
            phone=data.get("phone"),
            business_type=data.get("business_type"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
    except Exception as e:
        logger.error(f"Error retrieving profile for seller {seller.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve seller profile."
        )


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    req: ProfileUpdateRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller)
) -> ProfileResponse:
    """
    Update the authenticated seller's profile.
    Only allows updating business_name, phone, and business_type.
    Never permits modifying id, ownership, or internal database metadata.
    """
    update_data = req.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid profile fields provided for update."
        )

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        res = (
            seller.db.table("profiles")
            .update(update_data)
            .eq("id", seller.id)
            .execute()
        )

        extracted = _extract_single_record(res.data)
        if not extracted:
            # Fallback in case profile row wasn't pre-created by trigger
            update_data["id"] = seller.id
            upsert_res = (
                seller.db.table("profiles")
                .upsert(update_data)
                .execute()
            )
            updated_row = _extract_single_record(upsert_res.data) or update_data
        else:
            updated_row = extracted

        return ProfileResponse(
            id=seller.id,
            business_name=updated_row.get("business_name"),
            phone=updated_row.get("phone"),
            business_type=updated_row.get("business_type"),
            created_at=updated_row.get("created_at"),
            updated_at=updated_row.get("updated_at"),
        )

    except Exception as e:
        logger.error(f"Failed to update profile for seller {seller.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile."
        )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(req: ResetPasswordRequest) -> ResetPasswordResponse:
    """
    Request a password reset link.
    Never exposes whether an email address exists in the system to prevent user enumeration.
    """
    auth_client = get_supabase_client()
    try:
        auth_client.auth.reset_password_for_email(str(req.email))
    except Exception as e:
        logger.info(f"Password reset triggered (logged safely without leaking status): {type(e).__name__}")

    return ResetPasswordResponse(
        success=True,
        message="If this email is registered in our system, a password reset link has been dispatched."
    )
