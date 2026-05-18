-- Migration: Update organization API key columns
-- Description: Rename existing API key columns and add new provider columns

-- Rename existing columns to match new naming convention
ALTER TABLE organizations RENAME COLUMN encrypted_openai_admin_key TO openai_api_key_encrypted;
ALTER TABLE organizations RENAME COLUMN encrypted_anthropic_admin_key TO anthropic_api_key_encrypted;

-- Add new API key columns for additional providers
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS gemini_api_key_encrypted VARCHAR;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deepseek_api_key_encrypted VARCHAR;

-- Add comments to columns
COMMENT ON COLUMN organizations.openai_api_key_encrypted IS 'Encrypted OpenAI admin API key';
COMMENT ON COLUMN organizations.anthropic_api_key_encrypted IS 'Encrypted Anthropic admin API key';
COMMENT ON COLUMN organizations.gemini_api_key_encrypted IS 'Encrypted Gemini API key';
COMMENT ON COLUMN organizations.deepseek_api_key_encrypted IS 'Encrypted DeepSeek API key';
