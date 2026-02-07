# Release Playbook — Prompt & Agent Behavior Changes

Standard process for safely shipping new prompt versions or agent behavior changes.

---

## Step 1: Create Experiment

Insert a new experiment row in the `experiments` table:

```sql
INSERT INTO public.experiments (key, variants, is_active, metadata)
VALUES (
    'dom_mapping_prompt_v1_vs_v2',
    '[{"name":"v1","traffic_pct":90},{"name":"v2","traffic_pct":10}]',
    true,
    '{"description":"Test new DOM mapping prompt with improved select handling"}'
);
```

Register the new prompt version in `backend/llm/prompt_registry.py`:

```python
register_prompt("dom_mapping", "v2", DOM_MAPPING_PROMPT_V2)
```

## Step 2: Deploy

- Deploy the code with the new prompt registered but behind the experiment.
- Only 10% of tenants will be assigned to `v2`.
- The remaining 90% continue using `v1`.

## Step 3: Monitor (24–48 hours)

Check the following metrics:

1. **Error rates**: `agent.applications_failed` counter in `/healthz` metrics.
2. **FAILED status rate**: Query `agent_evaluations` for `label='FAILURE'` grouped by experiment variant.
3. **User feedback**: Check for `source='USER'` evaluations with `label='FAILURE'`.
4. **Hold question rate**: Compare avg hold questions between variants.

Use the experiment readout endpoint:

```
GET /admin/experiments/dom_mapping_prompt_v1_vs_v2/results
```

Or run the SQL directly:

```sql
SELECT ea.variant, ev.label, COUNT(*)
FROM experiment_assignments ea
JOIN applications a ON a.tenant_id = ea.subject_id
JOIN agent_evaluations ev ON ev.application_id = a.id
WHERE ea.experiment_id = (SELECT id FROM experiments WHERE key = 'dom_mapping_prompt_v1_vs_v2')
  AND ev.source = 'SYSTEM'
GROUP BY ea.variant, ev.label;
```

## Step 4: Ramp or Rollback

**If metrics are good** (v2 success rate ≥ v1):

```sql
UPDATE experiments
SET variants = '[{"name":"v2","traffic_pct":100}]'
WHERE key = 'dom_mapping_prompt_v1_vs_v2';
```

Then in a follow-up deploy, make `v2` the default and retire `v1`.

**If metrics are bad**:

```sql
UPDATE experiments SET is_active = false
WHERE key = 'dom_mapping_prompt_v1_vs_v2';
```

All tenants will fall back to the default prompt version immediately.

## Step 5: Cleanup

After the new version is proven stable:

1. Update `_register_builtin_prompts()` to set the new version as `default=True`.
2. Remove the experiment row.
3. Optionally remove the old prompt template from the codebase.

---

## Emergency Hotfix

If something goes critically wrong mid-experiment:

1. **Disable the agent entirely**:
   ```
   AGENT_ENABLED=false
   ```
   Restart the worker. No tasks will be processed.

2. **Force a specific prompt version**:
   ```
   PROMPT_VERSION_OVERRIDE=v1
   ```
   Restart the worker. All tasks will use `v1` regardless of experiments.

3. **Deactivate all experiments**:
   ```sql
   UPDATE experiments SET is_active = false;
   ```
   No experiment assignments will be made; default prompts are used.
