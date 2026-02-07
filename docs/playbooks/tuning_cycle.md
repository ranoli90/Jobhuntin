# Weekly Tuning Cycle

A structured loop for reviewing agent performance and deriving improvements.

---

## Schedule

Run this review weekly (e.g., Monday morning).

## Step 1: Pull Performance Summary

Use the admin endpoint or run directly:

```
GET /admin/agent-performance?date_from=2025-01-27&date_to=2025-02-03
```

Or via SQL:

```sql
-- Success rate by blueprint this week
SELECT
    a.blueprint_key,
    e.label,
    COUNT(*)::int AS count
FROM agent_evaluations e
JOIN applications a ON a.id = e.application_id
WHERE e.source = 'SYSTEM'
  AND e.created_at >= now() - interval '7 days'
GROUP BY a.blueprint_key, e.label
ORDER BY a.blueprint_key, e.label;
```

## Step 2: Review Top Failure Reasons

```sql
SELECT reason, COUNT(*) AS count
FROM agent_evaluations
WHERE source = 'SYSTEM' AND label = 'FAILURE'
  AND created_at >= now() - interval '7 days'
GROUP BY reason
ORDER BY count DESC
LIMIT 20;
```

Common patterns to look for:
- **"No form fields detected"** → site structure changed or JS-heavy SPA not loading.
- **"Could not locate a submit button"** → submit button selectors need updating.
- **"LLM rate limit exceeded"** → increase `LLM_RATE_LIMIT_PER_MINUTE` or add backoff.
- **"Page load timeout"** → increase `PAGE_TIMEOUT_MS` or check network.

## Step 3: Review Most Common Hold Questions

```sql
SELECT question, COUNT(*) AS count
FROM application_inputs
WHERE created_at >= now() - interval '7 days'
  AND resolved = false
GROUP BY question
ORDER BY count DESC
LIMIT 20;
```

If the same question appears frequently:
1. **Add it to the profile schema** — pre-collect the data during onboarding.
2. **Improve the prompt** — teach the LLM to infer the answer from existing profile data.
3. **Add a UI pre-fill** — ask the user once and store the answer for future applications.

## Step 4: Review User Feedback

```sql
SELECT label, reason, COUNT(*) AS count
FROM agent_evaluations
WHERE source = 'USER'
  AND created_at >= now() - interval '7 days'
GROUP BY label, reason
ORDER BY count DESC
LIMIT 20;
```

## Step 5: Derive Action Items

Based on the above, create concrete tasks:

| Finding | Action | Type |
|---------|--------|------|
| "Expected salary" asked 40 times | Add `expected_salary` to profile | Profile schema |
| Submit button not found on greenhouse.io | Add `button:has-text("Submit Application")` to job-app selectors | Blueprint fix |
| v2 prompt has 5% higher success rate | Ramp v2 to 100% | Experiment |
| "Form structure unsupported" for multi-iframe sites | Log and skip; add to known-unsupported list | Agent logic |

## Step 6: Implement and Test

1. Create prompt tweaks behind experiments (see `release.md`).
2. Profile schema additions → migration + model update.
3. Blueprint selector fixes → direct code change + deploy.
4. UI improvements → mobile app update.

## Step 7: Record Decisions

Update `AGENT_TODO.md` (or your project tracker) with:
- What was changed and why.
- Expected impact.
- How to verify (which metrics to watch).

---

## Metrics to Track Over Time

| Metric | Target | Source |
|--------|--------|--------|
| Agent success rate (SUCCESS / total) | > 80% | `agent_evaluations` |
| Agent partial rate (PARTIAL / total) | < 15% | `agent_evaluations` |
| Avg hold questions per application | < 2.0 | `application_inputs` |
| User feedback FAILURE rate | < 5% | `agent_evaluations` (USER) |
| P95 LLM latency | < 10s | `agent.llm_latency_seconds` metric |
