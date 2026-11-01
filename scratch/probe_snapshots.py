from backend.app.core.supabase_client import get_supabase_client

supabase = get_supabase_client()

more_candidates = {
    "profiles": [
        "settings", "metadata", "avatar_url", "is_verified", "verified_at"
    ],
    "customers": [
        "avatar_url", "email", "metadata", "created_by", "updated_by"
    ],
    "products": [
        "metadata", "image_url", "slug", "created_by", "updated_by"
    ],
    "product_variants": [
        "title", "option1", "option2", "option3", "weight", "inventory_quantity", "metadata"
    ],
    "inventory": [
        "last_restocked_at", "metadata", "created_at"
    ],
    "orders": [
        "order_number", "payment_status", "fulfillment_status", "delivery_status",
        "paid_amount", "metadata", "placed_at", "completed_at", "cancelled_at"
    ],
    "order_items": [
        "product_name_snapshot", "sku_snapshot", "price_snapshot", "image_snapshot",
        "metadata", "created_at", "updated_at"
    ],
    "payments": [
        "paid_at", "payment_method", "currency", "metadata", "provider", "gateway",
        "verified_at", "verified_by", "receipt_url"
    ],
    "privacy_settings": [
        "notes", "reason", "created_at", "metadata"
    ],
    "media_files": [
        "filename", "mime_type", "size", "bytes", "metadata", "updated_at"
    ],
    "agent_logs": [
        "level", "session_id", "trace_id", "event_type", "error", "error_message"
    ]
}

print("=== CHECKING ADDITIONAL SYSTEM & SNAPSHOT COLUMNS ===")
for table, cols in more_candidates.items():
    found = []
    for c in cols:
        try:
            supabase.table(table).select(c).limit(1).execute()
            found.append(c)
        except Exception:
            pass
    if found:
        print(f"[{table}] FOUND NEW: {found}")
    else:
        print(f"[{table}] No additional columns from this batch.")

