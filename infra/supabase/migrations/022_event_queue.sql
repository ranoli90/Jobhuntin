-- Migration 022: Event Job Queue (LISTEN/NOTIFY)
--
-- Enables event-driven job processing by notifying workers when new jobs are queued.

CREATE OR REPLACE FUNCTION public.notify_job_queue()
RETURNS trigger AS $$
BEGIN
    -- Payload is optional, just waking up workers to check the queue
    PERFORM pg_notify('job_queue', 'check');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_notify_job_queue ON public.applications;

-- Trigger notification on new jobs or whenever a job is moved to QUEUED state
CREATE TRIGGER tr_notify_job_queue
AFTER INSERT OR UPDATE OF status ON public.applications
FOR EACH ROW
WHEN (NEW.status = 'QUEUED')
EXECUTE FUNCTION public.notify_job_queue();
