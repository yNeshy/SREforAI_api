-- Enable UUID extension for secure, non-sequential IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ORGANIZATIONS TABLE
-- Stores client info and securely holds encrypted credentials.
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    -- Store encrypted keys here. Never store raw API keys in plain text!
    encrypted_openai_admin_key TEXT,
    encrypted_anthropic_admin_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. DAILY USAGE CACHE TABLE
-- Partitioning or indexing by timestamp is essential here for fast analytical queries.
CREATE TABLE daily_usage_cache (
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
    
    -- Time tracking (bucketed to the day)
    usage_date DATE NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure we don't duplicate rows if the ingestion engine runs multiple times a day
    CONSTRAINT unique_org_provider_model_key_date UNIQUE (org_id, provider, model, api_key_id, usage_date)
);

-- 3. ALERTS & WEBHOOKS CONFIGURATION TABLE
-- For the alert/fallback notification feature you wanted to track.
CREATE TABLE budget_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    monthly_budget_usd NUMERIC(10, 2) NOT NULL,
    alert_threshold_percentage INT NOT NULL DEFAULT 80, -- e.g., trigger at 80% of budget
    webhook_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. PERFORMANCE & AGGREGATION INDEXES
-- SRE Optimization: Speed up the dashboards fetching historical metrics by org and date range.
CREATE INDEX idx_usage_org_date ON daily_usage_cache(org_id, usage_date);
CREATE INDEX idx_usage_provider_model ON daily_usage_cache(provider, model);

-- Automatically handle the updated_at timestamp for organizations
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_org_modtime
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();