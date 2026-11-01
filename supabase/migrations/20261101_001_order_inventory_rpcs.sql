-- ============================================================================
-- Migration: 20261101_001_order_inventory_rpcs.sql
-- Description: Atomic PostgreSQL transactional operations for Munim AI
--              1. Inventory quantity check constraint
--              2. create_order_with_reservation_rpc
--              3. fulfill_order_rpc
--              4. cancel_order_rpc
-- ============================================================================

-- Step 1: Enforce inventory semantic bounds at database engine level
-- 0 <= reserved_quantity <= available_quantity
DO $$
BEGIN
    -- Fix any historical inconsistencies before adding constraint:
    -- Clamp reserved_quantity between 0 and available_quantity
    UPDATE public.inventory
    SET reserved_quantity = GREATEST(0, LEAST(reserved_quantity, available_quantity))
    WHERE reserved_quantity < 0 OR reserved_quantity > available_quantity;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_inventory_quantities_valid'
    ) THEN
        ALTER TABLE public.inventory
        ADD CONSTRAINT chk_inventory_quantities_valid
        CHECK (reserved_quantity >= 0 AND available_quantity >= 0 AND reserved_quantity <= available_quantity);
    END IF;
END $$;


-- ============================================================================
-- 1. Atomic Order Creation with Inventory Reservation
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
    v_variant_rec record;
    v_inv_rec record;
    v_line_total numeric(12, 2);
    v_total_amount numeric(12, 2) := 0.00;
    v_result jsonb;
    v_distinct_variants int;
    v_total_items int;
BEGIN
    -- 1. Validate caller identity / seller context
    v_seller_id := auth.uid();
    IF v_seller_id IS NULL THEN
        -- Allow trusted backend service_role or direct DB admin sessions (session_user)
        -- Note: inside SECURITY DEFINER, current_user is the owner (postgres), so we check session_user / JWT claims
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

    -- 4. Consistent lock ordering on inventory rows
    -- Lock all relevant inventory rows in ascending order of variant_id to guarantee deadlock-free concurrency
    PERFORM 1
    FROM public.inventory i
    WHERE i.seller_id = v_seller_id
      AND i.variant_id IN (
          SELECT (elem->>'variant_id')::uuid
          FROM jsonb_array_elements(p_items) AS elem
      )
    ORDER BY i.variant_id ASC
    FOR UPDATE;

    -- 5. Allocate order ID
    v_order_id := gen_random_uuid();

    -- 6. Iterate through items in deterministic ascending order of variant_id
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

        -- Check variant ownership and fetch parent product information
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

        -- Lock and inspect inventory row
        SELECT
            i.available_quantity,
            i.reserved_quantity
        INTO v_inv_rec
        FROM public.inventory i
        WHERE i.variant_id = v_item.variant_id
          AND i.seller_id = v_seller_id
        FOR UPDATE;

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

        -- Calculate authoritative line total using PostgreSQL numeric arithmetic
        v_line_total := ROUND(v_variant_rec.price * v_item.quantity, 2);
        v_total_amount := v_total_amount + v_line_total;

        -- Increment reserved stock
        UPDATE public.inventory
        SET reserved_quantity = reserved_quantity + v_item.quantity,
            updated_at = NOW()
        WHERE variant_id = v_item.variant_id
          AND seller_id = v_seller_id;

        -- Insert line item with canonical snapshots
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
            v_item.variant_id,
            v_item.quantity,
            v_variant_rec.price,
            v_line_total,
            v_variant_rec.product_name,
            jsonb_build_object(
                'sku', v_variant_rec.sku,
                'size', v_variant_rec.size,
                'color', v_variant_rec.color
            )
        );
    END LOOP;

    -- 7. Insert master order record
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

    -- 8. Return complete created order and its items
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


