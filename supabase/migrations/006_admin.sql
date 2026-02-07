-- Migration 006: Admin support
--
-- Adds is_system_admin flag to users for internal admin access.
-- SUPPORT_AGENT role already exists in tenant_member_role enum (from 004).

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS is_system_admin boolean NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_users_system_admin ON public.users (is_system_admin) WHERE is_system_admin = true;
