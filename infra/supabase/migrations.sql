-- SEO Engine checkpoint table for durable progress tracking
CREATE TABLE IF NOT EXISTS seo_engine_progress (
  id SERIAL PRIMARY KEY,
  service_id TEXT UNIQUE NOT NULL,
  last_index INTEGER NOT NULL DEFAULT 0,
  last_submission_at TIMESTAMPTZ,
  daily_quota_used INTEGER NOT NULL DEFAULT 0,
  daily_quota_reset TIMESTAMPTZ NOT NULL DEFAULT (now() AT TIME ZONE 'utc' + interval '1 day'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_seo_engine_progress_service_id ON seo_engine_progress(service_id);

-- Optional: submission log for audit
CREATE TABLE IF NOT EXISTS seo_submission_log (
  id SERIAL PRIMARY KEY,
  service_id TEXT NOT NULL,
  batch_url_file TEXT,
  urls_submitted INTEGER NOT NULL,
  success BOOLEAN NOT NULL,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_seo_submission_log_service_id ON seo_submission_log(service_id);

-- Enable RLS for safety (optional, if you want to restrict access)
-- ALTER TABLE seo_engine_progress ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE seo_submission_log ENABLE ROW LEVEL SECURITY;
