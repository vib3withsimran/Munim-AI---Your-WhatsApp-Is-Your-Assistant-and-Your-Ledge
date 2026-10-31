import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import getpass

from supabase import create_client
from backend.app.core.config import settings

supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_PUBLISHABLE_KEY
)

# Sign in as Seller A
print("LOGIN AS SELLER A")
email_a = input("Seller A email: ")
password_a = getpass.getpass("Seller A password: ")

seller_a = supabase.auth.sign_in_with_password({
    "email": email_a,
    "password": password_a
})

seller_a_id = seller_a.user.id
print("Seller A authenticated:", seller_a_id)

# Create a temporary customer belonging to Seller A
test_phone = "999000000001"

insert_response = (
    supabase.table("customers")
    .insert({
        "seller_id": seller_a_id,
        "name": "RLS Test Customer",
        "phone": test_phone
    })
    .execute()
)

print("Temporary customer created:", bool(insert_response.data))

# Sign out Seller A
supabase.auth.sign_out()

# Sign in as Seller B
print("\nLOGIN AS SELLER B")
email_b = input("Seller B email: ")
password_b = getpass.getpass("Seller B password: ")

seller_b = supabase.auth.sign_in_with_password({
    "email": email_b,
    "password": password_b
})

seller_b_id = seller_b.user.id
print("Seller B authenticated:", seller_b_id)

if seller_a_id == seller_b_id:
    raise RuntimeError("Both logins resolved to the same seller!")

# Try to read Seller A's customer as Seller B
check_response = (
    supabase.table("customers")
    .select("id, seller_id, name, phone")
    .eq("phone", test_phone)
    .execute()
)

if check_response.data:
    print("FAIL: Seller B can see Seller A's customer!")
else:
    print("PASS: Seller B cannot see Seller A's customer.")

# Sign out
supabase.auth.sign_out()
