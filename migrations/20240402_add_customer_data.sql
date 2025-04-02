-- Add new columns to brand_analysis table
ALTER TABLE brand_analysis
ADD COLUMN IF NOT EXISTS ideal_customer TEXT,
ADD COLUMN IF NOT EXISTS icp_pain_points TEXT,
ADD COLUMN IF NOT EXISTS unique_value TEXT,
ADD COLUMN IF NOT EXISTS proof_points TEXT,
ADD COLUMN IF NOT EXISTS energizing_topics TEXT,
ADD COLUMN IF NOT EXISTS decision_maker TEXT,
ADD COLUMN IF NOT EXISTS content_pillars TEXT[],
ADD COLUMN IF NOT EXISTS key_topics TEXT[]; 