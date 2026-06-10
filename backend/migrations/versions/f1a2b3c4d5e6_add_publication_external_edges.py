"""Add publication_external_edges table for typed citation/patent edges.

Revision ID: f1a2b3c4d5e6
Revises: e7a3d9c2b1f4
Create Date: 2026-06-10 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'f1a2b3c4d5e6'
down_revision = 'e7a3d9c2b1f4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'publication_external_edges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('publication_id', sa.Integer(),
                  sa.ForeignKey('publications.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('object_id_kind', sa.String(20), nullable=False),
        sa.Column('object_id', sa.String(255), nullable=False),
        sa.Column('object_label', sa.String(500), nullable=True),
        sa.Column('relation', sa.String(40), nullable=False),
        sa.Column('source_name', sa.String(50), nullable=False),
        sa.Column('confidence', sa.String(20), nullable=True),
        sa.Column('raw_metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint(
        'uq_publication_external_edge',
        'publication_external_edges',
        ['publication_id', 'relation', 'object_id_kind', 'object_id', 'source_name'],
    )
    op.create_index(
        'ix_publication_external_edges_object',
        'publication_external_edges',
        ['object_id_kind', 'object_id'],
    )
    op.create_index(
        'ix_publication_external_edges_relation',
        'publication_external_edges',
        ['publication_id', 'relation'],
    )


def downgrade():
    op.drop_index('ix_publication_external_edges_relation', table_name='publication_external_edges')
    op.drop_index('ix_publication_external_edges_object', table_name='publication_external_edges')
    op.drop_constraint('uq_publication_external_edge', 'publication_external_edges', type_='unique')
    op.drop_table('publication_external_edges')
