"""add last_checked_at to harvest_source_collections

The every-minute check asks DSpace for records changed since the last
successful pass over a collection; this column records when that pass started.

Revision ID: b84d1e0c27f6
Revises: f2a9c4e71b30
Create Date: 2026-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b84d1e0c27f6'
down_revision = 'f2a9c4e71b30'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('harvest_source_collections', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_checked_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('harvest_source_collections', schema=None) as batch_op:
        batch_op.drop_column('last_checked_at')
