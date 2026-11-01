import urllib.request
import json
from backend.app.core.config import settings

def test_post(table, payload):
    url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/{table}"
    headers = {
        'apikey': settings.SUPABASE_PUBLISHABLE_KEY,
        'Authorization': f"Bearer {settings.SUPABASE_PUBLISHABLE_KEY}",
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

print("--- Test 1: customers without phone (NOT NULL) ---")
print(test_post("customers", {"seller_id": "00000000-0000-0000-0000-000000000000"}))

print("--- Test 2: customers with phone ---")
print(test_post("customers", {"seller_id": "00000000-0000-0000-0000-000000000000", "phone": "9999999999"}))

print("--- Test 3: payments without order_id ---")
print(test_post("payments", {"seller_id": "00000000-0000-0000-0000-000000000000", "amount": 500}))

print("--- Test 4: payments with order_id = None ---")
print(test_post("payments", {"seller_id": "00000000-0000-0000-0000-000000000000", "amount": 500, "order_id": None}))

print("--- Test 5: payments with non-existent order_id ---")
print(test_post("payments", {"seller_id": "00000000-0000-0000-0000-000000000000", "amount": 500, "order_id": "00000000-0000-0000-0000-000000000000"}))

print("--- Test 6: payments without amount (NOT NULL) ---")
print(test_post("payments", {"seller_id": "00000000-0000-0000-0000-000000000000"}))

