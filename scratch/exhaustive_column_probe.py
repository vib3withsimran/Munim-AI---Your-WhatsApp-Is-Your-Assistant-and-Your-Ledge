from backend.app.core.supabase_client import get_supabase_client

supabase = get_supabase_client()

exhaustive_candidates = {
    "profiles": [
        "id", "business_name", "owner_name", "phone", "business_type",
        "created_at", "updated_at", "email", "address", "currency", "full_name",
        "user_id", "city", "state", "pincode", "country", "logo_url", "is_active", "status"
    ],
    "customers": [
        "id", "seller_id", "phone", "name", "notes", "created_at", "updated_at",
        "status", "last_seen", "total_due", "due_amount", "is_private", "tags",
        "address", "email", "alt_phone", "balance", "order_count"
    ],
    "products": [
        "id", "seller_id", "name", "description", "category", "image_path",
        "is_active", "created_at", "updated_at", "price", "base_price",
        "stock_qty", "stock", "quantity", "sku", "aliases", "unit", "image_url", "images"
    ],
    "product_variants": [
        "id", "product_id", "seller_id", "sku", "size", "color", "price",
        "is_active", "created_at", "updated_at", "title", "name", "stock_quantity",
        "stock_qty", "inventory_qty", "barcode", "mrp", "cost_price"
    ],
    "inventory": [
        "id", "seller_id", "variant_id", "product_variant_id", "product_id",
        "available_quantity", "reserved_quantity", "low_stock_threshold",
        "created_at", "updated_at", "quantity", "stock", "location", "sku", "reorder_level"
    ],
    "orders": [
        "id", "seller_id", "customer_id", "status", "total_amount", "currency",
        "notes", "delivery_address", "created_at", "updated_at", "customer_phone",
        "amount_paid", "amount_due", "payment_status", "items_json", "order_number", "shipping_address"
    ],
    "order_items": [
        "id", "order_id", "seller_id", "variant_id", "product_variant_id",
        "product_id", "quantity", "unit_price", "line_total", "product_name",
        "variant_name", "product_snapshot", "variant_snapshot", "created_at",
        "updated_at", "price", "total", "discount"
    ],
    "payments": [
        "id", "seller_id", "order_id", "customer_id", "amount", "currency",
        "payment_method", "method", "status", "transaction_reference",
        "upi_txn_id", "screenshot_url", "verified", "verified_at",
        "created_at", "updated_at", "notes", "raw_data", "reference_id", "amount_paid"
    ],
    "privacy_settings": [
        "id", "seller_id", "customer_id", "phone", "is_private", "paused_at",
        "resumed_at", "created_at", "updated_at", "settings", "enabled", "notes"
    ],
    "media_files": [
        "id", "seller_id", "bucket", "file_path", "filename", "mime_type",
        "size_bytes", "storage_path", "public_url", "entity_type", "entity_id",
        "created_at", "updated_at", "file_type", "url"
    ],
    "agent_logs": [
        "id", "seller_id", "agent_name", "action", "message_id", "customer_phone",
        "input_text", "output_text", "confidence", "metadata", "status",
        "created_at", "updated_at", "operation", "details", "log_level"
    ],
}

print("=== EXHAUSTIVE COLUMN VERIFICATION ===")
for table, cols in exhaustive_candidates.items():
    confirmed = []
    absent = []
    for col in cols:
        try:
            supabase.table(table).select(col).limit(1).execute()
            confirmed.append(col)
        except Exception as e:
            if "does not exist" in str(e):
                absent.append(col)
            else:
                confirmed.append(f"{col}")
    print(f"\n[{table}] ({len(confirmed)} confirmed):")
    print("  CONFIRMED:", confirmed)
    print("  ABSENT:", absent)

