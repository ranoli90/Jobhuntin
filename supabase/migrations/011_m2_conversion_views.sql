-- Migration 011: M2 Conversion Funnel + Cohort Views
--
-- Materialized views for tracking signup→activation→conversion funnel,
-- weekly cohort retention, and referral performance.

-- ============================================================
-- 1. Signup → Activation → Conversion funnel (rolling 30d)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_conversion_funnel AS
WITH
signups AS (
    SELECT id AS user_id, created_at
    FROM auth.users
    WHERE created_at >= now() - interval '30 days'
),
onboarded AS (
    SELECT id AS user_id
    FROM auth.users
    WHERE onboarding_completed_at IS NOT NULL
      AND created_at >= now() - interval '30 days'
),
has_resume AS (
    SELECT DISTINCT user_id
    FROM public.profiles
    WHERE created_at >= now() - interval '30 days'
),
first_app AS (
    SELECT DISTINCT user_id
    FROM public.applications
    WHERE created_at >= now() - interval '30 days'
),
pro_users AS (
    SELECT DISTINCT tm.user_id
    FROM public.tenant_members tm
    JOIN public.tenants t ON t.id = tm.tenant_id
    WHERE t.plan = 'PRO'
      AND tm.user_id IN (SELECT user_id FROM signups)
)
SELECT
    (SELECT COUNT(*) FROM signups)::int AS total_signups,
    (SELECT COUNT(*) FROM onboarded)::int AS onboarded,
    (SELECT COUNT(*) FROM has_resume)::int AS uploaded_resume,
    (SELECT COUNT(*) FROM first_app)::int AS first_application,
    (SELECT COUNT(*) FROM pro_users)::int AS converted_pro,
    ROUND(
        (SELECT COUNT(*) FROM onboarded)::numeric /
        NULLIF((SELECT COUNT(*) FROM signups), 0) * 100, 1
    ) AS onboarding_rate,
    ROUND(
        (SELECT COUNT(*) FROM first_app)::numeric /
        NULLIF((SELECT COUNT(*) FROM signups), 0) * 100, 1
    ) AS activation_rate,
    ROUND(
        (SELECT COUNT(*) FROM pro_users)::numeric /
        NULLIF((SELECT COUNT(*) FROM signups), 0) * 100, 1
    ) AS conversion_rate;

-- ============================================================
-- 2. Weekly cohort retention
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_weekly_cohorts AS
WITH cohorts AS (
    SELECT
        id AS user_id,
        date_trunc('week', created_at)::date AS cohort_week
    FROM auth.users
    WHERE created_at >= now() - interval '12 weeks'
),
activity AS (
    SELECT
        user_id,
        date_trunc('week', created_at)::date AS active_week
    FROM public.analytics_events
    WHERE created_at >= now() - interval '12 weeks'
    GROUP BY user_id, date_trunc('week', created_at)::date
)
SELECT
    c.cohort_week,
    COUNT(DISTINCT c.user_id)::int AS cohort_size,
    COUNT(DISTINCT CASE WHEN a.active_week = c.cohort_week THEN c.user_id END)::int AS week_0,
    COUNT(DISTINCT CASE WHEN a.active_week = c.cohort_week + interval '1 week' THEN c.user_id END)::int AS week_1,
    COUNT(DISTINCT CASE WHEN a.active_week = c.cohort_week + interval '2 weeks' THEN c.user_id END)::int AS week_2,
    COUNT(DISTINCT CASE WHEN a.active_week = c.cohort_week + interval '3 weeks' THEN c.user_id END)::int AS week_3,
    COUNT(DISTINCT CASE WHEN a.active_week = c.cohort_week + interval '4 weeks' THEN c.user_id END)::int AS week_4
FROM cohorts c
LEFT JOIN activity a ON a.user_id = c.user_id
GROUP BY c.cohort_week
ORDER BY c.cohort_week DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_weekly_cohorts_week
    ON public.mv_weekly_cohorts (cohort_week);

-- ============================================================
-- 3. Referral performance
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_referral_stats AS
SELECT
    COUNT(*)::int AS total_referrals,
    COUNT(*) FILTER (WHERE status = 'rewarded')::int AS successful,
    COUNT(*) FILTER (WHERE status = 'pending')::int AS pending,
    SUM(reward_amount) FILTER (WHERE status = 'rewarded')::int AS total_bonus_apps_granted,
    COUNT(DISTINCT referrer_id) FILTER (WHERE status = 'rewarded')::int AS unique_referrers
FROM public.referrals;

-- ============================================================
-- 4. UTM source attribution
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_signup_sources AS
SELECT
    COALESCE(ae.properties->>'utm_source', 'direct') AS source,
    COALESCE(ae.properties->>'utm_medium', 'none') AS medium,
    COALESCE(ae.properties->>'utm_campaign', 'none') AS campaign,
    COUNT(DISTINCT ae.user_id)::int AS signups,
    COUNT(DISTINCT a.user_id)::int AS activated,
    COUNT(DISTINCT CASE WHEN t.plan = 'PRO' THEN tm.user_id END)::int AS converted
FROM public.analytics_events ae
LEFT JOIN public.applications a ON a.user_id = ae.user_id
LEFT JOIN public.tenant_members tm ON tm.user_id = ae.user_id
LEFT JOIN public.tenants t ON t.id = tm.tenant_id
WHERE ae.event_type = 'onboarding_completed'
  AND ae.created_at >= now() - interval '30 days'
GROUP BY source, medium, campaign
ORDER BY signups DESC;

-- ============================================================
-- 5. Refresh function
-- ============================================================

CREATE OR REPLACE FUNCTION public.refresh_m2_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW public.mv_conversion_funnel;
    REFRESH MATERIALIZED VIEW public.mv_weekly_cohorts;
    REFRESH MATERIALIZED VIEW public.mv_referral_stats;
    REFRESH MATERIALIZED VIEW public.mv_signup_sources;
END;
$$ LANGUAGE plpgsql;
