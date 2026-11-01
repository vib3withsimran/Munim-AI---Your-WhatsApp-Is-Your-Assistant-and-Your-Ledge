-- ============================================================================
-- Migration: 20261101_002_fix_create_order_rpc_two_pass.sql
-- Description: Hardened two-pass atomic order creation with price consistency & inventory integrity:
--              1. Prevents foreign-key failure (inserts parent 'orders' before 'order_items')
--              2. Eliminates price-consistency race condition: Pass 1 buffers validated
--                 unit prices and snapshots in memory; Pass 2 reuses buffered data.
--              3. Deterministic catalog & inventory row locking:
--                 - products locked FOR SHARE OF p in p.id ASC order (blocks concurrent name/is_active updates)
--                 - product_variants locked FOR SHARE OF pv in pv.id ASC order (blocks concurrent price/sku/size/color updates)
--                 - inventory locked FOR UPDATE OF i in i.variant_id ASC order (serializes reservations, prevents deadlocks)
--              4. Inventory reservation integrity:
--                 - UPDATE public.inventory enforces (reserved_quantity + quantity) <= available_quantity
--                 - GET DIAGNOSTICS v_rows_updated = ROW_COUNT ensures exactly 1 row updated
--                 - Raises exception and triggers full rollback if row count <> 1
--              5. Guarantees orders.total_amount = SUM(order_items.line_total).
--              6. Atomic rollback on any failure.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.create_order_with_reservation_rpc(
    p_customer_id uuid,
    p_items jsonb,
    p_currency text DEFAULT 'INR',
    p_notes text DEFAULT NULL,
    p_seller_id uuid DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth, pg_temp
AS $$
DECLARE
    v_seller_id uuid;
    v_order_id uuid;
    v_item record;
    v_buffered_item record;
    v_variant_rec record;
    v_inv_rec record;
    v_line_total numeric(12, 2);
    v_total_amount numeric(12, 2) := 0.00;
    v_result jsonb;
    v_distinct_variants int;
    v_total_items int;
    v_validated_items jsonb := '[]'::jsonb;
    v_rows_updated integer;
BEGIN
    -- 1. Validate caller identity / seller context
    v_seller_id := auth.uid();
    IF v_seller_id IS NULL THEN
        -- Allow trusted backend service_role or direct DB admin sessions (session_user)
        IF p_seller_id IS NOT NULL AND (
            COALESCE(auth.jwt() ->> 'role', current_setting('request.jwt.claim.role', true)) = 'service_role'
            OR session_user IN ('postgres', 'supabase_admin')
        ) THEN
            v_seller_id := p_seller_id;
        ELSE
            RAISE EXCEPTION 'UNAUTHENTICATED: Caller must be authenticated' USING ERRCODE = '42501';
        END IF;
    ELSIF p_seller_id IS NOT NULL AND p_seller_id <> v_seller_id THEN
        RAISE EXCEPTION 'PERMISSION_DENIED: Caller seller_id mismatch' USING ERRCODE = '42501';
    END IF;

    -- 2. Validate customer ownership
    IF NOT EXISTS (
        SELECT 1 FROM public.customers
        WHERE id = p_customer_id AND seller_id = v_seller_id
    ) THEN
        RAISE EXCEPTION 'NOT_FOUND: Customer % not found or not owned by seller', p_customer_id USING ERRCODE = 'P0002';
    END IF;

    -- 3. Validate items payload
    IF p_items IS NULL OR jsonb_typeof(p_items) <> 'array' OR jsonb_array_length(p_items) = 0 THEN
        RAISE EXCEPTION 'INVALID_INPUT: Order items must be a non-empty array' USING ERRCODE = '22023';
    END IF;

    -- Validate each element has required fields
    IF EXISTS (
        SELECT 1 FROM jsonb_array_elements(p_items) AS elem
        WHERE elem->>'variant_id' IS NULL OR elem->>'quantity' IS NULL
    ) THEN
        RAISE EXCEPTION 'INVALID_INPUT: Each item must contain variant_id and quantity' USING ERRCODE = '22023';
    END IF;

    v_total_items := jsonb_array_length(p_items);
    SELECT count(DISTINCT (elem->>'variant_id')::uuid) INTO v_distinct_variants
    FROM jsonb_array_elements(p_items) AS elem;

    IF v_distinct_variants <> v_total_items THEN
        RAISE EXCEPTION 'DUPLICATE_ITEM: Duplicate variant_id in order items' USING ERRCODE = '22023';
    END IF;

    -- 4. Consistent lock ordering on catalog & inventory rows
    -- Lock parent products in ascending product id order (FOR SHARE OF p)
    -- This blocks concurrent UPDATE on products (e.g. name, is_active) until order creation completes
    PERFORM 1
    FROM public.products p
    WHERE p.seller_id = v_seller_id
      AND p.id IN (
          SELECT DISTINCT pv.product_id
          FROM public.product_variants pv
          WHERE pv.seller_id = v_seller_id
            AND pv.id IN (
                SELECT (elem->>'variant_id')::uuid
                FROM jsonb_array_elements(p_items) AS elem
            )
      )
    ORDER BY p.id ASC
    FOR SHARE OF p;

    -- Lock product_variants in ascending variant id order (FOR SHARE OF pv)
    -- This blocks concurrent UPDATE on product_variants (e.g. price, sku, size, color) until order creation completes
    PERFORM 1
    FROM public.product_variants pv
    WHERE pv.seller_id = v_seller_id
      AND pv.id IN (
          SELECT (elem->>'variant_id')::uuid
          FROM jsonb_array_elements(p_items) AS elem
      )
    ORDER BY pv.id ASC
    FOR SHARE OF pv;

    -- Lock inventory rows in ascending variant id order (FOR UPDATE OF i)
    -- This serializes stock reservations and eliminates deadlock risk
    PERFORM 1
    FROM public.inventory i
    WHERE i.seller_id = v_seller_id
      AND i.variant_id IN (
          SELECT (elem->>'variant_id')::uuid
          FROM jsonb_array_elements(p_items) AS elem
      )
    ORDER BY i.variant_id ASC
    FOR UPDATE OF i;

    -- 5. Allocate order ID
    v_order_id := gen_random_uuid();

    -- =========================================================================
    -- FIRST PASS: Validate items, verify active products, check stock,
    -- calculate line totals and total_amount, and buffer validated snapshot data.
    -- (NO MUTATIONS TO inventory OR order_items)
    -- =========================================================================
    FOR v_item IN
        SELECT
            (elem->>'variant_id')::uuid AS variant_id,
            (elem->>'quantity')::integer AS quantity
        FROM jsonb_array_elements(p_items) AS elem
        ORDER BY (elem->>'variant_id')::uuid ASC
    LOOP
        -- Check positive integer quantity
        IF v_item.quantity IS NULL OR v_item.quantity <= 0 THEN
            RAISE EXCEPTION 'INVALID_QUANTITY: Item quantity must be greater than 0' USING ERRCODE = '22023';
        END IF;

        -- Check variant ownership and parent product active status
        SELECT
            pv.id AS variant_id,
            pv.product_id,
            pv.sku,
            pv.size,
            pv.color,
            pv.price,
            p.name AS product_name,
            p.is_active
        INTO v_variant_rec
        FROM public.product_variants pv
        JOIN public.products p ON p.id = pv.product_id
        WHERE pv.id = v_item.variant_id
          AND pv.seller_id = v_seller_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'NOT_FOUND: Variant % not found or not owned by seller', v_item.variant_id USING ERRCODE = 'P0002';
        END IF;

        IF NOT v_variant_rec.is_active THEN
            RAISE EXCEPTION 'INACTIVE_PRODUCT: Product "%" (variant %) is inactive', v_variant_rec.product_name, v_item.variant_id USING ERRCODE = '22000';
        END IF;

        -- Check inventory record and sellable stock
        SELECT
            i.available_quantity,
            i.reserved_quantity
        INTO v_inv_rec
        FROM public.inventory i
        WHERE i.variant_id = v_item.variant_id
          AND i.seller_id = v_seller_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'NOT_FOUND: Inventory record for variant % not found', v_item.variant_id USING ERRCODE = 'P0002';
        END IF;

        -- Sellable stock = available_quantity - reserved_quantity
        IF (v_inv_rec.available_quantity - v_inv_rec.reserved_quantity) < v_item.quantity THEN
            RAISE EXCEPTION 'INSUFFICIENT_STOCK: Insufficient sellable stock for variant %. Available sellable: %, requested: %',
                v_item.variant_id,
                (v_inv_rec.available_quantity - v_inv_rec.reserved_quantity),
                v_item.quantity
                USING ERRCODE = 'P0001';
        END IF;

        -- Authoritative line total calculation
        v_line_total := ROUND(v_variant_rec.price * v_item.quantity, 2);
        v_total_amount := v_total_amount + v_line_total;

        -- Buffer validated item snapshot to guarantee Pass 2 uses EXACT same prices and details
        v_validated_items := v_validated_items || jsonb_build_array(
            jsonb_build_object(
                'variant_id', v_item.variant_id,
                'quantity', v_item.quantity,
                'unit_price', v_variant_rec.price,
                'line_total', v_line_total,
                'product_name_snapshot', v_variant_rec.product_name,
                'variant_snapshot', jsonb_build_object(
                    'sku', v_variant_rec.sku,
                    'size', v_variant_rec.size,
                    'color', v_variant_rec.color
                )
            )
        );
    END LOOP;

    -- =========================================================================
    -- INSERT PARENT ORDERS ROW FIRST
    -- (Satisfies foreign key constraint order_items_order_id_seller_id_fkey)
    -- =========================================================================
    INSERT INTO public.orders (
        id,
        seller_id,
        customer_id,
        status,
        total_amount,
        currency,
        notes,
        created_at,
        updated_at
    ) VALUES (
        v_order_id,
        v_seller_id,
        p_customer_id,
        'pending',
        v_total_amount,
        COALESCE(NULLIF(TRIM(p_currency), ''), 'INR'),
        p_notes,
        NOW(),
        NOW()
    );

    -- =========================================================================
    -- SECOND PASS: Mutate inventory (reserve stock) and insert order_items
    -- Uses buffered snapshots directly - ZERO re-queries of product_variants
    -- =========================================================================
    FOR v_buffered_item IN
        SELECT
            (elem->>'variant_id')::uuid AS variant_id,
            (elem->>'quantity')::integer AS quantity,
            (elem->>'unit_price')::numeric(12, 2) AS unit_price,
            (elem->>'line_total')::numeric(12, 2) AS line_total,
            elem->>'product_name_snapshot' AS product_name_snapshot,
            elem->'variant_snapshot' AS variant_snapshot
        FROM jsonb_array_elements(v_validated_items) AS elem
    LOOP
        -- Increment reserved stock atomically while enforcing reserved_quantity <= available_quantity
        UPDATE public.inventory
        SET reserved_quantity = reserved_quantity + v_buffered_item.quantity,
            updated_at = NOW()
        WHERE variant_id = v_buffered_item.variant_id
          AND seller_id = v_seller_id
          AND (reserved_quantity + v_buffered_item.quantity) <= available_quantity;

        GET DIAGNOSTICS v_rows_updated = ROW_COUNT;

        IF v_rows_updated <> 1 THEN
            RAISE EXCEPTION 'INSUFFICIENT_STOCK: Inventory reservation failed for variant % (expected 1 row updated, got %; stock condition violated or record missing)',
                v_buffered_item.variant_id,
                v_rows_updated
                USING ERRCODE = 'P0001';
        END IF;

        -- Insert line item with guaranteed price consistency and snapshots
        INSERT INTO public.order_items (
            id,
            order_id,
            seller_id,
            variant_id,
            quantity,
            unit_price,
            line_total,
            product_name_snapshot,
            variant_snapshot
        ) VALUES (
            gen_random_uuid(),
            v_order_id,
            v_seller_id,
            v_buffered_item.variant_id,
            v_buffered_item.quantity,
            v_buffered_item.unit_price,
            v_buffered_item.line_total,
            v_buffered_item.product_name_snapshot,
            v_buffered_item.variant_snapshot
        );
    END LOOP;

    -- Return complete created order and its items
    SELECT jsonb_build_object(
        'id', o.id,
        'seller_id', o.seller_id,
        'customer_id', o.customer_id,
        'status', o.status,
        'total_amount', o.total_amount,
        'currency', o.currency,
        'notes', o.notes,
        'created_at', o.created_at,
        'updated_at', o.updated_at,
        'items', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', oi.id,
                    'order_id', oi.order_id,
                    'seller_id', oi.seller_id,
                    'variant_id', oi.variant_id,
                    'quantity', oi.quantity,
                    'unit_price', oi.unit_price,
                    'line_total', oi.line_total,
                    'product_name_snapshot', oi.product_name_snapshot,
                    'variant_snapshot', oi.variant_snapshot
                )
            )
            FROM public.order_items oi
            WHERE oi.order_id = o.id
        )
    ) INTO v_result
    FROM public.orders o
    WHERE o.id = v_order_id;

    RETURN v_result;
END;
$$;

-- Security Permissions
REVOKE ALL ON FUNCTION public.create_order_with_reservation_rpc(uuid, jsonb, text, text, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.create_order_with_reservation_rpc(uuid, jsonb, text, text, uuid) FROM anon;
GRANT EXECUTE ON FUNCTION public.create_order_with_reservation_rpc(uuid, jsonb, text, text, uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.create_order_with_reservation_rpc(uuid, jsonb, text, text, uuid) TO service_role;
