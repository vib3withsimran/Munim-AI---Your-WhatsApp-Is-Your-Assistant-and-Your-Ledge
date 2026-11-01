import urllib.request
import json
from backend.app.core.config import settings

def test_post(table, payload):
    url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/{table}"
    headers = {
        'apikey': settings.SUPABASE_PUBLISHABLE_KEY,
        'Authorization': f"Bearer {settings.SUPABASE_PUBLISHABLE_KEY}",
        'Content-Type': 'application/json'
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

print("Type syntax test on order_id:", test_post("payments", {"order_id": "not-a-uuid"}))

