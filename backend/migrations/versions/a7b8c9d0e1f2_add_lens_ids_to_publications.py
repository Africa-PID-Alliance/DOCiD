"""Add lens_patent_id and lens_scholar_id columns to publications.

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-06-10 10:01:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'a7b8c9d0e1f2'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('publications', sa.Column('lens_patent_id', sa.String(50), nullable=True))
    op.add_column('publications', sa.Column('lens_scholar_id', sa.String(50), nullable=True))
    op.create_index('ix_publications_lens_patent_id', 'publications', ['lens_patent_id'])
    op.create_index('ix_publications_lens_scholar_id', 'publications', ['lens_scholar_id'])


def downgrade():
    op.drop_index('ix_publications_lens_scholar_id', table_name='publications')
    op.drop_index('ix_publications_lens_patent_id', table_name='publications')
    op.drop_column('publications', 'lens_scholar_id')
    op.drop_column('publications', 'lens_patent_id')
