-- Migration: Additional Composite Indexes for Performance
-- Date: 2026-03-09
-- Purpose: Add missing composite indexes identified in audit

-- MEDIUM: Composite index for job search with filters
-- Improves performance of filtered job queries (location, is_remote, job_type)
CREATE INDEX IF NOT EXISTS idx_jobs_search_composite 
ON public.jobs (location, is_remote, job_type, created_at DESC)
WHERE is_remote = true;

-- MEDIUM: Composite index for application status queries with tenant
-- Improves performance of application listing by status and tenant
CREATE INDEX IF NOT EXISTS idx_applications_status_tenant 
ON public.applications (tenant_id, status, created_at DESC)
WHERE status IN ('QUEUED', 'PROCESSING', 'APPLIED', 'HOLD');

-- HIGH: Cursor-friendly application listing for profile/dashboard/export flows.
-- Matches ORDER BY updated_at DESC, id DESC while keeping user_id selective.
CREATE INDEX IF NOT EXISTS idx_applications_user_updated_at_id
ON public.applications (user_id, updated_at DESC, id DESC);

-- HIGH: Fast unresolved hold-question lookup for application list/detail queries.
CREATE INDEX IF NOT EXISTS idx_application_inputs_application_unresolved_created_at
ON public.application_inputs (application_id, created_at)
WHERE resolved = false;

-- HIGH: Supports tenant dashboard joins from tenants -> profiles -> applications.
CREATE INDEX IF NOT EXISTS idx_profiles_tenant_user_id
ON public.profiles (tenant_id, user_id)
WHERE tenant_id IS NOT NULL;

-- MEDIUM: Matches saved-jobs tenant listings and counts ordered by newest first.
CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_tenant_created_at
ON public.saved_jobs (user_id, tenant_id, created_at DESC);

-- Note: These indexes support common query patterns:
-- 1. Job search with multiple filters (location, remote, type)
-- 2. Application listing by tenant and status
-- 3. User application/profile dashboard flows and unresolved hold-question lookups
-- 4. Saved-jobs list/count queries in tenant-aware flows
