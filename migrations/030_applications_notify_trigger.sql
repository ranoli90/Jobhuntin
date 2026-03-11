-- P0-3: NOTIFY job_queue on applications INSERT (status=QUEUED)
-- Ensures mobile Supabase inserts wake the worker immediately, same as web API.
-- +migrate Up
CREATE OR REPLACE FUNCTION public.notify_job_queue_on_application()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'QUEUED' THEN
    PERFORM pg_notify('job_queue', '');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_applications_notify_job_queue ON public.applications;
CREATE TRIGGER trg_applications_notify_job_queue
  AFTER INSERT OR UPDATE OF status ON public.applications
  FOR EACH ROW
  WHEN (NEW.status = 'QUEUED')
  EXECUTE FUNCTION public.notify_job_queue_on_application();

-- +migrate Down
DROP TRIGGER IF EXISTS trg_applications_notify_job_queue ON public.applications;
DROP FUNCTION IF EXISTS public.notify_job_queue_on_application();
