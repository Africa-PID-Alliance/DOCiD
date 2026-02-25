"""Add ringgold_institutions table for local African institution data

Revision ID: add_ringgold_institutions
Revises: c85e997ed2ef
Create Date: 2024-12-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_ringgold_institutions'
down_revision = 'c85e997ed2ef'
branch_labels = None
depends_on = None


def upgrade():
    # Create the ringgold_institutions table
    op.create_table('ringgold_institutions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ringgold_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=200), nullable=True),
        sa.Column('post_code', sa.String(length=50), nullable=True),
        sa.Column('administrative_area_level_1', sa.String(length=200), nullable=True),
        sa.Column('administrative_area_level_2', sa.String(length=200), nullable=True),
        sa.Column('administrative_area_level_3', sa.String(length=200), nullable=True),
        sa.Column('isni', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for fast lookups
    with op.batch_alter_table('ringgold_institutions', schema=None) as batch_op:
        batch_op.create_index('ix_ringgold_institutions_ringgold_id', ['ringgold_id'], unique=True)
        batch_op.create_index('ix_ringgold_institutions_name', ['name'], unique=False)
        batch_op.create_index('ix_ringgold_institutions_country', ['country'], unique=False)
        batch_op.create_index('ix_ringgold_institutions_isni', ['isni'], unique=False)


def downgrade():
    with op.batch_alter_table('ringgold_institutions', schema=None) as batch_op:
        batch_op.drop_index('ix_ringgold_institutions_isni')
        batch_op.drop_index('ix_ringgold_institutions_country')
        batch_op.drop_index('ix_ringgold_institutions_name')
        batch_op.drop_index('ix_ringgold_institutions_ringgold_id')

    op.drop_table('ringgold_institutions')
