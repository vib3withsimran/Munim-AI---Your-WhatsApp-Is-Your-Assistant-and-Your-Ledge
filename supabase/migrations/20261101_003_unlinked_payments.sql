-- ============================================================================
-- Migration: 20261101_003_unlinked_payments.sql
-- Description: Phase 3F - Unlinked Payment Support
--              1. Alter column order_id on public.payments to DROP NOT NULL.
--              2. Preserves the composite foreign key payments_order_id_seller_id_fkey.
--              3. Adds partial indexes for efficient querying of unlinked payments
--                 and lookup of transaction references.
--              4. Safe to execute against existing database records without data loss.
-- ============================================================================

BEGIN;

-- Step 1: Make order_id nullable on payments table
ALTER TABLE public.payments
    ALTER COLUMN order_id DROP NOT NULL;

-- Step 2: Create index on seller_id for unlinked payments
CREATE INDEX IF NOT EXISTS idx_payments_seller_unlinked
    ON public.payments (seller_id, created_at DESC)
    WHERE order_id IS NULL;

-- Step 3: Create index on transaction_reference for fast lookup and matching
CREATE INDEX IF NOT EXISTS idx_payments_seller_txn_ref
    ON public.payments (seller_id, transaction_reference)
    WHERE transaction_reference IS NOT NULL;

COMMIT;

