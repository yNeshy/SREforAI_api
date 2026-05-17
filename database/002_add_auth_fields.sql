-- Migration to add authentication fields to organizations table
-- This adds email and password_hash fields for JWT-based authentication

ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS email VARCHAR(255) NOT NULL DEFAULT '',
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) NOT NULL DEFAULT '';

-- Add unique constraint on email
ALTER TABLE organizations
ADD CONSTRAINT organizations_email_key UNIQUE (email);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_organizations_email ON organizations(email);

-- Update the trigger to handle the new fields
-- (The existing update_org_modtime trigger should still work)
