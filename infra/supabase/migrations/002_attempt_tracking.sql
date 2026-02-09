-- Migration 002: Add retry tracking and error context to applications
--
-- Adds: attempt_count, last_error, last_processed_at

ALTER TABLE public.applications
    ADD COLUMN IF NOT EXISTS attempt_count     integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error        text,
    ADD COLUMN IF NOT EXISTS last_processed_at timestamptz;
