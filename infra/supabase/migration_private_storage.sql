-- Migration: Make resume storage bucket private and add RLS policies
-- This ensures resumes are only accessible via authenticated/signed URLs.
--
-- Run this migration against your Supabase project to:
-- 1. Set the resumes bucket to private (non-public)
-- 2. Add RLS policies so only the file owner (or service role) can access files
-- 3. Add a policy for authenticated signed URL access

-- ============================================================
-- 1. Set bucket to private (disable public access)
-- ============================================================
UPDATE storage.buckets
SET public = false
WHERE id = 'resumes';

-- ============================================================
-- 2. Enable RLS on storage.objects (if not already enabled)
-- ============================================================
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 3. Policy: Users can only read their own resume files
--    Resume path format: {user_id}/{uuid}.pdf
-- ============================================================
DROP POLICY IF EXISTS "Users can read own resumes" ON storage.objects;
CREATE POLICY "Users can read own resumes"
ON storage.objects
FOR SELECT
TO authenticated
USING (
    bucket_id = 'resumes'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- ============================================================
-- 4. Policy: Users can upload to their own folder
-- ============================================================
DROP POLICY IF EXISTS "Users can upload own resumes" ON storage.objects;
CREATE POLICY "Users can upload own resumes"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'resumes'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- ============================================================
-- 5. Policy: Users can update (overwrite) their own files
-- ============================================================
DROP POLICY IF EXISTS "Users can update own resumes" ON storage.objects;
CREATE POLICY "Users can update own resumes"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
    bucket_id = 'resumes'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- ============================================================
-- 6. Policy: Service role has full access (for server-side operations)
--    The service_role key bypasses RLS by default in Supabase,
--    but this explicit policy documents intent.
-- ============================================================
DROP POLICY IF EXISTS "Service role full access to resumes" ON storage.objects;
CREATE POLICY "Service role full access to resumes"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'resumes')
WITH CHECK (bucket_id = 'resumes');

-- ============================================================
-- 7. Also secure the avatars bucket
-- ============================================================
UPDATE storage.buckets
SET public = false
WHERE id = 'avatars';

DROP POLICY IF EXISTS "Users can read own avatars" ON storage.objects;
CREATE POLICY "Users can read own avatars"
ON storage.objects
FOR SELECT
TO authenticated
USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

DROP POLICY IF EXISTS "Users can upload own avatars" ON storage.objects;
CREATE POLICY "Users can upload own avatars"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

DROP POLICY IF EXISTS "Service role full access to avatars" ON storage.objects;
CREATE POLICY "Service role full access to avatars"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'avatars')
WITH CHECK (bucket_id = 'avatars');
