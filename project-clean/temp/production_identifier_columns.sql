-- =====================================================================
-- Production SQL Script to Add Identifier Columns
-- =====================================================================
-- This script adds identifier and identifier_type columns to:
-- 1. publication_creators
-- 2. publication_funders  
-- 3. publication_organizations
--
-- Run this on production server as:
-- psql -U your_prod_user -d your_prod_db -f production_identifier_columns.sql
-- =====================================================================

-- Start transaction for safety
BEGIN;

-- =====================================================================
-- 1. PUBLICATION_CREATORS - Add identifier columns
-- =====================================================================
DO $$
BEGIN
    -- Add identifier_type column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'publication_creators' 
        AND column_name = 'identifier_type'
    ) THEN
        ALTER TABLE publication_creators 
        ADD COLUMN identifier_type VARCHAR(50);
        
        COMMENT ON COLUMN publication_creators.identifier_type 
        IS 'Stores the identifier type (e.g., orcid, isni, viaf)';
        
        RAISE NOTICE '✓ Added identifier_type column to publication_creators';
    ELSE
        RAISE NOTICE '⚠ identifier_type column already exists in publication_creators';
    END IF;
    
    -- Modify identifier column to support longer URLs if needed
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'publication_creators' 
        AND column_name = 'identifier'
        AND character_maximum_length < 500
    ) THEN
        ALTER TABLE publication_creators 
        ALTER COLUMN identifier TYPE VARCHAR(500);
        
        COMMENT ON COLUMN publication_creators.identifier 
        IS 'Stores the full resolvable URL (e.g., https://orcid.org/0000-0002-1981-4157)';
        
        RAISE NOTICE '✓ Updated identifier column size in publication_creators';
    ELSE
        RAISE NOTICE '⚠ identifier column already correct size in publication_creators';
    END IF;
END $$;

-- =====================================================================
-- 2. PUBLICATION_FUNDERS - Add identifier columns
-- =====================================================================
DO $$
BEGIN
    -- Add identifier column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'publication_funders' 
        AND column_name = 'identifier'
    ) THEN
        ALTER TABLE publication_funders 
        ADD COLUMN identifier VARCHAR(500);
        
        COMMENT ON COLUMN publication_funders.identifier 
        IS 'Stores the full resolvable URL (e.g., https://ror.org/01bj3aw27)';
        
        RAISE NOTICE '✓ Added identifier column to publication_funders';
    ELSE
        RAISE NOTICE '⚠ identifier column already exists in publication_funders';
    END IF;
    
    -- Add identifier_type column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'publication_funders' 
        AND column_name = 'identifier_type'
    ) THEN
        ALTER TABLE publication_funders 
        ADD COLUMN identifier_type VARCHAR(50);
        
        COMMENT ON COLUMN publication_funders.identifier_type 
        IS 'Stores the identifier type (e.g., ror, fundref, isni)';
        
        RAISE NOTICE '✓ Added identifier_type column to publication_funders';
    ELSE
        RAISE NOTICE '⚠ identifier_type column already exists in publication_funders';
    END IF;
END $$;

-- =====================================================================
-- 3. PUBLICATION_ORGANIZATIONS - Add identifier columns
-- =====================================================================
DO $$
BEGIN
    -- Add identifier column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'publication_organizations' 
        AND column_name = 'identifier'
    ) THEN
        ALTER TABLE publication_organizations 
        ADD COLUMN identifier VARCHAR(500);
        
        COMMENT ON COLUMN publication_organizations.identifier 
        IS 'Stores the full resolvable URL (e.g., https://ror.org/02nr0ka47)';
        
        RAISE NOTICE '✓ Added identifier column to publication_organizations';
    ELSE
        RAISE NOTICE '⚠ identifier column already exists in publication_organizations';
    END IF;
    
    -- Add identifier_type column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'publication_organizations' 
        AND column_name = 'identifier_type'
    ) THEN
        ALTER TABLE publication_organizations 
        ADD COLUMN identifier_type VARCHAR(50);
        
        COMMENT ON COLUMN publication_organizations.identifier_type 
        IS 'Stores the identifier type (e.g., ror, grid, isni)';
        
        RAISE NOTICE '✓ Added identifier_type column to publication_organizations';
    ELSE
        RAISE NOTICE '⚠ identifier_type column already exists in publication_organizations';
    END IF;
END $$;

-- =====================================================================
-- 4. CREATE INDEXES for better query performance
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_publication_creators_identifier_type 
ON publication_creators(identifier_type) 
WHERE identifier_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_publication_funders_identifier_type 
ON publication_funders(identifier_type)
WHERE identifier_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_publication_organizations_identifier_type 
ON publication_organizations(identifier_type)
WHERE identifier_type IS NOT NULL;

