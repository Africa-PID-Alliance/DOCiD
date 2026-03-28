"""add ui_base_url to harvest_sources

Revision ID: 96caa4925d61
Revises: d34c9d15387d
Create Date: 2026-03-28 11:11:40.046717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96caa4925d61'
down_revision = 'd34c9d15387d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('harvest_sources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ui_base_url', sa.String(length=500), nullable=True))

    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.alter_column('doi', existing_type=sa.String(length=50), nullable=True)


def downgrade():
    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.alter_column('doi', existing_type=sa.String(length=50), nullable=False)

    with op.batch_alter_table('harvest_sources', schema=None) as batch_op:
        batch_op.drop_column('ui_base_url')
