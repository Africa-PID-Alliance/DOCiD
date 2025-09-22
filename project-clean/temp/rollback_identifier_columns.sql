-- SQL Script to rollback/remove identifier columns from publication_creators and publication_funders tables
-- Use this script if you need to undo the changes
-- Usage: psql -U your_username -d your_database -f rollback_identifier_columns.sql

-- Start transaction
BEGIN;

-- Remove identifier_type column from publication_creators table
ALTER TABLE publication_creators 
DROP COLUMN IF EXISTS identifier_type;

-- Revert identifier column in publication_creators back to VARCHAR(255)
ALTER TABLE publication_creators 
ALTER COLUMN identifier TYPE VARCHAR(255);

-- Remove identifier and identifier_type columns from publication_funders table
ALTER TABLE publication_funders 
DROP COLUMN IF EXISTS identifier;

ALTER TABLE publication_funders 
DROP COLUMN IF EXISTS identifier_type;

-- Remove indexes if they exist
DROP INDEX IF EXISTS idx_publication_creators_identifier_type;
DROP INDEX IF EXISTS idx_publication_funders_identifier_type;

-- Revert the alembic_version table if needed
UPDATE alembic_version 
SET version_num = '7faa322ba678' 
WHERE version_num = 'df906eb48852';

-- Verify the rollback
DO $$
BEGIN
    RAISE NOTICE 'Checking rollback status...';
    
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'publication_creators' 
        AND column_name = 'identifier_type'
    ) THEN
        RAISE NOTICE '✓ identifier_type column removed from publication_creators';
    ELSE
        RAISE WARNING '✗ identifier_type column still exists in publication_creators';
    END IF;

    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'publication_funders' 
        AND column_name = 'identifier'
    ) THEN
        RAISE NOTICE '✓ identifier column removed from publication_funders';
    ELSE
        RAISE WARNING '✗ identifier column still exists in publication_funders';
    END IF;

    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'publication_funders' 
        AND column_name = 'identifier_type'
    ) THEN
        RAISE NOTICE '✓ identifier_type column removed from publication_funders';
    ELSE
        RAISE WARNING '✗ identifier_type column still exists in publication_funders';
    END IF;
END $$;

-- Show the current table structures
\d publication_creators
\d publication_funders

-- Commit the transaction
COMMIT;

-- Display success message
SELECT 'Successfully rolled back identifier columns from publication_creators and publication_funders tables' AS status;