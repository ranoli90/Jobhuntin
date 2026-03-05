-- Migration 002: Onboarding support tables
-- These tables are referenced by API endpoints in main.py but were missing
-- from the initial schema.

-- Work style profiles (POST /me/work-style)
CREATE TABLE IF NOT EXISTS public.work_style_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    autonomy_preference   TEXT NOT NULL DEFAULT 'medium',
    learning_style        TEXT NOT NULL DEFAULT 'building',
    company_stage_preference TEXT NOT NULL DEFAULT 'flexible',
    communication_style   TEXT NOT NULL DEFAULT 'mixed',
    pace_preference       TEXT NOT NULL DEFAULT 'steady',
    ownership_preference  TEXT NOT NULL DEFAULT 'team',
    career_trajectory     TEXT NOT NULL DEFAULT 'open',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_work_style_user UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS idx_work_style_user ON public.work_style_profiles(user_id);

-- User skills (POST /me/skills)
CREATE TABLE IF NOT EXISTS public.user_skills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    skill           TEXT NOT NULL,
    confidence      REAL NOT NULL DEFAULT 0.5,
    years_actual    REAL,
    context         TEXT DEFAULT '',
    last_used       TEXT,
    verified        BOOLEAN NOT NULL DEFAULT false,
    related_to      TEXT[] DEFAULT '{}',
    source          TEXT NOT NULL DEFAULT 'resume',
    project_count   INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_skill UNIQUE (user_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_user_skills_user ON public.user_skills(user_id);

-- Answer memory for smart pre-fill (POST /me/answer-memory)
CREATE TABLE IF NOT EXISTS public.answer_memory (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    field_label   TEXT NOT NULL,
    field_type    TEXT NOT NULL DEFAULT 'text',
    answer_value  TEXT NOT NULL,
    use_count     INTEGER NOT NULL DEFAULT 1,
    last_used_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_answer_memory UNIQUE (user_id, field_label)
);

CREATE INDEX IF NOT EXISTS idx_answer_memory_user ON public.answer_memory(user_id);
