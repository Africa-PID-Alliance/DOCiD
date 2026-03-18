"""add harvest sources and field mappings tables

Revision ID: d34c9d15387d
Revises: 2c4c45bded5d
Create Date: 2026-03-18 21:10:25.082130

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd34c9d15387d'
down_revision = '2c4c45bded5d'
branch_labels = None
depends_on = None


def upgrade():
    # Create harvest_sources table
    op.create_table('harvest_sources',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('base_url', sa.String(length=500), nullable=False),
    sa.Column('dspace_version', sa.String(length=20), nullable=True),
    sa.Column('api_type', sa.String(length=20), nullable=False),
    sa.Column('auth_required', sa.Boolean(), nullable=True),
    sa.Column('encrypted_username', sa.Text(), nullable=True),
    sa.Column('encrypted_password', sa.Text(), nullable=True),
    sa.Column('owner_name', sa.String(length=255), nullable=False),
    sa.Column('harvest_frequency', sa.String(length=20), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('last_harvested_at', sa.DateTime(), nullable=True),
    sa.Column('total_items_synced', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    # Create harvest_source_field_mappings table
    op.create_table('harvest_source_field_mappings',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('harvest_source_id', sa.Integer(), nullable=False),
    sa.Column('docid_field', sa.String(length=100), nullable=False),
    sa.Column('source_field', sa.String(length=200), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['harvest_source_id'], ['harvest_sources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('harvest_source_id', 'docid_field', 'source_field', name='uq_source_docid_field_mapping')
    )
    with op.batch_alter_table('harvest_source_field_mappings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_harvest_source_field_mappings_harvest_source_id'), ['harvest_source_id'], unique=False)


def downgrade():
    with op.batch_alter_table('harvest_source_field_mappings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_harvest_source_field_mappings_harvest_source_id'))

    op.drop_table('harvest_source_field_mappings')
    op.drop_table('harvest_sources')