-- =====================================================================
-- 5. UPDATE ALEMBIC VERSION (to prevent migration conflicts)
-- =====================================================================
-- Update to latest migration version to prevent Flask-Migrate conflicts
-- Replace with your actual latest migration ID if different
INSERT INTO alembic_version (version_num) 
VALUES ('9d6930747dbb')
ON CONFLICT (version_num) DO NOTHING;

-- =====================================================================
-- 6. VERIFICATION QUERIES
-- =====================================================================
-- Check the results
SELECT 
    '=== VERIFICATION RESULTS ===' AS info;

-- Check publication_creators
SELECT 
    'publication_creators' AS table_name,
    COUNT(*) FILTER (WHERE column_name = 'identifier') AS has_identifier,
    COUNT(*) FILTER (WHERE column_name = 'identifier_type') AS has_identifier_type,
    MAX(character_maximum_length) FILTER (WHERE column_name = 'identifier') AS identifier_max_length
FROM 
    information_schema.columns
WHERE 
    table_name = 'publication_creators'
    AND column_name IN ('identifier', 'identifier_type');

-- Check publication_funders
SELECT 
    'publication_funders' AS table_name,
    COUNT(*) FILTER (WHERE column_name = 'identifier') AS has_identifier,
    COUNT(*) FILTER (WHERE column_name = 'identifier_type') AS has_identifier_type,
    MAX(character_maximum_length) FILTER (WHERE column_name = 'identifier') AS identifier_max_length
FROM 
    information_schema.columns
WHERE 
    table_name = 'publication_funders'
    AND column_name IN ('identifier', 'identifier_type');

-- Check publication_organizations
SELECT 
    'publication_organizations' AS table_name,
    COUNT(*) FILTER (WHERE column_name = 'identifier') AS has_identifier,
    COUNT(*) FILTER (WHERE column_name = 'identifier_type') AS has_identifier_type,
    MAX(character_maximum_length) FILTER (WHERE column_name = 'identifier') AS identifier_max_length
FROM 
    information_schema.columns
WHERE 
    table_name = 'publication_organizations'
    AND column_name IN ('identifier', 'identifier_type');

-- =====================================================================
-- 7. DATA MIGRATION (Optional - Convert existing ORCID data)
-- =====================================================================
-- If you have existing data where identifier contains 'orcid' instead of URLs
-- Uncomment and run this section:

/*
-- Update creators where identifier contains 'orcid' text
UPDATE publication_creators 
SET 
    identifier_type = 'orcid',
    identifier = NULL
WHERE 
    identifier = 'orcid' 
    AND identifier_type IS NULL;

-- If you have ORCID IDs stored somewhere else, you can update them here
-- Example: If ORCID IDs are in a separate column or format
*/

-- =====================================================================
-- 8. SAMPLE DATA CHECK
-- =====================================================================
SELECT 
    '=== SAMPLE DATA CHECK ===' AS info;

-- Show sample of any existing identifier data
SELECT 
    'Creators with identifiers:' AS info,
    COUNT(*) AS count
FROM publication_creators 
WHERE identifier IS NOT NULL OR identifier_type IS NOT NULL

UNION ALL

SELECT 
    'Funders with identifiers:' AS info,
    COUNT(*) AS count
FROM publication_funders 
WHERE identifier IS NOT NULL OR identifier_type IS NOT NULL

UNION ALL

SELECT 
    'Organizations with identifiers:' AS info,
    COUNT(*) AS count
FROM publication_organizations 
WHERE identifier IS NOT NULL OR identifier_type IS NOT NULL;

-- =====================================================================
-- COMMIT or ROLLBACK
-- =====================================================================
-- If everything looks good, the transaction will commit
-- If there's an error, it will automatically rollback

COMMIT;

-- =====================================================================
-- POST-DEPLOYMENT VERIFICATION
-- =====================================================================
-- After deployment, run these queries to verify:

/*
-- Check column existence
\d publication_creators
\d publication_funders
\d publication_organizations

-- Test with sample data (adjust IDs as needed)
SELECT id, family_name, given_name, identifier, identifier_type 
FROM publication_creators 
WHERE publication_id IN (SELECT id FROM publications ORDER BY id DESC LIMIT 5);

SELECT id, name, identifier, identifier_type 
FROM publication_funders 
WHERE publication_id IN (SELECT id FROM publications ORDER BY id DESC LIMIT 5);

SELECT id, name, identifier, identifier_type 
FROM publication_organizations 
WHERE publication_id IN (SELECT id FROM publications ORDER BY id DESC LIMIT 5);
*/

-- =====================================================================
-- SUCCESS MESSAGE
-- =====================================================================
SELECT 
    '✅ IDENTIFIER COLUMNS SUCCESSFULLY ADDED!' AS status,
    'All tables now support persistent identifiers' AS message;