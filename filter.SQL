select time_when_posted, link, title, compensation, location, company, listing_id, source
from job_listings jl
where company not in (
'HireMeFast LLC', -- Collecting resumes for junior jobs that don't exist
'DataAnnotation', -- Jobs training AI to code
'Talentify.io', -- Have to interview with an AI, mostly just data training/collection?
'Phoenix Recruitment', -- Collecting resumes for junior jobs that don't exist
'Team Remotely Inc', -- Collecting resumes for junior jobs that don't exist
'Patterned Learning Career', -- Collecting resumes for junior jobs that don't exist
'SynergisticIT', -- Weird youtube links in the job posting, seems to be preying on juniors
'Recruiter.com', -- Some sort of scam "Check Your Email Inbox Immediately After Applying For Next Steps"
'Providence Health & Services', -- Recruiting for medical coder, can refine sql later to make sure I don't exclude real dev jobs
'Actalent', -- Seems to just spam food QA jobs for Columbus, OH which aren't related to tech
'Get It Recruit - Information Technology', -- Seems like a bad job board with way too much spam email & outdated listings
'SimplyApply', -- Spammer, no profile 1-person LinkedIn "company", reposting JPMC jobs you could apply to directly
'Opinion Focus Panel', -- Money for focus panels, probably a scam but also unrelated
'AB Media Publishing, LLC', -- Money for focus panels, probably a scam but also unrelated (same description as above?)
'IDR, Inc.' -- Uses "Jamie" virtual recruiter, makes you get recorded while talking to an AI for screening...
)
AND NOT (
title ILIKE '%senior%'
OR title ILIKE '%sr%'
OR title ILIKE '%sr.%'
OR title ILIKE '%principal%'
OR title ILIKE '%lead%'
OR title ILIKE '%staff%'
OR title ILIKE '%architect%'
OR title ILIKE '%android%'
OR title ILIKE '%salesforce%'
OR title ILIKE '%machine learning%'
OR title ILIKE '%mainframe%'
OR title ILIKE '%tableau%'
OR title ILIKE '%sharepoint%'
OR title ILIKE '%ml%'
OR title ILIKE '%ai%'
OR title ILIKE '%data%'
OR title ILIKE '%systems%'
OR title ILIKE '%solutions%'
OR title ILIKE '%devops%'
OR title ILIKE '%security%'
)
order by time_when_posted desc

-- Get table estimated size in an efficient/low-resource use kind of way:
-- SELECT reltuples AS estimate FROM pg_class WHERE relname = 'job_listings';