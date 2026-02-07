-- Migration 020: M6 Platform Telemetry — ARR breakdown, API usage, vertical stats
--
-- Materialized views for platform dashboard, investor data room,
-- and vertical-level revenue attribution.

-- ============================================================
-- 1. ARR breakdown by vertical / blueprint
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_arr_by_vertical AS
WITH verticals AS (
    SELECT
        t.id AS tenant_id,
        t.plan::text,
        COALESCE(t.blueprint_key, 'job-app') AS vertical,
        t.billing_interval,
        CASE
            WHEN t.plan = 'PRO' THEN
                CASE WHEN t.billing_interval = 'annual' THEN ROUND(29 * 12 * 0.8 / 12) ELSE 29 END
            WHEN t.plan = 'TEAM' THEN
                CASE WHEN t.billing_interval = 'annual'
                    THEN ROUND((199 + GREATEST(t.seat_count - 3, 0) * 49) * 12 * 0.8 / 12)
                    ELSE 199 + GREATEST(t.seat_count - 3, 0) * 49
                END
            WHEN t.plan = 'ENTERPRISE' THEN
                COALESCE(t.contract_value_cents / 100,
                    CASE WHEN t.billing_interval = 'annual' THEN ROUND(999 * 0.8) ELSE 999 END)
            ELSE 0
        END::int AS mrr
    FROM public.tenants t
    WHERE t.plan != 'FREE'
)
SELECT
    vertical,
    COUNT(*)::int AS tenant_count,
    SUM(mrr)::int AS total_mrr,
    SUM(mrr * 12)::int AS total_arr,
    COUNT(*) FILTER (WHERE plan = 'ENTERPRISE')::int AS enterprise_count,
    COUNT(*) FILTER (WHERE billing_interval = 'annual')::int AS annual_count
FROM verticals
GROUP BY vertical
ORDER BY total_mrr DESC;

-- ============================================================
-- 2. API v2 usage analytics
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_api_v2_usage AS
SELECT
    DATE(au.created_at) AS day,
    au.endpoint,
    au.method,
    COUNT(*)::int AS calls,
    COUNT(DISTINCT au.api_key_id)::int AS unique_keys,
    COUNT(DISTINCT au.tenant_id)::int AS unique_tenants,
    AVG(au.latency_ms)::int AS avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY au.latency_ms)::int AS p95_latency_ms,
    COUNT(*) FILTER (WHERE au.status_code >= 400)::int AS error_count
FROM public.api_usage au
WHERE au.created_at >= now() - interval '90 days'
GROUP BY DATE(au.created_at), au.endpoint, au.method
ORDER BY day DESC, calls DESC;

-- ============================================================
-- 3. Blueprint install heatmap (by category + week)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_blueprint_heatmap AS
SELECT
    mb.category,
    mb.slug,
    mb.name,
    date_trunc('week', bi.installed_at)::date AS week,
    COUNT(*)::int AS installs,
    COUNT(DISTINCT bi.tenant_id)::int AS unique_tenants
FROM public.blueprint_installations bi
JOIN public.marketplace_blueprints mb ON mb.id = bi.blueprint_id
WHERE bi.installed_at >= now() - interval '90 days'
GROUP BY mb.category, mb.slug, mb.name, date_trunc('week', bi.installed_at)
ORDER BY week DESC, installs DESC;

-- ============================================================
-- 4. Revenue per blueprint (marketplace)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_revenue_per_blueprint AS
SELECT
    mb.id AS blueprint_id,
    mb.slug,
    mb.name,
    mb.category,
    mb.author_tenant_id,
    mb.price_cents,
    mb.install_count,
    (mb.price_cents * mb.install_count)::int AS gross_revenue_cents,
    ROUND(mb.price_cents * mb.install_count * (100 - COALESCE(mb.revenue_share_pct, 70)) / 100)::int AS platform_revenue_cents,
    ROUND(mb.price_cents * mb.install_count * COALESCE(mb.revenue_share_pct, 70) / 100)::int AS author_revenue_cents,
    mb.rating_avg,
    mb.rating_count
FROM public.marketplace_blueprints mb
WHERE mb.approval_status = 'approved' AND mb.price_cents > 0
ORDER BY gross_revenue_cents DESC;

-- ============================================================
-- 5. Staffing agency performance
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_staffing_performance AS
SELECT
    date_trunc('week', sb.created_at)::date AS week,
    COUNT(*)::int AS total_batches,
    SUM(sb.candidate_count)::int AS total_candidates,
    SUM(sb.succeeded)::int AS total_succeeded,
    SUM(sb.failed)::int AS total_failed,
    ROUND(SUM(sb.succeeded)::numeric / NULLIF(SUM(sb.candidate_count), 0) * 100, 1) AS success_rate,
    SUM(sb.succeeded * sb.price_per_submission_cents)::int AS revenue_cents,
    COUNT(DISTINCT sb.tenant_id)::int AS unique_agencies
FROM public.staffing_batches sb
WHERE sb.created_at >= now() - interval '90 days'
GROUP BY date_trunc('week', sb.created_at)
ORDER BY week DESC;

-- ============================================================
-- 6. University partner ROI
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_university_roi AS
SELECT
    up.id AS partner_id,
    up.name,
    up.domain,
    up.total_students,
    up.active_students,
    up.total_applications,
    up.revenue_share_pct,
    (SELECT COUNT(*)::int FROM public.platform_telemetry pt
     WHERE pt.event_type = 'student_imported'
       AND pt.metadata->>'partner_id' = up.id::text) AS imported_students,
    (SELECT COUNT(*)::int FROM public.tenants t
     WHERE t.plan = 'PRO' AND t.id IN (
         SELECT pt2.tenant_id FROM public.platform_telemetry pt2
         WHERE pt2.event_type = 'student_imported'
           AND pt2.metadata->>'partner_id' = up.id::text
     )) AS pro_upgrades
FROM public.university_partners up
WHERE up.is_active = true;

-- ============================================================
-- 7. Integrator usage (3rd-party API consumers)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_integrator_stats AS
SELECT
    ak.tenant_id,
    t.name AS tenant_name,
    ak.tier,
    COUNT(au.id)::int AS total_calls,
    COUNT(DISTINCT DATE(au.created_at))::int AS active_days,
    MIN(au.created_at) AS first_call,
    MAX(au.created_at) AS last_call,
    AVG(au.latency_ms)::int AS avg_latency
FROM public.api_keys ak
JOIN public.tenants t ON t.id = ak.tenant_id
LEFT JOIN public.api_usage au ON au.api_key_id = ak.id
WHERE ak.is_active = true
GROUP BY ak.tenant_id, t.name, ak.tier
ORDER BY total_calls DESC;

-- ============================================================
-- 8. Refresh function
-- ============================================================

CREATE OR REPLACE FUNCTION public.refresh_m6_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW public.mv_arr_by_vertical;
    REFRESH MATERIALIZED VIEW public.mv_api_v2_usage;
    REFRESH MATERIALIZED VIEW public.mv_blueprint_heatmap;
    REFRESH MATERIALIZED VIEW public.mv_revenue_per_blueprint;
    REFRESH MATERIALIZED VIEW public.mv_staffing_performance;
    REFRESH MATERIALIZED VIEW public.mv_university_roi;
    REFRESH MATERIALIZED VIEW public.mv_integrator_stats;
END;
$$ LANGUAGE plpgsql;
