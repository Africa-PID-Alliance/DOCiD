-- =====================================================================
-- Production SQL Script: Add identifier columns to publication_projects
-- Date: 2025-08-08
-- Purpose: Add identifier and identifier_type columns to publication_projects table
-- =====================================================================

-- Start transaction for safety
BEGIN;

-- Check current schema
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'publication_projects' 
ORDER BY ordinal_position;

-- Add identifier column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'publication_projects' 
        AND column_name = 'identifier'
    ) THEN
        ALTER TABLE publication_projects 
        ADD COLUMN identifier VARCHAR(500);
        
        RAISE NOTICE 'Added identifier column to publication_projects';
    ELSE
        RAISE NOTICE 'identifier column already exists in publication_projects';
    END IF;
END $$;

-- Add identifier_type column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'publication_projects' 
        AND column_name = 'identifier_type'
    ) THEN
        ALTER TABLE publication_projects 
        ADD COLUMN identifier_type VARCHAR(50);
        
        RAISE NOTICE 'Added identifier_type column to publication_projects';
    ELSE
        RAISE NOTICE 'identifier_type column already exists in publication_projects';
    END IF;
END $$;

-- Optional: Migrate existing raid_id data to new columns
-- This will copy existing RAID IDs to the new identifier column with type='raid'
UPDATE publication_projects 
SET identifier = raid_id,
    identifier_type = 'raid'
WHERE raid_id IS NOT NULL 
AND raid_id != ''
AND identifier IS NULL;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_publication_projects_identifier_type 
ON publication_projects(identifier_type);

CREATE INDEX IF NOT EXISTS idx_publication_projects_identifier 
ON publication_projects(identifier);

-- Update alembic_version to prevent migration conflicts
-- Get the latest revision and update it
DO $$ 
DECLARE
    current_revision VARCHAR(32);
BEGIN
    -- Get current revision
    SELECT version_num INTO current_revision 
    FROM alembic_version 
    LIMIT 1;
    
    -- Only update if not already at the target revision
    IF current_revision != '917f22740106' THEN
        UPDATE alembic_version 
        SET version_num = '917f22740106';
        
        RAISE NOTICE 'Updated alembic_version to 917f22740106';
    ELSE
        RAISE NOTICE 'alembic_version already at 917f22740106';
    END IF;
END $$;

-- Verify the changes
SELECT 
    'publication_projects' as table_name,
    COUNT(*) as total_records,
    COUNT(identifier) as records_with_identifier,
    COUNT(identifier_type) as records_with_identifier_type,
    COUNT(raid_id) as records_with_raid_id
FROM publication_projects;

-- Show sample data
SELECT 
    id,
    title,
    raid_id,
    identifier,
    identifier_type,
    publication_id
FROM publication_projects
ORDER BY id DESC
LIMIT 5;

-- Show final schema
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'publication_projects'
AND column_name IN ('raid_id', 'identifier', 'identifier_type')
ORDER BY ordinal_position;

-- Commit the transaction if everything is successful
COMMIT;

-- =====================================================================
-- Rollback Script (if needed)
-- =====================================================================
-- To rollback these changes, run:
/*
BEGIN;

-- Remove the columns
ALTER TABLE publication_projects DROP COLUMN IF EXISTS identifier;
ALTER TABLE publication_projects DROP COLUMN IF EXISTS identifier_type;

-- Drop the indexes
DROP INDEX IF EXISTS idx_publication_projects_identifier_type;
DROP INDEX IF EXISTS idx_publication_projects_identifier;

-- Revert alembic version to previous
UPDATE alembic_version SET version_num = '9d6930747dbb';

COMMIT;
*/

-- =====================================================================
-- Notes for Production Deployment:
-- =====================================================================
-- 1. Backup the database before running this script
-- 2. Run during maintenance window or low-traffic period
-- 3. Test on staging environment first
-- 4. Monitor application logs after deployment
-- 5. The script is idempotent - safe to run multiple times
-- 6. Existing raid_id column is preserved for backward compatibility
-- 7. New data will be stored in both raid_id and identifier columns