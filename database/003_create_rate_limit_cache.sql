-- Migration: Create rate_limit_cache table
-- Description: Stores normalized rate limits and utilization data fetched by cron job

CREATE TABLE IF NOT EXISTS rate_limit_cache (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    api_key_id VARCHAR(255) NOT NULL,
    utilization JSONB NOT NULL,
    limits JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_rate_limit_cache_provider ON rate_limit_cache(provider);
CREATE INDEX IF NOT EXISTS idx_rate_limit_cache_api_key_id ON rate_limit_cache(api_key_id);
CREATE INDEX IF NOT EXISTS idx_rate_limit_cache_provider_api_key ON rate_limit_cache(provider, api_key_id);
CREATE INDEX IF NOT EXISTS idx_rate_limit_cache_updated_at ON rate_limit_cache(updated_at);

-- Add comment to table
COMMENT ON TABLE rate_limit_cache IS 'Cached rate limits and utilization data for various providers. Refreshed every 15 minutes by cron job.';
