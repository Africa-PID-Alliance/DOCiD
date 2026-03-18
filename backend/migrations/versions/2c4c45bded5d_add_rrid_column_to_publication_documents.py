"""Add rrid column to publication_documents

Revision ID: 2c4c45bded5d
Revises: 633ee4b7df07
Create Date: 2026-03-18 20:40:43.328184

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c4c45bded5d'
down_revision = '633ee4b7df07'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('publication_documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rrid', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('publication_documents', schema=None) as batch_op:
        batch_op.drop_column('rrid')
