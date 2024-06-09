-- Will need to create a job_listings PostgreSQL database and then run this script:

CREATE TABLE public.job_listings (
	listing_id text NOT NULL,
	link text NOT NULL,
	title text NOT NULL,
	company text NOT NULL,
	time_when_scraped timestamp NOT NULL,
	"source" text NOT NULL,
	"location" text NULL,
	compensation text NULL,
	CONSTRAINT composite_key PRIMARY KEY (listing_id, source)
);