-- Migration: Add handle_identifier fields to PublicationFiles and PublicationDocuments
-- Date: 2025-08-01
-- Description: Adds support for storing both Handle identifiers (for CORDRA) and external identifiers (DOIs from DataCite/Crossref)

-- Add columns to publications_files table
ALTER TABLE publications_files 
ADD COLUMN IF NOT EXISTS handle_identifier VARCHAR(100),
ADD COLUMN IF NOT EXISTS external_identifier VARCHAR(100),
ADD COLUMN IF NOT EXISTS external_identifier_type VARCHAR(50);

-- Add columns to publication_documents table
ALTER TABLE publication_documents 
ADD COLUMN IF NOT EXISTS handle_identifier VARCHAR(100),
ADD COLUMN IF NOT EXISTS external_identifier VARCHAR(100),
ADD COLUMN IF NOT EXISTS external_identifier_type VARCHAR(50);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_publications_files_handle_identifier ON publications_files(handle_identifier);
CREATE INDEX IF NOT EXISTS idx_publications_files_external_identifier ON publications_files(external_identifier);
CREATE INDEX IF NOT EXISTS idx_publication_documents_handle_identifier ON publication_documents(handle_identifier);
CREATE INDEX IF NOT EXISTS idx_publication_documents_external_identifier ON publication_documents(external_identifier);

-- Add comments to describe the columns
COMMENT ON COLUMN publications_files.handle_identifier IS 'Handle identifier for CORDRA integration';
COMMENT ON COLUMN publications_files.external_identifier IS 'External identifier (e.g., DOI from DataCite or Crossref)';
COMMENT ON COLUMN publications_files.external_identifier_type IS 'Type of external identifier (e.g., DOI)';

COMMENT ON COLUMN publication_documents.handle_identifier IS 'Handle identifier for CORDRA integration';
COMMENT ON COLUMN publication_documents.external_identifier IS 'External identifier (e.g., DOI from DataCite or Crossref)';
COMMENT ON COLUMN publication_documents.external_identifier_type IS 'Type of external identifier (e.g., DOI)';