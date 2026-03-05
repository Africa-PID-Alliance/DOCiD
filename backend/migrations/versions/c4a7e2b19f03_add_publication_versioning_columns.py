"""Add publication versioning columns (parent_id, version_number)

Revision ID: c4a7e2b19f03
Revises: b8c3a1f5d720
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4a7e2b19f03'
down_revision = 'b8c3a1f5d720'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('publications', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('publications', sa.Column('version_number', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_publications_parent_id',
        'publications', 'publications',
        ['parent_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_publications_parent_id', 'publications', ['parent_id'])


def downgrade():
    op.drop_index('ix_publications_parent_id', table_name='publications')
    op.drop_constraint('fk_publications_parent_id', 'publications', type_='foreignkey')
    op.drop_column('publications', 'version_number')
    op.drop_column('publications', 'parent_id')
