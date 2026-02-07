-- Migration 014: M3 Dashboard Materialized Views
--
-- Team vs individual metrics, blueprint performance, churn risk, MRR by plan.

-- ============================================================
-- 1. Team metrics
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_team_metrics AS
SELECT
    COUNT(*)::int AS total_teams,
    SUM(seat_count)::int AS total_team_seats,
    COUNT(*) FILTER (WHERE seat_count >= 3)::int AS teams_with_3_plus,
    AVG(seat_count)::numeric(5,1) AS avg_seats_per_team,
    SUM(CASE WHEN plan = 'TEAM' THEN 199 + GREATEST(seat_count - 3, 0) * 49 ELSE 0 END)::int AS team_mrr
FROM public.tenants
WHERE plan IN ('TEAM', 'ENTERPRISE');

-- ============================================================
-- 2. Blueprint performance (last 30 days)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_blueprint_performance AS
SELECT
    COALESCE(a.blueprint_key, 'job-app') AS blueprint_key,
    COUNT(*)::int AS total,
    COUNT(*) FILTER (WHERE a.status IN ('APPLIED','SUBMITTED','COMPLETED'))::int AS succeeded,
    COUNT(*) FILTER (WHERE a.status = 'FAILED')::int AS failed,
    COUNT(*) FILTER (WHERE a.status = 'REQUIRES_INPUT')::int AS on_hold,
    ROUND(
        COUNT(*) FILTER (WHERE a.status IN ('APPLIED','SUBMITTED','COMPLETED'))::numeric /
        NULLIF(COUNT(*), 0) * 100, 1
    ) AS success_rate
FROM public.applications a
WHERE a.created_at >= now() - interval '30 days'
GROUP BY COALESCE(a.blueprint_key, 'job-app');

-- ============================================================
-- 3. MRR by plan
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_mrr_by_plan AS
SELECT
    plan::text AS plan,
    COUNT(*)::int AS tenant_count,
    CASE
        WHEN plan = 'FREE' THEN 0
        WHEN plan = 'PRO' THEN COUNT(*) * 29
        WHEN plan = 'TEAM' THEN SUM(199 + GREATEST(seat_count - 3, 0) * 49)
        WHEN plan = 'ENTERPRISE' THEN COUNT(*) * 999
        ELSE 0
    END::int AS plan_mrr
FROM public.tenants
GROUP BY plan;

-- ============================================================
-- 4. Churn risk (teams inactive > 7 days)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_churn_risk AS
SELECT
    t.id AS tenant_id,
    t.name,
    t.plan::text AS plan,
    t.seat_count,
    EXTRACT(DAY FROM now() - MAX(a.created_at))::int AS days_inactive
FROM public.tenants t
LEFT JOIN public.tenant_members tm ON tm.tenant_id = t.id
LEFT JOIN public.applications a ON a.user_id = tm.user_id
WHERE t.plan IN ('PRO', 'TEAM', 'ENTERPRISE')
GROUP BY t.id, t.name, t.plan, t.seat_count
HAVING MAX(a.created_at) IS NULL OR MAX(a.created_at) < now() - interval '7 days'
ORDER BY days_inactive DESC NULLS FIRST;

-- ============================================================
-- 5. Team vs individual usage comparison
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_team_vs_individual AS
WITH team_stats AS (
    SELECT
        'team' AS segment,
        COUNT(DISTINCT a.user_id)::int AS active_users,
        COUNT(*)::int AS total_apps,
        ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT a.user_id), 0), 1) AS apps_per_user
    FROM public.applications a
    JOIN public.tenant_members tm ON tm.user_id = a.user_id
    JOIN public.tenants t ON t.id = tm.tenant_id
    WHERE t.plan IN ('TEAM', 'ENTERPRISE')
      AND a.created_at >= now() - interval '30 days'
),
individual_stats AS (
    SELECT
        'individual' AS segment,
        COUNT(DISTINCT a.user_id)::int AS active_users,
        COUNT(*)::int AS total_apps,
        ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT a.user_id), 0), 1) AS apps_per_user
    FROM public.applications a
    JOIN public.tenant_members tm ON tm.user_id = a.user_id
    JOIN public.tenants t ON t.id = tm.tenant_id
    WHERE t.plan IN ('FREE', 'PRO')
      AND a.created_at >= now() - interval '30 days'
)
SELECT * FROM team_stats
UNION ALL
SELECT * FROM individual_stats;

-- ============================================================
-- 6. Refresh function
-- ============================================================

CREATE OR REPLACE FUNCTION public.refresh_m3_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW public.mv_team_metrics;
    REFRESH MATERIALIZED VIEW public.mv_blueprint_performance;
    REFRESH MATERIALIZED VIEW public.mv_mrr_by_plan;
    REFRESH MATERIALIZED VIEW public.mv_churn_risk;
    REFRESH MATERIALIZED VIEW public.mv_team_vs_individual;
END;
$$ LANGUAGE plpgsql;
