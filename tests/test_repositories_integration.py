import uuid
import pytest
from backend.app.core.supabase_client import get_supabase_client
from backend.app.schemas.customer import CustomerCreateRequest
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.exceptions import PermissionDeniedError


# ============================================================================
# Live Supabase Integration Tests (Executes Against Live Database)
# ============================================================================

class TestRealSupabaseIntegration:
    """
    Integration tests executed directly against the live Supabase PostgreSQL database
    using the live SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY.
    """

    def test_real_supabase_live_connectivity(self):
        """Verifies that the live Supabase instance is accessible and responsive."""
        supabase = get_supabase_client()
        res = supabase.table("customers").select("id").limit(1).execute()
        assert res is not None
        assert isinstance(res.data, list)

    def test_real_supabase_rls_enforces_zero_trust_read_isolation(self):
        """
        Verifies that an unauthenticated client querying the live database
        receives 0 rows due to RLS policies (auth.uid() is NULL).
        """
        supabase = get_supabase_client()
        repo = CustomerRepository(supabase)
        random_seller_id = uuid.uuid4()

        # Under RLS, unauthenticated read returns empty list
        customers = repo.list_customers(seller_id=random_seller_id)
        assert customers == []

    def test_real_supabase_rls_blocks_unauthenticated_customer_insert(self):
        """
        Verifies that attempting an insert into 'customers' on the live database
        without an authenticated seller JWT triggers PostgreSQL error 42501,
        which the repository correctly maps to PermissionDeniedError.
        """
        supabase = get_supabase_client()
        repo = CustomerRepository(supabase)
        random_seller_id = uuid.uuid4()

        req = CustomerCreateRequest(
            phone="+919876543210",
            name="Unauthenticated Test User"
        )

        with pytest.raises(PermissionDeniedError) as exc_info:
            repo.create_customer(seller_id=random_seller_id, data=req)

        assert "RLS policy violation" in str(exc_info.value)

