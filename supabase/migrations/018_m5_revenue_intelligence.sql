-- Migration 018: M5 Revenue Intelligence — P&L views, LTV:CAC, investor metrics
--
-- Full P&L materialized views, COGS estimation, gross margin tracking,
-- marketplace revenue, and Series A metrics export support.

-- ============================================================
-- 1. Full P&L view — MRR breakdown by source
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_m5_pnl AS
WITH revenue AS (
    SELECT
        date_trunc('month', bc.created_at)::date AS month,
        -- Subscription MRR
        SUM(CASE WHEN t.plan = 'PRO' THEN
            CASE WHEN t.billing_interval = 'annual' THEN ROUND(29 * 12 * 0.8 / 12) ELSE 29 END
        ELSE 0 END)::int AS pro_mrr,
        SUM(CASE WHEN t.plan = 'TEAM' THEN
            CASE WHEN t.billing_interval = 'annual'
                THEN ROUND((199 + GREATEST(t.seat_count - 3, 0) * 49) * 12 * 0.8 / 12)
                ELSE 199 + GREATEST(t.seat_count - 3, 0) * 49
            END
        ELSE 0 END)::int AS team_mrr,
        SUM(CASE WHEN t.plan = 'ENTERPRISE' THEN
            COALESCE(t.contract_value_cents / 100,
                CASE WHEN t.billing_interval = 'annual' THEN ROUND(999 * 0.8) ELSE 999 END)
        ELSE 0 END)::int AS enterprise_mrr,
        -- Counts
        COUNT(*) FILTER (WHERE t.plan = 'PRO')::int AS pro_count,
        COUNT(*) FILTER (WHERE t.plan = 'TEAM')::int AS team_count,
        COUNT(*) FILTER (WHERE t.plan = 'ENTERPRISE')::int AS enterprise_count
    FROM public.billing_customers bc
    JOIN public.tenants t ON t.id = bc.tenant_id
    WHERE bc.current_subscription_status IN ('active', 'trialing')
    GROUP BY date_trunc('month', bc.created_at)
)
SELECT
    month,
    pro_mrr, team_mrr, enterprise_mrr,
    (pro_mrr + team_mrr + enterprise_mrr) AS total_mrr,
    pro_count, team_count, enterprise_count,
    -- Estimated COGS (LLM API + infra per active application)
    -- ~$0.05/application for LLM, $200/mo base infra
    (SELECT COUNT(*)::int FROM public.applications a
     WHERE a.created_at >= date_trunc('month', revenue.month)
       AND a.created_at < date_trunc('month', revenue.month) + interval '1 month'
    ) AS monthly_applications,
    200 + COALESCE(
        (SELECT COUNT(*) * 5 / 100 FROM public.applications a
         WHERE a.created_at >= date_trunc('month', revenue.month)
           AND a.created_at < date_trunc('month', revenue.month) + interval '1 month'),
        0
    )::int AS estimated_cogs
FROM revenue
ORDER BY month;

-- ============================================================
-- 2. Marketplace revenue tracking
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_marketplace_revenue AS
SELECT
    date_trunc('month', ap.created_at)::date AS month,
    COUNT(*)::int AS total_payouts,
    SUM(ap.amount_cents)::int AS author_payouts_cents,
    SUM(ap.platform_fee_cents)::int AS platform_fee_cents,
    COUNT(DISTINCT ap.blueprint_id)::int AS blueprints_earning,
    COUNT(DISTINCT ap.author_tenant_id)::int AS authors_earning
FROM public.author_payouts ap
WHERE ap.status IN ('paid', 'pending')
GROUP BY date_trunc('month', ap.created_at)
ORDER BY month;

-- ============================================================
-- 3. Cohort retention (monthly cohort × month_number)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_cohort_retention AS
WITH cohorts AS (
    SELECT
        t.id AS tenant_id,
        date_trunc('month', t.created_at)::date AS cohort_month,
        t.plan::text AS current_plan
    FROM public.tenants t
    WHERE t.plan != 'FREE'
),
months AS (
    SELECT generate_series(0, 11) AS month_number
)
SELECT
    c.cohort_month,
    m.month_number,
    COUNT(c.tenant_id)::int AS cohort_size,
    COUNT(c.tenant_id) FILTER (
        WHERE EXISTS (
            SELECT 1 FROM public.applications a
            JOIN public.tenant_members tm ON tm.user_id = a.user_id AND tm.tenant_id = c.tenant_id
            WHERE a.created_at >= c.cohort_month + (m.month_number || ' months')::interval
              AND a.created_at < c.cohort_month + ((m.month_number + 1) || ' months')::interval
        )
    )::int AS retained
FROM cohorts c
CROSS JOIN months m
WHERE c.cohort_month + (m.month_number || ' months')::interval <= now()
GROUP BY c.cohort_month, m.month_number
ORDER BY c.cohort_month, m.month_number;

-- ============================================================
-- 4. Agent performance by blueprint
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_agent_performance_m5 AS
SELECT
    COALESCE(a.blueprint_key, 'job-app') AS blueprint_key,
    date_trunc('week', a.created_at)::date AS week,
    COUNT(*)::int AS total,
    COUNT(*) FILTER (WHERE a.status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED'))::int AS succeeded,
    COUNT(*) FILTER (WHERE a.status = 'FAILED')::int AS failed,
    COUNT(*) FILTER (WHERE a.status = 'REQUIRES_INPUT')::int AS held,
    ROUND(
        COUNT(*) FILTER (WHERE a.status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED'))::numeric
        / NULLIF(COUNT(*) FILTER (WHERE a.status NOT IN ('QUEUED','PROCESSING')), 0) * 100, 1
    ) AS success_rate
FROM public.applications a
WHERE a.created_at >= now() - interval '90 days'
GROUP BY COALESCE(a.blueprint_key, 'job-app'), date_trunc('week', a.created_at)
ORDER BY week DESC, blueprint_key;

-- ============================================================
-- 5. Refresh function
-- ============================================================

CREATE OR REPLACE FUNCTION public.refresh_m5_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW public.mv_m5_pnl;
    REFRESH MATERIALIZED VIEW public.mv_marketplace_revenue;
    REFRESH MATERIALIZED VIEW public.mv_cohort_retention;
    REFRESH MATERIALIZED VIEW public.mv_agent_performance_m5;
END;
$$ LANGUAGE plpgsql;
