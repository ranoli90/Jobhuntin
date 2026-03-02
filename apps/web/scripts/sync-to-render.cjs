/**
 * DEPRECATED: Use scripts/sync_render_envs.py instead.
 *
 *   export RENDER_API_KEY=your-key
 *   PYTHONPATH=packages python scripts/sync_render_envs.py
 *
 * This script previously had hardcoded secrets (removed for security).
 * For one-off env var updates, use the Python script or Render dashboard.
 */
console.warn(
  'sync-to-render.cjs is deprecated. Use: PYTHONPATH=packages python scripts/sync_render_envs.py'
);
