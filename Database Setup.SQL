-- Create a new PostgreSQL database named 'job_listings' manually then paste everything below this line:
-- May need to do a generate script later to update more columns etc.

-- Create the 'LinkedIn' table
CREATE TABLE IF NOT EXISTS linkedin (
    linked_in_id TEXT PRIMARY KEY,
    link TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    time_when_posted TIMESTAMP NOT NULL
);