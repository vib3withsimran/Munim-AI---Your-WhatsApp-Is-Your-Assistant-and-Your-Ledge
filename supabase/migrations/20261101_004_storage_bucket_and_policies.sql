-- ============================================================================
-- Migration: 20261101_004_storage_bucket_and_policies.sql
-- Description: Phase 3G - Supabase Storage Integration & Security Policies
--              1. Creates private 'munim-media' bucket with 10MB limit and MIME filters.
--              2. Establishes seller-scoped folder isolation RLS policies on storage.objects.
--              3. Adds performance indexes on public.media_files.
-- ============================================================================

BEGIN;

-- Step 1: Create private storage bucket 'munim-media'
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'munim-media',
    'munim-media',
    false,
    10485760, -- 10 MB limit
    ARRAY[
        'image/jpeg',
        'image/png',
        'image/webp',
        'application/pdf',
        'audio/mpeg',
        'audio/mp3',
        'audio/mp4',
        'audio/x-m4a',
        'audio/ogg',
        'audio/webm',
        'audio/wav',
        'audio/x-wav'
    ]
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Step 2: Storage RLS Policies on storage.objects for 'munim-media'
-- Enforces seller-scoped path structure: {seller_id}/category/uuid.ext

-- 2a. SELECT (Download / Read)
DROP POLICY IF EXISTS "Sellers can view own media objects" ON storage.objects;
CREATE POLICY "Sellers can view own media objects"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'munim-media'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- 2b. INSERT (Upload)
DROP POLICY IF EXISTS "Sellers can upload own media objects" ON storage.objects;
CREATE POLICY "Sellers can upload own media objects"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'munim-media'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- 2c. UPDATE (Modify)
DROP POLICY IF EXISTS "Sellers can update own media objects" ON storage.objects;
CREATE POLICY "Sellers can update own media objects"
    ON storage.objects FOR UPDATE
    TO authenticated
    USING (
        bucket_id = 'munim-media'
        AND (storage.foldername(name))[1] = auth.uid()::text
    )
    WITH CHECK (
        bucket_id = 'munim-media'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- 2d. DELETE (Remove)
DROP POLICY IF EXISTS "Sellers can delete own media objects" ON storage.objects;
CREATE POLICY "Sellers can delete own media objects"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'munim-media'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Step 3: Indexes on public.media_files for fast seller lookup
CREATE INDEX IF NOT EXISTS idx_media_files_seller_created
    ON public.media_files (seller_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_media_files_seller_purpose
    ON public.media_files (seller_id, purpose)
    WHERE purpose IS NOT NULL;

COMMIT;

