import re

with open('backend/app/services/dashboard_service.py', encoding='utf-8') as f:
    content = f.read()

# Match multiline db.table("...").select("...")
pattern = re.compile(r'db\.table\(\s*["\'](\w+)["\']\s*\)\s*\.select\(\s*["\']([^"\']+)["\']\s*\)', re.DOTALL)
matches = pattern.findall(content)
print("SELECT calls in dashboard_service.py:")
for tbl, cols in set(matches):
    clean_cols = " ".join(cols.split())
    print(f"  {tbl} -> {clean_cols}")
