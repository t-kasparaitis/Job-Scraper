select *
from linkedin l
where company not in (
'HireMeFast LLC', -- Collecting resumes for junior jobs that don't exist
'DataAnnotation', -- Jobs training AI to code
'Talentify.io', -- Have to interview with an AI, mostly just data training/collection?
'Phoenix Recruitment', -- Collecting resumes for junior jobs that don't exist
'Team Remotely Inc', -- Collecting resumes for junior jobs that don't exist
'Patterned Learning Career', -- Collecting resumes for junior jobs that don't exist
'SynergisticIT', -- Weird youtube links in the job posting, seems to be preying on juniors
'Recruiter.com', -- Some sort of scam "Check Your Email Inbox Immediately After Applying For Next Steps"
'Providence Health & Services' -- Recruiting for medical coder, can refine sql later to make sure I don't exclude real dev jobs
)
order by time_when_posted desc