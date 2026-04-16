"""Add DataCite resource types for Figshare/DSpace/OJS integrations

Revision ID: b8c3a1f5d720
Revises: 4e67049fd9a2
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8c3a1f5d720'
down_revision = '30fd2740d9c1'
branch_labels = None
depends_on = None


# DataCite resource types were added and later removed.
# This migration is now a no-op but kept to preserve the Alembic revision chain.

def upgrade():
    pass


def downgrade():
    pass
