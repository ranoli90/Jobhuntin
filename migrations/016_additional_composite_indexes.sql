-- Migration: Additional Composite Indexes for Performance
-- Date: 2026-03-09
-- Purpose: Add missing composite indexes identified in audit

-- MEDIUM: Composite index for job search with filters
-- Improves performance of filtered job queries (location, remote, job_type)
CREATE INDEX IF NOT EXISTS idx_jobs_search_composite 
ON public.jobs (is_active, location, remote, job_type, created_at DESC)
WHERE is_active = true;

-- MEDIUM: Composite index for application status queries with tenant
-- Improves performance of application listing by status and tenant
CREATE INDEX IF NOT EXISTS idx_applications_status_tenant 
ON public.applications (tenant_id, status, created_at DESC)
WHERE status IN ('QUEUED', 'PROCESSING', 'APPLIED', 'HOLD');

-- Note: These indexes support common query patterns:
-- 1. Job search with multiple filters (location, remote, type)
-- 2. Application listing by tenant and status
-- Both are frequently used in the application and benefit from composite indexes
