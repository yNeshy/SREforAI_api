-- Enable UUID extension for secure, non-sequential IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ORGANIZATIONS TABLE
-- Stores client info and securely holds encrypted credentials.
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    -- Store encrypted keys here. Never store raw API keys in plain text!
    encrypted_openai_admin_key TEXT,
    encrypted_anthropic_admin_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. HOURLY_DAILY_USAGE_CACHE TABLE
-- Tracks usage with hourly granularity for precise analytics
CREATE TABLE IF NOT EXISTS hourly_daily_usage_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Categorization dimensions
    provider VARCHAR(50) NOT NULL,       -- 'openai', 'anthropic'
    model VARCHAR(100) NOT NULL,         -- 'gpt-4o', 'claude-3-5-sonnet'
    api_key_id VARCHAR(255) NOT NULL,    -- The client's internal sub-key hash/identifier
    
    -- Quantitative metrics
    input_tokens BIGINT NOT NULL DEFAULT 0,
    output_tokens BIGINT NOT NULL DEFAULT 0,
    cached_tokens BIGINT NOT NULL DEFAULT 0,
    
    -- Cost tracking (NUMERIC avoids floating-point errors inherent to REAL/DOUBLE)
    raw_cost_usd NUMERIC(12, 6) NOT NULL DEFAULT 0.000000,
    
    -- Time tracking (bucketed to the hour for granular analytics)
    timestamp_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure we don't duplicate rows if the ingestion engine runs multiple times
    CONSTRAINT unique_org_provider_model_key_time UNIQUE (org_id, provider, model, api_key_id, timestamp_bucket)
);

-- 3. PERFORMANCE & AGGREGATION INDEXES
-- SRE Optimization: Speed up the dashboards fetching historical metrics by org and date range.
CREATE INDEX IF NOT EXISTS idx_usage_org_timestamp ON hourly_daily_usage_cache(org_id, timestamp_bucket);
CREATE INDEX IF NOT EXISTS idx_usage_provider_model ON hourly_daily_usage_cache(provider, model);
CREATE INDEX IF NOT EXISTS idx_usage_api_key ON hourly_daily_usage_cache(api_key_id);
CREATE INDEX IF NOT EXISTS idx_usage_date_range ON hourly_daily_usage_cache(timestamp_bucket DESC);

-- Automatically handle the updated_at timestamp for organizations
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_org_modtime ON organizations;
CREATE TRIGGER update_org_modtime
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();
