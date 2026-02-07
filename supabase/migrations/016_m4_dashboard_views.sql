-- Migration 016: M4 Enterprise Analytics Materialized Views
--
-- MRR cohort analysis, expansion revenue, churn prediction,
-- LTV:CAC ratio, net revenue retention.

-- ============================================================
-- 1. MRR cohort analysis (monthly cohorts by signup month)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_mrr_cohorts AS
WITH cohorts AS (
    SELECT
        date_trunc('month', t.created_at)::date AS cohort_month,
        t.id AS tenant_id,
        t.plan::text AS current_plan,
        t.seat_count,
        CASE
            WHEN t.plan = 'FREE' THEN 0
            WHEN t.plan = 'PRO' THEN 29
            WHEN t.plan = 'TEAM' THEN 199 + GREATEST(t.seat_count - 3, 0) * 49
            WHEN t.plan = 'ENTERPRISE' THEN COALESCE(
                (SELECT es.monthly_price / 100 FROM public.enterprise_settings es WHERE es.tenant_id = t.id),
                999
            )
            ELSE 0
        END AS mrr_dollars
    FROM public.tenants t
)
SELECT
    cohort_month,
    COUNT(*)::int AS tenants,
    COUNT(*) FILTER (WHERE current_plan != 'FREE')::int AS paying,
    SUM(mrr_dollars)::int AS cohort_mrr,
    ROUND(AVG(mrr_dollars), 2) AS avg_mrr_per_tenant
FROM cohorts
GROUP BY cohort_month
ORDER BY cohort_month;

-- ============================================================
-- 2. Expansion revenue tracking (plan upgrades over time)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_expansion_revenue AS
SELECT
    date_trunc('month', al.created_at)::date AS month,
    COUNT(*) FILTER (WHERE al.action = 'billing.changed' AND (al.details->>'new_plan') IN ('PRO','TEAM','ENTERPRISE'))::int AS upgrades,
    COUNT(*) FILTER (WHERE al.action = 'billing.changed' AND (al.details->>'new_plan') = 'FREE')::int AS downgrades,
    COUNT(*) FILTER (WHERE al.action = 'billing.seats.updated')::int AS seat_expansions
FROM public.audit_log al
WHERE al.action IN ('billing.changed', 'billing.seats.updated')
GROUP BY date_trunc('month', al.created_at)
ORDER BY month;

-- ============================================================
-- 3. Churn prediction signals
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_churn_prediction AS
SELECT
    t.id AS tenant_id,
    t.name,
    t.plan::text AS plan,
    t.seat_count,
    CASE
        WHEN t.plan = 'PRO' THEN 29
        WHEN t.plan = 'TEAM' THEN 199 + GREATEST(t.seat_count - 3, 0) * 49
        WHEN t.plan = 'ENTERPRISE' THEN 999
        ELSE 0
    END AS mrr_at_risk,
    COALESCE(
        EXTRACT(DAY FROM now() - last_app.last_activity)::int,
        999
    ) AS days_since_last_activity,
    COALESCE(last_app.apps_last_30d, 0) AS apps_last_30d,
    COALESCE(last_app.apps_last_7d, 0) AS apps_last_7d,
    CASE
        WHEN COALESCE(EXTRACT(DAY FROM now() - last_app.last_activity), 999) > 14 THEN 'high'
        WHEN COALESCE(EXTRACT(DAY FROM now() - last_app.last_activity), 999) > 7 THEN 'medium'
        ELSE 'low'
    END AS churn_risk_level
FROM public.tenants t
LEFT JOIN LATERAL (
    SELECT
        MAX(a.created_at) AS last_activity,
        COUNT(*) FILTER (WHERE a.created_at >= now() - interval '30 days')::int AS apps_last_30d,
        COUNT(*) FILTER (WHERE a.created_at >= now() - interval '7 days')::int AS apps_last_7d
    FROM public.applications a
    JOIN public.tenant_members tm ON tm.user_id = a.user_id AND tm.tenant_id = t.id
) last_app ON true
WHERE t.plan != 'FREE'
ORDER BY days_since_last_activity DESC;

-- ============================================================
-- 4. Net Revenue Retention (NRR) — monthly calculation
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_nrr_monthly AS
WITH monthly AS (
    SELECT
        date_trunc('month', bc.created_at)::date AS month,
        SUM(CASE
            WHEN t.plan = 'PRO' THEN 29
            WHEN t.plan = 'TEAM' THEN 199 + GREATEST(t.seat_count - 3, 0) * 49
            WHEN t.plan = 'ENTERPRISE' THEN 999
            ELSE 0
        END)::int AS ending_mrr
    FROM public.billing_customers bc
    JOIN public.tenants t ON t.id = bc.tenant_id
    WHERE bc.current_subscription_status IN ('active', 'trialing')
    GROUP BY date_trunc('month', bc.created_at)
)
SELECT
    month,
    ending_mrr,
    LAG(ending_mrr) OVER (ORDER BY month) AS starting_mrr,
    CASE
        WHEN LAG(ending_mrr) OVER (ORDER BY month) > 0
        THEN ROUND(ending_mrr::numeric / LAG(ending_mrr) OVER (ORDER BY month) * 100, 1)
        ELSE NULL
    END AS nrr_pct
FROM monthly
ORDER BY month;

-- ============================================================
-- 5. Enterprise pipeline
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_enterprise_pipeline AS
SELECT
    t.id AS tenant_id,
    t.name,
    t.plan::text AS plan,
    t.seat_count,
    es.sla_tier,
    es.contract_start,
    es.contract_end,
    COALESCE(es.monthly_price, 0) / 100 AS contract_mrr,
    CASE
        WHEN es.contract_end IS NOT NULL AND es.contract_end < now() + interval '30 days' THEN 'renewal_due'
        WHEN t.plan = 'TEAM' AND t.seat_count >= 5 THEN 'expansion_candidate'
        WHEN t.plan = 'TEAM' AND t.seat_count >= 3 THEN 'upsell_candidate'
        ELSE 'active'
    END AS pipeline_stage
FROM public.tenants t
LEFT JOIN public.enterprise_settings es ON es.tenant_id = t.id
WHERE t.plan IN ('TEAM', 'ENTERPRISE')
ORDER BY t.seat_count DESC;

-- ============================================================
-- 6. Refresh function
-- ============================================================

CREATE OR REPLACE FUNCTION public.refresh_m4_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW public.mv_mrr_cohorts;
    REFRESH MATERIALIZED VIEW public.mv_expansion_revenue;
    REFRESH MATERIALIZED VIEW public.mv_churn_prediction;
    REFRESH MATERIALIZED VIEW public.mv_nrr_monthly;
    REFRESH MATERIALIZED VIEW public.mv_enterprise_pipeline;
END;
$$ LANGUAGE plpgsql;
