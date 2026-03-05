"""Add collection_name column to publications

Revision ID: a3f1c8d52e91
Revises: c4a7e2b19f03
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f1c8d52e91'
down_revision = 'c4a7e2b19f03'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('publications', sa.Column('collection_name', sa.String(500), nullable=True))


def downgrade():
    op.drop_column('publications', 'collection_name')
