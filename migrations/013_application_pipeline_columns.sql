-- Migration 013: Add stage and tenant_id to applications for pipeline view and multi-tenant isolation
-- Fixes: applications table lacks stage column, lacks tenant_id (audit #177, #178)

-- Add tenant_id to applications (nullable for backward compat; backfill from tenant_members)
ALTER TABLE applications ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_applications_tenant_id ON applications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_tenant ON applications(user_id, tenant_id);

-- Add stage column for pipeline view (maps to status; pipeline uses stage IDs like draft, applying, submitted)
ALTER TABLE applications ADD COLUMN IF NOT EXISTS stage VARCHAR(50);

-- Backfill tenant_id from tenant_members for existing applications
UPDATE applications a
SET tenant_id = (
  SELECT tm.tenant_id
  FROM tenant_members tm
  WHERE tm.user_id = a.user_id
  ORDER BY tm.created_at ASC
  LIMIT 1
)
WHERE a.tenant_id IS NULL;
