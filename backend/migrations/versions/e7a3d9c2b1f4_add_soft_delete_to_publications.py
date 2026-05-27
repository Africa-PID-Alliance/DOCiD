"""Add soft-delete columns (deleted_at, deleted_by, deletion_reason) to publications.

Keeps minted DOCiD handles resolving after retirement by tombstoning the row
instead of removing it.

Revision ID: e7a3d9c2b1f4
Revises: d2f4e1a8b6c7
Create Date: 2026-05-27 21:15:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'e7a3d9c2b1f4'
down_revision = 'd2f4e1a8b6c7'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_cols = {c['name'] for c in insp.get_columns('publications')}
    existing_indexes = {ix['name'] for ix in insp.get_indexes('publications')}

    if 'deleted_at' not in existing_cols:
        op.add_column('publications', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    if 'deleted_by' not in existing_cols:
        op.add_column(
            'publications',
            sa.Column('deleted_by', sa.Integer(), sa.ForeignKey('user_accounts.user_id'), nullable=True),
        )
    if 'deletion_reason' not in existing_cols:
        op.add_column('publications', sa.Column('deletion_reason', sa.Text(), nullable=True))

    if 'ix_publications_deleted_at' not in existing_indexes:
        op.create_index('ix_publications_deleted_at', 'publications', ['deleted_at'])


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_indexes = {ix['name'] for ix in insp.get_indexes('publications')}
    existing_cols = {c['name'] for c in insp.get_columns('publications')}

    if 'ix_publications_deleted_at' in existing_indexes:
        op.drop_index('ix_publications_deleted_at', table_name='publications')
    if 'deletion_reason' in existing_cols:
        op.drop_column('publications', 'deletion_reason')
    if 'deleted_by' in existing_cols:
        op.drop_column('publications', 'deleted_by')
    if 'deleted_at' in existing_cols:
        op.drop_column('publications', 'deleted_at')
