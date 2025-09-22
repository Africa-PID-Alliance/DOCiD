-- SQL Script to check the current state of identifier columns
-- Usage: psql -U your_username -d your_database -f check_identifier_columns.sql

-- Check publication_creators table structure
SELECT 
    '=== PUBLICATION_CREATORS TABLE ===' AS info;

SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM 
    information_schema.columns
WHERE 
    table_name = 'publication_creators'
    AND column_name IN ('identifier', 'identifier_type')
ORDER BY 
    ordinal_position;

-- Check publication_funders table structure
SELECT 
    '=== PUBLICATION_FUNDERS TABLE ===' AS info;

SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM 
    information_schema.columns
WHERE 
    table_name = 'publication_funders'
    AND column_name IN ('identifier', 'identifier_type')
ORDER BY 
    ordinal_position;

-- Check if there's any data in these columns
SELECT 
    '=== DATA CHECK ===' AS info;

SELECT 
    'publication_creators' AS table_name,
    COUNT(*) AS total_records,
    COUNT(identifier) AS records_with_identifier,
    COUNT(identifier_type) AS records_with_identifier_type
FROM 
    publication_creators

UNION ALL

SELECT 
    'publication_funders' AS table_name,
    COUNT(*) AS total_records,
    COUNT(identifier) AS records_with_identifier,
    COUNT(identifier_type) AS records_with_identifier_type
FROM 
    publication_funders;

-- Show sample data from publication_creators
SELECT 
    '=== SAMPLE DATA: PUBLICATION_CREATORS ===' AS info;

SELECT 
    id,
    publication_id,
    family_name,
    given_name,
    identifier,
    identifier_type
FROM 
    publication_creators
WHERE 
    identifier IS NOT NULL 
    OR identifier_type IS NOT NULL
ORDER BY 
    id DESC
LIMIT 5;

-- Show sample data from publication_funders
SELECT 
    '=== SAMPLE DATA: PUBLICATION_FUNDERS ===' AS info;

SELECT 
    id,
    publication_id,
    name,
    identifier,
    identifier_type
FROM 
    publication_funders
WHERE 
    identifier IS NOT NULL 
    OR identifier_type IS NOT NULL
ORDER BY 
    id DESC
LIMIT 5;

-- Check current alembic version
SELECT 
    '=== ALEMBIC MIGRATION VERSION ===' AS info;

SELECT 
    version_num AS current_migration_version
FROM 
    alembic_version;