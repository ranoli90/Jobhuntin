-- Migration 010: M2 Growth Features
--
-- Tables for push notifications, referral program, and email digest tracking.

-- ============================================================
-- 1. Push notification tokens
-- ============================================================

CREATE TABLE IF NOT EXISTS public.push_tokens (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    tenant_id   uuid REFERENCES public.tenants (id) ON DELETE SET NULL,
    token       text NOT NULL,
    platform    text NOT NULL DEFAULT 'expo',  -- expo, apns, fcm
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_push_tokens_user_token
    ON public.push_tokens (user_id, token);
CREATE INDEX IF NOT EXISTS idx_push_tokens_active
    ON public.push_tokens (is_active) WHERE is_active = true;

ALTER TABLE public.push_tokens ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own push tokens" ON public.push_tokens;
CREATE POLICY "Users manage own push tokens"
    ON public.push_tokens FOR ALL
    USING (user_id = auth.uid());

-- ============================================================
-- 2. Notification log (sent push / email history)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.notification_log (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    tenant_id       uuid REFERENCES public.tenants (id) ON DELETE SET NULL,
    channel         text NOT NULL,  -- push, email, in_app
    notification_type text NOT NULL,  -- application_submitted, hold_questions, weekly_digest, referral_reward
    title           text,
    body            text,
    metadata        jsonb NOT NULL DEFAULT '{}'::jsonb,
    sent_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notification_log_user
    ON public.notification_log (user_id, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_log_type
    ON public.notification_log (notification_type, sent_at DESC);

ALTER TABLE public.notification_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users read own notifications" ON public.notification_log;
CREATE POLICY "Users read own notifications"
    ON public.notification_log FOR SELECT
    USING (user_id = auth.uid());

-- ============================================================
-- 3. Referral program
-- ============================================================

CREATE TABLE IF NOT EXISTS public.referrals (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id     uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    referee_id      uuid REFERENCES auth.users (id) ON DELETE SET NULL,
    referral_code   text NOT NULL UNIQUE,
    status          text NOT NULL DEFAULT 'pending',  -- pending, signed_up, rewarded
    reward_type     text NOT NULL DEFAULT 'bonus_apps',  -- bonus_apps, credit
    reward_amount   int NOT NULL DEFAULT 5,  -- e.g., 5 bonus applications
    created_at      timestamptz NOT NULL DEFAULT now(),
    redeemed_at     timestamptz
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer
    ON public.referrals (referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_code
    ON public.referrals (referral_code);
CREATE INDEX IF NOT EXISTS idx_referrals_referee
    ON public.referrals (referee_id) WHERE referee_id IS NOT NULL;

ALTER TABLE public.referrals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users read own referrals" ON public.referrals;
CREATE POLICY "Users read own referrals"
    ON public.referrals FOR SELECT
    USING (referrer_id = auth.uid() OR referee_id = auth.uid());

-- ============================================================
-- 4. Bonus application credits (from referrals, promos)
-- ============================================================

ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS bonus_app_credits int NOT NULL DEFAULT 0;

-- ============================================================
-- 5. Email digest tracking
-- ============================================================

CREATE TABLE IF NOT EXISTS public.email_digest_log (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    tenant_id   uuid REFERENCES public.tenants (id) ON DELETE SET NULL,
    period_start timestamptz NOT NULL,
    period_end  timestamptz NOT NULL,
    stats       jsonb NOT NULL DEFAULT '{}'::jsonb,  -- apps_submitted, apps_completed, etc.
    sent_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_email_digest_user
    ON public.email_digest_log (user_id, sent_at DESC);

-- ============================================================
-- 6. Onboarding state tracking
-- ============================================================

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS onboarding_completed_at timestamptz,
    ADD COLUMN IF NOT EXISTS referral_code text;

CREATE INDEX IF NOT EXISTS idx_users_referral_code
    ON public.users (referral_code) WHERE referral_code IS NOT NULL;