-- ============================================================================
-- 2. Atomic Order Fulfillment RPC
-- ============================================================================
CREATE OR REPLACE FUNCTION public.fulfill_order_rpc(
    p_order_id uuid,
    p_seller_id uuid DEFAULT NULL,
    p_target_status text DEFAULT 'completed'
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth, pg_temp
AS $$
DECLARE
    v_seller_id uuid;
    v_order_rec record;
    v_item record;
    v_inv_rec record;
    v_result jsonb;
    v_target_status text;
BEGIN
    -- 1. Validate caller identity / seller context
    v_seller_id := auth.uid();
    IF v_seller_id IS NULL THEN
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

    -- Validate target status
    v_target_status := LOWER(TRIM(COALESCE(p_target_status, 'completed')));
    IF v_target_status NOT IN ('shipped', 'completed', 'delivered') THEN
        RAISE EXCEPTION 'INVALID_INPUT: Target fulfillment status must be shipped, completed, or delivered' USING ERRCODE = '22023';
    END IF;

    -- 2. Lock and verify order ownership
    SELECT id, seller_id, status, total_amount
    INTO v_order_rec
    FROM public.orders
    WHERE id = p_order_id AND seller_id = v_seller_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'NOT_FOUND: Order % not found or not owned by seller', p_order_id USING ERRCODE = 'P0002';
    END IF;

    -- 3. Verify eligible status
    IF v_order_rec.status IN ('shipped', 'completed', 'delivered') THEN
        RAISE EXCEPTION 'INVALID_ORDER_TRANSITION: Order % is already fulfilled (current status: %)', p_order_id, v_order_rec.status USING ERRCODE = '22000';
    ELSIF v_order_rec.status = 'cancelled' THEN
        RAISE EXCEPTION 'INVALID_ORDER_TRANSITION: Cannot fulfill cancelled order %', p_order_id USING ERRCODE = '22000';
    ELSIF v_order_rec.status NOT IN ('pending', 'confirmed', 'processing') THEN
        RAISE EXCEPTION 'INVALID_ORDER_TRANSITION: Cannot fulfill order % with status %', p_order_id, v_order_rec.status USING ERRCODE = '22000';
    END IF;

    -- 4. Lock related inventory rows in consistent ascending order
    PERFORM 1
    FROM public.inventory i
    WHERE i.seller_id = v_seller_id
      AND i.variant_id IN (
          SELECT oi.variant_id
          FROM public.order_items oi
          WHERE oi.order_id = p_order_id AND oi.seller_id = v_seller_id
      )
    ORDER BY i.variant_id ASC
    FOR UPDATE;

    -- 5. Full fulfillment check & deduction: Partial fulfillment is explicitly rejected
    FOR v_item IN
        SELECT oi.variant_id, oi.quantity
        FROM public.order_items oi
        WHERE oi.order_id = p_order_id AND oi.seller_id = v_seller_id
        ORDER BY oi.variant_id ASC
    LOOP
        SELECT available_quantity, reserved_quantity
        INTO v_inv_rec
        FROM public.inventory
        WHERE variant_id = v_item.variant_id AND seller_id = v_seller_id
        FOR UPDATE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'NOT_FOUND: Inventory record for variant % not found', v_item.variant_id USING ERRCODE = 'P0002';
        END IF;

        IF v_inv_rec.available_quantity < v_item.quantity THEN
            RAISE EXCEPTION 'INSUFFICIENT_STOCK: Physical available quantity (%) is less than order quantity (%) for variant %',
                v_inv_rec.available_quantity, v_item.quantity, v_item.variant_id USING ERRCODE = 'P0001';
        END IF;

        IF v_inv_rec.reserved_quantity < v_item.quantity THEN
            RAISE EXCEPTION 'INSUFFICIENT_STOCK: Reserved quantity (%) is less than order quantity (%) for variant %',
                v_inv_rec.reserved_quantity, v_item.quantity, v_item.variant_id USING ERRCODE = 'P0001';
        END IF;

        -- Decrement physical available stock and release corresponding reserved stock
        UPDATE public.inventory
        SET available_quantity = available_quantity - v_item.quantity,
            reserved_quantity = reserved_quantity - v_item.quantity,
            updated_at = NOW()
        WHERE variant_id = v_item.variant_id AND seller_id = v_seller_id;
    END LOOP;

    -- 6. Update order status
    UPDATE public.orders
    SET status = v_target_status,
        updated_at = NOW()
    WHERE id = p_order_id AND seller_id = v_seller_id;

    -- 7. Return updated order
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
    WHERE o.id = p_order_id;

    RETURN v_result;
END;
$$;


-- ============================================================================
-- 3. Atomic Order Cancellation RPC
-- ============================================================================
CREATE OR REPLACE FUNCTION public.cancel_order_rpc(
    p_order_id uuid,
    p_seller_id uuid DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth, pg_temp
AS $$
DECLARE
    v_seller_id uuid;
    v_order_rec record;
    v_item record;
    v_inv_rec record;
    v_result jsonb;
BEGIN
    -- 1. Validate caller identity / seller context
    v_seller_id := auth.uid();
    IF v_seller_id IS NULL THEN
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

    -- 2. Lock and verify order ownership
    SELECT id, seller_id, status, total_amount
    INTO v_order_rec
    FROM public.orders
    WHERE id = p_order_id AND seller_id = v_seller_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'NOT_FOUND: Order % not found or not owned by seller', p_order_id USING ERRCODE = 'P0002';
    END IF;

    -- 3. Verify cancellation is permitted
    IF v_order_rec.status = 'cancelled' THEN
        RAISE EXCEPTION 'INVALID_ORDER_TRANSITION: Order % is already cancelled', p_order_id USING ERRCODE = '22000';
    ELSIF v_order_rec.status IN ('shipped', 'completed', 'delivered') THEN
        RAISE EXCEPTION 'INVALID_ORDER_TRANSITION: Cannot cancel already fulfilled order % (current status: %)', p_order_id, v_order_rec.status USING ERRCODE = '22000';
    END IF;

    -- 4. Lock related inventory rows in consistent ascending order
    PERFORM 1
    FROM public.inventory i
    WHERE i.seller_id = v_seller_id
      AND i.variant_id IN (
          SELECT oi.variant_id
          FROM public.order_items oi
          WHERE oi.order_id = p_order_id AND oi.seller_id = v_seller_id
      )
    ORDER BY i.variant_id ASC
    FOR UPDATE;

    -- 5. Release reserved stock exactly once without touching available physical stock
    FOR v_item IN
        SELECT oi.variant_id, oi.quantity
        FROM public.order_items oi
        WHERE oi.order_id = p_order_id AND oi.seller_id = v_seller_id
        ORDER BY oi.variant_id ASC
    LOOP
        SELECT reserved_quantity
        INTO v_inv_rec
        FROM public.inventory
        WHERE variant_id = v_item.variant_id AND seller_id = v_seller_id
        FOR UPDATE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'NOT_FOUND: Inventory record for variant % not found', v_item.variant_id USING ERRCODE = 'P0002';
        END IF;

        IF v_inv_rec.reserved_quantity < v_item.quantity THEN
            RAISE EXCEPTION 'CONSTRAINT_VIOLATION: Reserved quantity (%) is less than order item quantity (%) for variant %',
                v_inv_rec.reserved_quantity, v_item.quantity, v_item.variant_id USING ERRCODE = '23514';
        END IF;

        -- Release reservation: decrement reserved_quantity, keep available_quantity intact
        UPDATE public.inventory
        SET reserved_quantity = reserved_quantity - v_item.quantity,
            updated_at = NOW()
        WHERE variant_id = v_item.variant_id AND seller_id = v_seller_id;
    END LOOP;

    -- 6. Update order status to cancelled
    UPDATE public.orders
    SET status = 'cancelled',
        updated_at = NOW()
    WHERE id = p_order_id AND seller_id = v_seller_id;

    -- 7. Return updated order with historical order items intact
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
    WHERE o.id = p_order_id;

    RETURN v_result;
END;
$$;


-- ============================================================================
-- Security Permissions: Restrict RPC Execution
-- ============================================================================
-- Revoke all permissions from public and anonymous callers
REVOKE ALL ON FUNCTION public.create_order_with_reservation_rpc(uuid, jsonb, text, text, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.create_order_with_reservation_rpc(uuid, jsonb, text, text, uuid) FROM anon;

REVOKE ALL ON FUNCTION public.fulfill_order_rpc(uuid, uuid, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.fulfill_order_rpc(uuid, uuid, text) FROM anon;

REVOKE ALL ON FUNCTION public.cancel_order_rpc(uuid, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.cancel_order_rpc(uuid, uuid) FROM anon;

-- Grant execution to authenticated sellers and service_role
GRANT EXECUTE ON FUNCTION public.create_order_with_reservation_rpc(uuid, jsonb, text, text, uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.create_order_with_reservation_rpc(uuid, jsonb, text, text, uuid) TO service_role;

GRANT EXECUTE ON FUNCTION public.fulfill_order_rpc(uuid, uuid, text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.fulfill_order_rpc(uuid, uuid, text) TO service_role;

GRANT EXECUTE ON FUNCTION public.cancel_order_rpc(uuid, uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.cancel_order_rpc(uuid, uuid) TO service_role;
