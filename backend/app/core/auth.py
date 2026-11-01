
import logging
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from backend.app.core.config import settings
from backend.app.core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedSeller:
    id: str
    db: Client
    access_token: str = ""


def get_current_seller(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedSeller:

    # 1. Require a Bearer token
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = credentials.credentials

    try:
        # 2. Ask Supabase Auth to validate the token
        auth_client = get_supabase_client()
        user_response = auth_client.auth.get_user(access_token)

        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        seller_id = str(user_response.user.id)

        # 3. Create a NEW client for this request.
        # Never mutate a shared client's authorization token:
        # concurrent sellers must not share authentication state.
        seller_db = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_PUBLISHABLE_KEY,
        )

        # 4. Forward the verified seller's JWT to PostgREST and Storage.
        seller_db.postgrest.auth(access_token)
        seller_db.options.headers["Authorization"] = f"Bearer {access_token}"
        seller_db._storage = None

        return AuthenticatedSeller(
            id=seller_id,
            db=seller_db,
            access_token=access_token,
        )

    except HTTPException:
        raise

    except Exception:
        logger.warning("Seller authentication failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
