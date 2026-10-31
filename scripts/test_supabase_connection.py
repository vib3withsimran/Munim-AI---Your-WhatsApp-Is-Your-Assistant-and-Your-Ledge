from backend.app.core.config import settings
from backend.app.core.supabase_client import get_supabase_client


def main():
    print("\n--- Munim AI: Supabase Connection Test ---")

    # Test 1: Environment variables
    print("\n[1] Checking configuration...")

    if not settings.SUPABASE_URL:
        print("FAILED: SUPABASE_URL is missing")
        return

    if not settings.SUPABASE_PUBLISHABLE_KEY:
        print("FAILED: SUPABASE_PUBLISHABLE_KEY is missing")
        return

    print("SUCCESS: Supabase credentials loaded")

    # Test 2: Client initialization
    print("\n[2] Initializing Supabase client...")

    try:
        supabase = get_supabase_client()
        print("SUCCESS: Supabase client initialized")

    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return

    # Test 3: Database API query
    print("\n[3] Testing PostgreSQL access...")

    try:
        response = (
            supabase
            .table("profiles")
            .select("id")
            .limit(1)
            .execute()
        )

        print("SUCCESS: Database query executed")
        print(f"Rows returned: {len(response.data)}")

    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return

    print("\n--- Supabase Connection Test Completed ---")


if __name__ == "__main__":
    main()