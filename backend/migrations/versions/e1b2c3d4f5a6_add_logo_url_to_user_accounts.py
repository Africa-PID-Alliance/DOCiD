"""add logo_url to user_accounts

Revision ID: e1b2c3d4f5a6
Revises: a4f9d2b7c1e0
Create Date: 2026-04-27 18:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1b2c3d4f5a6'
down_revision = 'a4f9d2b7c1e0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_accounts', sa.Column('logo_url', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('user_accounts', 'logo_url')
