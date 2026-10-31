"""
Munim AI — Environment & API Validator (Twilio & Meta Support)
Run: python scripts/check_env.py
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")

# Load .env manually
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
env_vars = {}
if os.path.isfile(env_path):
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                env_vars[key.strip()] = val.strip()

def get(key):
    return env_vars.get(key, "")

OK   = "[OK] "
FAIL = "[FAIL]"
WARN = "[WARN]"

results = []

def check(label, passed, note=""):
    icon = OK if passed else FAIL
    results.append(passed)
    print(f"  {icon}  {label}" + (f"  →  {note}" if note else ""))

def warn(label, note=""):
    print(f"  {WARN}  {label}" + (f"  →  {note}" if note else ""))

# ── 1. Required fields in .env ────────────────────────────────────────────────
print("\n[1] Checking environment fields in .env")

# Provider check: Twilio preferred
twilio_configured = bool(get("TWILIO_ACCOUNT_SID") and get("TWILIO_AUTH_TOKEN"))
if twilio_configured:
    check("TWILIO_ACCOUNT_SID", bool(get("TWILIO_ACCOUNT_SID")), "Found")
    check("TWILIO_AUTH_TOKEN", bool(get("TWILIO_AUTH_TOKEN")), "Found")
    check("TWILIO_WHATSAPP_NUMBER", bool(get("TWILIO_WHATSAPP_NUMBER")), f"Using: {get('TWILIO_WHATSAPP_NUMBER')}")
else:
    warn("Twilio credentials not found in .env", "Add TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to .env")
    check("WHATSAPP_PHONE_NUMBER_ID (Meta fallback)", bool(get("WHATSAPP_PHONE_NUMBER_ID")))

core_required = [
    "OWNER_WHATSAPP_NUMBER",
    "GOOGLE_SHEET_ID",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "DATABASE_URL",
    "APP_SECRET_KEY",
]
for key in core_required:
    val = get(key)
    check(key, bool(val), "MISSING" if not val else "")

# ── 2. Format checks ──────────────────────────────────────────────────────────
print("\n[2] Format checks")

sheet_id = get("GOOGLE_SHEET_ID")
check("GOOGLE_SHEET_ID — clean ID",
      not sheet_id.startswith("http"),
      "Remove full URL, keep only the ID between /d/ and /edit" if sheet_id.startswith("http") else "")

owner = get("OWNER_WHATSAPP_NUMBER")
check("OWNER_WHATSAPP_NUMBER — digits only",
      owner.isdigit(),
      f"Got: '{owner}'" if not owner.isdigit() else f"Got: {owner}")

gemini_key = get("GEMINI_API_KEY")
valid_prefix = gemini_key.startswith("AIza") or gemini_key.startswith("AQ.")
check("GEMINI_API_KEY format", valid_prefix)

svc_path = get("GOOGLE_SERVICE_ACCOUNT_JSON")
svc_full = os.path.join(os.path.dirname(__file__), "..", svc_path.lstrip("./"))
check("service_account.json file exists", os.path.isfile(svc_full))

# ── 3. Live API checks ────────────────────────────────────────────────────────
print("\n[3] Live API checks (needs internet)")

# 3a. WhatsApp Provider (Twilio or Meta)
twilio_sid = get("TWILIO_ACCOUNT_SID")
twilio_token = get("TWILIO_AUTH_TOKEN")

if twilio_sid and twilio_token:
    print("  Checking Twilio API...")
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}.json"
        req = urllib.request.Request(url)
        cred_b64 = base64.b64encode(f"{twilio_sid}:{twilio_token}".encode()).decode()
        req.add_header("Authorization", f"Basic {cred_b64}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        check("Twilio API — Account SID & Auth Token valid", True, f"Account: {data.get('friendly_name', 'Active')}")
    except urllib.error.HTTPError as e:
        check("Twilio API — Token valid", False, f"HTTP {e.code}: {e.read().decode()[:100]}")
    except Exception as e:
        check("Twilio API — Reachable", False, str(e)[:80])
else:
    print("  Checking Meta WhatsApp Cloud API (Fallback)...")
    wa_token = get("WHATSAPP_ACCESS_TOKEN")
    wa_phone_id = get("WHATSAPP_PHONE_NUMBER_ID")
    wa_version = get("WHATSAPP_API_VERSION") or "v19.0"
    try:
        url = f"https://graph.facebook.com/{wa_version}/{wa_phone_id}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {wa_token}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        check("WhatsApp Cloud API — token valid", True, f"Number: {data.get('display_phone_number','?')}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        check("WhatsApp Cloud API — token valid", False, f"HTTP {e.code}: {body[:120]}")
    except Exception as e:
        check("WhatsApp Cloud API — reachable", False, str(e)[:80])

# 3b. Gemini API
print("  Checking Gemini API...")
gemini_key = get("GEMINI_API_KEY")
gemini_model = get("GEMINI_MODEL") or "gemini-3.5-flash"
try:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
    payload = json.dumps({"contents":[{"parts":[{"text":"Reply with just the word OK"}]}]}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    reply = data.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","?")
    check("Gemini API — key valid & model reachable", True, f"Model replied: {reply.strip()[:40]}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    check("Gemini API — key valid", False, f"HTTP {e.code}: {body[:120]}")
except Exception as e:
    check("Gemini API — reachable", False, str(e)[:80])

# 3c. Groq API
print("  Checking Groq API...")
groq_key = get("GROQ_API_KEY")
try:
    url = "https://api.groq.com/openai/v1/models"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {groq_key}",
        "User-Agent": "MunimAI/1.0"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    models = [m["id"] for m in data.get("data", []) if "whisper" in m["id"].lower()]
    check("Groq API — key valid", True, f"Whisper models: {', '.join(models) or 'none found'}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    check("Groq API — key valid", False, f"HTTP {e.code}: {body[:120]}")
except Exception as e:
    check("Groq API — reachable", False, str(e)[:80])

# 3d. Google Sheets
print("  Checking Google service account JSON...")
if os.path.isfile(svc_full):
    try:
        with open(svc_full, encoding="utf-8") as f:
            svc = json.load(f)
        expected_keys = {"type","project_id","private_key","client_email"}
        missing = expected_keys - set(svc.keys())
        check("service_account.json — valid structure", not missing,
              f"Account: {svc.get('client_email','?')}")
    except Exception as e:
        check("service_account.json — parseable JSON", False, str(e))
else:
    check("service_account.json — file found", False, "Missing in backend/data/service_account.json")

# ── Summary ───────────────────────────────────────────────────────────────────
passed = sum(results)
total  = len(results)
print(f"\n{'='*50}")
print(f"  Result: {passed}/{total} checks passed")
print(f"{'='*50}\n")
