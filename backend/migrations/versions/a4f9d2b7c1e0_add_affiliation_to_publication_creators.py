"""Add affiliation column to publication_creators

Revision ID: a4f9d2b7c1e0
Revises: 8bc3acb9b6f2
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa


revision = 'a4f9d2b7c1e0'
down_revision = '8bc3acb9b6f2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('publication_creators', schema=None) as batch_op:
        batch_op.add_column(sa.Column('affiliation', sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table('publication_creators', schema=None) as batch_op:
        batch_op.drop_column('affiliation')
