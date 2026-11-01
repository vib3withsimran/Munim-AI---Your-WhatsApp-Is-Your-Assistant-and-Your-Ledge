import logging
from functools import lru_cache

from supabase import Client, create_client

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    if not settings.SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is missing")

    if not settings.SUPABASE_PUBLISHABLE_KEY:
        raise RuntimeError("SUPABASE_PUBLISHABLE_KEY is missing")

    client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_PUBLISHABLE_KEY
    )

    logger.info("Supabase client initialized")
    return client
