"""add rrid to publication_organizations

Revision ID: 43bbf20ef475
Revises: 96caa4925d61
Create Date: 2026-04-08 11:23:29.296839

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43bbf20ef475'
down_revision = '96caa4925d61'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('publication_organizations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rrid', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('publication_organizations', schema=None) as batch_op:
        batch_op.drop_column('rrid')
