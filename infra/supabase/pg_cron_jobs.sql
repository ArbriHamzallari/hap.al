-- pg_cron job: call Railway /internal/process-followups every 5 minutes.
--
-- Prerequisites (Supabase Dashboard → Database → Extensions):
--   1. Enable pg_cron
--   2. Enable pg_net
--
-- Replace YOUR_INTERNAL_CRON_SECRET with the same value as INTERNAL_CRON_SECRET on Railway.

SELECT cron.schedule(
  'hap-process-followups',
  '*/5 * * * *',
  $$
  SELECT net.http_post(
    url := 'https://hapal-production.up.railway.app/internal/process-followups',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer YOUR_INTERNAL_CRON_SECRET'
    ),
    body := '{}'::jsonb
  ) AS request_id;
  $$
);

-- Verify the job exists:
-- SELECT jobid, jobname, schedule, active FROM cron.job WHERE jobname = 'hap-process-followups';

-- Check recent runs:
-- SELECT jobid, status, return_message, start_time
-- FROM cron.job_run_details
-- WHERE jobid = (SELECT jobid FROM cron.job WHERE jobname = 'hap-process-followups')
-- ORDER BY start_time DESC LIMIT 5;

-- Unschedule (for reference):
-- SELECT cron.unschedule('hap-process-followups');
