import urllib.request
from backend.app.core.config import settings

url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/rpc/"
headers = {
    'apikey': settings.SUPABASE_PUBLISHABLE_KEY,
    'Authorization': f"Bearer {settings.SUPABASE_PUBLISHABLE_KEY}"
}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode())
except Exception as e:
    print('Err:', e)

