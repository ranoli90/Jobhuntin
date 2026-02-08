"""
Experiment readout — compare variant-level performance metrics.

Joins experiment_assignments with applications and agent_evaluations
to produce per-variant success rates and hold-question averages.
"""

from __future__ import annotations

from typing import Any

import asyncpg

EXPERIMENT_RESULTS_SQL = """
WITH assignments AS (
    SELECT
        ea.variant,
        ea.subject_type,
        ea.subject_id
    FROM public.experiment_assignments ea
    JOIN public.experiments e ON e.id = ea.experiment_id
    WHERE e.key = $1
),
app_variants AS (
    SELECT
        a.id AS application_id,
        a.tenant_id,
        a.status,
        a.attempt_count,
        asgn.variant
    FROM public.applications a
    JOIN assignments asgn
        ON asgn.subject_type = 'TENANT' AND asgn.subject_id = a.tenant_id
),
evals AS (
    SELECT
        av.variant,
        ev.label,
        COUNT(*)::int AS eval_count
    FROM app_variants av
    JOIN public.agent_evaluations ev ON ev.application_id = av.application_id
    WHERE ev.source = 'SYSTEM'
    GROUP BY av.variant, ev.label
),
holds AS (
    SELECT
        av.variant,
        COUNT(DISTINCT av.application_id)::int AS app_count,
        COUNT(i.id)::int AS hold_count,
        ROUND(
            COUNT(i.id)::numeric / NULLIF(COUNT(DISTINCT av.application_id), 0), 2
        ) AS avg_holds
    FROM app_variants av
    LEFT JOIN public.application_inputs i ON i.application_id = av.application_id
    GROUP BY av.variant
)
SELECT
    COALESCE(e.variant, h.variant) AS variant,
    COALESCE(h.app_count, 0) AS total_applications,
    COALESCE(h.hold_count, 0) AS total_hold_questions,
    COALESCE(h.avg_holds, 0) AS avg_hold_questions_per_app,
    json_object_agg(
        COALESCE(e.label, '_none'),
        COALESCE(e.eval_count, 0)
    ) FILTER (WHERE e.label IS NOT NULL) AS eval_breakdown
FROM evals e
FULL OUTER JOIN holds h ON h.variant = e.variant
GROUP BY COALESCE(e.variant, h.variant), h.app_count, h.hold_count, h.avg_holds
ORDER BY variant
"""


async def get_experiment_results(
    conn: asyncpg.Connection,
    experiment_key: str,
) -> list[dict[str, Any]]:
    """
    Return per-variant performance stats for an experiment.

    Each row contains:
      - variant: str
      - total_applications: int
      - total_hold_questions: int
      - avg_hold_questions_per_app: float
      - eval_breakdown: dict mapping label → count
    """
    rows = await conn.fetch(EXPERIMENT_RESULTS_SQL, experiment_key)
    results = []
    for r in rows:
        row_dict = dict(r)
        # Parse eval_breakdown from JSON string if needed
        eb = row_dict.get("eval_breakdown")
        if isinstance(eb, str):
            import json
            row_dict["eval_breakdown"] = json.loads(eb)
        results.append(row_dict)
    return results
