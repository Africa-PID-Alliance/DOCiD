-- SQL Script to add identifier columns to publication_creators and publication_funders tables
-- Run this script directly in PostgreSQL to add the columns without using Flask migrations
-- Usage: psql -U your_username -d your_database -f add_identifier_columns.sql

-- Start transaction
BEGIN;

-- Add identifier_type column to publication_creators table
ALTER TABLE publication_creators 
ADD COLUMN IF NOT EXISTS identifier_type VARCHAR(50);

-- Modify identifier column in publication_creators to support longer URLs
ALTER TABLE publication_creators 
ALTER COLUMN identifier TYPE VARCHAR(500);

-- Add comment to describe the columns
COMMENT ON COLUMN publication_creators.identifier IS 'Stores the full resolvable URL (e.g., https://orcid.org/0000-0002-1981-4157)';
COMMENT ON COLUMN publication_creators.identifier_type IS 'Stores the identifier type (e.g., orcid, isni, viaf)';

-- Add identifier and identifier_type columns to publication_funders table
ALTER TABLE publication_funders 
ADD COLUMN IF NOT EXISTS identifier VARCHAR(500);

ALTER TABLE publication_funders 
ADD COLUMN IF NOT EXISTS identifier_type VARCHAR(50);

-- Add comments to describe the columns
COMMENT ON COLUMN publication_funders.identifier IS 'Stores the full resolvable URL (e.g., https://ror.org/01ej9dk98)';
COMMENT ON COLUMN publication_funders.identifier_type IS 'Stores the identifier type (e.g., ror, fundref, isni)';

-- Optional: Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_publication_creators_identifier_type 
ON publication_creators(identifier_type);

CREATE INDEX IF NOT EXISTS idx_publication_funders_identifier_type 
ON publication_funders(identifier_type);

-- Update the alembic_version table to mark these migrations as completed
-- This prevents Flask-Migrate from trying to apply them again
-- Replace with your actual migration revision IDs if different
UPDATE alembic_version 
SET version_num = 'df906eb48852' 
WHERE version_num = '7faa322ba678';

-- If the above doesn't work (no matching row), insert the latest revision
INSERT INTO alembic_version (version_num) 
SELECT 'df906eb48852' 
WHERE NOT EXISTS (
    SELECT 1 FROM alembic_version WHERE version_num = 'df906eb48852'
);

-- Verify the changes
DO $$
BEGIN
    RAISE NOTICE 'Checking publication_creators table...';
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'publication_creators' 
        AND column_name = 'identifier_type'
    ) THEN
        RAISE NOTICE '✓ identifier_type column added to publication_creators';
    ELSE
        RAISE WARNING '✗ identifier_type column NOT found in publication_creators';
    END IF;

    RAISE NOTICE 'Checking publication_funders table...';
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'publication_funders' 
        AND column_name = 'identifier'
    ) THEN
        RAISE NOTICE '✓ identifier column added to publication_funders';
    ELSE
        RAISE WARNING '✗ identifier column NOT found in publication_funders';
    END IF;

    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'publication_funders' 
        AND column_name = 'identifier_type'
    ) THEN
        RAISE NOTICE '✓ identifier_type column added to publication_funders';
    ELSE
        RAISE WARNING '✗ identifier_type column NOT found in publication_funders';
    END IF;
END $$;

-- Show the current table structures
\d publication_creators
\d publication_funders

-- Commit the transaction
COMMIT;

-- Display success message
SELECT 'Successfully added identifier columns to publication_creators and publication_funders tables' AS status;