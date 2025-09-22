"""Add handle_identifier fields to PublicationFiles and PublicationDocuments

Revision ID: add_handle_identifiers
Revises: 
Create Date: 2025-08-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_handle_identifiers'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add fields to publications_files table
    op.add_column('publications_files', sa.Column('handle_identifier', sa.String(100), nullable=True))
    op.add_column('publications_files', sa.Column('external_identifier', sa.String(100), nullable=True))
    op.add_column('publications_files', sa.Column('external_identifier_type', sa.String(50), nullable=True))
    
    # Add fields to publication_documents table
    op.add_column('publication_documents', sa.Column('handle_identifier', sa.String(100), nullable=True))
    op.add_column('publication_documents', sa.Column('external_identifier', sa.String(100), nullable=True))
    op.add_column('publication_documents', sa.Column('external_identifier_type', sa.String(50), nullable=True))


def downgrade():
    # Remove fields from publication_documents table
    op.drop_column('publication_documents', 'external_identifier_type')
    op.drop_column('publication_documents', 'external_identifier')
    op.drop_column('publication_documents', 'handle_identifier')
    
    # Remove fields from publications_files table
    op.drop_column('publications_files', 'external_identifier_type')
    op.drop_column('publications_files', 'external_identifier')
    op.drop_column('publications_files', 'handle_identifier')