-- Migration 009: M1 Dashboard Views
--
-- Materialized views for the M1 closed-beta monitoring dashboard.
-- Refresh periodically via pg_cron or manual REFRESH MATERIALIZED VIEW.

-- ============================================================
-- 1. Daily application stats (last 90 days)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_daily_app_stats AS
SELECT
    date_trunc('day', a.created_at)::date AS day,
    COUNT(*)::int AS total_created,
    COUNT(*) FILTER (WHERE a.status IN ('APPLIED', 'SUBMITTED', 'COMPLETED'))::int AS total_succeeded,
    COUNT(*) FILTER (WHERE a.status = 'FAILED')::int AS total_failed,
    COUNT(*) FILTER (WHERE a.status = 'REQUIRES_INPUT')::int AS total_on_hold,
    COUNT(DISTINCT a.user_id)::int AS unique_users
FROM public.applications a
WHERE a.created_at >= now() - interval '90 days'
GROUP BY day
ORDER BY day DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_app_stats_day
    ON public.mv_daily_app_stats (day);

-- ============================================================
-- 2. Agent success rate (rolling 7-day and 30-day)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_agent_success_rates AS
WITH recent AS (
    SELECT
        e.label,
        e.created_at,
        CASE WHEN e.created_at >= now() - interval '7 days' THEN true ELSE false END AS in_7d,
        CASE WHEN e.created_at >= now() - interval '30 days' THEN true ELSE false END AS in_30d
    FROM public.agent_evaluations e
    WHERE e.source = 'SYSTEM'
      AND e.created_at >= now() - interval '30 days'
)
SELECT
    COUNT(*) FILTER (WHERE in_7d)::int AS total_7d,
    COUNT(*) FILTER (WHERE in_7d AND label = 'SUCCESS')::int AS success_7d,
    COUNT(*) FILTER (WHERE in_7d AND label = 'PARTIAL')::int AS partial_7d,
    COUNT(*) FILTER (WHERE in_7d AND label = 'FAILURE')::int AS failure_7d,
    ROUND(
        COUNT(*) FILTER (WHERE in_7d AND label = 'SUCCESS')::numeric /
        NULLIF(COUNT(*) FILTER (WHERE in_7d), 0) * 100, 1
    ) AS success_rate_7d,
    COUNT(*) FILTER (WHERE in_30d)::int AS total_30d,
    COUNT(*) FILTER (WHERE in_30d AND label = 'SUCCESS')::int AS success_30d,
    COUNT(*) FILTER (WHERE in_30d AND label = 'PARTIAL')::int AS partial_30d,
    COUNT(*) FILTER (WHERE in_30d AND label = 'FAILURE')::int AS failure_30d,
    ROUND(
        COUNT(*) FILTER (WHERE in_30d AND label = 'SUCCESS')::numeric /
        NULLIF(COUNT(*) FILTER (WHERE in_30d), 0) * 100, 1
    ) AS success_rate_30d
FROM recent;

-- ============================================================
-- 3. MAU / WAU counters
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_active_users AS
SELECT
    COUNT(DISTINCT user_id) FILTER (
        WHERE created_at >= now() - interval '30 days'
    )::int AS mau,
    COUNT(DISTINCT user_id) FILTER (
        WHERE created_at >= now() - interval '7 days'
    )::int AS wau,
    COUNT(DISTINCT user_id) FILTER (
        WHERE created_at >= now() - interval '1 day'
    )::int AS dau
FROM public.analytics_events;

-- ============================================================
-- 4. Plan distribution
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_plan_distribution AS
SELECT
    plan::text AS plan,
    COUNT(*)::int AS tenant_count,
    (SELECT COUNT(DISTINCT tm.user_id)
     FROM public.tenant_members tm
     JOIN public.tenants t2 ON t2.id = tm.tenant_id
     WHERE t2.plan::text = t.plan::text
    )::int AS user_count
FROM public.tenants t
GROUP BY plan;

-- ============================================================
-- 5. Refresh function (call from pg_cron or manually)
-- ============================================================

CREATE OR REPLACE FUNCTION public.refresh_m1_dashboard()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_daily_app_stats;
    REFRESH MATERIALIZED VIEW public.mv_agent_success_rates;
    REFRESH MATERIALIZED VIEW public.mv_active_users;
    REFRESH MATERIALIZED VIEW public.mv_plan_distribution;
END;
$$ LANGUAGE plpgsql;
