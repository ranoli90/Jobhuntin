-- Migration 003: Add resolved flag and rich metadata to application_inputs
--
-- resolved: tracks whether the user has answered this hold question.
-- meta: stores field_type, label, options, step_index from the DOM extraction.

ALTER TABLE public.application_inputs
    ADD COLUMN IF NOT EXISTS resolved boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS meta     jsonb   DEFAULT '{}'::jsonb;
