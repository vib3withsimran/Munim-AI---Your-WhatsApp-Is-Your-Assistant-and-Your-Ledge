import urllib.request
import json
from backend.app.core.config import settings

for tbl in ['profiles', 'customers', 'products', 'product_variants', 'inventory', 'orders', 'order_items', 'payments', 'privacy_settings', 'media_files', 'agent_logs']:
    url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/{tbl}"
    headers = {
        'apikey': settings.SUPABASE_PUBLISHABLE_KEY,
        'Authorization': f"Bearer {settings.SUPABASE_PUBLISHABLE_KEY}"
    }
    req = urllib.request.Request(url, headers=headers, method='OPTIONS')
    try:
        with urllib.request.urlopen(req) as response:
            print(f"=== {tbl} OPTIONS ===")
            print("Headers:")
            for h, v in response.headers.items():
                print(f"  {h}: {v}")
            body = response.read().decode()
            if body:
                print("  Body:", body[:500])
    except Exception as e:
        print(f"{tbl}: {e}")

