import urllib.request
from backend.app.core.config import settings

url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/"
headers = {
    'apikey': settings.SUPABASE_PUBLISHABLE_KEY,
    'Authorization': f"Bearer {settings.SUPABASE_PUBLISHABLE_KEY}",
    'Accept': 'application/openapi+json'
}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        print(resp.read().decode()[:500])
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode())
except Exception as e:
    print('Err:', e)

