select time_when_posted, link, title, company, compensation, location, source, listing_id
from job_listings jl
where company not in (
-- Collecting resumes for (junior) jobs that don't exist:
'Gainwell Technologies',
'HireMeFast LLC', 
'Phoenix Recruitment',
'Team Remotely Inc',
'Patterned Learning Career',
'RemoteWorker US', -- Too much stupid spam, including survey takers...
'RemoteWorker UK', -- not for us market
'TransPerfect', -- some weird in-car audio collection?
'DolphinsElite', -- Paid subscription to apply to jobs that pay 30-40k?!
'Canonical', -- The company developing Ubuntu, crazy reqs & low pay
'SynergisticIT', -- Weird youtube links in the job posting, seems to be preying on juniors
'DataAnnotation', -- Jobs training AI to code
'Talentify.io', -- Have to interview with an AI, mostly just data training/collection?
'Recruiter.com', -- Some sort of scam "Check Your Email Inbox Immediately After Applying For Next Steps"
'Providence Health & Services', -- Recruiting for medical coder, can refine sql later to make sure I don't exclude real dev jobs
'Actalent', -- Seems to just spam food QA jobs for Columbus, OH which aren't related to tech
'Get It Recruit - Information Technology', -- Seems like a bad job board with way too much spam email & outdated listings
'SimplyApply', -- Spammer, no profile 1-person LinkedIn "company", reposting JPMC jobs you could apply to directly
'Opinion Focus Panel', -- Money for focus panels, probably a scam but also unrelated
'AB Media Publishing, LLC', -- Money for focus panels, probably a scam but also unrelated (same description as above?)
-- Unrelated listing for data entry? has to be some sort of scam, all of these have the same description:
'Opinion Focus Panel LLC', 
'Webpratodos Marketing Digital',
'Diverserec',
'FONDS DE DOTATION FUTUR AU PRESENT',
'IDR, Inc.', -- Uses "Jamie" virtual recruiter, makes you get recorded while talking to an AI for screening...
'TalentBurst, Inc.', -- Uses "Jamie" virtual recruiter, makes you get recorded while talking to an AI for screening...
'Dexian Inc', -- Has 2 associated members on LinkedIn, doesn't feel legit; Dexian is legit but this is pretending to be Dexian?
'ManTech', -- Requires clearance, gov jobs
'ARCTOS LLC', -- Requires clearance, gov jobs
'Northrop Grumman', -- Requires clearance, gov jobs
'HII' -- Requires clearance, gov jobs
)
AND NOT (
title ILIKE '%senior%'
OR title ILIKE '%sr%'
OR title ILIKE '%sr.%'
OR title ILIKE '%principal%'
OR title ILIKE '%lead%'
OR title ILIKE '%vice president%'
OR title ILIKE '%staff%'
OR title ILIKE '%tableau%'
OR title ILIKE '%architect%'
OR title ILIKE '%manager%'
OR title ILIKE '%director%'
OR title ILIKE '%supervisor%'
OR title ILIKE '%scrum%'
OR title ILIKE '%front end%'
OR title ILIKE '%front-end%'
OR title ILIKE '%frontend%'
OR title ILIKE '%web%'
OR title ILIKE '%php%'
OR title ILIKE '%desktop%'
OR title ILIKE '%android%'
OR title ILIKE '%ios%'
OR title ILIKE '%mobile%'
OR title ILIKE '%salesforce%'
OR title ILIKE '%power bi%'
OR title ILIKE '%peoplesoft%'
OR title ILIKE '%mulesoft%'
OR title ILIKE '%servicenow%'
OR title ILIKE '%ab initio%'
OR title ILIKE '%wordpress%'
OR title ~* '\yma\y'
OR title ~* '\yai\y'
OR title ILIKE '%machine learning%'
OR title ILIKE '%mainframe%'
OR title ILIKE '%tableau%'
OR title ILIKE '%sharepoint%'
OR title ILIKE '%data%'
OR title ILIKE '%analyst%'
OR title ILIKE '%system%'
OR title ILIKE '%solution%'
OR title ILIKE '%devops%'
OR title ILIKE '%reliability%'
OR title ILIKE '%security%'
OR title ILIKE '%firmware%'
OR title ILIKE '%embedded%'
OR title ILIKE '%as400%'
OR title ILIKE '%technician%'
OR title ILIKE '%tech%'
OR title ILIKE '%supplier%'
OR title ILIKE '%inspector%'
OR title ILIKE '%specialist%'
OR title ILIKE '%support%'
OR title ILIKE '%coordinator%'
)
and ("location" ilike '%columbus%' or 
"location" ilike '%remote%')
-- Quick search for junior positions when I'm low on time:
--and (title ilike '%junior%' 
--or title ilike '%jr%'
--or title ilike '%jr.%')
order by time_when_posted desc

-- Get table estimated size in an efficient/low-resource use kind of way:
--SELECT reltuples AS estimate FROM pg_class WHERE relname = 'job_listings';

-- Get jobs per day:
--SELECT DATE(time_when_posted) AS date_only,
--       TO_CHAR(time_when_posted, 'Day') AS day_of_week,
--       COUNT(*) AS number_of_jobs_posted
--FROM job_listings jl 
--GROUP BY DATE(time_when_posted), TO_CHAR(time_when_posted, 'Day')
--ORDER BY date_only;

-- Get jobs per week:
--SELECT EXTRACT(YEAR FROM time_when_posted) AS year,
--       EXTRACT(WEEK FROM time_when_posted) AS week,
--       COUNT(*) AS number_of_jobs_posted
--FROM job_listings jl 
--GROUP BY EXTRACT(YEAR FROM time_when_posted), EXTRACT(WEEK FROM time_when_posted)
--ORDER BY year, week;

-- Get jobs per year:
--SELECT EXTRACT(YEAR FROM time_when_posted) AS year,
--       COUNT(*) AS number_of_jobs_posted
--FROM job_listings jl 
--GROUP BY EXTRACT(YEAR FROM time_when_posted)
--ORDER BY year;

-- Get all roles on my database:
--SELECT 
--    r.rolname, 
--    ARRAY(
--        SELECT b.rolname
--        FROM pg_catalog.pg_auth_members m
--        JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid)
--        WHERE m.member = r.oid
--    ) as memberof
--FROM pg_catalog.pg_roles r
--WHERE r.rolname NOT IN (
--    'pg_signal_backend',
--    'rds_iam',
--    'rds_replication',
--    'rds_superuser',
--    'rdsadmin',
--    'rdsrepladmin',
--    'pg_checkpoint',
--    'pg_create_subscription',
--    'pg_database_owner',
--    'pg_execute_server_program',
--    'pg_monitor',
--    'pg_read_all_data',
--    'pg_read_all_settings',
--    'pg_read_all_stats',
--    'pg_read_server_files',
--    'pg_stat_scan_tables',
--    'pg_use_reserved_connections',
--    'pg_write_all_data',
--    'pg_write_server_files',
--    'rds_ad',
--    'rds_password',
--    'rdstopmgr'
--)
--ORDER BY 1;